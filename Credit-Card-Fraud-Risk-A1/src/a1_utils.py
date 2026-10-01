"""Data integrity, splitting and export helpers for Appendix A.1.

This module intentionally contains no model training.  Appendix A.1 owns the
raw-data audit, exact-duplicate removal, leakage-safe split and train-only EDA.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42
TARGET = "Class"
ID_COLUMN = "source_row"
EXPECTED_SHA256 = "76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89"
EXPECTED_FILE_SIZE = 150_828_752
EXPECTED_RAW_ROWS = 284_807
EXPECTED_RAW_FRAUD = 492
EXPECTED_DUPLICATES = 1_081
EXPECTED_CLEAN_ROWS = 283_726
EXPECTED_CLEAN_FRAUD = 473

ORIGINAL_COLUMNS = ["Time", *[f"V{i}" for i in range(1, 29)], "Amount", TARGET]
RAW_FEATURE_COLUMNS = [column for column in ORIGINAL_COLUMNS if column != TARGET]
MODEL_FEATURE_COLUMNS = [*RAW_FEATURE_COLUMNS, "LogAmount"]
PROCESSED_COLUMNS = [ID_COLUMN, *MODEL_FEATURE_COLUMNS, TARGET]


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    """Return the SHA-256 digest of *path* without loading it into memory."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_raw_dataframe(df: pd.DataFrame, *, strict: bool = True) -> dict[str, int]:
    """Validate the ULB/Kaggle raw schema and basic data-quality invariants."""

    if list(df.columns) != ORIGINAL_COLUMNS:
        missing = [column for column in ORIGINAL_COLUMNS if column not in df.columns]
        extra = [column for column in df.columns if column not in ORIGINAL_COLUMNS]
        raise ValueError(
            "Schema không đúng hoặc sai thứ tự cột. "
            f"Thiếu={missing}; dư={extra}; nhận được={list(df.columns)}"
        )

    non_numeric = [column for column in ORIGINAL_COLUMNS if not is_numeric_dtype(df[column])]
    if non_numeric:
        raise TypeError(f"Các cột phải là kiểu số, nhưng nhận được: {non_numeric}")

    missing_count = int(df.isna().sum().sum())
    infinity_count = int(np.isinf(df.to_numpy(dtype=np.float64, copy=False)).sum())
    if missing_count:
        raise ValueError(f"Dữ liệu có {missing_count} giá trị thiếu.")
    if infinity_count:
        raise ValueError(f"Dữ liệu có {infinity_count} giá trị vô hạn.")
    if not set(df[TARGET].unique()).issubset({0, 1}):
        raise ValueError("Class chỉ được nhận 0 hoặc 1.")
    if (df["Amount"] < 0).any():
        raise ValueError("Amount không được âm.")
    if (df["Time"] < 0).any():
        raise ValueError("Time không được âm.")

    duplicate_count = int(df.duplicated(subset=ORIGINAL_COLUMNS, keep="first").sum())
    summary = {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "fraud": int(df[TARGET].sum()),
        "missing": missing_count,
        "infinity": infinity_count,
        "exact_duplicates": duplicate_count,
    }

    if strict:
        expected = {
            "rows": EXPECTED_RAW_ROWS,
            "columns": len(ORIGINAL_COLUMNS),
            "fraud": EXPECTED_RAW_FRAUD,
            "exact_duplicates": EXPECTED_DUPLICATES,
        }
        mismatches = {
            key: (summary[key], value)
            for key, value in expected.items()
            if summary[key] != value
        }
        if mismatches:
            raise AssertionError(f"Dữ liệu không khớp bộ ULB chuẩn: {mismatches}")
    return summary


def verify_raw_file(path: Path, *, strict: bool = True) -> dict[str, str | int]:
    """Verify file existence, size and SHA-256 before pandas reads the CSV."""

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Không thấy {path}. Chạy `python scripts/get_data.py` từ thư mục gốc dự án."
        )
    file_size = path.stat().st_size
    digest = sha256_file(path)
    if strict and file_size != EXPECTED_FILE_SIZE:
        raise AssertionError(
            f"Kích thước creditcard.csv sai: {file_size} != {EXPECTED_FILE_SIZE} byte."
        )
    if strict and digest != EXPECTED_SHA256:
        raise AssertionError(f"SHA-256 creditcard.csv sai: {digest} != {EXPECTED_SHA256}")
    return {"path": str(path), "file_size_bytes": file_size, "sha256": digest}


