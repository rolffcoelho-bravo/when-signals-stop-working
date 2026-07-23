from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v2.contracts import HoldoutAccessError
from shockbridge_signal_validity.v2.inventory import build_candidate_inventory
from shockbridge_signal_validity.v2.partitions import (
    assert_development_only,
    build_development_partition,
)
from shockbridge_signal_validity.v2.registry import load_v2_registry
from shockbridge_signal_validity.v2.signals import (
    add_soft_state_interactions,
    build_bollinger_signal_features,
    build_rsi_signal_features,
)
from shockbridge_signal_validity.v2.splits import (
    build_nested_fold_plan,
    purged_expanding_folds,
)
from shockbridge_signal_validity.v2.targets import build_development_targets


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configs" / "v2_experiment_registry.json"


def _index(rows: int = 200) -> pd.DatetimeIndex:
    return pd.date_range("2025-01-01", periods=rows, freq="4h", tz="UTC")


def test_registry_is_frozen_and_partitions_do_not_overlap() -> None:
    registry = load_v2_registry(REGISTRY)
    assert registry.payload["freeze_status"] == "FROZEN_BEFORE_IMPLEMENTATION"
    assert registry.development_end < registry.holdout_start
    assert registry.horizons == (1, 2, 3, 6)


def test_development_partition_excludes_locked_rows() -> None:
    registry = load_v2_registry(REGISTRY)
    index = pd.date_range(
        registry.development_start,
        registry.holdout_end,
        freq="4h",
    )
    frame = pd.DataFrame({"value": np.arange(len(index))}, index=index)
    partition = build_development_partition(frame, registry)
    assert partition.frame.index.max() == registry.development_end
    assert partition.frame.index.max() < registry.holdout_start
    with pytest.raises(HoldoutAccessError):
        assert_development_only(frame, registry)


def test_targets_never_cross_development_boundary() -> None:
    index = _index(100)
    close = pd.Series(np.exp(np.linspace(4.0, 4.2, len(index))), index=index)
    development_end = index[-1]
    targets = build_development_targets(close, [1, 2, 3, 6], development_end)
    for horizon in (1, 2, 3, 6):
        timestamps = targets[f"target_timestamp_h{horizon}"].dropna()
        assert timestamps.max() <= development_end
        assert targets[f"future_log_return_h{horizon}"].notna().sum() == len(index) - horizon


def test_purged_folds_are_chronological_and_horizon_safe() -> None:
    folds = purged_expanding_folds(600, n_splits=5, purge_gap=6)
    assert len(folds) == 5
    for fold in folds:
        assert len(fold.purge_indices) == 6
        assert fold.train_indices.max() < fold.purge_indices.min()
        assert fold.purge_indices.max() < fold.test_indices.min()


def test_nested_fold_plan_has_declared_shape() -> None:
    index = _index(1000)
    plan = build_nested_fold_plan(index, [1, 2, 3, 6], 5, 3)
    assert len(plan) == 4 * 5 * 4
    assert (plan["purge_rows"] == plan["horizon_candles"]).all()
    assert set(plan["level"]) == {"outer", "inner"}


def test_candidate_inventory_matches_registered_confirmatory_space() -> None:
    registry = load_v2_registry(REGISTRY)
    inventory = build_candidate_inventory(registry)
    assert inventory["candidate_id"].is_unique
    assert set(inventory["signal_family"]) == {"rsi", "bollinger"}
    assert len(inventory) == 6048
    assert len(inventory.query("signal_family == 'rsi'")) == 3456
    assert len(inventory.query("signal_family == 'bollinger'")) == 2592


def test_signal_interpretations_are_explicit() -> None:
    index = _index(100)
    close = pd.Series(100.0 + np.sin(np.arange(100) / 4.0), index=index)
    rsi_contrarian = build_rsi_signal_features(close, 14, 30, 70, "contrarian")
    rsi_continuation = build_rsi_signal_features(close, 14, 30, 70, "continuation")
    assert np.allclose(
        rsi_contrarian["rsi_signal_score"].dropna(),
        -rsi_continuation["rsi_signal_score"].dropna(),
    )
    bb = build_bollinger_signal_features(close, 20, 2.0, "continuous")
    assert {"bb_percent_b", "bb_bandwidth", "bb_signal_score"}.issubset(bb)


def test_soft_state_interactions_require_probabilities() -> None:
    index = _index(20)
    signal = pd.Series(np.linspace(-1.0, 1.0, len(index)), index=index)
    probabilities = pd.DataFrame(
        {
            "state_p_range": 0.5,
            "state_p_trend": 0.3,
            "state_p_stress": 0.2,
        },
        index=index,
    )
    interactions = add_soft_state_interactions(signal, probabilities)
    assert interactions.shape == (20, 3)
    bad = probabilities.copy()
    bad["state_p_stress"] = 0.4
    with pytest.raises(Exception):
        add_soft_state_interactions(signal, bad)


def test_runtime_defaults_disable_model_fitting_and_holdout() -> None:
    payload = json.loads(
        (ROOT / "configs" / "v2_runtime_defaults.json").read_text(encoding="utf-8")
    )
    assert payload["model_fitting_enabled"] is False
    assert payload["holdout_performance_access_enabled"] is False
