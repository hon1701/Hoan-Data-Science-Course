"""Add concise learning notes and computed interpretations to the source notebooks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def cell(kind: str, text: str, key: str) -> dict:
    result = {"cell_type": kind, "metadata": {}, "id": "eccc-" + hashlib.sha256(key.encode()).hexdigest()[:8],
              "source": text.splitlines(keepends=True)}
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    return result


def enhance(root: Path = ROOT) -> None:
    notes = {
        "01_data_eda.ipynb": (
            "## Đầu vào và điều cần hiểu\nMỗi dòng là một giao dịch; `Class=1` là gian lận. Dữ liệu gốc phải đúng hash trước khi chạy. "
            "`source_row` giữ vị trí dòng gốc để truy vết. Sau làm sạch, ba tập có cùng schema 33 cột. "
            "A.1 giữ cả `Amount` và `LogAmount` để phân tích; A.2 dùng **30 feature** gồm Time, V1–V28 và LogAmount. "
            "`Class`, `source_row` và Amount gốc không được đưa vào mô hình. Chỉ train được dùng cho EDA.", None),
        "02_modeling.ipynb": (
            "## Cách đọc thí nghiệm\n`train.csv` dùng để học tham số; `validation.csv` dùng để chọn cấu hình. "
            "StandardScaler nằm trong Pipeline nên chỉ fit trên train. Mỗi họ Logistic/RF thử hai cấu hình đã chốt. "
            "Dummy most_frequent minh họa accuracy cao khi bỏ qua fraud; Dummy stratified là baseline được giữ cố định. "
            "Chọn Logistic/RF bằng Average Precision (AP); nếu chênh AP < 0,01 thì ưu tiên Logistic. "
            "AP lấy từ score của Class=1 và không phụ thuộc một threshold đơn lẻ.",
            "print(f\"Train: {summary['train_rows']:,} dòng; validation: {summary['validation_rows']:,} dòng, {summary['validation_fraud']} fraud.\")\n"
            "print('Model chọn:', summary['selected_family'], '/', summary['selected_candidate'])\n"
            "print('AP validation theo từng họ:')\n"
            "display(pd.DataFrame(summary['best_candidates']).T[['candidate', 'validation_ap']])\n"
            "print('Baseline AP (prevalence):', summary['validation_baseline_ap'])"),
        "03_evaluation.ipynb": (
            "## Ngưỡng và ngân sách kiểm tra\nNgưỡng chính giảm `(20×FN + FP)/N_validation`. Tỷ lệ 20:1 là giả định học thuật. "
            "Có xét cả lựa chọn không phát cảnh báo; khi hòa chi phí, ưu tiên recall cao. Quyết định và hash model được ghi vào "
            "`decision_lock.json` trước khi đọc test. Ngưỡng F1 là đối chiếu đã chọn trên validation. "
            "Top-p dùng `k=ceil(p×N_test)`; Precision@k=TP/k, Recall@k=TP/tổng fraud, Lift=Precision@k/tỷ lệ fraud. "
            "Tăng k thường tìm thêm fraud nhưng tăng khối lượng kiểm tra.",
            "display(pd.DataFrame([summary['test']['cost_threshold_metrics'], summary['test']['validation_f1_threshold_metrics']], "
            "index=['Ngưỡng chi phí', 'Ngưỡng F1 validation']))\n"
            "for row in top_p.itertuples():\n"
            "    print(f'Top {row.top_p_percent:g}%: kiểm tra {row.k} dòng, tìm {row.tp}/{summary[\"test\"][\"fraud\"]} fraud; ' "
            "f'Precision={row.precision_at_k:.2%}, Recall={row.recall_at_k:.2%}, Lift={row.lift_at_k:.2f}.')"),
        "Fraud_Project_Final.ipynb": (
            "## Câu hỏi kết luận\nMô hình có giúp ưu tiên giao dịch để kiểm tra hay không? Đọc cùng AP, precision/recall tại ngưỡng "
            "và số fraud tìm được khi chỉ kiểm tra Top-p. Notebook này tổng hợp cùng một lần chạy; số liệu chuẩn nằm trong "
            "`evaluation_summary.json`. AP dùng cách tổng có trọng số của scikit-learn, không nội suy hình thang diện tích PR. "
            "Dữ liệu hai ngày và phép chia ngẫu nhiên có phân tầng chỉ đánh giá nội bộ; chưa chứng minh khả năng dự báo giao dịch tương lai.",
            "primary = evaluation['test']['cost_threshold_metrics']\n"
            "print(f\"Ngưỡng chính tạo {primary['tp']+primary['fp']} cảnh báo; trong đó {primary['tp']} fraud và {primary['fp']} cảnh báo nhầm.\")\n"
            "print(f\"Còn bỏ sót {primary['fn']} fraud; chi phí giả định mỗi giao dịch là {primary['expected_cost_per_transaction']:.6f}.\")\n"
            "print('Cấu hình đã giữ nguyên trước khi đọc test; kết quả này dùng để thảo luận giới hạn và ngân sách kiểm tra.')"),
    }
    for name, (intro, code) in notes.items():
        path = root / "notebooks" / name
        notebook = json.loads(path.read_text(encoding="utf-8"))
        cells = [c for c in notebook["cells"] if not c.get("id", "").startswith("eccc-")]
        cells.insert(1, cell("markdown", intro, name + "intro"))
        if code:
            cells.extend([cell("markdown", "## Diễn giải kết quả của lần chạy\nCác con số dưới đây được tính từ output vừa tạo.", name + "interpret"),
                          cell("code", code, name + "code")])
        notebook["cells"] = cells
        path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    enhance()
