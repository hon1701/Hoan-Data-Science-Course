"""Generate the three full-project notebooks with reproducible cell order."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"

ROOT_CELL = """from pathlib import Path
import json
import sys

def find_project_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / 'config' / 'a1_config.json').is_file():
            return candidate
    raise FileNotFoundError('Không tìm thấy thư mục gốc dự án.')

PROJECT_ROOT = find_project_root(Path.cwd().resolve())
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
print('PROJECT_ROOT:', PROJECT_ROOT)
"""


def save_notebook(name: str, title: str, cells: list) -> None:
    notebook = nbf.v4.new_notebook()
    notebook["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    }
    notebook["cells"] = [nbf.v4.new_markdown_cell(f"# {title}"), *cells]
    nbf.write(notebook, NOTEBOOKS / name)


def main() -> None:
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)

    save_notebook(
        "02_modeling.ipynb",
        "02 - Modeling trên train/validation",
        [
            nbf.v4.new_markdown_cell(
                "Notebook này chỉ đọc `train.csv` và `validation.csv`. Test không được truy cập ở giai đoạn "
                "chọn cấu hình/mô hình. Feature cốt lõi là `Time`, `V1`-`V28`, `LogAmount`; loại `Amount`, "
                "`Class` và `source_row`."
            ),
            nbf.v4.new_code_cell(ROOT_CELL),
            nbf.v4.new_code_cell(
                "from IPython.display import display\n"
                "import pandas as pd\n"
                "from src.modeling import MODEL_FEATURE_COLUMNS, train_models\n\n"
                "print('Số feature:', len(MODEL_FEATURE_COLUMNS))\n"
                "print(MODEL_FEATURE_COLUMNS)\n"
                "summary = train_models(PROJECT_ROOT)\n"
                "print(summary['selection_reason'])"
            ),
            nbf.v4.new_markdown_cell(
                "Các candidate được thử có kiểm soát: Dummy (`most_frequent`, `stratified`), Logistic "
                "Regression (standard/balanced) và Random Forest (standard/balanced). Mỗi họ giữ candidate "
                "có Average Precision validation cao nhất; tie-break 0,01 giữa Logistic và Random Forest được "
                "áp dụng trước khi mở test."
            ),
            nbf.v4.new_code_cell(
                "candidates = pd.read_csv(PROJECT_ROOT / 'outputs/tables/model_candidates.csv')\n"
                "comparison = pd.read_csv(PROJECT_ROOT / 'outputs/tables/model_comparison.csv')\n"
                "display(candidates)\n"
                "display(comparison)\n"
                "assert summary['test_accessed'] is False"
            ),
            nbf.v4.new_markdown_cell(
                "**Bàn giao:** `validation_scores.csv`, `model_candidates.csv`, `model_comparison.csv`, "
                "`modeling_summary.json` và các model đã fit trong `outputs/models/`."
            ),
        ],
    )

    save_notebook(
        "03_evaluation.ipynb",
        "03 - Evaluation, threshold và Top-p",
        [
            nbf.v4.new_markdown_cell(
                "Notebook chọn threshold trên validation rồi mới đánh giá test một lần. Threshold chính tối "
                "thiểu hóa chi phí học thuật `20 x FN + 1 x FP`; threshold tối đa F1 được báo cáo để đối chiếu."
            ),
            nbf.v4.new_code_cell(ROOT_CELL),
            nbf.v4.new_code_cell(
                "from IPython.display import Image, display\n"
                "import pandas as pd\n"
                "from src.evaluation import evaluate_project\n\n"
                "summary = evaluate_project(PROJECT_ROOT, bootstrap_iterations=1000)\n"
                "print(summary['selection_reason'])\n"
                "print('Selected:', summary['selected_family'])\n"
                "print('Test AP:', summary['test']['average_precision'])"
            ),
            nbf.v4.new_code_cell(
                "comparison = pd.read_csv(PROJECT_ROOT / 'outputs/tables/model_comparison.csv')\n"
                "top_p = pd.read_csv(PROJECT_ROOT / 'outputs/tables/top_p_metrics.csv')\n"
                "errors = pd.read_csv(PROJECT_ROOT / 'outputs/tables/error_examples.csv')\n"
                "display(comparison)\n"
                "display(top_p)\n"
                "display(errors)"
            ),
            nbf.v4.new_code_cell(
                "for name in ['validation_pr_curve.png', 'test_pr_curve.png', 'test_confusion_matrix.png', "
                "'top_p_performance.png', 'feature_importance.png']:\n"
                "    display(Image(filename=str(PROJECT_ROOT / 'outputs/figures' / name)))"
            ),
            nbf.v4.new_markdown_cell(
                "Kết quả FP/FN chỉ mô tả mẫu số học của biến đã ẩn danh; không suy ra nguyên nhân gian lận hay "
                "hành vi khách hàng."
            ),
        ],
    )

    save_notebook(
        "Fraud_Project_Final.ipynb",
        "Fraud Project Final - Báo cáo có thể truy vết",
        [
            nbf.v4.new_markdown_cell(
                "Notebook tổng hợp này được thực thi sau 01, 02 và 03 bởi `scripts/run_full_project.py`. Nó chỉ "
                "đọc các artifact của cùng lần chạy cuối để tránh vô tình chọn lại model/threshold sau khi đã "
                "mở test."
            ),
            nbf.v4.new_code_cell(ROOT_CELL),
            nbf.v4.new_code_cell(
                "from IPython.display import Image, display\n"
                "import pandas as pd\n\n"
                "audit = pd.read_csv(PROJECT_ROOT / 'outputs/tables/data_audit.csv')\n"
                "comparison = pd.read_csv(PROJECT_ROOT / 'outputs/tables/model_comparison.csv')\n"
                "top_p = pd.read_csv(PROJECT_ROOT / 'outputs/tables/top_p_metrics.csv')\n"
                "evaluation = json.loads((PROJECT_ROOT / 'outputs/tables/evaluation_summary.json').read_text(encoding='utf-8'))\n"
                "display(audit)\n"
                "display(comparison)\n"
                "display(top_p)"
            ),
            nbf.v4.new_code_cell(
                "test = evaluation['test']\n"
                "primary = test['cost_threshold_metrics']\n"
                "print(f\"Mô hình chính: {evaluation['selected_family']}\")\n"
                "print(f\"Test AP: {test['average_precision']:.6f} "
                "(95% bootstrap CI {test['ap_bootstrap_95_ci'][0]:.6f} - {test['ap_bootstrap_95_ci'][1]:.6f})\")\n"
                "print(f\"ROC-AUC: {test['roc_auc']:.6f}\")\n"
                "print(f\"Threshold chi phí: {primary['threshold']:.8f}; "
                "Precision={primary['precision']:.4f}; Recall={primary['recall']:.4f}; F1={primary['f1']:.4f}\")"
            ),
            nbf.v4.new_code_cell(
                "for name in ['class_distribution.png', 'amount_by_class.png', 'time_by_class.png', "
                "'selected_correlations.png', 'validation_pr_curve.png', 'test_pr_curve.png', "
                "'test_confusion_matrix.png', 'top_p_performance.png', 'feature_importance.png']:\n"
                "    path = PROJECT_ROOT / 'outputs/figures' / name\n"
                "    assert path.is_file(), path\n"
                "    display(Image(filename=str(path)))"
            ),
            nbf.v4.new_markdown_cell(
                "**Giới hạn:** dữ liệu chỉ bao phủ khoảng hai ngày, V1-V28 đã ẩn danh, không có lịch sử khách "
                "hàng và giả định chi phí là học thuật. Đầu ra dùng để xếp hạng ưu tiên kiểm tra, không tự động "
                "khóa thẻ."
            ),
        ],
    )
    print("[OK] Đã tạo 02_modeling.ipynb, 03_evaluation.ipynb và Fraud_Project_Final.ipynb")


if __name__ == "__main__":
    main()
