# Dữ liệu gốc

Không commit `creditcard.csv` lên GitHub. Từ thư mục gốc dự án, chạy:

```powershell
python scripts/get_data.py
```

Hoặc tải thủ công bộ **Credit Card Fraud Detection** của MLG-ULB trên Kaggle,
giải nén và đặt đúng tại:

```text
data/raw/creditcard.csv
```

Notebook chỉ chấp nhận bản chuẩn có:

- 150.828.752 byte;
- SHA-256 `76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89`;
- 284.807 dòng, 31 cột và 492 giao dịch `Class = 1`.

Không mở rồi lưu lại CSV bằng Excel vì thao tác đó có thể làm đổi byte và SHA-256.

