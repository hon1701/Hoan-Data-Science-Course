# ECCC-LITE — Xếp hạng nguy cơ gian lận thẻ

Dự án môn Cơ sở Khoa học Dữ liệu: kiểm chứng dữ liệu, EDA, huấn luyện và so sánh mô hình, khóa lựa chọn trên validation, đánh giá test, xếp hạng Top-p và lập báo cáo có thể truy vết.

## Kết quả đã xác minh

- GitHub Actions run [36662669830](https://github.com/hon1701/Hoan-Data-Science-Course/actions/runs/36662669830): dữ liệu thật qua kiểm tra SHA-256, 10 test đạt, bốn notebook chạy trong kernel mới; báo cáo Word được dựng và verifier xác nhận.
- Chọn Random Forest `standard` theo AP validation **0,8782** (Logistic Regression: **0,7983**). Threshold chi phí được khóa trên validation ở **0,222083**, với giả định học thuật FN:FP = 20:1.
- Trên test (56.746 giao dịch, 95 fraud): AP **0,7922**, ROC-AUC **0,9324**, Precision **0,8795**, Recall **0,7684**, F1 **0,8202**; phát hiện 73/95 fraud, có 10 cảnh báo nhầm.
- Top 1% (568 giao dịch điểm cao nhất) thu hồi **79/95 fraud** (Recall **83,16%**). Bảng Top 0,5%/1%/2% và khoảng tin cậy AP bootstrap nằm trong báo cáo và bảng kết quả.
- Báo cáo Word khớp `evaluation_summary.json`; PDF 22 trang có bảng pivot và hình Seaborn từ train, 33 mục lục được đối chiếu đúng trang.

## Quy tắc thực nghiệm đã khóa

- Nguồn `creditcard.csv`, 150.828.752 byte, SHA-256 `76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89`.
- Loại 1.081 dòng trùng chính xác; chia train/validation/test 60/20/20 có phân tầng theo `Class`, seed 42.
- EDA và các bước fit chỉ dùng train. Feature mô hình gồm `Time`, `V1`–`V28`, `LogAmount`; không dùng `Amount`, `Class` hay `source_row` làm feature.
- `groupby` và `pivot_table` tổng hợp từ từng dòng train; năm hình EDA có bốn kiểu biểu đồ trở lên, gồm scatterplot đa biến bằng Seaborn và 2–3 câu nhận xét ngay sau mỗi hình. Scatterplot lấy mẫu 5.000 giao dịch hợp lệ và giữ toàn bộ 284 fraud để dễ quan sát, nên tỷ lệ màu không đại diện prevalence.
- So sánh Dummy, Logistic Regression và Random Forest bằng Average Precision trên validation; nếu Logistic và Random Forest chênh dưới 0,01 thì ưu tiên Logistic Regression.
- Threshold chi phí tối thiểu hóa `20 × FN + FP` trên validation. Test chỉ được đánh giá sau khi model và threshold đã được khóa.
- Top-p lấy `ceil(p × N)` dòng; score bằng nhau được phân xử theo `source_row` tăng dần.

## Đối chiếu yêu cầu đồ án Buổi 9, slide 77–78

| Yêu cầu | Bằng chứng chạy lại |
| --- | --- |
| Dữ liệu thật, làm sạch, schema, missing/trùng | `notebooks/01_data_eda.ipynb`, `data_audit.csv` và SHA-256 trong manifest |
| `groupby`, `pivot_table`, biến phái sinh | Cell mục 6–7; `train_class_summary.csv`, `train_time_class_pivot.csv`, `LogAmount` |
| Tối thiểu bốn loại biểu đồ và Seaborn đa biến | Bar, histogram, boxplot, thanh tương quan, scatterplot `sns.scatterplot` trên train |
| Mỗi hình 2–3 câu và 3–5 phát hiện | Markdown ngay sau năm hình; mục “Bốn phát hiện từ train” của notebook 01 |
| Có thể Restart & Run All | Bốn notebook được chạy trong kernel mới bằng `scripts/run_full_project.py`; CI lưu bản đã chạy trong artifact |

Biểu đồ Seaborn lấy 5.000 giao dịch hợp lệ và toàn bộ 284 fraud trên train với seed cố định để nhìn lớp hiếm; không đọc test và không dùng tỷ lệ màu làm tỷ lệ gian lận thật.

## Cấu trúc chính

```text
ECCC-LITE-FINAL/
├── notebooks/                  # 4 notebook nguồn
├── src/                         # tiện ích dữ liệu, modeling, evaluation
├── scripts/                     # chạy pipeline, tạo báo cáo, verifier
├── tests/                       # regression/unit tests
├── outputs/                     # sinh ra khi chạy, không commit dữ liệu lớn
└── reports/                     # báo cáo Word/PDF và dữ liệu mục lục
```

## Chạy lại trên Windows PowerShell

```powershell
# Tạo môi trường một lần, từ thư mục dự án:
conda env create -f environment.yml
conda activate eccc-lite

python -m pip install -r requirements.txt
python -X utf8 scripts/run_full_project.py
```

Hoặc chạy `.\run_project.ps1`. Pipeline tải/kiểm chứng dữ liệu khi chưa có bản hash hợp lệ, chạy test, thực thi bốn notebook theo thứ tự đã nêu, đối chiếu metric rồi tạo và kiểm tra báo cáo Word. Có thể mở notebook đã chạy trong `outputs/notebooks/`.

Các lệnh kiểm tra riêng:

```powershell
python -m pytest -q
python -X utf8 scripts/verify_project.py
python -X utf8 scripts/verify_report.py
```

`outputs/requirements-lock.txt` ghi phiên bản của lần chạy CI. Các notebook nguồn ở `notebooks/`; notebook có output và bằng chứng kết quả nằm trong gói dự án đầy đủ. Raw CSV, split CSV và model được loại khỏi Git vì kích thước lớn, được tái tạo qua pipeline.

## Artifact và báo cáo

- `outputs/tables/evaluation_summary.json`: kết quả chuẩn dùng dựng báo cáo.
- `outputs/tables/decision_lock.json`: model, feature và threshold đã khóa.
- `outputs/tables/model_candidates.csv`, `model_comparison.csv`, `top_p_metrics.csv`: so sánh và kết quả Top-p.
- `outputs/tables/train_time_class_pivot.csv`: pivot Time × Class từ train và tỷ lệ fraud theo cửa sổ.
- `outputs/figures/`: năm biểu đồ EDA trên train, các hình đánh giá và `seaborn_error_cases_multivariate.png` mô tả lỗi test sau khi khóa quyết định.
- `outputs/notebooks/*.executed.ipynb`: bốn notebook có kết quả chạy.
- `reports/BaoCao_NOP.docx` và `reports/BaoCao_NOP.pdf`: báo cáo bàn giao.
- `CHECKLIST_BAN_GIAO.md`: danh sách bằng chứng đã đối chiếu.

## Giới hạn

Dữ liệu chỉ bao phủ khoảng hai ngày, `V1`–`V28` đã ẩn danh và thiếu lịch sử khách hàng. Tỷ lệ chi phí FN/FP là giả định học thuật. Score chỉ hỗ trợ xếp hạng để ưu tiên kiểm tra, chưa phải mô hình triển khai trong ngân hàng hay quyết định tự động khóa thẻ.