def clean_and_add_features(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Add source_row, remove exact raw duplicates, then create LogAmount."""

    working = df.copy()
    working.insert(0, ID_COLUMN, np.arange(len(working), dtype=np.int64))
    duplicate_mask = working.duplicated(subset=ORIGINAL_COLUMNS, keep="first")
    duplicate_count = int(duplicate_mask.sum())
    clean = working.loc[~duplicate_mask].copy()
    clean["LogAmount"] = np.log1p(clean["Amount"])
    clean = clean.loc[:, PROCESSED_COLUMNS].reset_index(drop=True)

    if clean[ID_COLUMN].duplicated().any():
        raise AssertionError("source_row phải duy nhất sau làm sạch.")
    if not np.isfinite(clean["LogAmount"]).all():
        raise AssertionError("LogAmount có giá trị không hữu hạn.")
    return clean, duplicate_count


def stratified_split(
    clean: pd.DataFrame,
    *,
    random_state: int = RANDOM_STATE,
) -> dict[str, pd.DataFrame]:
    """Split 60/20/20 using two stratified train_test_split calls."""

    train_validation, test = train_test_split(
        clean,
        test_size=0.20,
        stratify=clean[TARGET],
        random_state=random_state,
    )
    train, validation = train_test_split(
        train_validation,
        test_size=0.25,
        stratify=train_validation[TARGET],
        random_state=random_state,
    )
    splits = {
        "train": train.reset_index(drop=True),
        "validation": validation.reset_index(drop=True),
        "test": test.reset_index(drop=True),
    }
    assert_split_contract(splits, expected_total=len(clean))
    return splits


def assert_split_contract(
    splits: Mapping[str, pd.DataFrame],
    *,
    expected_total: int,
) -> None:
    """Assert schema, unique IDs, disjointness and row conservation."""

    if set(splits) != {"train", "validation", "test"}:
        raise AssertionError("Phải có đúng ba split: train, validation và test.")

    id_sets: dict[str, set[int]] = {}
    for name, frame in splits.items():
        if list(frame.columns) != PROCESSED_COLUMNS:
            raise AssertionError(f"Schema của {name} không đúng contract.")
        if frame[ID_COLUMN].duplicated().any():
            raise AssertionError(f"source_row bị trùng trong {name}.")
        id_sets[name] = set(frame[ID_COLUMN].astype(int))

    if id_sets["train"] & id_sets["validation"]:
        raise AssertionError("Train và validation giao nhau.")
    if id_sets["train"] & id_sets["test"]:
        raise AssertionError("Train và test giao nhau.")
    if id_sets["validation"] & id_sets["test"]:
        raise AssertionError("Validation và test giao nhau.")
    if sum(len(frame) for frame in splits.values()) != expected_total:
        raise AssertionError("Tổng số dòng ba split không bằng dữ liệu sau làm sạch.")


def split_summary(splits: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Return row and class counts for the three splits."""

    records = []
    for name in ("train", "validation", "test"):
        frame = splits[name]
        fraud = int(frame[TARGET].sum())
        records.append(
            {
                "split": name,
                "rows": int(len(frame)),
                "class_0": int(len(frame) - fraud),
                "class_1": fraud,
                "fraud_rate": fraud / len(frame),
            }
        )
    return pd.DataFrame(records)


def build_audit_table(
    *,
    file_info: Mapping[str, str | int],
    raw_summary: Mapping[str, int],
    clean: pd.DataFrame,
    duplicate_count: int,
    splits: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Create the long-form audit table cited by the report."""

    rows: list[dict[str, object]] = [
        {"metric": "source_path", "value": file_info["path"]},
        {"metric": "source_file_size_bytes", "value": file_info["file_size_bytes"]},
        {"metric": "source_sha256", "value": file_info["sha256"]},
        {"metric": "random_state", "value": RANDOM_STATE},
        {"metric": "raw_rows", "value": raw_summary["rows"]},
        {"metric": "raw_columns", "value": raw_summary["columns"]},
        {"metric": "raw_class_1", "value": raw_summary["fraud"]},
        {"metric": "raw_missing", "value": raw_summary["missing"]},
        {"metric": "raw_infinity", "value": raw_summary["infinity"]},
        {"metric": "exact_duplicates_removed", "value": duplicate_count},
        {"metric": "clean_rows", "value": len(clean)},
        {"metric": "clean_class_1", "value": int(clean[TARGET].sum())},
    ]
    for record in split_summary(splits).to_dict(orient="records"):
        name = record.pop("split")
        for metric, value in record.items():
            rows.append({"metric": f"{name}_{metric}", "value": value})
    return pd.DataFrame(rows)


def model_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the agreed features and explicitly exclude Class/source_row."""

    features = frame.loc[:, MODEL_FEATURE_COLUMNS].copy()
    forbidden = {TARGET, ID_COLUMN} & set(features.columns)
    if forbidden:
        raise AssertionError(f"Leakage contract bị vi phạm: {sorted(forbidden)}")
    return features


def atomic_write_csv(frame: pd.DataFrame, path: Path) -> None:
    """Write CSV through a temporary file so interrupted runs do not look valid."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def atomic_write_json(payload: object, path: Path) -> None:
    """Write UTF-8 JSON atomically."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary, path)

