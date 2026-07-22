from __future__ import annotations

import numpy as np
import pandas as pd

from shockbridge_signal_validity.v2.predictive_screening import (
    preliminary_gate_summary,
    select_screening_specification,
    unique_signal_specifications,
)


def test_unique_signal_specifications_deduplicates_inventory() -> None:
    inventory = pd.DataFrame(
        [
            {"signal_family": "rsi", "interpretation": "continuous", "period": 14, "lower_threshold": 30.0, "upper_threshold": 70.0, "standard_deviations": np.nan},
            {"signal_family": "rsi", "interpretation": "continuous", "period": 14, "lower_threshold": 30.0, "upper_threshold": 70.0, "standard_deviations": np.nan},
            {"signal_family": "bollinger", "interpretation": "contrarian", "period": 20, "lower_threshold": np.nan, "upper_threshold": np.nan, "standard_deviations": 2.0},
        ]
    )
    specifications = unique_signal_specifications(inventory)
    assert len(specifications) == 2
    assert len({value.signal_spec_id for value in specifications}) == 2


def test_inner_selection_prefers_incremental_loss_subject_to_calibration() -> None:
    frame = pd.DataFrame(
        {
            "signal_spec_id": ["a", "a", "a", "b", "b", "b"],
            "inner_fold": [1, 2, 3, 1, 2, 3],
            "incremental_log_loss": [0.01, 0.02, 0.015, 0.03, 0.03, 0.03],
            "candidate_brier": [0.20, 0.20, 0.20, 0.25, 0.25, 0.25],
            "benchmark_brier": [0.20, 0.20, 0.20, 0.20, 0.20, 0.20],
        }
    )
    selected = select_screening_specification(frame)
    assert selected["signal_spec_id"] == "a"


def test_preliminary_gate_summary_requires_stability_and_concentration() -> None:
    rows = []
    for fold, value in enumerate([0.01, 0.01, 0.01, -0.001, -0.001], start=1):
        rows.append({"signal_family": "rsi", "horizon_candles": 1, "outer_fold": fold, "incremental_log_loss": value})
    summary = preliminary_gate_summary(pd.DataFrame(rows))
    assert bool(summary.iloc[0]["screening_gate_pass"])
    assert summary.iloc[0]["governance_interpretation"] == "PRELIMINARY_SCREENING_ONLY_NOT_FINAL_GATE_2"
