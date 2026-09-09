# Bộ notebook ôn tập Buổi 1-9

Bộ này đi theo một pipeline thống nhất thay vì chép lại slide:

```text
Python/OOP -> NumPy -> Pandas -> Load -> Clean/Combine
           -> GroupBy/Pivot -> String/Time -> Visualization -> EDA
```

## Cách học hiệu quả

1. Mở đúng môi trường Conda `ds_course` và chạy notebook từ trên xuống.
2. Trả lời phần **Chẩn đoán nhanh** trước khi mở đáp án.
3. Ở mỗi cell, đoán output trước khi chạy và giải thích theo ba ý: đầu vào, phép biến đổi, đầu ra.
4. Làm **Bài tự luyện** trước khi mở gợi ý.
5. Chỉ chuyển buổi khi hoàn thành **Phiếu rời buổi**; nếu chưa chắc, quay lại đúng mục trong slide được dẫn.

Các notebook dùng `numpy`, `pandas`, `matplotlib` và `seaborn`. Riêng môi trường hiện tại đã được bổ sung `seaborn==0.13.2` để chạy Buổi 9.

## Lộ trình

| Buổi | Notebook | Trọng tâm |
|---:|---|---|
| 1 | [on_tap_01_python_oop.ipynb](on_tap_01_python_oop.ipynb) | Workflow, object, class, state, `fit/transform` |
| 2 | [on_tap_02_numpy.ipynb](on_tap_02_numpy.ipynb) | ndarray, axis, vectorization, broadcasting |
| 3 | [on_tap_03_pandas_co_ban.ipynb](on_tap_03_pandas_co_ban.ipynb) | Series, DataFrame, `loc/iloc`, alignment |
| 4 | [on_tap_04_doc_du_lieu.ipynb](on_tap_04_doc_du_lieu.ipynb) | CSV/JSON, tham số đọc file, chunk |
| 5 | [on_tap_05_missing_combine.ipynb](on_tap_05_missing_combine.ipynb) | Missing, MultiIndex, concat, merge |
| 6 | [on_tap_06_cleaning_groupby_pivot.ipynb](on_tap_06_cleaning_groupby_pivot.ipynb) | Cleaning, GroupBy, Pivot Table |
| 7 | [on_tap_07_string_time_series.ipynb](on_tap_07_string_time_series.ipynb) | `.str`, datetime, resample, rolling |
| 8 | [on_tap_08_matplotlib.ipynb](on_tap_08_matplotlib.ipynb) | Figure/Axes và chọn biểu đồ |
| 9 | [on_tap_09_seaborn_eda.ipynb](on_tap_09_seaborn_eda.ipynb) | Seaborn và EDA end-to-end |

## Tự rà theo 5 tầng

- Tầng 1: NumPy.
- Tầng 2: Pandas cơ bản và đọc dữ liệu.
- Tầng 3: Cleaning, missing và combine.
- Tầng 4: GroupBy, Pivot, String và Time Series.
- Tầng 5: Visualization và EDA.

Không cần học lại tuần tự nếu chỉ vướng một tầng. Hãy bắt đầu từ notebook của tầng đó, làm phần chẩn đoán và quay lại buổi trước chỉ khi thiếu kiến thức nền.

## Tái tạo bộ notebook

Chạy `scripts/build_review_notebooks.py` từ thư mục gốc repo. Script chỉ tạo lại chín file `on_tap_*.ipynb` trong thư mục này.
