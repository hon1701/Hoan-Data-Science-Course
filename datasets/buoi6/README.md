# Dữ liệu cho Buổi 6

Các tệp trong thư mục này phục vụ notebook `notebooks/buoi_06_pandas_nang_cao_ii.ipynb`.

| Tệp | Nguồn | Quy mô kỳ vọng |
| --- | --- | --- |
| `titanic.csv` | `mwaskom/seaborn-data` | 891 dòng |
| `planets.csv` | `mwaskom/seaborn-data` | 1.035 dòng |
| `births.csv` | `jakevdp/data-CDCbirths` | 15.547 dòng |
| `movielens/movies.dat` | `wesm/pydata-book`, dữ liệu MovieLens 1M | 3.883 dòng |
| `movielens/users.dat` | `wesm/pydata-book`, dữ liệu MovieLens 1M | 6.040 dòng |
| `movielens/ratings.dat` | GroupLens MovieLens 1M | 1.000.209 dòng |

Nguồn tải:

- <https://raw.githubusercontent.com/mwaskom/seaborn-data/master/titanic.csv>
- <https://raw.githubusercontent.com/mwaskom/seaborn-data/master/planets.csv>
- <https://raw.githubusercontent.com/jakevdp/data-CDCbirths/master/births.csv>
- <https://grouplens.org/datasets/movielens/1m/>

`ratings.dat` có thể chưa có nếu việc tải MovieLens bị gián đoạn. Notebook sẽ chỉ chạy case study MovieLens khi đủ cả ba tệp và `ratings.dat` có đúng 1.000.209 dòng; các phần còn lại vẫn chạy bình thường.
