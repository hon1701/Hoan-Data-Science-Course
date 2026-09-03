"""Leakage-safe model training for the ECCC-LITE fraud project.

Model selection is performed on the validation split only.  The test split is
deliberately not read by this module.
"""

from __future__ import annotations

import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.a1_utils import (
    ID_COLUMN,
    PROCESSED_COLUMNS,
    RANDOM_STATE,
    TARGET,
    atomic_write_csv,
    atomic_write_json,
)

MODEL_FEATURE_COLUMNS = ["Time", *[f"V{i}" for i in range(1, 29)], "LogAmount"]
MODEL_FAMILIES = ("dummy", "logistic", "random_forest")


def load_split(root: Path, name: str) -> pd.DataFrame:
    """Load one prepared split and enforce the A.1 handoff contract."""

    if name not in {"train", "validation", "test"}:
        raise ValueError(f"Tên split không hợp lệ: {name}")
    path = Path(root) / "data" / "processed" / f"{name}.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Thiếu {path}. Hãy chạy 01_data_eda.ipynb trước.")
    frame = pd.read_csv(path)
    if list(frame.columns) != PROCESSED_COLUMNS:
        raise AssertionError(f"Schema của {name}.csv không đúng contract A.1.")
    if frame[ID_COLUMN].duplicated().any():
        raise AssertionError(f"source_row bị trùng trong {name}.csv.")
    return frame


