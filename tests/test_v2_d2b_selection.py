from __future__ import annotations

import pandas as pd

from shockbridge_signal_validity.v2.pipeline_selection import (
    select_abstention_policy,
    select_calibration_method,
    select_structural_pipeline,
)


def test_structural_selection_respects_calibration_non_dominance() -> None:
    rows = []
    for fold in (1, 2, 3):
        rows.append(
            {
                "pipeline_id": "stable",
                "inner_fold": fold,
                "incremental_log_loss": 0.01,
                "benchmark_brier": 0.20,
                "candidate_brier": 0.20,
                "benchmark_ece": 0.03,
                "candidate_ece": 0.03,
                "complexity_rank": 1,
            }
        )
        rows.append(
            {
                "pipeline_id": "miscalibrated",
                "inner_fold": fold,
                "incremental_log_loss": 0.03,
                "benchmark_brier": 0.20,
                "candidate_brier": 0.25,
                "benchmark_ece": 0.03,
                "candidate_ece": 0.10,
                "complexity_rank": 2,
            }
        )
    selected = select_structural_pipeline(pd.DataFrame(rows))
    assert selected["pipeline_id"] == "stable"


def test_calibration_selection_excludes_isotonic() -> None:
    rows = []
    values = {
        "none": (0.01, 0.20, 0.03, True),
        "sigmoid": (0.012, 0.195, 0.02, True),
        "isotonic": (0.10, 0.10, 0.01, False),
    }
    for method, (gain, brier, ece, eligible) in values.items():
        for fold in (1, 2, 3):
            rows.append(
                {
                    "calibration_method": method,
                    "inner_fold": fold,
                    "incremental_log_loss": gain,
                    "candidate_brier": brier,
                    "candidate_ece": ece,
                    "eligible_for_selection": eligible,
                }
            )
    selected = select_calibration_method(pd.DataFrame(rows))
    assert selected["calibration_method"] == "sigmoid"


def test_abstention_selection_enforces_coverage_and_decisions() -> None:
    rows = []
    for fold in (1, 2, 3):
        rows.extend(
            [
                {"threshold": 0.0, "inner_fold": fold, "coverage": 1.0, "nonzero_decisions": 100, "mean_net_edge": 0.001},
                {"threshold": 0.05, "inner_fold": fold, "coverage": 0.30, "nonzero_decisions": 40, "mean_net_edge": 0.003},
                {"threshold": 0.10, "inner_fold": fold, "coverage": 0.05, "nonzero_decisions": 8, "mean_net_edge": 0.020},
            ]
        )
    selected = select_abstention_policy(pd.DataFrame(rows))
    assert selected["threshold"] == 0.05
    assert selected["governance_interpretation"] == "DEVELOPMENT_POLICY_SELECTION_NOT_ECONOMIC_GATE"
