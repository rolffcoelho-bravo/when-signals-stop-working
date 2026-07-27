from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v3.forecast_contract import (
    ForecastContract,
    ReservedSegmentAccessError,
)
from shockbridge_signal_validity.v3.forecast_targets import (
    apply_large_move_threshold,
    build_development_targets,
    fit_large_move_threshold,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"


def contract() -> ForecastContract:
    return ForecastContract.from_path(CONTRACT)


def close_series(rows: int = 400) -> pd.Series:
    index = pd.date_range("2021-01-01", periods=rows, freq="4h", tz="UTC")
    values = 30.0 * np.exp(0.001 * np.arange(rows) + 0.02 * np.sin(np.arange(rows) / 11.0))
    return pd.Series(values, index=index, name="close")


def test_contract_preserves_registered_horizons_and_partition() -> None:
    value = contract()
    assert value.horizons == (1, 2, 3, 6, 12, 18)
    assert value.outer_folds == 5
    assert value.inner_folds == 3
    assert value.classify_timestamp("2025-06-30T20:00:00Z") == "DEVELOPMENT"
    assert value.classify_timestamp("2025-07-01T00:00:00Z") == "SIGNAL_ESTABLISHMENT"
    assert value.classify_timestamp("2026-01-01T00:00:00Z") == "FINAL_FRAMEWORK_RESERVE"


def test_establishment_and_final_reserve_rows_fail_closed() -> None:
    value = contract()
    establishment = pd.date_range("2025-07-01", periods=2, freq="4h", tz="UTC")
    with pytest.raises(
        ReservedSegmentAccessError,
        match="SIGNAL_ESTABLISHMENT_SEGMENT_REQUIRES_AUTHORIZATION",
    ):
        value.assert_development_only(establishment)

    reserve = pd.date_range("2026-01-01", periods=2, freq="4h", tz="UTC")
    with pytest.raises(
        ReservedSegmentAccessError,
        match="PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED",
    ):
        value.assert_development_only(reserve)


def test_development_targets_are_horizon_tail_purged() -> None:
    value = contract()
    close = close_series()
    targets = build_development_targets(close, value)
    assert len(targets) == len(close) * len(value.horizons) - sum(value.horizons)
    assert set(targets["horizon_candles"].astype(int)) == set(value.horizons)
    assert set(targets["segment"]) == {"DEVELOPMENT"}
    assert pd.to_datetime(targets["target_timestamp"], utc=True).max() <= value.development_end
    for horizon in value.horizons:
        observed = targets.loc[targets["horizon_candles"] == horizon]
        assert len(observed) == len(close) - horizon


def test_target_prefix_is_invariant_before_the_append_boundary() -> None:
    value = contract()
    full = close_series(500)
    prefix = full.iloc[:400]
    prefix_targets = build_development_targets(prefix, value)
    full_targets = build_development_targets(full, value)
    safe_end = prefix.index[-1 - max(value.horizons)]
    left = prefix_targets.loc[prefix_targets["timestamp"] <= safe_end].reset_index(drop=True)
    right = full_targets.loc[full_targets["timestamp"] <= safe_end].reset_index(drop=True)
    pd.testing.assert_frame_equal(left, right)


def test_large_move_threshold_is_fitted_from_supplied_training_rows_only() -> None:
    returns = pd.Series(np.linspace(-0.05, 0.05, 200))
    threshold = fit_large_move_threshold(returns, horizon_candles=6)
    labels = apply_large_move_threshold(returns, threshold)
    assert threshold.training_rows == 200
    assert threshold.quantile == 0.90
    assert labels.notna().all()
    assert set(labels.astype(int).unique()).issubset({0, 1})
