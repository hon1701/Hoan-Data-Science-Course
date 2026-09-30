"""Verify the complete reproducible project handoff."""

from __future__ import annotations

import json
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.verify_a1_outputs import verify as verify_a1  # noqa: E402
from src.a1_utils import ID_COLUMN, sha256_file  # noqa: E402
from src.modeling import MODEL_FEATURE_COLUMNS  # noqa: E402
from src.evaluation import threshold_metrics, top_p_metrics, select_cost_threshold, select_f1_threshold  # noqa: E402
from sklearn.metrics import average_precision_score, roc_auc_score  # noqa: E402

EXPECTED_FIGURES = [
    "class_distribution.png",
    "amount_by_class.png",
    "time_by_class.png",
    "selected_correlations.png",
    "eda_seaborn_multivariate.png",
    "validation_pr_curve.png",
    "test_pr_curve.png",
    "test_confusion_matrix.png",
    "top_p_performance.png",
    "feature_importance.png",
]
EXPECTED_TABLES = [
    "data_audit.csv",
    "train_time_class_pivot.csv",
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
    "decision_lock.json",
]


def verify_saved_metrics(root: Path) -> None:
    """Recompute reported numbers from the exported scores, without fitting."""
    tables = root / "outputs" / "tables"
    read_json = lambda name: json.loads((tables / name).read_text(encoding="utf-8"))
    summary = read_json("evaluation_summary.json")
    lock = read_json("decision_lock.json")
    validation = pd.read_csv(tables / "validation_scores.csv", float_precision="round_trip")
    test = pd.read_csv(tables / "test_scores.csv", float_precision="round_trip")
    assert sha256_file(tables / "decision_lock.json") == summary["decision_lock_sha256"]
    for key, filename in [("validation_scores_sha256", "validation_scores.csv"),
                          ("modeling_summary_sha256", "modeling_summary.json")]:
        assert lock[key] == sha256_file(tables / filename), filename
    assert not set(validation[ID_COLUMN]) & set(test[ID_COLUMN])
    for frame in (validation, test):
        assert frame[ID_COLUMN].is_unique
    score_column = "score_" + summary["selected_family"]
    cost, _ = select_cost_threshold(validation.y_true.to_numpy(), validation[score_column].to_numpy())
    f1 = select_f1_threshold(validation.y_true.to_numpy(), validation[score_column].to_numpy())
    assert cost["threshold"] == lock["cost_threshold"]
    assert f1["threshold"] == lock["f1_threshold"]
    y, scores = test.y_true.to_numpy(), test.score.to_numpy()
    np.testing.assert_allclose(average_precision_score(y, scores), summary["test"]["average_precision"], rtol=0, atol=1e-12)
    np.testing.assert_allclose(roc_auc_score(y, scores), summary["test"]["roc_auc"], rtol=0, atol=1e-12)
    for threshold_key, metrics_key in [("cost_threshold", "cost_threshold_metrics"),
                                       ("f1_threshold", "validation_f1_threshold_metrics")]:
        actual = threshold_metrics(y, scores, lock[threshold_key])
        expected = summary["test"][metrics_key]
        for key, value in actual.items():
            np.testing.assert_allclose(value, expected[key], rtol=0, atol=1e-12)
    actual_top = top_p_metrics(y, scores, test[ID_COLUMN].to_numpy())
    expected_top = pd.read_csv(tables / "top_p_metrics.csv", float_precision="round_trip")
    np.testing.assert_allclose(actual_top.to_numpy(), expected_top.to_numpy(), rtol=1e-12, atol=1e-12)
    for filename in ["01_data_eda", "02_modeling", "03_evaluation", "Fraud_Project_Final"]:
        path = root / "outputs" / "notebooks" / (filename + ".executed.ipynb")
        notebook = json.loads(path.read_text(encoding="utf-8"))
        counts = []
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code" and "".join(cell["source"]).strip():
                assert cell["execution_count"] is not None, path
                counts.append(cell["execution_count"])
                assert not any(o["output_type"] == "error" for o in cell["outputs"]), path
        assert counts == list(range(1, len(counts) + 1)), path
        source_path = root / "notebooks" / (filename + ".ipynb")
        if source_path.exists():
            source = json.loads(source_path.read_text(encoding="utf-8"))
            # nbformat permits either a string or a list of lines for source.
            content = lambda nb: [(c["cell_type"], "".join(c["source"])) for c in nb["cells"]]
            assert content(source) == content(notebook), path
        expected_images = {"01_data_eda": 5, "02_modeling": 0, "03_evaluation": 5, "Fraud_Project_Final": 10}[filename]
        image_count = sum("image/png" in o.get("data", {}) for c in notebook["cells"] for o in c.get("outputs", []))
        assert image_count >= expected_images, f"Thiếu hình nhúng: {path}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-only", action="store_true", help="Đối chiếu số liệu đã xuất, không cần raw/model.")
    args = parser.parse_args()
    verify_saved_metrics(ROOT)
    if args.results_only:
        print("[OK] Metric, threshold, Top-p và bốn notebook đã được đối chiếu từ output.")
        return
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
    lock = json.loads((tables / "decision_lock.json").read_text(encoding="utf-8"))
    assert lock["model_sha256"] == sha256_file(ROOT / "outputs/models/selected_model.joblib")

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
