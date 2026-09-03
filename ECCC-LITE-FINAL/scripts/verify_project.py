"""Verify the complete reproducible project handoff."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.verify_a1_outputs import verify as verify_a1  # noqa: E402
from src.a1_utils import ID_COLUMN  # noqa: E402
from src.modeling import MODEL_FEATURE_COLUMNS  # noqa: E402

EXPECTED_FIGURES = [
    "class_distribution.png",
    "amount_by_class.png",
    "time_by_class.png",
    "selected_correlations.png",
    "validation_pr_curve.png",
    "test_pr_curve.png",
    "test_confusion_matrix.png",
    "top_p_performance.png",
    "feature_importance.png",
]
EXPECTED_TABLES = [
    "data_audit.csv",
    "model_candidates.csv",
    "validation_scores.csv",
    "model_comparison.csv",
    "threshold_search.csv",
    "test_scores.csv",
    "top_p_metrics.csv",
    "feature_importance.csv",
    "error_examples.csv",
    "modeling_summary.json",
    "evaluation_summary.json",
    "environment_summary.json",
]


def main() -> None:
    verify_a1(ROOT, strict=True)
    tables = ROOT / "outputs" / "tables"
    figures = ROOT / "outputs" / "figures"
    notebooks = ROOT / "outputs" / "notebooks"

    for filename in EXPECTED_TABLES:
        path = tables / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Thiếu artifact: {path}")
    for filename in EXPECTED_FIGURES:
        path = figures / filename
        if not path.is_file() or path.stat().st_size < 5_000:
            raise FileNotFoundError(f"Thiếu hoặc hình quá nhỏ: {path}")

    modeling = json.loads((tables / "modeling_summary.json").read_text(encoding="utf-8"))
    evaluation = json.loads((tables / "evaluation_summary.json").read_text(encoding="utf-8"))
    if modeling["feature_columns"] != MODEL_FEATURE_COLUMNS:
        raise AssertionError("Feature contract của modeling không đúng.")
    if {"Class", "source_row", "Amount"} & set(modeling["feature_columns"]):
        raise AssertionError("Feature contract chứa cột bị cấm.")
    if modeling["selected_family"] != evaluation["selected_family"]:
        raise AssertionError("Model đã chọn không nhất quán giữa modeling và evaluation.")
    if modeling["test_accessed"] is not False:
        raise AssertionError("Modeling không được truy cập test.")
    if evaluation["test_accessed_after_model_and_threshold_lock"] is not True:
        raise AssertionError("Không có xác nhận khóa model/threshold trước test.")

    validation_scores = pd.read_csv(tables / "validation_scores.csv")
    test_scores = pd.read_csv(tables / "test_scores.csv")
    if (len(validation_scores), int(validation_scores["y_true"].sum())) != (56_745, 94):
        raise AssertionError("Validation score không khớp split chuẩn.")
    if (len(test_scores), int(test_scores["y_true"].sum())) != (56_746, 95):
        raise AssertionError("Test score không khớp split chuẩn.")
    if validation_scores[ID_COLUMN].duplicated().any() or test_scores[ID_COLUMN].duplicated().any():
        raise AssertionError("source_row bị trùng trong score output.")
    for column in ["score_dummy", "score_logistic", "score_random_forest"]:
        if not validation_scores[column].between(0, 1).all():
            raise AssertionError(f"{column} ra ngoài [0,1].")
    if not test_scores["score"].between(0, 1).all():
        raise AssertionError("Test score ra ngoài [0,1].")

    top_p = pd.read_csv(tables / "top_p_metrics.csv")
    if top_p["k"].astype(int).tolist() != [284, 568, 1_135]:
        raise AssertionError("Top-p k không đúng quy ước ceil.")
    if not np.isfinite(top_p[["precision_at_k", "recall_at_k", "lift_at_k"]]).all().all():
        raise AssertionError("Top-p metric có NaN/infinity.")

    required_executed = [
        "01_data_eda.executed.ipynb",
        "02_modeling.executed.ipynb",
        "03_evaluation.executed.ipynb",
        "Fraud_Project_Final.executed.ipynb",
    ]
    for filename in required_executed:
        if not (notebooks / filename).is_file():
            raise FileNotFoundError(f"Thiếu notebook đã chạy: {filename}")

    print("[OK] A.1, modeling, evaluation và Top-p đều đúng contract.")
    print("[OK] Model/threshold được khóa trước test; score và artifact nhất quán.")
    print("[OK] Bộ dự án đầy đủ đã sẵn sàng để build báo cáo nộp.")


if __name__ == "__main__":
    main()

