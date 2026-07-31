from __future__ import annotations

import numpy as np
import pytest

from shockbridge_signal_validity.v3.forecast_contract import ForecastProtocolViolation
from shockbridge_signal_validity.v3.forecast_development_metrics import (
    classification_metrics,
    direction_positions,
    economic_metrics,
    expected_calibration_error,
    expected_return_positions,
    incremental_economic_gain,
    regression_metrics,
)


def test_direction_metrics_are_finite_and_bounded() -> None:
    target = np.array([0, 0, 1, 1, 0, 1])
    probability = np.array([0.1, 0.3, 0.7, 0.9, 0.4, 0.8])
    result = classification_metrics("direction", target, probability)
    assert result.primary_metric_name == "log_loss"
    assert result.primary_loss > 0.0
    assert 0.0 <= result.secondary_metrics["brier_score"] <= 1.0
    assert 0.0 <= result.secondary_metrics["expected_calibration_error"] <= 1.0
    assert 0.0 <= result.secondary_metrics["roc_auc"] <= 1.0


def test_large_move_metrics_include_pr_auc() -> None:
    target = np.array([0, 0, 0, 1, 0, 1])
    probability = np.array([0.05, 0.1, 0.2, 0.8, 0.15, 0.9])
    result = classification_metrics("large_move_probability", target, probability)
    assert result.primary_loss > 0.0
    assert 0.0 <= result.secondary_metrics["pr_auc"] <= 1.0


def test_regression_metrics_match_perfect_prediction() -> None:
    target = np.array([-0.2, -0.1, 0.1, 0.3])
    result = regression_metrics(target, target.copy())
    assert result.primary_loss == pytest.approx(0.0)
    assert result.secondary_metrics["mean_absolute_error"] == pytest.approx(0.0)
    assert result.secondary_metrics["directional_accuracy"] == pytest.approx(1.0)


def test_expected_calibration_error_rejects_invalid_probabilities() -> None:
    with pytest.raises(ForecastProtocolViolation, match=r"\[0,1\]"):
        expected_calibration_error([0, 1], [-0.1, 1.1])


def test_direction_positions_apply_abstention() -> None:
    probability = np.array([0.2, 0.49, 0.5, 0.51, 0.8])
    positions = direction_positions(probability, 0.05)
    np.testing.assert_array_equal(positions, np.array([-1.0, 0.0, 0.0, 0.0, 1.0]))


def test_expected_return_positions_are_clipped() -> None:
    positions = expected_return_positions([-2.0, -0.5, 0.0, 0.6, 3.0])
    np.testing.assert_allclose(positions, [-1.0, -0.5, 0.0, 0.6, 1.0])


def test_economic_metrics_use_horizon_spacing_and_turnover_cost() -> None:
    realized = np.full(12, 0.01)
    position = np.ones(12)
    result = economic_metrics(
        realized,
        position,
        one_way_cost_bps=10,
        horizon_candles=3,
    )
    assert result.observations == 4
    assert result.nonzero_decisions == 4
    assert result.coverage == pytest.approx(1.0)
    assert result.turnover == pytest.approx(1.0)
    assert result.transaction_cost == pytest.approx(0.001)
    assert result.net_return == pytest.approx(0.039)


def test_incremental_economic_gain_requires_matched_observations() -> None:
    first = economic_metrics([0.01, 0.02], [1, 1], one_way_cost_bps=10, horizon_candles=1)
    second = economic_metrics([0.01, 0.02, 0.03], [1, 1, 1], one_way_cost_bps=10, horizon_candles=1)
    with pytest.raises(ForecastProtocolViolation, match="observations differ"):
        incremental_economic_gain(first, second)
