"""Tạo bộ notebook ôn tập Buổi 1-9 từ một nguồn nội dung có thể tái tạo."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks"


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": dedent(text).strip() + "\n"}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(text).strip() + "\n",
    }


def notebook(cells: list[dict]) -> dict:
    for index, cell in enumerate(cells, 1):
        cell["id"] = f"cell-{index:03d}"
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python (ds_course)",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def setup(imports: str = "") -> dict:
    source = dedent(
        """
        from pathlib import Path

        HERE = Path.cwd().resolve()
        ROOT = next(
            (p for p in (HERE, *HERE.parents) if (p / "datasets").exists() and (p / "slides").exists()),
            None,
        )
        assert ROOT is not None, "Hãy mở notebook từ bên trong repo Hoan-Data-Science-Course."
        """
    ).strip()
    source += f"\n{imports.strip()}\nprint(f'Repo: {{ROOT}}')"
    return code(source)


def intro(number: int, title: str, duration: str, goals: list[str]) -> dict:
    goal_lines = "\n".join(f"- {goal}" for goal in goals)
    return md(
        f"""
        # Ôn tập Buổi {number:02d} - {title}

        **Thời lượng gợi ý:** {duration}  
        **Cách học:** trả lời câu hỏi trước khi chạy cell; sau mỗi ví dụ, tự nói thành lời *đầu vào - phép biến đổi - đầu ra*.

        ## Mục tiêu

        {goal_lines}

        > Notebook này là tài liệu ôn chủ động, không thay thế toàn bộ slide. Khi một câu tự kiểm tra chưa chắc, quay lại đúng mục tương ứng trong `slides/buoi{number}_python_datascience.pdf`.
        """
    )


def diagnostic(questions: list[tuple[str, str]]) -> dict:
    items = []
    for idx, (question, answer) in enumerate(questions, 1):
        items.append(
            f"**{idx}. {question}**\n\n<details><summary>Kiểm tra đáp án</summary>\n\n{answer}\n\n</details>"
        )
    return md("## 0. Chẩn đoán nhanh - chưa chạy code\n\n" + "\n\n".join(items))


def practice(prompt: str, answer: str) -> dict:
    return md(
        f"""
        ## Bài tự luyện

        {prompt}

        <details><summary>Gợi ý / đáp án tham khảo</summary>

        ```python
        {dedent(answer).strip()}
        ```

        </details>
        """
    )


def exit_ticket(items: list[str]) -> dict:
    checks = "\n".join(f"- [ ] {item}" for item in items)
    return md(
        f"""
        ## Phiếu rời buổi

        Không nhìn lại notebook, hãy tự xác nhận:

        {checks}

        Nếu chưa đánh dấu được một mục, ghi lại **một ví dụ do chính bạn nghĩ ra** rồi chạy thử.
        """
    )


def build_01() -> list[dict]:
    return [
        intro(1, "Data Science Foundation, Python và OOP", "45-60 phút", [
            "Đặt một thao tác vào đúng bước của Data Science workflow.",
            "Phân biệt class, object, attribute, method và object state.",
            "Hiểu vì sao API Data Science thường dùng `fit()`, `transform()` và `predict()`.",
        ]),
        setup("import sys\nprint(f\"Python: {sys.version.split()[0]}\")"),
        diagnostic([
            ("Trong `df.head()`, đâu là object và đâu là method?", "`df` là object; `head` là method của object đó."),
            ("Data Cleaning đứng trước hay sau EDA?", "Thường đứng trước EDA chi tiết, nhưng kiểm tra khám phá ban đầu có thể lặp lại để định hướng cleaning."),
            ("Sau `fit()`, một scaler lưu điều gì?", "Object state đã học từ training data, ví dụ mean và standard deviation."),
        ]),
        md("""
        ## 1. Bản đồ tổng thể

        ```text
        Business question -> Collect -> Clean -> EDA -> Features -> Model -> Evaluate -> Communicate/Deploy
        ```

        Công cụ chỉ có ý nghĩa khi gắn với câu hỏi. `dropna()` thuộc Cleaning; `hist()` thuộc EDA; `predict()` thuộc Modeling/Inference.
        """),
        code("""
        workflow = {
            "dropna": "Cleaning",
            "hist": "EDA",
            "fit": "Modeling",
            "precision": "Evaluation",
        }
        assert workflow["dropna"] == "Cleaning"
        workflow
        """),
        md("""
        ## 2. Built-in object trước khi tự tạo class

        **Đoán trước:** sau cell dưới, `unique_labels` có giữ thứ tự và phần tử trùng không?
        """),
        code("""
        features = ["age", "income", "age"]
        customer = {"id": "C001", "monthly_fee": 25.0}
        unique_labels = set(features)

        print(features[0], customer["id"], unique_labels)
        assert unique_labels == {"age", "income"}
        """),
        md("""
        ## 3. Class, object, attribute, method

        `DatasetSummary` đóng gói dữ liệu và hành vi liên quan. Property `n_rows` được tính từ state hiện tại thay vì lưu lặp lại.
        """),
        code("""
        class DatasetSummary:
            dataset_count = 0

            def __init__(self, name, values):
                self.name = name
                self.values = list(values)
                DatasetSummary.dataset_count += 1

            @property
            def n_rows(self):
                return len(self.values)

            def mean(self):
                if not self.values:
                    raise ValueError("Không thể tính mean của dữ liệu rỗng")
                return sum(self.values) / self.n_rows

            def __repr__(self):
                return f"DatasetSummary(name={self.name!r}, n_rows={self.n_rows})"

        scores = DatasetSummary("scores", [7.0, 8.5, 9.0])
        print(scores)
        print("mean =", scores.mean())
        assert scores.n_rows == 3 and scores.mean() == 8.166666666666666
        """),
        md("""
        ## 4. Object state và giao diện `fit/transform`

        **Điểm chống data leakage:** chỉ `fit()` trên training data; validation/test chỉ được `transform()` bằng state đã học.
        """),
        code("""
        class MeanCenterer:
            def fit(self, values):
                self.mean_ = sum(values) / len(values)
                return self

            def transform(self, values):
                if not hasattr(self, "mean_"):
                    raise RuntimeError("Phải fit trước khi transform")
                return [value - self.mean_ for value in values]

            def fit_transform(self, values):
                return self.fit(values).transform(values)

        train = [10, 12, 14]
        test = [20, 22]
        centerer = MeanCenterer().fit(train)
        train_centered = centerer.transform(train)
        test_centered = centerer.transform(test)

        print(centerer.mean_, train_centered, test_centered)
        assert centerer.mean_ == 12
        assert test_centered == [8, 10]
        """),
        practice(
            "Viết class `MinMaxScalerLite` có `fit()` lưu `min_`, `max_` và `transform()` đưa dữ liệu về `[0, 1]`. Báo lỗi nếu `max_ == min_`.",
            """
            class MinMaxScalerLite:
                def fit(self, values):
                    self.min_ = min(values)
                    self.max_ = max(values)
                    if self.max_ == self.min_:
                        raise ValueError("Không thể scale khi mọi giá trị bằng nhau")
                    return self

                def transform(self, values):
                    return [(x - self.min_) / (self.max_ - self.min_) for x in values]
            """,
        ),
        exit_ticket([
            "Tôi giải thích được pipeline Data Science bằng một ví dụ thực tế.",
            "Tôi phân biệt được class/object và attribute/method.",
            "Tôi giải thích được object state và vì sao chỉ fit trên train.",
        ]),
    ]


def build_02() -> list[dict]:
    return [
        intro(2, "NumPy Foundation", "60-75 phút", [
            "Đọc shape, dtype, axis và dự đoán đầu ra của phép toán mảng.",
            "Dùng vectorization, broadcasting, boolean mask và fancy indexing.",
            "Phân biệt view/copy và giải hồi quy tuyến tính nhỏ bằng `lstsq`.",
        ]),
        setup("import numpy as np\nprint(f\"NumPy: {np.__version__}\")"),
        diagnostic([
            ("Mảng shape `(3, 4)` có `sum(axis=0)` shape gì?", "`(4,)`: gộp theo chiều hàng, còn lại một kết quả cho mỗi cột."),
            ("Slicing NumPy thường trả về view hay copy?", "Thường là view; fancy indexing thường trả về copy."),
            ("Hai shape `(5, 3)` và `(3,)` có broadcast được không?", "Có; so từ chiều cuối: `3` khớp `3`."),
        ]),
        md("## 1. `ndarray`: shape, dtype, axis"),
        code("""
        x = np.arange(1, 13).reshape(3, 4)
        print(x)
        print("ndim:", x.ndim, "shape:", x.shape, "size:", x.size, "dtype:", x.dtype)
        print("theo cột:", x.sum(axis=0))
        print("theo hàng:", x.sum(axis=1))
        assert x.sum(axis=0).shape == (4,)
        assert x.sum(axis=1).shape == (3,)
        """),
        md("""
        ## 2. Indexing, slicing và view/copy

        **Đoán trước:** sửa `view[0]` có làm `a` đổi không? Còn `copied[0]`?
        """),
        code("""
        a = np.array([10, 20, 30, 40, 50])
        view = a[1:4]
        copied = a[[1, 2, 3]]
        view[0] = 999
        copied[1] = -1
        print("a:", a, "| view:", view, "| copied:", copied)
        assert a.tolist() == [10, 999, 30, 40, 50]
        assert copied.tolist() == [20, -1, 40]
        """),
        md("## 3. Vectorization, UFunc và aggregation"),
        code("""
        values = np.array([1.0, 4.0, 9.0, 16.0])
        roots = np.sqrt(values)
        standardized = (values - values.mean()) / values.std()
        print(roots)
        print(np.round(standardized, 3))
        assert np.allclose(roots, [1, 2, 3, 4])
        assert np.isclose(standardized.mean(), 0)
        """),
        md("""
        ## 4. Broadcasting và boolean mask

        `X - X.mean(axis=0)` trừ mean tương ứng khỏi từng cột vì vector `(3,)` được broadcast qua 4 hàng.
        """),
        code("""
        X = np.array([[10, 100, 1], [20, 120, 0], [30, 110, 1], [40, 130, 0]])
        centered = X - X.mean(axis=0)
        high_first_feature = X[X[:, 0] >= 30]
        print(centered)
        print(high_first_feature)
        assert np.allclose(centered.mean(axis=0), 0)
        assert high_first_feature.shape == (2, 3)
        """),
        md("## 5. Sorting và vị trí"),
        code("""
        scores = np.array([7.5, 9.0, 6.5, 8.5])
        order = np.argsort(scores)[::-1]
        print("thứ tự giảm dần:", order)
        print("điểm đã sắp:", scores[order])
        assert order[0] == scores.argmax()
        """),
        md("## 6. Ứng dụng: hồi quy tuyến tính bằng least squares"),
        code("""
        x_train = np.array([0., 1., 2., 3., 4.])
        y_train = np.array([1., 3., 5., 7., 9.])
        design = np.column_stack([x_train, np.ones_like(x_train)])
        slope, intercept = np.linalg.lstsq(design, y_train, rcond=None)[0]
        predictions = design @ np.array([slope, intercept])
        print(f"y = {slope:.1f}x + {intercept:.1f}")
        assert np.allclose([slope, intercept], [2, 1])
        assert np.allclose(predictions, y_train)
        """),
        practice(
            "Với ma trận `M = np.arange(20).reshape(5, 4)`: chuẩn hóa từng cột về z-score, rồi lấy các hàng có giá trị cột cuối lớn hơn mean cột cuối.",
            """
            M = np.arange(20).reshape(5, 4)
            z = (M - M.mean(axis=0)) / M.std(axis=0)
            selected = M[M[:, -1] > M[:, -1].mean()]
            """,
        ),
        exit_ticket([
            "Tôi đọc đúng `axis=0` và `axis=1`.",
            "Tôi biết khi nào slicing có thể làm đổi mảng gốc.",
            "Tôi kiểm tra broadcasting bằng cách so shape từ chiều cuối.",
        ]),
    ]


def build_03() -> list[dict]:
    return [
        intro(3, "Pandas Foundation", "60 phút", [
            "Tạo và kiểm tra Series/DataFrame có index.",
            "Chọn dữ liệu đúng bằng `loc`, `iloc` và boolean indexing.",
            "Nhận ra cơ chế alignment theo nhãn khi tính toán.",
        ]),
        setup("import numpy as np\nimport pandas as pd\nprint(f\"pandas: {pd.__version__}\")"),
        diagnostic([
            ("`loc` chọn theo gì? `iloc` chọn theo gì?", "`loc` theo label; `iloc` theo integer position."),
            ("Hai Series cộng nhau nhưng index lệch thì sao?", "Pandas căn chỉnh theo label; label thiếu ở một phía thường cho `NaN`."),
            ("Vì sao phải đặt ngoặc quanh từng điều kiện boolean?", "Do độ ưu tiên toán tử; mỗi điều kiện phải tạo Series boolean trước khi nối bằng `&`/`|`."),
        ]),
        md("## 1. Series = mảng 1D + index"),
        code("""
        scores = pd.Series([8.5, 7.0, 9.0], index=["An", "Binh", "Chi"], name="score")
        print(scores)
        print("label:", scores.loc["Binh"], "| position:", scores.iloc[1])
        assert scores.loc["Binh"] == scores.iloc[1] == 7.0
        """),
        md("""
        ## 2. Alignment - sức mạnh và cũng là bẫy

        **Đoán trước:** kết quả có bao nhiêu `NaN` khi hai Series không có cùng index?
        """),
        code("""
        midterm = pd.Series({"An": 8.0, "Binh": 7.0, "Chi": 9.0})
        final = pd.Series({"An": 9.0, "Chi": 8.0, "Dung": 7.5})
        average = (midterm + final) / 2
        print(average)
        assert average.isna().sum() == 2
        """),
        md("## 3. DataFrame và bộ kiểm tra phản xạ"),
        code("""
        students = pd.DataFrame({
            "name": ["An", "Binh", "Chi", "Dung", "Em"],
            "age": [20, 21, 20, 22, 21],
            "score": [8.5, 6.0, 9.0, np.nan, 7.5],
            "class": ["A", "A", "B", "B", "A"],
        })
        display(students.head())
        print("shape:", students.shape)
        display(students.dtypes.rename("dtype"))
        display(students.describe(include="all"))
        assert students.shape == (5, 4)
        """),
        md("## 4. Chọn dữ liệu: cột -> hàng/cột -> điều kiện"),
        code("""
        one_column = students["score"]
        by_label = students.loc[1:3, ["name", "score"]]
        by_position = students.iloc[:3, [0, 2]]
        strong = students[(students["score"] >= 8) & (students["age"] <= 20)]

        display(by_label)
        display(by_position)
        display(strong)
        assert one_column.ndim == 1
        assert strong["name"].tolist() == ["An", "Chi"]
        """),
        md("""
        ## 5. Biến đổi cột không dùng loop

        `assign()` tạo DataFrame mới; biểu thức cột được vector hóa và giữ index.
        """),
        code("""
        enriched = students.assign(
            passed=students["score"].ge(5),
            score_10=students["score"].clip(0, 10),
        ).sort_values("score", ascending=False, na_position="last")
        display(enriched)
        assert enriched.iloc[0]["name"] == "Chi"
        """),
        practice(
            "Từ `students`, lấy các bạn lớp A không thiếu điểm, chỉ giữ `name`, `score`, sắp điểm giảm dần và đặt `name` làm index.",
            """
            answer = (
                students.loc[(students["class"] == "A") & students["score"].notna(), ["name", "score"]]
                .sort_values("score", ascending=False)
                .set_index("name")
            )
            """,
        ),
        exit_ticket([
            "Tôi phân biệt Series với DataFrame một cột.",
            "Tôi chọn đúng `loc`/`iloc` và viết điều kiện nhiều vế.",
            "Tôi luôn kiểm tra shape, dtype, missing trước phân tích.",
        ]),
    ]


def build_04() -> list[dict]:
    return [
        intro(4, "Data Loading", "45-60 phút", [
            "Dùng `Path` và đọc CSV có header/separator/missing khác nhau.",
            "Kiểm tra dữ liệu ngay sau khi load.",
            "Đọc file lớn theo chunk mà không nạp toàn bộ vào RAM.",
        ]),
        setup("import json\nimport pandas as pd\nfrom io import StringIO\nDATA_DIR = ROOT / 'datasets' / 'pydata_book_examples'"),
        diagnostic([
            ("File không có header thì tham số nào cần dùng?", "`header=None`, thường đi cùng `names=[...]`."),
            ("`na_values` có tác dụng gì?", "Khai báo thêm các sentinel trong file cần coi là missing."),
            ("`chunksize=1000` trả về DataFrame hay iterator?", "Một `TextFileReader` để lặp qua từng DataFrame nhỏ."),
        ]),
        md("## 1. Quy trình Load -> Inspect -> Validate"),
        code("""
        ex1 = pd.read_csv(DATA_DIR / "ex1.csv")
        display(ex1.head())
        print(ex1.shape)
        display(ex1.dtypes.rename("dtype"))
        print("missing:", ex1.isna().sum().sum())
        assert ex1.shape == (3, 5)
        """),
        md("## 2. Không có header và separator là khoảng trắng"),
        code("""
        names = ["a", "b", "c", "d", "message"]
        ex2 = pd.read_csv(DATA_DIR / "ex2.csv", header=None, names=names)
        ex3 = pd.read_csv(DATA_DIR / "ex3.txt", sep=r"\\s+")
        display(ex2)
        display(ex3.head())
        assert ex2.columns.tolist() == names
        assert ex3.shape[1] == 3
        """),
        md("## 3. Bỏ dòng chú thích và khai báo missing"),
        code("""
        ex4 = pd.read_csv(DATA_DIR / "ex4.csv", skiprows=[0, 2, 3])
        ex5_default = pd.read_csv(DATA_DIR / "ex5.csv")
        ex5_custom = pd.read_csv(
            DATA_DIR / "ex5.csv",
            keep_default_na=False,
            na_values={"message": ["NA"], "c": [""]},
        )
        display(ex4)
        display(ex5_custom)
        assert ex4.shape == (3, 5)
        assert ex5_default.isna().sum().sum() == 2
        assert ex5_custom.isna().sum().sum() == 2
        """),
        md("""
        ## 4. File lớn: xử lý theo chunk

        Ví dụ tính tổng cột `one` mà mỗi lần chỉ giữ một phần dữ liệu trong bộ nhớ.
        """),
        code("""
        total = 0.0
        row_count = 0
        for chunk in pd.read_csv(DATA_DIR / "ex6.csv", chunksize=1000):
            total += chunk["one"].sum()
            row_count += len(chunk)
        print("rows:", row_count, "| sum(one):", round(total, 4))
        assert row_count > 1000
        """),
        md("## 5. JSON: cấu trúc lồng nhau cần normalize"),
        code("""
        raw = '''[
          {"id": 1, "student": {"name": "An", "class": "A"}, "scores": [8, 9]},
          {"id": 2, "student": {"name": "Binh", "class": "B"}, "scores": [7, 8]}
        ]'''
        records = json.loads(raw)
        flat = pd.json_normalize(records)
        display(flat)
        assert "student.name" in flat.columns
        """),
        practice(
            "Đọc `ex5.csv` với cột `something` làm index; coi chuỗi `NA` là missing nhưng giữ các quy ước missing mặc định. Kiểm tra shape và số missing theo cột.",
            """
            answer = pd.read_csv(DATA_DIR / "ex5.csv", index_col="something", na_values=["NA"])
            print(answer.shape)
            print(answer.isna().sum())
            """,
        ),
        exit_ticket([
            "Tôi biết chọn `header`, `names`, `sep`, `index_col`, `skiprows`, `na_values`.",
            "Tôi kiểm tra shape/dtype/missing ngay sau khi đọc.",
            "Tôi biết khi nào dùng `nrows` và `chunksize`.",
        ]),
    ]


def build_05() -> list[dict]:
    return [
        intro(5, "Missing Data và Combine", "60-75 phút", [
            "Chọn chiến lược missing dựa trên ý nghĩa dữ liệu.",
            "Phân biệt `concat` với `merge/join`.",
            "Kiểm tra tính toàn vẹn khóa khi ghép bảng.",
        ]),
        setup("import numpy as np\nimport pandas as pd\nSTATE_DIR = ROOT / 'datasets' / 'buoi5' / 'state'\nBABY_DIR = ROOT / 'datasets' / 'buoi5' / 'babynames_sample'"),
        diagnostic([
            ("Có `NaN` thì luôn `dropna()` đúng không?", "Không. Phải xét nguyên nhân thiếu, vai trò cột và chi phí mất dòng."),
            ("`concat` và `merge` khác nhau ở đâu?", "`concat` ghép theo trục; `merge` khớp bản ghi theo key."),
            ("Vì sao `validate='many_to_one'` hữu ích?", "Nó phát hiện key ở bảng phía `one` bị trùng, tránh nhân số dòng ngoài ý muốn."),
        ]),
        md("## 1. Audit missing trước khi xử lý"),
        code("""
        students = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "score": [8.0, np.nan, 7.5, np.nan, 9.0],
            "city": ["HCM", "HN", None, "HCM", "HN"],
        })
        missing_report = students.isna().agg(["sum", "mean"]).T
        missing_report.columns = ["missing_count", "missing_rate"]
        display(missing_report)
        assert missing_report.loc["score", "missing_count"] == 2
        """),
        md("""
        ## 2. Drop hay fill phải có lý do

        Ví dụ minh họa dùng median cho `score` vì ít nhạy với cực trị hơn mean. Đây không phải quy tắc áp cho mọi dataset.
        """),
        code("""
        cleaned = students.copy()
        cleaned["score"] = cleaned["score"].fillna(cleaned["score"].median())
        cleaned["city"] = cleaned["city"].fillna("Unknown")
        display(cleaned)
        assert cleaned.isna().sum().sum() == 0
        """),
        md("## 3. MultiIndex, `stack()` và `unstack()`"),
        code("""
        series = pd.Series(
            [100, 110, 90, 95],
            index=pd.MultiIndex.from_product([["HCM", "HN"], [2025, 2026]], names=["city", "year"]),
            name="population_index",
        )
        wide = series.unstack("year")
        long_again = wide.stack().rename("population_index")
        display(wide)
        assert long_again.sort_index().equals(series.sort_index())
        """),
        md("## 4. `concat`: gộp nhiều file cùng schema"),
        code("""
        pieces = []
        for path in sorted(BABY_DIR.glob("yob*.txt")):
            year = int(path.stem.removeprefix("yob"))
            piece = pd.read_csv(path, names=["name", "gender", "births"])
            piece["year"] = year
            pieces.append(piece)
        baby_names = pd.concat(pieces, ignore_index=True)
        print(baby_names.shape, sorted(baby_names["year"].unique()))
        assert baby_names["year"].nunique() == len(pieces) == 4
        """),
        md("## 5. `merge`: case study US State Population"),
        code("""
        population = pd.read_csv(STATE_DIR / "state-population.csv")
        areas = pd.read_csv(STATE_DIR / "state-areas.csv")
        abbrevs = pd.read_csv(STATE_DIR / "state-abbrevs.csv")

        merged = population.merge(
            abbrevs,
            how="left",
            left_on="state/region",
            right_on="abbreviation",
            validate="many_to_one",
            indicator=True,
        )
        print(merged["_merge"].value_counts())
        display(merged.loc[merged["state"].isna(), ["state/region"]].drop_duplicates())
        assert len(merged) == len(population)
        """),
        md("""
        Hai mã `PR` và `USA` không có trong bảng abbreviation; cần quyết định tường minh thay vì để missing âm thầm. Sau khi ghép diện tích, dòng tổng hợp toàn nước (`USA`) không phải một bang và không có diện tích trong bảng `state-areas`, nên phải được báo và loại khỏi phép tính mật độ.
        """),
        code("""
        merged["state"] = merged["state"].fillna(
            merged["state/region"].map({"PR": "Puerto Rico", "USA": "United States"})
        )
        final = merged.drop(columns=["abbreviation", "_merge"]).merge(
            areas, how="left", on="state", validate="many_to_one"
        )
        candidates_2010 = final.query("year == 2010 and ages == 'total'")
        excluded = candidates_2010.loc[
            candidates_2010[["population", "area (sq. mi)"]].isna().any(axis=1),
            ["state", "population", "area (sq. mi)"],
        ]
        print("Không đủ dữ liệu để tính density:")
        display(excluded)
        density_2010 = candidates_2010.dropna(subset=["population", "area (sq. mi)"]).assign(
            density=lambda d: d["population"] / d["area (sq. mi)"]
        )
        display(density_2010.nlargest(5, "density")[["state", "density"]])
        assert density_2010["density"].notna().all()
        """),
        practice(
            "Từ `baby_names`, tính tổng số trẻ theo `year` và `gender`, rồi chuyển thành bảng rộng có `gender` ở cột.",
            """
            answer = (
                baby_names.groupby(["year", "gender"], as_index=False)["births"].sum()
                .pivot(index="year", columns="gender", values="births")
            )
            """,
        ),
        exit_ticket([
            "Tôi không xử lý missing trước khi hiểu ngữ nghĩa.",
            "Tôi chọn được `concat` hay `merge` theo bài toán.",
            "Tôi dùng `validate`, `indicator` và kiểm tra số dòng sau merge.",
        ]),
    ]


def build_06() -> list[dict]:
    return [
        intro(6, "Cleaning, GroupBy và Pivot Table", "60-75 phút", [
            "Phát hiện duplicate/sentinel/outlier trước khi thay đổi.",
            "Dùng Split-Apply-Combine và named aggregation.",
            "Đọc pivot table cùng kích thước mẫu để tránh kết luận vội.",
        ]),
        setup("import numpy as np\nimport pandas as pd\nDATA_DIR = ROOT / 'datasets' / 'buoi6'"),
        diagnostic([
            ("`map()` gặp key không có trong dictionary thì sao?", "Thường trả `NaN`; phải kiểm tra sau ánh xạ."),
            ("`agg()` và `transform()` khác nhau thế nào?", "`agg()` thu gọn mỗi nhóm; `transform()` trả kết quả cùng số dòng để gắn lại dữ liệu gốc."),
            ("Có nên xóa mọi outlier?", "Không. Trước hết kiểm tra lỗi nhập liệu, đơn vị và bản chất hiện tượng."),
        ]),
        md("## 1. Duplicate, sentinel và chuẩn hóa nhãn"),
        code("""
        raw = pd.DataFrame({
            "id": [1, 2, 2, 3, 4],
            "city": [" HCM", "hcm", "hcm", "HN ", "unknown"],
            "score": [8, 7, 7, -999, 9],
        })
        audit = {"duplicate_rows": int(raw.duplicated().sum()), "sentinel_scores": int(raw["score"].eq(-999).sum())}
        print(audit)
        cleaned = raw.drop_duplicates().replace({"score": {-999: np.nan}}).copy()
        cleaned["city"] = cleaned["city"].str.strip().str.upper().replace("UNKNOWN", pd.NA)
        display(cleaned)
        assert len(cleaned) == 4
        """),
        md("## 2. `cut`, `qcut` và kiểm tra outlier"),
        code("""
        ages = pd.Series([18, 20, 22, 25, 31, 37, 45, 61], name="age")
        fixed_bins = pd.cut(ages, bins=[0, 24, 39, 59, np.inf], labels=["<=24", "25-39", "40-59", "60+"])
        quantile_bins = pd.qcut(ages, q=4, duplicates="drop")

        q1, q3 = ages.quantile([0.25, 0.75])
        iqr = q3 - q1
        bounds = (q1 - 1.5 * iqr, q3 + 1.5 * iqr)
        outlier_mask = ~ages.between(*bounds)
        print(pd.DataFrame({"age": ages, "fixed": fixed_bins, "quantile": quantile_bins, "outlier": outlier_mask}))
        assert fixed_bins.notna().all()
        """),
        md("## 3. GroupBy = Split -> Apply -> Combine"),
        code("""
        titanic = pd.read_csv(DATA_DIR / "titanic.csv")
        summary = (
            titanic.groupby(["class", "sex"], observed=True)
            .agg(passengers=("survived", "size"), survival_rate=("survived", "mean"), median_fare=("fare", "median"))
            .reset_index()
        )
        display(summary)
        assert summary["passengers"].sum() == len(titanic)
        """),
        md("""
        ## 4. `transform()` giữ nguyên số dòng

        `fare_vs_class_median > 1` nghĩa là giá vé cao hơn median trong chính hạng vé của hành khách đó.
        """),
        code("""
        class_median = titanic.groupby("class", observed=True)["fare"].transform("median")
        titanic_enriched = titanic.assign(fare_vs_class_median=titanic["fare"] / class_median)
        assert len(titanic_enriched) == len(titanic)
        display(titanic_enriched[["class", "fare", "fare_vs_class_median"]].head())
        """),
        md("## 5. Pivot table: hàng x cột và phải đọc cùng count"),
        code("""
        survival = pd.pivot_table(
            titanic, values="survived", index="sex", columns="class", aggfunc="mean", observed=True
        )
        counts = pd.pivot_table(
            titanic, values="survived", index="sex", columns="class", aggfunc="size", observed=True
        )
        display(survival.style.format("{:.1%}"))
        display(counts)
        assert int(counts.to_numpy().sum()) == len(titanic)
        """),
        practice(
            "Tạo bảng theo `embark_town` và `class` gồm số hành khách, tuổi trung vị, giá vé trung vị. Sắp nhóm có nhiều hành khách nhất lên đầu.",
            """
            answer = (
                titanic.groupby(["embark_town", "class"], observed=True)
                .agg(passengers=("survived", "size"), median_age=("age", "median"), median_fare=("fare", "median"))
                .sort_values("passengers", ascending=False)
            )
            """,
        ),
        exit_ticket([
            "Tôi audit trước khi drop/replace/cap dữ liệu.",
            "Tôi phân biệt `agg`, `transform`, `filter`, `apply`.",
            "Tôi đọc tỷ lệ cùng count trong GroupBy/Pivot.",
        ]),
    ]


def build_07() -> list[dict]:
    return [
        intro(7, "String và Time Series", "60 phút", [
            "Làm sạch chuỗi vectorized bằng `.str` và regex.",
            "Chuyển dữ liệu sang datetime an toàn.",
            "Phân biệt resample, shift và rolling.",
        ]),
        setup("import numpy as np\nimport pandas as pd\nDATA_DIR = ROOT / 'datasets' / 'buoi6'"),
        diagnostic([
            ("Vì sao dùng `.str` thay loop?", "Code ngắn, vectorized và xử lý missing nhất quán hơn."),
            ("`errors='coerce'` trong `to_datetime` làm gì?", "Giá trị không chuyển được thành `NaT`, giúp phát hiện và xử lý tường minh."),
            ("`rolling(7).mean()` và `resample('W').mean()` khác gì?", "Rolling là cửa sổ trượt trên quan sát; resample đổi tần suất theo các khoảng thời gian."),
        ]),
        md("## 1. Chuẩn hóa chuỗi và regex"),
        code(r'''
        contacts = pd.DataFrame({
            "name": ["  Nguyễn An ", "TRẦN BÌNH", None, "Lê Chi"],
            "email": ["AN@EXAMPLE.COM", "binh.example.com", None, "chi@school.edu.vn"],
        })
        contacts["name_clean"] = contacts["name"].str.strip().str.title()
        contacts["email_clean"] = contacts["email"].str.strip().str.lower()
        contacts["email_valid"] = contacts["email_clean"].str.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", na=False)
        contacts["domain"] = contacts["email_clean"].str.extract(r"@(.+)$", expand=False)
        display(contacts)
        assert contacts["email_valid"].tolist() == [True, False, False, True]
        '''),
        md("## 2. Multi-label bằng `str.get_dummies()`"),
        code("""
        movies = pd.DataFrame({"title": ["A", "B", "C"], "genres": ["Drama|Romance", "Action|Drama", "Comedy"]})
        genre_flags = movies["genres"].str.get_dummies(sep="|")
        display(pd.concat([movies, genre_flags], axis=1))
        assert genre_flags.loc[0, "Drama"] == 1
        """),
        md("## 3. Tạo datetime và audit ngày lỗi"),
        code("""
        births = pd.read_csv(DATA_DIR / "births.csv")
        births["date"] = pd.to_datetime(births[["year", "month", "day"]], errors="coerce")
        invalid_dates = births["date"].isna().sum()
        print("invalid dates:", invalid_dates)
        births_valid = births.dropna(subset=["date"]).set_index("date").sort_index()
        assert isinstance(births_valid.index, pd.DatetimeIndex)
        """),
        md("## 4. Resample: đổi tần suất thời gian"),
        code("""
        daily_births = births_valid.groupby(level=0)["births"].sum()
        yearly_births = daily_births.resample("YS").sum()
        display(yearly_births.head())
        assert yearly_births.index.is_monotonic_increasing
        """),
        md("""
        ## 5. `shift()` và `rolling()`

        - `shift(1)`: căn giá trị kỳ trước để tính thay đổi.
        - `rolling(30)`: tóm tắt cửa sổ 30 quan sát liên tiếp.
        """),
        code("""
        trend = pd.DataFrame({"births": daily_births})
        trend["change_from_previous_day"] = trend["births"] - trend["births"].shift(1)
        trend["rolling_30d_mean"] = trend["births"].rolling(30, min_periods=30).mean()
        display(trend.head(35).tail())
        assert trend["rolling_30d_mean"].first_valid_index() == trend.index[29]
        """),
        practice(
            "Từ `births_valid`, tính tổng births theo tháng, thêm phần trăm thay đổi so với tháng trước và rolling mean 12 tháng.",
            """
            monthly = births_valid["births"].resample("MS").sum().to_frame()
            monthly["pct_change"] = monthly["births"].pct_change()
            monthly["rolling_12m"] = monthly["births"].rolling(12).mean()
            """,
        ),
        exit_ticket([
            "Tôi dùng `.str` mà vẫn xử lý được missing.",
            "Tôi audit `NaT` sau `to_datetime(errors='coerce')`.",
            "Tôi phân biệt datetime index, resample, shift và rolling.",
        ]),
    ]


def build_08() -> list[dict]:
    return [
        intro(8, "Matplotlib", "60-75 phút", [
            "Dùng giao diện Figure/Axes thay vì phụ thuộc state toàn cục.",
            "Chọn line, scatter, histogram, bar theo câu hỏi.",
            "Gắn title, label, legend, annotation và colorbar có ý nghĩa.",
        ]),
        setup("import numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nDATA_DIR = ROOT / 'datasets' / 'buoi6'\nplt.style.use('seaborn-v0_8-whitegrid')"),
        diagnostic([
            ("Figure và Axes khác nhau thế nào?", "Figure là khung tổng; mỗi Axes là một hệ trục nơi dữ liệu được vẽ."),
            ("Xu hướng theo thời gian dùng biểu đồ gì?", "Line plot, nếu trục thời gian có thứ tự và khoảng cách phù hợp."),
            ("Colorbar cần gắn với object nào?", "Mappable tạo ra từ `scatter`, `imshow`, `contourf`... và Axes tương ứng."),
        ]),
        md("## 1. OO interface: Figure chứa Axes"),
        code("""
        x = np.linspace(0, 2 * np.pi, 200)
        fig, ax = plt.subplots(figsize=(7, 3.5))
        ax.plot(x, np.sin(x), label="sin(x)")
        ax.plot(x, np.cos(x), label="cos(x)", linestyle="--")
        ax.set(title="Hai hàm tuần hoàn", xlabel="x (radian)", ylabel="giá trị")
        ax.legend()
        fig.tight_layout()
        plt.show()
        """),
        md("## 2. Một câu hỏi - một biểu đồ"),
        code("""
        titanic = pd.read_csv(DATA_DIR / "titanic.csv")
        fig, axes = plt.subplots(1, 3, figsize=(13, 3.5))

        axes[0].hist(titanic["age"].dropna(), bins=20, edgecolor="white")
        axes[0].set(title="Phân phối tuổi", xlabel="Tuổi", ylabel="Số hành khách")

        axes[1].scatter(titanic["age"], titanic["fare"], alpha=0.35, s=18)
        axes[1].set(title="Tuổi và giá vé", xlabel="Tuổi", ylabel="Giá vé")

        survival = titanic.groupby("class", observed=True)["survived"].mean().sort_values()
        axes[2].bar(survival.index.astype(str), survival.values)
        axes[2].set(title="Tỷ lệ sống theo hạng", xlabel="Hạng", ylabel="Tỷ lệ")
        axes[2].set_ylim(0, 1)

        fig.tight_layout()
        plt.show()
        assert len(axes) == 3
        """),
        md("## 3. Màu phải mang thêm thông tin"),
        code("""
        plot_data = titanic.dropna(subset=["age", "fare"]).copy()
        fig, ax = plt.subplots(figsize=(7, 4))
        points = ax.scatter(
            plot_data["age"], plot_data["fare"],
            c=plot_data["survived"], cmap="viridis", alpha=0.5, s=24,
        )
        ax.set(title="Giá vé theo tuổi; màu = sống sót", xlabel="Tuổi", ylabel="Giá vé")
        colorbar = fig.colorbar(points, ax=ax, ticks=[0, 1])
        colorbar.set_label("Sống sót")
        fig.tight_layout()
        plt.show()
        """),
        md("## 4. Annotation chỉ dùng khi giúp đọc insight"),
        code("""
        yearly = (
            pd.read_csv(DATA_DIR / "births.csv")
            .groupby("year", as_index=True)["births"].sum()
        )
        peak_year = int(yearly.idxmax())
        peak_value = int(yearly.max())
        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.plot(yearly.index, yearly.values)
        ax.annotate(
            f"Cao nhất: {peak_year}", xy=(peak_year, peak_value),
            xytext=(peak_year - 8, peak_value * 0.9),
            arrowprops={"arrowstyle": "->"},
        )
        ax.set(title="Tổng số ca sinh theo năm", xlabel="Năm", ylabel="Số ca sinh")
        fig.tight_layout()
        plt.show()
        """),
        practice(
            "Tạo bố cục 2x2 cho Titanic: histogram `fare`, boxplot `age` theo `class`, bar tỷ lệ sống theo `sex`, scatter `age`-`fare`. Mỗi Axes phải có title và label phù hợp.",
            """
            fig, axes = plt.subplots(2, 2, figsize=(10, 7))
            axes[0, 0].hist(titanic["fare"], bins=25)
            titanic.boxplot(column="age", by="class", ax=axes[0, 1])
            titanic.groupby("sex")["survived"].mean().plot.bar(ax=axes[1, 0])
            axes[1, 1].scatter(titanic["age"], titanic["fare"], alpha=.3)
            fig.suptitle("Titanic - bốn góc nhìn")
            fig.tight_layout()
            """,
        ),
        exit_ticket([
            "Tôi tạo biểu đồ qua `fig, ax = plt.subplots()`.",
            "Tôi chọn loại biểu đồ từ câu hỏi, không từ sở thích.",
            "Màu, legend, annotation và colorbar đều có vai trò rõ ràng.",
        ]),
    ]


def build_09() -> list[dict]:
    return [
        intro(9, "Seaborn và EDA end-to-end", "75-90 phút", [
            "Chọn đúng họ biểu đồ Seaborn.",
            "Thực hiện EDA theo Load -> Inspect -> Quality -> Clean -> Analyze -> Visualize -> Interpret.",
            "Viết kết luận có bằng chứng, giới hạn và không nhầm tương quan với nhân quả.",
        ]),
        setup("import numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nDATA_DIR = ROOT / 'datasets' / 'buoi6'\nsns.set_theme(style='whitegrid')\nprint(f\"Seaborn: {sns.__version__}\")"),
        diagnostic([
            ("`pairplot` phù hợp khi nào?", "Khi muốn quét nhanh quan hệ từng cặp biến số; không phù hợp nếu có quá nhiều biến hoặc quá nhiều điểm."),
            ("Boxplot và violinplot khác nhau ở đâu?", "Boxplot tóm tắt median/quartile/outlier; violinplot cho thấy thêm hình dạng phân phối."),
            ("EDA có chứng minh nhân quả không?", "Không. EDA mô tả pattern/association; nhân quả cần thiết kế nghiên cứu và giả định mạnh hơn."),
        ]),
        md("""
        ## 1. Bốn họ biểu đồ

        | Câu hỏi | Họ biểu đồ | Hàm gợi ý |
        |---|---|---|
        | Phân phối ra sao? | Distribution | `histplot`, `kdeplot` |
        | X liên hệ Y thế nào? | Relational | `scatterplot`, `lineplot` |
        | Các nhóm khác nhau ra sao? | Categorical | `boxplot`, `violinplot`, `countplot` |
        | Nhiều biến/nhóm cùng lúc? | Multi-variable | `pairplot`, `jointplot`, `FacetGrid` |
        """),
        md("## 2. LOAD + INSPECT + QUALITY"),
        code("""
        titanic = pd.read_csv(DATA_DIR / "titanic.csv")
        display(titanic.head())
        quality = pd.DataFrame({
            "dtype": titanic.dtypes.astype(str),
            "missing_count": titanic.isna().sum(),
            "missing_rate": titanic.isna().mean(),
            "n_unique": titanic.nunique(dropna=True),
        }).sort_values("missing_rate", ascending=False)
        display(quality)
        print("shape:", titanic.shape, "| duplicate rows:", titanic.duplicated().sum())
        assert titanic.shape == (891, 15)
        """),
        md("""
        ## 3. CLEAN + TRANSFORM

        Không điền `deck`: tỷ lệ thiếu quá cao và cột không cần cho các câu hỏi bên dưới. Với `age`, giữ missing và để từng phân tích dùng tập con phù hợp. Dù có các hàng giống hệt nhau, file không có `passenger_id`, nên không đủ căn cứ để coi đó là cùng một hành khách và xóa bằng `drop_duplicates()`.
        """),
        code("""
        analysis = (
            titanic.copy()
            .assign(
                age_group=lambda d: pd.cut(d["age"], [0, 12, 18, 35, 60, np.inf], labels=["Child", "Teen", "Young adult", "Adult", "Senior"]),
                family_size=lambda d: d["sibsp"] + d["parch"] + 1,
            )
        )
        assert analysis["family_size"].ge(1).all()
        """),
        md("## 4. Distribution + Categorical"),
        code("""
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        sns.histplot(data=analysis, x="age", hue="survived", multiple="stack", bins=20, ax=axes[0])
        sns.boxplot(data=analysis, x="class", y="fare", hue="survived", ax=axes[1])
        axes[0].set_title("Phân phối tuổi theo sống sót")
        axes[1].set_title("Giá vé theo hạng và sống sót")
        axes[1].set_yscale("log")
        fig.tight_layout()
        plt.show()
        """),
        md("## 5. Relational + Facet"),
        code("""
        grid = sns.relplot(
            data=analysis, x="age", y="fare", hue="survived", col="sex",
            size="family_size", sizes=(15, 100), alpha=0.55, height=3.5,
        )
        grid.set_axis_labels("Tuổi", "Giá vé")
        grid.set_titles("Giới tính: {col_name}")
        plt.show()
        """),
        md("## 6. ANALYZE: tỷ lệ luôn đi cùng cỡ mẫu"),
        code("""
        evidence = (
            analysis.groupby(["sex", "class"], observed=True)
            .agg(n=("survived", "size"), survival_rate=("survived", "mean"), median_age=("age", "median"))
            .reset_index()
        )
        display(evidence.style.format({"survival_rate": "{:.1%}", "median_age": "{:.1f}"}))
        assert evidence["n"].sum() == len(analysis)
        """),
        md("""
        ## 7. INTERPRET - mẫu kết luận có kỷ luật

        - **Quan sát:** tỷ lệ sống khác nhau theo giới tính và hạng vé trong dữ liệu Titanic.
        - **Bằng chứng:** dùng bảng `n` + `survival_rate` và biểu đồ phía trên.
        - **Giới hạn:** đây là dữ liệu quan sát lịch sử; nhóm có nhiều yếu tố gây nhiễu và missing age/deck.
        - **Không được suy diễn:** không kết luận giới tính hay hạng vé *gây ra* sống sót chỉ từ EDA.
        """),
        md("## 8. Tự kiểm tra tích hợp"),
        code("""
        checks = {
            "raw_rows_preserved_without_identifier": len(analysis) == len(titanic),
            "survival_probability_valid": evidence["survival_rate"].between(0, 1).all(),
            "all_rows_accounted_for": evidence["n"].sum() == len(analysis),
            "derived_family_size_valid": analysis["family_size"].ge(1).all(),
        }
        print(checks)
        assert all(checks.values())
        """),
        practice(
            "Chọn một câu hỏi mới trên Titanic. Viết đủ 5 dòng: câu hỏi, cột dùng, kiểm tra chất lượng, bảng thống kê, biểu đồ và kết luận có giới hạn.",
            """
            question = "Đi một mình có liên hệ với tỷ lệ sống không?"
            table = analysis.groupby("alone").agg(n=("survived", "size"), survival_rate=("survived", "mean"))
            display(table)
            sns.barplot(data=analysis, x="alone", y="survived", errorbar=("ci", 95))
            plt.ylabel("Tỷ lệ sống ước tính")
            plt.show()
            # Kết luận phải đề cập n, chênh lệch quan sát và giới hạn dữ liệu quan sát.
            """,
        ),
        exit_ticket([
            "Tôi chọn biểu đồ dựa trên loại câu hỏi và biến.",
            "Tôi thực hiện đủ Load -> Inspect -> Quality -> Clean -> Analyze -> Visualize -> Interpret.",
            "Mọi kết luận của tôi có bằng chứng, cỡ mẫu và giới hạn.",
        ]),
    ]


BUILDERS = {
    "on_tap_01_python_oop.ipynb": build_01,
    "on_tap_02_numpy.ipynb": build_02,
    "on_tap_03_pandas_co_ban.ipynb": build_03,
    "on_tap_04_doc_du_lieu.ipynb": build_04,
    "on_tap_05_missing_combine.ipynb": build_05,
    "on_tap_06_cleaning_groupby_pivot.ipynb": build_06,
    "on_tap_07_string_time_series.ipynb": build_07,
    "on_tap_08_matplotlib.ipynb": build_08,
    "on_tap_09_seaborn_eda.ipynb": build_09,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, builder in BUILDERS.items():
        path = OUT / filename
        path.write_text(json.dumps(notebook(builder()), ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
