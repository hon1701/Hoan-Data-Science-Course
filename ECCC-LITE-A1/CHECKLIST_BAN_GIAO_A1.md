# Checklist bàn giao A.1 — Nguyễn Văn Hoan

Chỉ đánh dấu hoàn tất sau khi chạy notebook bằng dữ liệu thật.

- [ ] `python scripts/get_data.py` báo đúng SHA-256.
- [ ] `python -m pytest -q` không có test lỗi.
- [ ] `Kernel → Restart Kernel and Run All Cells` chạy hết.
- [ ] Raw có 284.807 dòng, 492 fraud và 1.081 exact duplicates.
- [ ] Sau làm sạch có 283.726 dòng và 473 fraud.
- [ ] Train/validation/test lần lượt có 170.235/56.745/56.746 dòng.
- [ ] Fraud từng split lần lượt là 284/94/95.
- [ ] Ba split không giao nhau theo `source_row`.
- [ ] Ba file processed có cùng schema và giữ `source_row`.
- [ ] `feature_contract.json` không chứa `Class` hoặc `source_row`.
- [ ] Có `data_audit.csv`, `split_summary.csv` và bốn hình EDA.
- [ ] `python scripts/verify_a1_outputs.py` báo ba dòng `[OK]`.
- [ ] `data/raw/creditcard.csv` không xuất hiện trong `git status`.
- [ ] Chỉ gửi kết quả của lần chạy hiện tại cho Huy/Sang.

Điểm dừng: nếu một assert hoặc một kiểm tra thất bại, sửa nguyên nhân tại nguồn;
không sửa tay CSV đầu ra và không cập nhật số vào báo cáo.

