from __future__ import annotations

import numpy as np
import pandas as pd

from shockbridge_signal_validity.v2.robustness_publication import (
    active_confidence_stratification,
    development_component_stability,
    joint_influence_trim_summary,
    leave_one_group_out_summary,
    matched_policy_contributions,
    robustness_classification,
    state_stratification,
)


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Timestamp": pd.date_range(
                "2026-01-01", periods=12, freq="4h", tz="UTC"
            ),
            "candidate_probability": [
                0.40,
                0.60,
                0.44,
                0.56,
                0.30,
                0.70,
                0.49,
                0.51,
                0.20,
                0.80,
                0.45,
                0.55,
            ],
            "benchmark_probability": [
                0.45,
                0.55,
                0.48,
                0.52,
                0.40,
                0.60,
                0.49,
                0.51,
                0.35,
                0.65,
                0.46,
                0.54,
            ],
            "future_return": [
                -0.01,
                0.01,
                -0.005,
                0.005,
                -0.02,
                0.02,
                0.001,
                -0.001,
                -0.03,
                0.03,
                -0.004,
                0.004,
            ],
            "incremental_observation_log_loss": np.linspace(
                -0.01, 0.02, 12
            ),
            "state_label": ["range"] * 6 + ["trend"] * 3 + ["stress"] * 3,
            "state_p_stress": [0.01] * 6 + [0.03] * 3 + [0.8] * 3,
        }
    )


def test_matched_policy_and_diagnostics_are_deterministic() -> None:
    policy = matched_policy_contributions(sample_frame(), 0.05, 10)
    assert len(policy) == 12
    assert {
        "candidate_decision_active",
        "benchmark_decision_active",
        "incremental_net_return",
        "candidate_confidence_distance",
    }.issubset(policy.columns)

    policy["calendar_month"] = [
        "2026-01"
    ] * 6 + ["2026-02"] * 6
    leave_out = leave_one_group_out_summary(
        policy,
        "calendar_month",
        "incremental_observation_log_loss",
        "incremental_net_return",
    )
    assert len(leave_out) == 2

    trimmed = joint_influence_trim_summary(
        policy,
        "incremental_observation_log_loss",
        "incremental_net_return",
        [0.0, 0.05],
    )
    assert trimmed["retained_rows"].iloc[1] <= trimmed["retained_rows"].iloc[0]


def test_state_and_confidence_outputs_are_diagnostic_only() -> None:
    policy = matched_policy_contributions(sample_frame(), 0.05, 10)
    states = state_stratification(policy, minimum_interpretable_rows=4)
    assert states["rows"].sum() == len(policy)
    assert set(states["confirmatory_effect"]) == {"NONE_DIAGNOSTIC_ONLY"}

    confidence = active_confidence_stratification(policy, quantiles=3)
    assert confidence["rows"].sum() == int(
        policy["candidate_decision_active"].sum()
    )
    assert set(confidence["confirmatory_effect"]) == {
        "NONE_DIAGNOSTIC_ONLY"
    }


def test_development_component_stability_does_not_execute_holdout() -> None:
    rows = []
    for fold in range(1, 6):
        rows.append(
            {
                "signal_family": "bollinger",
                "horizon_candles": 1,
                "outer_fold": fold,
                "selected_signal_spec_id": (
                    "bollinger-p10-k2.5-continuation"
                    if fold < 4
                    else "bollinger-p40-k1.5-continuation"
                ),
                "model_family": "shallow_hist_gradient_boosting",
                "window_scheme": "expanding",
                "regime_conditioned": True,
                "selected_calibration_method": "none",
                "selected_threshold": 0.05,
            }
        )
    table = development_component_stability(
        pd.DataFrame(rows),
        signal_family="bollinger",
        horizon_candles=1,
    )
    assert table.loc[
        table["component"].eq("model_family"), "modal_share"
    ].iloc[0] == 1.0
    assert not table["holdout_reexecution_performed"].any()


def test_robustness_classification_preserves_failure() -> None:
    matrix = pd.DataFrame(
        {"diagnostic_status": ["PASS", "CAUTION", "FAIL"]}
    )
    result = robustness_classification(matrix)
    assert result.determination == "FAVOURABLE_MEANS_NOT_CONFIDENCE_ROBUST"
    assert result.failed_diagnostics == 1
