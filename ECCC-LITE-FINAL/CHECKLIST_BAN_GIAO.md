# Checklist bàn giao dự án đầy đủ

- [ ] Dữ liệu raw đúng kích thước và SHA-256.
- [ ] `python -m pytest -q` không có lỗi.
- [ ] Bốn notebook chạy từ trên xuống dưới trong kernel mới.
- [ ] A.1 đúng raw/duplicate/split và không leakage.
- [ ] Modeling chỉ đọc train/validation; `modeling_summary.json` ghi `test_accessed=false`.
- [ ] Feature modeling không chứa `Amount`, `Class` hoặc `source_row`.
- [ ] Score Logistic/RF nằm trong `[0,1]` và có hơn 10 giá trị khác nhau.
- [ ] Model chọn theo AP validation và tie-break 0,01.
- [ ] Threshold chi phí và threshold F1 đều được chọn trên validation.
- [ ] Test chỉ chạy sau khi model/threshold đã khóa.
- [ ] Báo AP, ROC-AUC, Precision, Recall, F1 và confusion matrix.
- [ ] Top-0,5%/1%/2% có TP, FP, Precision, Recall và Lift.
- [ ] FP/FN được truy vết bằng `source_row`, không suy diễn biến ẩn danh.
- [ ] Mọi số trong báo cáo truy được về `outputs/tables/`.
- [ ] `BaoCao_NOP.docx` đã render và kiểm tra toàn bộ trang.
- [ ] `data/raw/creditcard.csv`, processed CSV và model không xuất hiện trong Git.

