
import numpy as np
import pandas as pd

from shockbridge_signal_validity.v2.confirmatory_inference import (
    holm_adjusted_pvalues,
    matched_policy_returns,
    moving_block_bootstrap_mean_interval,
    one_sided_predictive_comparison,
)


def test_holm_preserves_two_hypothesis_family() -> None:
    adjusted = holm_adjusted_pvalues({"H1": 1.0, "H2": 0.02})
    assert adjusted["H2"] == 0.04
    assert adjusted["H1"] == 1.0


def test_predictive_comparison_rewards_positive_loss_differential() -> None:
    comparison = one_sided_predictive_comparison([0.02, 0.01, 0.03, 0.02], horizon_candles=1)
    assert comparison.mean_loss_differential > 0.0
    assert comparison.statistic > 0.0
    assert comparison.one_sided_p_value < 0.5
    assert comparison.hac_lag == 0


def test_moving_block_bootstrap_is_deterministic() -> None:
    values = np.linspace(-0.01, 0.03, 40)
    first = moving_block_bootstrap_mean_interval(values, 200, 5, 0.95, 42)
    second = moving_block_bootstrap_mean_interval(values, 200, 5, 0.95, 42)
    assert first == second


def test_matched_policy_applies_same_threshold_and_cost() -> None:
    frame = pd.DataFrame({
        "candidate_probability": [0.60, 0.40, 0.51],
        "benchmark_probability": [0.54, 0.46, 0.50],
        "future_return": [0.01, -0.01, 0.02],
    })
    result = matched_policy_returns(frame, 0.05, 10)
    assert int(result["candidate_decision_active"].sum()) == 2
    assert int(result["benchmark_decision_active"].sum()) == 0
    assert "incremental_net_return" in result
