"""Verify the files produced by notebooks/01_data_eda.ipynb."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from src.a1_utils import (  # noqa: E402
    EXPECTED_CLEAN_FRAUD,
    EXPECTED_CLEAN_ROWS,
    ID_COLUMN,
    MODEL_FEATURE_COLUMNS,
    PROCESSED_COLUMNS,
    TARGET,
    assert_split_contract,
)

EXPECTED_STRICT_COUNTS = {
    "train": (170_235, 284),
    "validation": (56_745, 94),
    "test": (56_746, 95),
}
EXPECTED_FIGURES = [
    "class_distribution.png",
    "amount_by_class.png",
    "time_by_class.png",
    "selected_correlations.png",
]


def verify(root: Path, *, strict: bool) -> None:
    processed_dir = root / "data" / "processed"
    table_dir = root / "outputs" / "tables"
    figure_dir = root / "outputs" / "figures"

    splits: dict[str, pd.DataFrame] = {}
    for name in ("train", "validation", "test"):
        path = processed_dir / f"{name}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Thiếu đầu ra: {path}")
        frame = pd.read_csv(path)
        if list(frame.columns) != PROCESSED_COLUMNS:
            raise AssertionError(f"Schema {name}.csv không đúng.")
        if not np.allclose(frame["LogAmount"], np.log1p(frame["Amount"]), rtol=1e-10):
            raise AssertionError(f"LogAmount trong {name}.csv không khớp log1p(Amount).")
        splits[name] = frame

    total = sum(len(frame) for frame in splits.values())
    assert_split_contract(splits, expected_total=total)

    if strict:
        if total != EXPECTED_CLEAN_ROWS:
            raise AssertionError(f"Tổng số dòng sau làm sạch sai: {total}")
        if sum(int(frame[TARGET].sum()) for frame in splits.values()) != EXPECTED_CLEAN_FRAUD:
            raise AssertionError("Tổng Class 1 sau làm sạch sai.")
        for name, (expected_rows, expected_fraud) in EXPECTED_STRICT_COUNTS.items():
            actual = (len(splits[name]), int(splits[name][TARGET].sum()))
            if actual != (expected_rows, expected_fraud):
                raise AssertionError(
                    f"{name} sai (rows, fraud): {actual} != {(expected_rows, expected_fraud)}"
                )
    else:
        ratios = {name: len(frame) / total for name, frame in splits.items()}
        for name, expected in {"train": 0.60, "validation": 0.20, "test": 0.20}.items():
            if abs(ratios[name] - expected) > 0.01:
                raise AssertionError(f"Tỷ lệ {name} không gần {expected:.0%}: {ratios[name]:.3%}")

    for filename in ("data_audit.csv", "split_summary.csv", "train_class_summary.csv"):
        path = table_dir / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Thiếu bảng đầu ra hợp lệ: {path}")

    feature_contract_path = table_dir / "feature_contract.json"
    feature_contract = json.loads(feature_contract_path.read_text(encoding="utf-8"))
    if feature_contract["features"] != MODEL_FEATURE_COLUMNS:
        raise AssertionError("feature_contract.json không đúng thứ tự feature.")
    if {TARGET, ID_COLUMN} & set(feature_contract["features"]):
        raise AssertionError("Class/source_row không được xuất hiện trong feature contract.")

    for filename in EXPECTED_FIGURES:
        path = figure_dir / filename
        if not path.is_file() or path.stat().st_size < 5_000:
            raise FileNotFoundError(f"Thiếu hoặc hình quá nhỏ: {path}")

    print("[OK] Ba split đúng schema, không giao nhau và bảo toàn số dòng.")
    print("[OK] LogAmount, audit table, feature contract và bốn hình EDA hợp lệ.")
    print("[OK] Bộ đầu ra A.1 đã sẵn sàng bàn giao cho Huy/Sang.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Kiểm tra đầu ra của Phụ lục A.1")
    parser.add_argument(
        "--root",
        type=Path,
        default=PACKAGE_ROOT,
        help="Thư mục chứa data/processed và outputs/.",
    )
    parser.add_argument(
        "--relaxed",
        action="store_true",
        help="Chỉ kiểm tra contract; dùng cho smoke test dữ liệu tổng hợp.",
    )
    args = parser.parse_args()
    verify(args.root.resolve(), strict=not args.relaxed)


if __name__ == "__main__":
    main()

