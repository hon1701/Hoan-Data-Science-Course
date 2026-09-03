# ECCC-LITE - Phân tích và xếp hạng nguy cơ gian lận thẻ

Đây là bản dự án đầy đủ, được tách riêng khỏi `ECCC-LITE-A1`. Dự án thực hiện
audit dữ liệu, EDA, huấn luyện mô hình, lựa chọn trên validation, đánh giá test
một lần, Top-p, phân tích lỗi và báo cáo có thể truy vết.

## Quy tắc khoa học đã khóa

- Nguồn chuẩn: `creditcard.csv`, 150.828.752 byte, SHA-256
  `76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89`.
- Loại 1.081 exact duplicates trước khi chia.
- Train/validation/test = 60/20/20, `stratify=Class`, `random_state=42`.
- EDA và mọi bước fit chỉ học từ train.
- Feature modeling: `Time`, `V1`-`V28`, `LogAmount`; loại `Amount`, `Class`,
  `source_row`.
- Chọn cấu hình và model bằng Average Precision trên validation.
- Nếu AP Logistic Regression và Random Forest chênh dưới 0,01, chọn Logistic
  Regression theo tie-break đã chốt.
- Threshold chính tối thiểu hóa chi phí học thuật `20 x FN + 1 x FP` trên
  validation. Threshold tối đa F1 được báo cáo để đối chiếu.
- Test chỉ được mở sau khi model và threshold đã khóa.
- Top-p dùng 0,5%, 1% và 2%; nếu score bằng nhau, `source_row` tăng dần là
  tie-break.

## Cấu trúc

```text
ECCC-LITE-FINAL/
├── data/raw/creditcard.csv
├── data/processed/{train,validation,test}.csv
├── notebooks/
│   ├── 01_data_eda.ipynb
│   ├── 02_modeling.ipynb
│   ├── 03_evaluation.ipynb
│   └── Fraud_Project_Final.ipynb
├── src/{a1_utils,modeling,evaluation}.py
├── scripts/
├── outputs/{tables,figures,models,notebooks}/
├── reports/BaoCao_NOP.docx
└── tests/
```

## Cách chạy

```powershell
conda activate ds_course
cd "DUONG_DAN_DEN_ECCC-LITE-FINAL"
python -m pip install -r requirements.txt
.\run_project.ps1
```

Hoặc:

```powershell
$env:PYTHONUTF8 = "1"
python -X utf8 scripts/run_full_project.py
```

Kiểm tra nhanh:

```powershell
python -m pytest -q
python -X utf8 scripts/verify_project.py
```

## Artifact chính

- `outputs/tables/data_audit.csv`: nguồn, hash, duplicate và split.
- `outputs/tables/validation_scores.csv`: score validation của ba họ mô hình.
- `outputs/tables/model_candidates.csv`: cấu hình thử có kiểm soát.
- `outputs/tables/model_comparison.csv`: AP/ROC-AUC và metric theo threshold.
- `outputs/tables/test_scores.csv`: score test của model đã khóa.
- `outputs/tables/top_p_metrics.csv`: Precision/Recall/Lift tại Top-p.
- `outputs/tables/error_examples.csv`: ví dụ FP/FN theo `source_row`.
- `outputs/tables/evaluation_summary.json`: nguồn số liệu chính cho báo cáo.
- `outputs/figures/*.png`: hình EDA và đánh giá.
- `outputs/notebooks/*.executed.ipynb`: notebook đã chạy theo đúng thứ tự.
- `reports/BaoCao_NOP.docx`: báo cáo cuối sau render QA.

## Giới hạn

Dữ liệu chỉ bao phủ khoảng hai ngày, V1-V28 đã ẩn danh và không có lịch sử
khách hàng. Chi phí FN/FP là giả định học thuật. Score dùng để xếp hạng ưu tiên
kiểm tra, không phải quyết định tự động khóa thẻ và chưa phải mô hình triển khai
trong ngân hàng.

