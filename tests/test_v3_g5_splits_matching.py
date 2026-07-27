from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v3.forecast_contract import (
    ForecastContract,
    ReservedSegmentAccessError,
)
from shockbridge_signal_validity.v3.forecast_matching import (
    build_matched_pair,
    matched_pair_manifest,
)
from shockbridge_signal_validity.v3.forecast_splits import (
    build_nested_fold_plan,
    purged_expanding_folds,
)
from shockbridge_signal_validity.v3.forecast_targets import build_development_targets

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"


def contract() -> ForecastContract:
    return ForecastContract.from_path(CONTRACT)


def close_series(rows: int = 3000) -> pd.Series:
    index = pd.date_range("2021-01-01", periods=rows, freq="4h", tz="UTC")
    values = 40.0 * np.exp(0.0002 * np.arange(rows) + 0.015 * np.sin(np.arange(rows) / 17.0))
    return pd.Series(values, index=index, name="close")


def test_purged_expanding_folds_have_disjoint_ordered_partitions() -> None:
    folds = purged_expanding_folds(n_samples=1000, n_splits=5, purge_gap=18)
    assert len(folds) == 5
    for fold in folds:
        assert fold.purge_rows == 18
        assert fold.train_indices[-1] < fold.purge_indices[0]
        assert fold.purge_indices[-1] < fold.test_indices[0]
        assert set(fold.train_indices).isdisjoint(fold.test_indices)


def test_nested_fold_plan_has_registered_identity_and_target_purging() -> None:
    value = contract()
    targets = build_development_targets(close_series(), value)
    plan = build_nested_fold_plan(targets, value)
    assert len(plan) == 120
    assert int((plan["level"] == "outer").sum()) == 30
    assert int((plan["level"] == "inner").sum()) == 90
    assert set(plan["purge_rows"].astype(int)) == set(value.horizons)
    assert (pd.to_datetime(plan["maximum_train_target_timestamp_utc"], utc=True) < pd.to_datetime(plan["test_start_utc"], utc=True)).all()
    assert not plan["shuffle"].any()


def test_matched_pair_uses_one_complete_row_intersection() -> None:
    value = contract()
    index = pd.date_range("2021-01-01", periods=300, freq="4h", tz="UTC")
    benchmark = pd.DataFrame(
        {
            "sol_ret_1": np.arange(300, dtype=float),
            "btc_ret_1": np.arange(300, dtype=float) / 2.0,
        },
        index=index,
    )
    candidate = pd.DataFrame({"rsi_level": np.sin(np.arange(300))}, index=index)
    benchmark.iloc[5, 0] = np.nan
    candidate.iloc[7, 0] = np.nan
    target = pd.Series((np.arange(300) % 2).astype(float), index=index)
    target.iloc[9] = np.nan

    pair = build_matched_pair(
        benchmark_features=benchmark,
        candidate_features=candidate,
        target=target,
        candidate_id="v3g5:single:" + "a" * 64,
        horizon_candles=1,
        contract=value,
    )
    assert pair.rows == 297
    assert pair.benchmark.index.equals(pair.candidate.index)
    assert pair.benchmark.index.equals(pair.target.index)
    assert list(pair.candidate.columns) == ["sol_ret_1", "btc_ret_1", "rsi_level"]
    manifest = matched_pair_manifest(pair)
    assert manifest["matched_rows"] == 297
    assert manifest["candidate_only_columns"] == ["rsi_level"]


def test_matched_pair_rejects_reserved_rows() -> None:
    value = contract()
    index = pd.date_range("2026-01-01", periods=50, freq="4h", tz="UTC")
    benchmark = pd.DataFrame({"benchmark": np.arange(50)}, index=index)
    candidate = pd.DataFrame({"signal": np.arange(50)}, index=index)
    target = pd.Series(np.arange(50) % 2, index=index)
    with pytest.raises(
        ReservedSegmentAccessError,
        match="PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED",
    ):
        build_matched_pair(
            benchmark_features=benchmark,
            candidate_features=candidate,
            target=target,
            candidate_id="v3g5:single:" + "b" * 64,
            horizon_candles=1,
            contract=value,
        )


def test_matched_pair_rejects_signal_columns_already_in_benchmark() -> None:
    value = contract()
    index = pd.date_range("2021-01-01", periods=50, freq="4h", tz="UTC")
    benchmark = pd.DataFrame({"shared": np.arange(50)}, index=index)
    candidate = pd.DataFrame({"shared": np.arange(50)}, index=index)
    target = pd.Series(np.arange(50) % 2, index=index)
    with pytest.raises(Exception, match="duplicate benchmark information"):
        build_matched_pair(
            benchmark_features=benchmark,
            candidate_features=candidate,
            target=target,
            candidate_id="v3g5:single:" + "c" * 64,
            horizon_candles=1,
            contract=value,
        )