def split_xy(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return the fixed model feature set and target without leakage columns."""

    missing = [column for column in MODEL_FEATURE_COLUMNS if column not in frame.columns]
    if missing:
        raise AssertionError(f"Thiếu feature: {missing}")
    features = frame.loc[:, MODEL_FEATURE_COLUMNS].copy()
    if set(features.columns) != set(MODEL_FEATURE_COLUMNS):
        raise AssertionError("Sai feature set dùng cho modeling.")
    if {TARGET, ID_COLUMN, "Amount"} & set(features.columns):
        raise AssertionError("Class/source_row/Amount không được dùng trong feature cốt lõi.")
    target = frame[TARGET].astype(int).copy()
    return features, target


def positive_class_scores(model: Any, features: pd.DataFrame) -> np.ndarray:
    """Return predict_proba for Class=1 after checking the class order."""

    classes = np.asarray(model.classes_)
    locations = np.flatnonzero(classes == 1)
    if locations.size != 1:
        raise AssertionError(f"Không xác định được cột xác suất Class=1: {classes}")
    scores = np.asarray(model.predict_proba(features)[:, int(locations[0])], dtype=float)
    return scores


def validate_scores(
    scores: np.ndarray,
    expected_rows: int,
    *,
    min_unique: int | None = None,
) -> np.ndarray:
    """Validate score length, finiteness, range and optional score diversity."""

    values = np.asarray(scores, dtype=float)
    if values.ndim != 1 or len(values) != expected_rows:
        raise AssertionError(f"Score sai shape: {values.shape}; expected={expected_rows}")
    if not np.isfinite(values).all():
        raise AssertionError("Score có NaN hoặc infinity.")
    if values.min() < 0.0 or values.max() > 1.0:
        raise AssertionError("Score phải nằm trong [0, 1].")
    if min_unique is not None and np.unique(values).size < min_unique:
        raise AssertionError("Score có quá ít giá trị khác nhau; có thể đã xuất nhầm nhãn.")
    return values


def _atomic_joblib_dump(model: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    joblib.dump(model, temporary)
    os.replace(temporary, path)


def _candidate_record(
    *,
    family: str,
    candidate: str,
    parameters: dict[str, Any],
    y_true: pd.Series,
    scores: np.ndarray,
) -> dict[str, Any]:
    labels = (scores >= 0.5).astype(int)
    return {
        "family": family,
        "candidate": candidate,
        "parameters": json.dumps(parameters, ensure_ascii=False, sort_keys=True),
        "validation_ap": average_precision_score(y_true, scores),
        "validation_roc_auc": roc_auc_score(y_true, scores),
        "validation_accuracy_at_0_5": accuracy_score(y_true, labels),
    }


def train_models(root: Path, *, random_state: int = RANDOM_STATE) -> dict[str, Any]:
    """Fit controlled candidates, select on validation AP and persist artifacts."""

    root = Path(root).resolve()
    output_tables = root / "outputs" / "tables"
    output_models = root / "outputs" / "models"
    output_tables.mkdir(parents=True, exist_ok=True)
    output_models.mkdir(parents=True, exist_ok=True)

    train = load_split(root, "train")
    validation = load_split(root, "validation")
    if set(train[ID_COLUMN]) & set(validation[ID_COLUMN]):
        raise AssertionError("Train và validation giao nhau.")

    x_train, y_train = split_xy(train)
    x_validation, y_validation = split_xy(validation)
    baseline_ap = float(y_validation.mean())

    records: list[dict[str, Any]] = []
    fitted: dict[str, list[tuple[str, Any, np.ndarray, dict[str, Any], float]]] = {
        family: [] for family in MODEL_FAMILIES
    }

    dummy_specs = [
        ("most_frequent", {"strategy": "most_frequent"}),
        ("stratified", {"strategy": "stratified", "random_state": random_state}),
    ]
    for candidate, parameters in dummy_specs:
        model = DummyClassifier(**parameters)
        model.fit(x_train, y_train)
        scores = validate_scores(
            positive_class_scores(model, x_validation),
            len(validation),
        )
        record = _candidate_record(
            family="dummy",
            candidate=candidate,
            parameters=parameters,
            y_true=y_validation,
            scores=scores,
        )
        records.append(record)
        fitted["dummy"].append((candidate, model, scores, parameters, record["validation_ap"]))

    logistic_specs = [
        ("standard", {"C": 1.0, "class_weight": None}),
        ("balanced", {"C": 1.0, "class_weight": "balanced"}),
    ]
    for candidate, parameters in logistic_specs:
        model = Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        C=parameters["C"],
                        class_weight=parameters["class_weight"],
                        max_iter=2_000,
                        solver="lbfgs",
                        random_state=random_state,
                    ),
                ),
            ]
        )
        model.fit(x_train, y_train)
        scores = validate_scores(
            positive_class_scores(model, x_validation),
            len(validation),
            min_unique=11,
        )
        record = _candidate_record(
            family="logistic",
            candidate=candidate,
            parameters=parameters,
            y_true=y_validation,
            scores=scores,
        )
        records.append(record)
        fitted["logistic"].append((candidate, model, scores, parameters, record["validation_ap"]))

    forest_specs = [
        (
            "standard",
            {
                "n_estimators": 160,
                "max_depth": None,
                "min_samples_leaf": 2,
                "class_weight": None,
            },
        ),
        (
            "balanced",
            {
                "n_estimators": 160,
                "max_depth": None,
                "min_samples_leaf": 2,
                "class_weight": "balanced_subsample",
            },
        ),
    ]
    for candidate, parameters in forest_specs:
        model = RandomForestClassifier(
            **parameters,
            max_features="sqrt",
            n_jobs=-1,
            random_state=random_state,
        )
        model.fit(x_train, y_train)
        scores = validate_scores(
            positive_class_scores(model, x_validation),
            len(validation),
            min_unique=11,
        )
        record = _candidate_record(
            family="random_forest",
            candidate=candidate,
            parameters=parameters,
            y_true=y_validation,
            scores=scores,
        )
        records.append(record)
        fitted["random_forest"].append(
            (candidate, model, scores, parameters, record["validation_ap"])
        )

    candidates = pd.DataFrame(records).sort_values(
        ["family", "validation_ap"], ascending=[True, False]
    )
    atomic_write_csv(candidates, output_tables / "model_candidates.csv")

    best: dict[str, tuple[str, Any, np.ndarray, dict[str, Any], float]] = {}
    for family in MODEL_FAMILIES:
        if family == "dummy":
            # Keep most_frequent only as the high-accuracy/zero-recall illustration.
            # The score-bearing baseline must be stratified as specified by the report.
            best[family] = next(item for item in fitted[family] if item[0] == "stratified")
        else:
            best[family] = max(fitted[family], key=lambda item: item[4])
        _atomic_joblib_dump(best[family][1], output_models / f"{family}.joblib")

    logistic_ap = float(best["logistic"][4])
    forest_ap = float(best["random_forest"][4])
    difference = abs(logistic_ap - forest_ap)
    if difference < 0.01:
        selected_family = "logistic"
        selection_reason = (
            "Chênh lệch AP validation dưới 0,01; chọn Logistic Regression theo tie-break "
            "đã chốt vì đơn giản và dễ giải thích hơn."
        )
    elif logistic_ap > forest_ap:
        selected_family = "logistic"
        selection_reason = "Logistic Regression có AP validation cao hơn Random Forest."
    else:
        selected_family = "random_forest"
        selection_reason = "Random Forest có AP validation cao hơn Logistic Regression."

    selected = best[selected_family]
    _atomic_joblib_dump(selected[1], output_models / "selected_model.joblib")

    validation_scores = pd.DataFrame(
        {
            ID_COLUMN: validation[ID_COLUMN].astype(int),
            "y_true": y_validation,
            "score_dummy": best["dummy"][2],
            "score_logistic": best["logistic"][2],
            "score_random_forest": best["random_forest"][2],
        }
    )
    atomic_write_csv(validation_scores, output_tables / "validation_scores.csv")

    comparison = pd.DataFrame(
        [
            {
                "model": "no_skill",
                "candidate": "prevalence",
                "validation_ap": baseline_ap,
                "baseline_ap": baseline_ap,
                "ap_over_baseline": 1.0,
                "selected": False,
            },
            *[
                {
                    "model": family,
                    "candidate": best[family][0],
                    "validation_ap": float(best[family][4]),
                    "baseline_ap": baseline_ap,
                    "ap_over_baseline": float(best[family][4]) / baseline_ap,
                    "selected": family == selected_family,
                }
                for family in MODEL_FAMILIES
            ],
        ]
    )
    atomic_write_csv(comparison, output_tables / "model_comparison.csv")

    summary = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "random_state": random_state,
        "feature_columns": MODEL_FEATURE_COLUMNS,
        "train_rows": len(train),
        "validation_rows": len(validation),
        "validation_fraud": int(y_validation.sum()),
        "validation_baseline_ap": baseline_ap,
        "best_candidates": {
            family: {
                "candidate": best[family][0],
                "parameters": best[family][3],
                "validation_ap": float(best[family][4]),
            }
            for family in MODEL_FAMILIES
        },
        "selected_family": selected_family,
        "selected_candidate": selected[0],
        "validation_ap_difference_logistic_vs_rf": difference,
        "selection_reason": selection_reason,
        "test_accessed": False,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }
    atomic_write_json(summary, output_tables / "modeling_summary.json")
    return summary
