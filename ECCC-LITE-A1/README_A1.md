# Phụ lục A.1 — `01_data_eda.ipynb`

**Phụ trách:** Nguyễn Văn Hoan  
**Đề tài:** Phân tích dữ liệu và xếp hạng nguy cơ gian lận trong giao dịch thẻ
**Phiên bản:** 1.1 — sửa tương thích `boxplot` cho các phiên bản Matplotlib mới.

## 1. Phạm vi

Bộ file này thực hiện đúng phần A.1 của Hoan:

1. kiểm chứng nguồn dữ liệu bằng kích thước và SHA-256;
2. kiểm tra schema, kiểu dữ liệu, missing, infinity và phân bố `Class`;
3. tạo `source_row` để truy vết;
4. loại 1.081 bản ghi trùng hoàn toàn trên 31 cột gốc;
5. tạo `LogAmount = log1p(Amount)`;
6. chia train/validation/test theo tỷ lệ 60/20/20, có `stratify=Class`,
   `random_state=42`;
7. EDA chỉ trên train;
8. xuất dữ liệu và bảng audit để Huy/Sang sử dụng.

A.1 không huấn luyện mô hình, không chọn threshold và không dùng test để chọn
feature. `Class` và `source_row` bị loại khỏi feature contract.

## 2. Cấu trúc

```text
ECCC-LITE-A1/
├── config/a1_config.json
├── data/
│   ├── raw/README.md
│   └── processed/
├── notebooks/01_data_eda.ipynb
├── outputs/
│   ├── figures/
│   ├── notebooks/
│   └── tables/
├── scripts/
│   ├── get_data.py
│   ├── run_a1.py
│   ├── smoke_test_notebook.py
│   └── verify_a1_outputs.py
├── src/a1_utils.py
├── tests/test_a1_utils.py
├── requirements.txt
├── environment.yml
└── run_a1.ps1
```

Khi ghép vào repository ECCC-LITE, chép các thư mục/tệp trên vào thư mục gốc
của repository và giữ nguyên đường dẫn tương đối.

## 3. Cách chạy trên Windows

### Cách 1 — dùng môi trường `ds_course` hiện có

Mở **Anaconda Prompt** hoặc PowerShell đã kích hoạt Conda:

```powershell
conda activate ds_course
cd "DUONG_DAN_DEN_ECCC-LITE-A1"
python -m pip install -r requirements.txt
python scripts/run_a1.py
```

Lệnh cuối tự thực hiện ba việc: tải/kiểm chứng dữ liệu, chạy toàn bộ notebook và
kiểm tra đầu ra.

Từ lần chạy thứ hai, có thể bỏ bước tải:

```powershell
python scripts/run_a1.py --skip-download
```

### Cách 2 — tạo môi trường riêng

```powershell
conda env create -f environment.yml
conda activate eccc-lite
python scripts/run_a1.py
```

### Cách 3 — mở notebook để học từng cell

```powershell
jupyter lab notebooks/01_data_eda.ipynb
```

Sau khi mở: **Kernel → Restart Kernel and Run All Cells**. Chỉ chạy khi
`data/raw/creditcard.csv` đã được tải đúng.

## 4. Đầu ra bắt buộc

Sau một lần chạy chuẩn, phải có:

```text
data/processed/train.csv
data/processed/validation.csv
data/processed/test.csv
outputs/tables/data_audit.csv
outputs/tables/split_summary.csv
outputs/tables/train_class_summary.csv
outputs/tables/feature_contract.json
outputs/figures/class_distribution.png
outputs/figures/amount_by_class.png
outputs/figures/time_by_class.png
outputs/figures/selected_correlations.png
outputs/notebooks/01_data_eda.executed.ipynb
```

Giá trị kiểm tra cho bản dữ liệu chuẩn:

| Tập | Số dòng | Class 0 | Class 1 |
|---|---:|---:|---:|
| Raw | 284.807 | 284.315 | 492 |
| Sau bỏ trùng | 283.726 | 283.253 | 473 |
| Train | 170.235 | 169.951 | 284 |
| Validation | 56.745 | 56.651 | 94 |
| Test | 56.746 | 56.651 | 95 |

## 5. Kiểm tra trước bàn giao

```powershell
python -m pytest -q
python scripts/smoke_test_notebook.py
python scripts/verify_a1_outputs.py
```

- `pytest`: kiểm tra utility, duplicate, split và leakage contract mà không cần
  dữ liệu thật.
- `smoke_test_notebook.py`: thực thi tuần tự mọi code cell trên dữ liệu tổng hợp
  tạm thời; dữ liệu này bị xóa ngay và không dùng cho báo cáo.
- `verify_a1_outputs.py`: kiểm tra đầu ra thật theo số liệu chuẩn.

Nếu bất kỳ lệnh nào lỗi, không bàn giao split và không chép số vào báo cáo.

## 6. Nguồn dữ liệu

- MLG-ULB/Kaggle: <https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud>
- Bản byte-identical dùng trong hướng dẫn chính thức của TensorFlow:
  <https://storage.googleapis.com/download.tensorflow.org/data/creditcard.csv>
- Hướng dẫn TensorFlow về dữ liệu mất cân bằng:
  <https://www.tensorflow.org/tutorials/structured_data/imbalanced_data>

Dữ liệu không nằm trong bộ file và không được commit lên GitHub. Mã nguồn của
dự án không thay đổi điều khoản sử dụng của bộ dữ liệu gốc.
