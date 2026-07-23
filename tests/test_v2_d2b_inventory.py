from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from shockbridge_signal_validity.v2.pipeline_selection import (
    apply_training_window,
    build_structural_pipeline_inventory,
)


def registry_payload() -> dict:
    return json.loads(Path("configs/v2_experiment_registry.json").read_text(encoding="utf-8"))


def test_d2b_structural_inventory_matches_frozen_grid() -> None:
    inventory = build_structural_pipeline_inventory(registry_payload())
    assert len(inventory) == 90
    assert inventory["pipeline_id"].is_unique
    assert inventory.groupby("model_family").size().to_dict() == {
        "regularized_linear": 18,
        "spline_regularized": 24,
        "shallow_hist_gradient_boosting": 48,
    }
    assert set(inventory["window_scheme"]) == {
        "expanding",
        "rolling_one_year",
        "rolling_two_year",
    }
    assert set(inventory["regime_conditioned"]) == {False, True}


def test_training_window_uses_only_trailing_training_rows() -> None:
    index = pd.date_range("2021-01-01", periods=5000, freq="4h", tz="UTC")
    frame = pd.DataFrame({"x": range(len(index))}, index=index)
    registry = registry_payload()
    one_year = apply_training_window(frame, "rolling_one_year", registry)
    two_year = apply_training_window(frame, "rolling_two_year", registry)
    expanding = apply_training_window(frame, "expanding", registry)
    assert len(one_year) == 2190
    assert len(two_year) == 4380
    assert len(expanding) == 5000
    assert one_year.index[-1] == frame.index[-1]
    assert one_year.index[0] == frame.index[-2190]
