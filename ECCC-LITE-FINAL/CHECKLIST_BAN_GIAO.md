# Checklist bàn giao dự án đầy đủ

- [x] Dữ liệu raw đúng kích thước và SHA-256.
- [x] `python -m pytest -q` không có lỗi.
- [x] Bốn notebook chạy từ trên xuống dưới trong kernel mới.
- [x] A.1 đúng raw/duplicate/split và không leakage.
- [x] Modeling chỉ đọc train/validation; `modeling_summary.json` ghi `test_accessed=false`.
- [x] Feature modeling không chứa `Amount`, `Class` hoặc `source_row`.
- [x] Score Logistic/RF nằm trong `[0,1]` và có hơn 10 giá trị khác nhau.
- [x] Model chọn theo AP validation và tie-break 0,01.
- [x] Threshold chi phí và threshold F1 đều được chọn trên validation.
- [x] Test chỉ chạy sau khi model/threshold đã khóa.
- [x] Báo AP, ROC-AUC, Precision, Recall, F1 và confusion matrix.
- [x] Top-0,5%/1%/2% có TP, FP, Precision, Recall và Lift.
- [x] FP/FN được truy vết bằng `source_row`, không suy diễn biến ẩn danh.
- [x] Mọi số trong báo cáo truy được về `outputs/tables/`.
- [x] `BaoCao_NOP.docx` đã render và kiểm tra toàn bộ trang.
- [x] `data/raw/creditcard.csv`, processed CSV và model không xuất hiện trong Git.
