import numpy as np
import pandas as pd

from shockbridge_signal_validity.v2.locked_evaluation import (
    assign_equal_chronological_subperiods,
    build_dual_boundary_targets,
)
from shockbridge_signal_validity.v2.registry import load_v2_registry


def test_equal_chronological_subperiods_are_complete_and_ordered() -> None:
    index = pd.date_range("2026-01-01", periods=10, freq="4h", tz="UTC")
    labels = assign_equal_chronological_subperiods(index)
    assert set(labels) == {"P1", "P2", "P3"}
    assert labels.iloc[0] == "P1"
    assert labels.iloc[-1] == "P3"


def test_dual_boundary_targets_do_not_cross_partition_ends() -> None:
    registry = load_v2_registry()
    index = pd.date_range(
        registry.development_start,
        registry.holdout_end,
        freq="4h",
        tz="UTC",
    )
    close = pd.Series(np.exp(np.linspace(0.0, 0.5, len(index))), index=index)
    target, future, target_timestamp = build_dual_boundary_targets(close, 1, registry)
    assert pd.isna(target.loc[registry.development_end])
    assert pd.isna(future.loc[registry.holdout_end])
    usable_holdout = target_timestamp.loc[registry.holdout_start : registry.holdout_end].dropna()
    assert usable_holdout.max() <= registry.holdout_end
