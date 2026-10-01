# Checklist bàn giao

## Kiểm tra dữ liệu, code và notebook

- [x] `creditcard.csv` tải từ nguồn công khai; kích thước và SHA-256 khớp manifest.
- [x] Audit ghi nhận 284.807 dòng gốc, 1.081 dòng trùng bị loại, 283.726 dòng sạch và 473 fraud còn lại.
- [x] Buổi 9, slide 77–78: `groupby`, `pivot_table` trên train, `LogAmount`, năm hình EDA gồm Seaborn đa biến và 2–3 câu nhận xét sau từng hình; kết luận nêu bốn phát hiện.
- [x] Chia train/validation/test 60/20/20, stratify theo `Class`, seed 42; không giao nhau.
- [x] `pytest`: 10 test đạt, gồm kiểm tra regression cho ngưỡng không cảnh báo và xử lý score trùng.
- [x] Cả bốn notebook nguồn chạy từ đầu bằng kernel mới; thứ tự EDA → modeling → evaluation → notebook tổng hợp.
- [x] Feature mô hình loại `Amount`, `Class`, `source_row`; kiểm tra miền score và lớp dương.
- [x] Chọn model bằng AP validation; ngưỡng chi phí/F1 chọn trên validation rồi khóa trước khi đánh giá test.
- [x] Báo cáo kết quả test bằng AP, ROC-AUC, Precision, Recall, F1, confusion matrix, Top-0,5%/1%/2%, bootstrap AP và phân tích FP/FN.
- [x] Hình Seaborn FP/FN trong Word được sinh từ 20 lỗi test sau khi khóa mô hình/ngưỡng bởi `src/evaluation.py`.
- [x] Kết quả báo cáo khớp `evaluation_summary.json`; verifier kiểm tra hash, ngưỡng, các metric và Top-p.

## Báo cáo và bàn giao

- [x] Word giữ bìa mẫu, có mục lục đủ 33 mục với số trang đã đối chiếu.
- [x] DOCX được dựng và PDF 22 trang được render; 33 mục lục đối chiếu đúng số trang, hình Seaborn/bảng pivot đã rà trực quan.
- [x] Có hướng dẫn chạy lại Windows PowerShell trong `README.md`.
- [x] Raw dataset, các split CSV và model huấn luyện không được đưa vào Git.
- [x] Notebook có output và bảng/hình kết quả được đóng gói riêng; log, manifest và lock phiên bản đi cùng để truy vết.

## Giới hạn cần nêu khi nộp

- Dữ liệu chỉ phủ khoảng hai ngày; V1–V28 ẩn danh và không có lịch sử khách hàng.
- Chi phí 20:1 là giả định học thuật; kết quả chưa chứng minh khả năng triển khai ngân hàng.
- Kết quả là một lần chia ngẫu nhiên phân tầng; bootstrap AP đo bất định trên test cố định, không thay thế kiểm định thời gian hay kiểm định ngoài mẫu.
