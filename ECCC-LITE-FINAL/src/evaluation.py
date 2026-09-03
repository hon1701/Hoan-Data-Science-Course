"""Validation threshold selection and one-time final test evaluation."""

from __future__ import annotations

import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.a1_utils import ID_COLUMN, RANDOM_STATE, TARGET, atomic_write_csv, atomic_write_json
from src.modeling import (
    MODEL_FEATURE_COLUMNS,
    load_split,
    positive_class_scores,
    split_xy,
    validate_scores,
)


def threshold_metrics(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, Any]:
    """Compute classification metrics for score >= threshold."""

    labels = (np.asarray(scores) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, labels, labels=[0, 1]).ravel()
    return {
        "threshold": float(threshold),
        "precision": float(precision_score(y_true, labels, zero_division=0)),
        "recall": float(recall_score(y_true, labels, zero_division=0)),
        "f1": float(f1_score(y_true, labels, zero_division=0)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def select_f1_threshold(y_true: np.ndarray, scores: np.ndarray) -> dict[str, Any]:
    """Choose the validation threshold with maximum F1, breaking ties by recall."""

    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    if len(thresholds) == 0:
        raise AssertionError("Không có threshold để chọn.")
    p = precision[:-1]
    r = recall[:-1]
    f1 = np.divide(2 * p * r, p + r, out=np.zeros_like(p), where=(p + r) > 0)
    max_f1 = f1.max()
    candidates = np.flatnonzero(np.isclose(f1, max_f1, rtol=0, atol=1e-12))
    best = int(candidates[np.argmax(r[candidates])])
    result = threshold_metrics(np.asarray(y_true), np.asarray(scores), float(thresholds[best]))
    result["selection"] = "max_f1"
    return result


def cost_curve(
    y_true: np.ndarray,
    scores: np.ndarray,
    *,
    false_negative_cost: float = 20.0,
    false_positive_cost: float = 1.0,
) -> pd.DataFrame:
    """Return exact threshold outcomes using stable descending score order."""

    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=float)
    order = np.argsort(-s, kind="mergesort")
    sorted_y = y[order]
    sorted_s = s[order]
    cumulative_tp = np.cumsum(sorted_y == 1)
    cumulative_fp = np.cumsum(sorted_y == 0)
    group_end = np.r_[sorted_s[1:] != sorted_s[:-1], True]
    tp = cumulative_tp[group_end]
    fp = cumulative_fp[group_end]
    thresholds = sorted_s[group_end]
    positives = int(y.sum())
    fn = positives - tp
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / max(positives, 1)
    f1 = np.divide(
        2 * precision * recall,
        precision + recall,
        out=np.zeros_like(precision, dtype=float),
        where=(precision + recall) > 0,
    )
    expected_cost = (false_negative_cost * fn + false_positive_cost * fp) / len(y)
    return pd.DataFrame(
        {
            "threshold": thresholds,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "expected_cost_per_transaction": expected_cost,
        }
    )


def select_cost_threshold(
    y_true: np.ndarray,
    scores: np.ndarray,
    *,
    false_negative_cost: float = 20.0,
    false_positive_cost: float = 1.0,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Choose minimum expected-cost threshold; break ties by higher recall."""

    curve = cost_curve(
        y_true,
        scores,
        false_negative_cost=false_negative_cost,
        false_positive_cost=false_positive_cost,
    )
    minimum = curve["expected_cost_per_transaction"].min()
    candidates = curve[np.isclose(curve["expected_cost_per_transaction"], minimum)]
    row = candidates.sort_values(["recall", "threshold"], ascending=[False, True]).iloc[0]
    result = threshold_metrics(np.asarray(y_true), np.asarray(scores), float(row["threshold"]))
    result.update(
        {
            "selection": "minimum_expected_cost",
            "false_negative_cost": false_negative_cost,
            "false_positive_cost": false_positive_cost,
            "expected_cost_per_transaction": float(row["expected_cost_per_transaction"]),
        }
    )
    return result, curve


def top_p_metrics(
    y_true: np.ndarray,
    scores: np.ndarray,
    source_rows: np.ndarray,
    rates: tuple[float, ...] = (0.005, 0.01, 0.02),
) -> pd.DataFrame:
    """Calculate deterministic Top-p metrics using source_row as score tie-break."""

    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=float)
    ids = np.asarray(source_rows, dtype=int)
    order = np.lexsort((ids, -s))
    total_fraud = int(y.sum())
    prevalence = total_fraud / len(y)
    rows = []
    for rate in rates:
        k = int(math.ceil(rate * len(y)))
        selected = order[:k]
        tp = int(y[selected].sum())
        fp = int(k - tp)
        precision = tp / k
        recall = tp / total_fraud
        rows.append(
            {
                "top_p": rate,
                "top_p_percent": rate * 100,
                "k": k,
                "tp": tp,
                "fp": fp,
                "precision_at_k": precision,
                "recall_at_k": recall,
                "lift_at_k": precision / prevalence,
            }
        )
    return pd.DataFrame(rows)


def bootstrap_ap_interval(
    y_true: np.ndarray,
    scores: np.ndarray,
    *,
    iterations: int = 1_000,
    random_state: int = RANDOM_STATE,
) -> tuple[float, float, int]:
    """Estimate a percentile 95% CI for AP with non-parametric bootstrap."""

    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=float)
    rng = np.random.default_rng(random_state)
    estimates: list[float] = []
    attempts = 0
    while len(estimates) < iterations and attempts < iterations * 2:
        attempts += 1
        sample = rng.integers(0, len(y), size=len(y))
        if np.unique(y[sample]).size < 2:
            continue
        estimates.append(float(average_precision_score(y[sample], s[sample])))
    if len(estimates) != iterations:
        raise AssertionError("Không tạo đủ bootstrap sample hợp lệ.")
    low, high = np.quantile(estimates, [0.025, 0.975])
    return float(low), float(high), len(estimates)


def _save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _plot_validation_pr(
    validation_scores: pd.DataFrame,
    baseline: float,
    path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    for column, label, color in [
        ("score_dummy", "Dummy stratified", "#7f8c8d"),
        ("score_logistic", "Logistic Regression", "#1976d2"),
        ("score_random_forest", "Random Forest", "#d84315"),
    ]:
        precision, recall, _ = precision_recall_curve(validation_scores["y_true"], validation_scores[column])
        ap = average_precision_score(validation_scores["y_true"], validation_scores[column])
        ax.plot(recall, precision, label=f"{label} (AP={ap:.4f})", color=color, linewidth=1.8)
    ax.axhline(baseline, color="black", linestyle="--", linewidth=1, label=f"No-skill={baseline:.4f}")
    ax.set(xlabel="Recall", ylabel="Precision", title="Precision-Recall trên validation")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.grid(alpha=0.2)
    ax.legend(loc="best", fontsize=8)
    _save_figure(fig, path)


def _plot_test_pr(y_true: np.ndarray, scores: np.ndarray, model_label: str, path: Path) -> None:
    precision, recall, _ = precision_recall_curve(y_true, scores)
    ap = average_precision_score(y_true, scores)
    baseline = float(np.mean(y_true))
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    ax.plot(recall, precision, color="#1976d2", linewidth=2, label=f"{model_label} (AP={ap:.4f})")
    ax.axhline(baseline, color="black", linestyle="--", linewidth=1, label=f"No-skill={baseline:.4f}")
    ax.set(xlabel="Recall", ylabel="Precision", title="Precision-Recall trên test đã khóa")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.grid(alpha=0.2)
    ax.legend(loc="best")
    _save_figure(fig, path)


def _plot_confusion(metrics: dict[str, Any], model_label: str, path: Path) -> None:
    matrix = np.array([[metrics["tn"], metrics["fp"]], [metrics["fn"], metrics["tp"]]])
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    image = ax.imshow(matrix, cmap="Blues")
    for (row, column), value in np.ndenumerate(matrix):
        ax.text(column, row, f"{value:,}", ha="center", va="center", fontsize=12)
    ax.set_xticks([0, 1], labels=["Dự đoán 0", "Dự đoán 1"])
    ax.set_yticks([0, 1], labels=["Thực tế 0", "Thực tế 1"])
    ax.set_title(f"Confusion matrix - {model_label}\nthreshold={metrics['threshold']:.6f}")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    _save_figure(fig, path)


def _plot_top_p(table: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2))
    labels = [f"{value:g}%" for value in table["top_p_percent"]]
    axes[0].bar(labels, table["recall_at_k"], color="#1976d2")
    axes[0].set(title="Recall theo năng lực kiểm tra", xlabel="Top-p", ylabel="Recall@Top-p", ylim=(0, 1))
    axes[1].bar(labels, table["lift_at_k"], color="#ef6c00")
    axes[1].set(title="Lift so với chọn ngẫu nhiên", xlabel="Top-p", ylabel="Lift@Top-p")
    for ax in axes:
        ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    _save_figure(fig, path)


def _feature_importance(model: Any, selected_family: str) -> pd.DataFrame:
    if selected_family == "logistic":
        estimator = model.named_steps["model"]
        values = np.abs(estimator.coef_[0])
        signed = estimator.coef_[0]
        return pd.DataFrame(
            {"feature": MODEL_FEATURE_COLUMNS, "importance": values, "signed_effect": signed}
        ).sort_values("importance", ascending=False)
    values = np.asarray(model.feature_importances_)
    return pd.DataFrame(
        {"feature": MODEL_FEATURE_COLUMNS, "importance": values, "signed_effect": np.nan}
    ).sort_values("importance", ascending=False)


def _plot_importance(table: pd.DataFrame, selected_family: str, path: Path) -> None:
    top = table.head(15).sort_values("importance")
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    ax.barh(top["feature"], top["importance"], color="#455a64")
    label = "|hệ số chuẩn hóa|" if selected_family == "logistic" else "feature importance"
    ax.set(xlabel=label, title=f"Biến ảnh hưởng mạnh nhất - {selected_family}")
    ax.grid(axis="x", alpha=0.2)
    _save_figure(fig, path)


def evaluate_project(
    root: Path,
    *,
    random_state: int = RANDOM_STATE,
    bootstrap_iterations: int = 1_000,
) -> dict[str, Any]:
    """Select thresholds on validation, then evaluate the locked test split once."""

    root = Path(root).resolve()
    tables = root / "outputs" / "tables"
    figures = root / "outputs" / "figures"
    models = root / "outputs" / "models"
    modeling_summary = json.loads((tables / "modeling_summary.json").read_text(encoding="utf-8"))
    validation_scores = pd.read_csv(tables / "validation_scores.csv")
    expected_score_columns = {
        ID_COLUMN,
        "y_true",
        "score_dummy",
        "score_logistic",
        "score_random_forest",
    }
    if set(validation_scores.columns) != expected_score_columns:
        raise AssertionError("validation_scores.csv sai schema.")
    if validation_scores[ID_COLUMN].duplicated().any():
        raise AssertionError("source_row bị trùng trong validation_scores.csv.")

    selected_family = modeling_summary["selected_family"]
    selected_column = f"score_{selected_family}"
    y_validation = validation_scores["y_true"].to_numpy(dtype=int)
    selected_validation_scores = validate_scores(
        validation_scores[selected_column].to_numpy(), len(validation_scores), min_unique=11
    )
    f1_threshold = select_f1_threshold(y_validation, selected_validation_scores)
    cost_threshold, curve = select_cost_threshold(y_validation, selected_validation_scores)
    atomic_write_csv(curve, tables / "threshold_search.csv")

    test = load_split(root, "test")
    x_test, y_test_series = split_xy(test)
    y_test = y_test_series.to_numpy(dtype=int)
    model = joblib.load(models / "selected_model.joblib")
    test_scores = validate_scores(
        positive_class_scores(model, x_test), len(test), min_unique=11
    )
    test_score_table = pd.DataFrame(
        {ID_COLUMN: test[ID_COLUMN].astype(int), "y_true": y_test, "score": test_scores}
    )
    atomic_write_csv(test_score_table, tables / "test_scores.csv")

    test_ap = float(average_precision_score(y_test, test_scores))
    test_roc_auc = float(roc_auc_score(y_test, test_scores))
    test_baseline = float(y_test.mean())
    test_cost_metrics = threshold_metrics(y_test, test_scores, cost_threshold["threshold"])
    test_f1_metrics = threshold_metrics(y_test, test_scores, f1_threshold["threshold"])
    ci_low, ci_high, valid_bootstraps = bootstrap_ap_interval(
        y_test,
        test_scores,
        iterations=bootstrap_iterations,
        random_state=random_state,
    )

    top_p = top_p_metrics(y_test, test_scores, test[ID_COLUMN].to_numpy())
    atomic_write_csv(top_p, tables / "top_p_metrics.csv")

    comparison_rows: list[dict[str, Any]] = []
    baseline_validation = float(y_validation.mean())
    for family in ("dummy", "logistic", "random_forest"):
        scores = validation_scores[f"score_{family}"].to_numpy()
        own_threshold = select_f1_threshold(y_validation, scores)
        comparison_rows.append(
            {
                "split": "validation",
                "model": family,
                "candidate": modeling_summary["best_candidates"][family]["candidate"],
                "ap": average_precision_score(y_validation, scores),
                "roc_auc": roc_auc_score(y_validation, scores),
                "baseline_ap": baseline_validation,
                "ap_over_baseline": average_precision_score(y_validation, scores) / baseline_validation,
                "threshold_type": "max_f1",
                **own_threshold,
            }
        )
    for threshold_type, metrics in [
        ("minimum_expected_cost", test_cost_metrics),
        ("validation_max_f1", test_f1_metrics),
    ]:
        comparison_rows.append(
            {
                "split": "test",
                "model": selected_family,
                "candidate": modeling_summary["selected_candidate"],
                "ap": test_ap,
                "roc_auc": test_roc_auc,
                "baseline_ap": test_baseline,
                "ap_over_baseline": test_ap / test_baseline,
                "threshold_type": threshold_type,
                **metrics,
            }
        )
    comparison = pd.DataFrame(comparison_rows)
    atomic_write_csv(comparison, tables / "model_comparison.csv")

    primary_labels = (test_scores >= cost_threshold["threshold"]).astype(int)
    importance = _feature_importance(model, selected_family)
    atomic_write_csv(importance, tables / "feature_importance.csv")
    top_features = importance.head(5)["feature"].tolist()
    error_feature_columns = list(dict.fromkeys(["Time", "Amount", "LogAmount", *top_features]))
    errors = test.loc[
        primary_labels != y_test,
        [ID_COLUMN, TARGET, *error_feature_columns],
    ].copy()
    errors.insert(2, "score", test_scores[primary_labels != y_test])
    errors.insert(3, "predicted", primary_labels[primary_labels != y_test])
    errors.insert(4, "error_type", np.where(errors[TARGET].eq(0), "False Positive", "False Negative"))
    fp_examples = errors[errors["error_type"].eq("False Positive")].nlargest(10, "score")
    fn_examples = errors[errors["error_type"].eq("False Negative")].nsmallest(10, "score")
    error_examples = pd.concat([fp_examples, fn_examples], ignore_index=True)
    atomic_write_csv(error_examples, tables / "error_examples.csv")

    model_label = "Logistic Regression" if selected_family == "logistic" else "Random Forest"
    _plot_validation_pr(validation_scores, baseline_validation, figures / "validation_pr_curve.png")
    _plot_test_pr(y_test, test_scores, model_label, figures / "test_pr_curve.png")
    _plot_confusion(test_cost_metrics, model_label, figures / "test_confusion_matrix.png")
    _plot_top_p(top_p, figures / "top_p_performance.png")
    _plot_importance(importance, selected_family, figures / "feature_importance.png")

    summary = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "selected_family": selected_family,
        "selected_candidate": modeling_summary["selected_candidate"],
        "selection_reason": modeling_summary["selection_reason"],
        "validation": {
            "rows": len(validation_scores),
            "fraud": int(y_validation.sum()),
            "baseline_ap": baseline_validation,
            "selected_model_ap": float(average_precision_score(y_validation, selected_validation_scores)),
            "cost_threshold": cost_threshold,
            "f1_threshold": f1_threshold,
        },
        "test": {
            "rows": len(test),
            "fraud": int(y_test.sum()),
            "baseline_ap": test_baseline,
            "average_precision": test_ap,
            "roc_auc": test_roc_auc,
            "ap_over_baseline": test_ap / test_baseline,
            "ap_bootstrap_95_ci": [ci_low, ci_high],
            "bootstrap_iterations": valid_bootstraps,
            "cost_threshold_metrics": test_cost_metrics,
            "validation_f1_threshold_metrics": test_f1_metrics,
        },
        "top_p": top_p.to_dict(orient="records"),
        "cost_assumption": {
            "false_negative": cost_threshold["false_negative_cost"],
            "false_positive": cost_threshold["false_positive_cost"],
            "unit": "relative academic cost per transaction",
        },
        "test_accessed_after_model_and_threshold_lock": True,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "matplotlib": matplotlib.__version__,
        },
    }
    atomic_write_json(summary, tables / "evaluation_summary.json")
    atomic_write_json(summary["environment"], tables / "environment_summary.json")
    return summary
