import pandas as pd

from shockbridge_signal_validity.v2.development_admission import (
    build_family_horizon_admission,
    select_family_decisions,
)


def config() -> dict:
    return {
        "admission_gates": {
            "required_outer_folds": 5,
            "minimum_positive_outer_folds": 3,
            "maximum_single_fold_share_of_positive_gain": 0.6,
            "brier_tolerance": 0.0025,
            "ece_tolerance": 0.01,
            "minimum_mean_policy_coverage": 0.1,
            "minimum_total_policy_decisions": 100,
        }
    }


def outer_frame() -> pd.DataFrame:
    rows = []
    for family in ("rsi", "bollinger"):
        for horizon in (1, 2, 3, 6):
            gains = [0.02, 0.015, 0.01, -0.002, 0.005] if horizon == 1 else [-0.01] * 5
            for fold, gain in enumerate(gains, 1):
                rows.append(
                    {
                        "signal_family": family,
                        "horizon_candles": horizon,
                        "outer_fold": fold,
                        "incremental_log_loss": gain,
                        "benchmark_brier": 0.25,
                        "candidate_brier": 0.249,
                        "benchmark_ece": 0.04,
                        "candidate_ece": 0.041,
                        "policy_coverage": 0.5,
                        "policy_nonzero_decisions": 30,
                        "policy_mean_net_edge": 0.0,
                    }
                )
    return pd.DataFrame(rows)


def test_admission_requires_all_frozen_development_gates() -> None:
    result = build_family_horizon_admission(outer_frame(), config())
    passed = result.loc[result["development_admission_pass"]]
    assert len(passed) == 2
    assert set(passed["horizon_candles"]) == {1}
    assert not result["economic_gate_evaluated"].any()
    assert not result["holdout_evidence_used"].any()


def test_family_decision_selects_only_admitted_horizon() -> None:
    admission = build_family_horizon_admission(outer_frame(), config())
    decisions = select_family_decisions(admission)
    assert decisions["pipeline_admitted"].all()
    assert set(decisions["selected_horizon_candles"]) == {1}
