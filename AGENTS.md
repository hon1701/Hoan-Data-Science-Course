# Project instructions - Data Science coursework

## Project goal

Đây là project môn Cơ sở Khoa học Dữ liệu. Ưu tiên tính đúng, khả năng chạy lại
và giải thích được trước khi tối ưu hoặc mở rộng mô hình.

## Environment and structure

- Môi trường dự kiến: Conda `ds_course`.
- Hãy tự đọc repo để xác nhận thư mục notebook, `src/`, `data/`, `scripts/`, `reports/` và test thật.
- Đường dẫn dữ liệu phải chạy từ thư mục gốc repo; ưu tiên `pathlib.Path`.
- Không đổi hoặc tải lại dataset lớn khi file hợp lệ đã tồn tại.
- Không commit dataset, model hoặc output lớn nếu `.gitignore` đang loại trừ chúng.

## Notebook rules

- Giữ thứ tự cell có thể chạy từ trên xuống dưới trong kernel mới.
- Không phụ thuộc vào biến được tạo bởi cell chạy ngoài thứ tự.
- Không sửa output bằng tay để che lỗi code.
- Khi notebook lỗi, xác định rõ file, cell hoặc đoạn code liên quan.
- Với yêu cầu học, giải thích tối đa khoảng 10 cell mỗi lượt nếu người dùng không yêu cầu khác.

## Data integrity

- Không tự tạo dữ liệu giả, nhãn giả hoặc số liệu báo cáo nếu chưa được yêu cầu.
- Trước biến đổi lớn, kiểm tra `shape`, kiểu dữ liệu, missing, duplicate và phân bố nhãn.
- Tránh data leakage: split trước các phép fit có thể học từ dữ liệu.
- Với phân lớp mất cân bằng, không kết luận chỉ từ accuracy.
- Nếu dùng `predict_proba`, xác nhận đúng cột xác suất lớp dương và kiểm tra miền `[0, 1]`.
- Giữ random seed cố định khi cần tái lập và ghi rõ vị trí đặt seed.

## Fraud-detection evaluation

- Báo ROC-AUC cùng PR-AUC, precision, recall, F1 và confusion matrix khi phù hợp.
- Nếu bài yêu cầu vận hành, đánh giá Top-k ở 0.5%, 1% và 2% hoặc đúng các mức trong đề.
- Không chọn threshold từ test set; tách vai trò validation và test.
- Với threshold theo chi phí, ghi rõ công thức, giả định chi phí và đơn vị.
- Mọi con số trong báo cáo phải truy được về code hoặc output có thể tái tạo.

## Implementation

- Ưu tiên pandas, NumPy và scikit-learn đang có trong môi trường.
- Không viết lại utility đã tồn tại trong `src/`; đọc và tái sử dụng nó.
- Tránh làm sạch trùng ở notebook và module; chọn một nguồn logic chính.
- Giữ API của các hàm đang được notebook hoặc script khác sử dụng.

## Validation

Sau khi sửa, chọn các kiểm tra phù hợp với repo:

1. chạy import/syntax cho module đã đổi;
2. chạy script hoặc test liên quan;
3. chạy notebook từ kernel sạch khi môi trường cho phép;
4. kiểm tra output chính, shape, missing, split và metric;
5. xem diff và đối chiếu code với số liệu trong báo cáo.

Không giả định một lệnh cụ thể. Hãy đọc README, environment file và script của
repo để xác định lệnh thật trước khi chạy.

## Completion report

Khi kết thúc, báo: file/cell đã đổi; lỗi và nguyên nhân; cách sửa; kiểm tra đã
chạy; kết quả; rủi ro còn lại; ba kiến thức người học cần hiểu.

