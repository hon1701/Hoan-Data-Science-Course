from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.a1_utils import (
    ID_COLUMN,
    MODEL_FEATURE_COLUMNS,
    ORIGINAL_COLUMNS,
    TARGET,
    assert_split_contract,
    clean_and_add_features,
    model_features,
    split_summary,
    stratified_split,
    validate_raw_dataframe,
)


def sample_raw(rows: int = 500) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    target = np.zeros(rows, dtype=int)
    target[:50] = 1
    rng.shuffle(target)
    data: dict[str, np.ndarray] = {"Time": np.arange(rows, dtype=float)}
    for index in range(1, 29):
        data[f"V{index}"] = rng.normal(size=rows)
    data["Amount"] = rng.lognormal(mean=2.0, sigma=0.8, size=rows)
    data[TARGET] = target
    return pd.DataFrame(data, columns=ORIGINAL_COLUMNS)


def test_validation_and_duplicate_removal() -> None:
    raw = sample_raw()
    raw_with_duplicates = pd.concat([raw, raw.iloc[[0, 1, 2]]], ignore_index=True)
    summary = validate_raw_dataframe(raw_with_duplicates, strict=False)
    clean, duplicate_count = clean_and_add_features(raw_with_duplicates)

    assert summary["exact_duplicates"] == 3
    assert duplicate_count == 3
    assert len(clean) == len(raw)
    assert clean[ID_COLUMN].is_unique
    assert np.allclose(clean["LogAmount"], np.log1p(clean["Amount"]))


def test_stratified_split_is_disjoint_and_reproducible() -> None:
    clean, _ = clean_and_add_features(sample_raw())
    first = stratified_split(clean, random_state=42)
    second = stratified_split(clean, random_state=42)
    assert_split_contract(first, expected_total=len(clean))

    assert [len(first[name]) for name in ("train", "validation", "test")] == [300, 100, 100]
    for name in first:
        assert first[name][ID_COLUMN].tolist() == second[name][ID_COLUMN].tolist()
    assert split_summary(first)["class_1"].tolist() == [30, 10, 10]


def test_feature_contract_excludes_target_and_identifier() -> None:
    clean, _ = clean_and_add_features(sample_raw())
    features = model_features(clean)
    assert list(features.columns) == MODEL_FEATURE_COLUMNS
    assert TARGET not in features.columns
    assert ID_COLUMN not in features.columns


def test_invalid_schema_is_rejected() -> None:
    invalid = sample_raw().drop(columns=["V28"])
    with pytest.raises(ValueError, match="Schema"):
        validate_raw_dataframe(invalid, strict=False)

