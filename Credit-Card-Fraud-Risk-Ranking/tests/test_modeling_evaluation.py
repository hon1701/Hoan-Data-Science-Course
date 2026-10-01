from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.a1_utils import ID_COLUMN, PROCESSED_COLUMNS, TARGET
from src.evaluation import cost_curve, select_cost_threshold, select_f1_threshold, top_p_metrics
from src.modeling import MODEL_FEATURE_COLUMNS, split_xy, validate_scores


def sample_processed(rows: int = 20) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    data = {ID_COLUMN: np.arange(rows), "Time": np.arange(rows, dtype=float)}
    for index in range(1, 29):
        data[f"V{index}"] = rng.normal(size=rows)
    data["Amount"] = rng.lognormal(size=rows)
    data["LogAmount"] = np.log1p(data["Amount"])
    data[TARGET] = np.resize([0, 0, 0, 1], rows)
    return pd.DataFrame(data, columns=PROCESSED_COLUMNS)


def test_model_feature_contract_excludes_leakage_and_raw_amount() -> None:
    x, y = split_xy(sample_processed())
    assert list(x.columns) == MODEL_FEATURE_COLUMNS
    assert TARGET not in x.columns
    assert ID_COLUMN not in x.columns
    assert "Amount" not in x.columns
    assert len(y) == len(x)


def test_validate_scores_rejects_invalid_values() -> None:
    with pytest.raises(AssertionError, match=r"\[0, 1\]"):
        validate_scores(np.array([0.1, 1.2]), 2)
    with pytest.raises(AssertionError, match="NaN"):
        validate_scores(np.array([0.1, np.nan]), 2)


def test_threshold_selection_returns_valid_metrics() -> None:
    y = np.array([0, 0, 1, 1, 0, 1])
    scores = np.array([0.05, 0.3, 0.4, 0.9, 0.2, 0.8])
    f1_choice = select_f1_threshold(y, scores)
    cost_choice, curve = select_cost_threshold(y, scores)
    assert 0 <= f1_choice["threshold"] <= 1
    assert 0 <= cost_choice["threshold"] <= 1
    assert {"threshold", "expected_cost_per_transaction"} <= set(curve.columns)


def test_top_p_uses_source_row_as_deterministic_tie_break() -> None:
    y = np.array([1, 0, 1, 0])
    scores = np.array([0.8, 0.8, 0.2, 0.1])
    ids = np.array([20, 10, 30, 40])
    table = top_p_metrics(y, scores, ids, rates=(0.25,))
    assert table.loc[0, "k"] == 1
    assert table.loc[0, "tp"] == 0


def test_cost_threshold_can_choose_no_alerts() -> None:
    y = np.array([0, 1])
    scores = np.array([0.9, 0.1])
    chosen, _ = select_cost_threshold(y, scores, false_negative_cost=0.1)
    assert chosen["threshold"] > scores.max()
    assert (chosen["tp"], chosen["fp"], chosen["fn"]) == (0, 0, 1)
    assert chosen["expected_cost_per_transaction"] == pytest.approx(0.05)


def test_cost_curve_matches_direct_predictions_including_ties() -> None:
    y = np.array([0, 1, 1, 0, 1])
    scores = np.array([1.0, 1.0, 0.5, 0.5, 0.0])
    curve = cost_curve(y, scores)
    assert len(curve) == len(np.unique(scores)) + 1
    for row in curve.itertuples():
        predicted = scores >= row.threshold
        fp = np.sum(predicted & (y == 0))
        fn = np.sum(~predicted & (y == 1))
        assert row.fp == fp and row.fn == fn
        assert row.expected_cost_per_transaction == pytest.approx((20 * fn + fp) / len(y))
