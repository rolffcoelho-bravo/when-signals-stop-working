from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
)

from .forecast_contract import ForecastProtocolViolation


@dataclass(frozen=True)
class MetricBundle:
    target_name: str
    primary_metric_name: str
    primary_loss: float
    secondary_metrics: dict[str, float]


@dataclass(frozen=True)
class EconomicBundle:
    observations: int
    nonzero_decisions: int
    coverage: float
    gross_return: float
    turnover: float
    transaction_cost: float
    net_return: float


def _finite_vector(values: Any, label: str) -> np.ndarray:
    vector = np.asarray(values, dtype=float).reshape(-1)
    if vector.size == 0 or not np.isfinite(vector).all():
        raise ForecastProtocolViolation(f"{label} must be finite and nonempty.")
    return vector


def expected_calibration_error(
    y_true: Any,
    probability: Any,
    *,
    bins: int = 10,
) -> float:
    target = _finite_vector(y_true, "Calibration target")
    estimate = _finite_vector(probability, "Calibration probability")
    if len(target) != len(estimate):
        raise ForecastProtocolViolation("Calibration rows differ.")
    if not set(np.unique(target)).issubset({0.0, 1.0}):
        raise ForecastProtocolViolation("Calibration target must be binary.")
    if ((estimate < 0.0) | (estimate > 1.0)).any() or int(bins) < 2:
        raise ForecastProtocolViolation("Calibration probability or bin count is invalid.")
    edges = np.linspace(0.0, 1.0, int(bins) + 1)
    assignments = np.minimum(np.digitize(estimate, edges[1:-1], right=True), int(bins) - 1)
    error = 0.0
    for bin_index in range(int(bins)):
        mask = assignments == bin_index
        if mask.any():
            error += float(mask.mean()) * abs(float(target[mask].mean()) - float(estimate[mask].mean()))
    return float(error)


def classification_metrics(
    target_name: str,
    y_true: Any,
    probability: Any,
) -> MetricBundle:
    target = _finite_vector(y_true, "Classification target")
    estimate = _finite_vector(probability, "Classification probability")
    if len(target) != len(estimate):
        raise ForecastProtocolViolation("Classification rows differ.")
    if not set(np.unique(target)).issubset({0.0, 1.0}):
        raise ForecastProtocolViolation("Classification target must be binary.")
    if ((estimate < 0.0) | (estimate > 1.0)).any():
        raise ForecastProtocolViolation("Classification probabilities must lie in [0,1].")
    clipped = np.clip(estimate, 1e-12, 1.0 - 1e-12)
    secondary: dict[str, float] = {
        "brier_score": float(brier_score_loss(target, estimate)),
    }
    if target_name == "direction":
        secondary["expected_calibration_error"] = expected_calibration_error(target, estimate)
        secondary["roc_auc"] = (
            float(roc_auc_score(target, estimate)) if len(np.unique(target)) == 2 else float("nan")
        )
    elif target_name == "large_move_probability":
        secondary["pr_auc"] = (
            float(average_precision_score(target, estimate)) if target.sum() > 0 else float("nan")
        )
    else:
        raise ForecastProtocolViolation(f"Unknown classification target: {target_name}")
    return MetricBundle(
        target_name=target_name,
        primary_metric_name="log_loss",
        primary_loss=float(log_loss(target, clipped, labels=[0.0, 1.0])),
        secondary_metrics=secondary,
    )


def regression_metrics(y_true: Any, prediction: Any) -> MetricBundle:
    target = _finite_vector(y_true, "Regression target")
    estimate = _finite_vector(prediction, "Regression prediction")
    if len(target) != len(estimate):
        raise ForecastProtocolViolation("Regression rows differ.")
    return MetricBundle(
        target_name="expected_return",
        primary_metric_name="mean_squared_error",
        primary_loss=float(mean_squared_error(target, estimate)),
        secondary_metrics={
            "mean_absolute_error": float(mean_absolute_error(target, estimate)),
            "directional_accuracy": float(np.mean(np.sign(target) == np.sign(estimate))),
        },
    )


def direction_positions(probability: Any, abstention_threshold: float) -> np.ndarray:
    estimate = _finite_vector(probability, "Direction probability")
    threshold = float(abstention_threshold)
    if threshold < 0.0 or threshold >= 0.5:
        raise ForecastProtocolViolation("Direction abstention threshold is invalid.")
    distance = np.abs(estimate - 0.5)
    return np.where(distance >= threshold, np.sign(estimate - 0.5), 0.0)


def expected_return_positions(prediction: Any) -> np.ndarray:
    estimate = _finite_vector(prediction, "Expected-return prediction")
    return np.clip(estimate, -1.0, 1.0)


def economic_metrics(
    realized_log_return: Any,
    position: Any,
    *,
    one_way_cost_bps: float,
    horizon_candles: int,
) -> EconomicBundle:
    realized = _finite_vector(realized_log_return, "Realized log return")
    positions = _finite_vector(position, "Position")
    if len(realized) != len(positions):
        raise ForecastProtocolViolation("Economic rows differ.")
    if float(one_way_cost_bps) < 0.0 or int(horizon_candles) < 1:
        raise ForecastProtocolViolation("Economic cost or horizon is invalid.")
    decision_mask = np.arange(len(realized)) % int(horizon_candles) == 0
    spaced_returns = realized[decision_mask]
    spaced_positions = positions[decision_mask]
    previous = np.concatenate(([0.0], spaced_positions[:-1]))
    turnover = np.abs(spaced_positions - previous)
    cost_rate = float(one_way_cost_bps) / 10000.0
    gross = spaced_positions * spaced_returns
    costs = turnover * cost_rate
    observations = int(len(spaced_returns))
    nonzero = int(np.count_nonzero(spaced_positions))
    return EconomicBundle(
        observations=observations,
        nonzero_decisions=nonzero,
        coverage=float(nonzero / observations) if observations else 0.0,
        gross_return=float(gross.sum()),
        turnover=float(turnover.sum()),
        transaction_cost=float(costs.sum()),
        net_return=float((gross - costs).sum()),
    )


def incremental_economic_gain(candidate: EconomicBundle, benchmark: EconomicBundle) -> float:
    if candidate.observations != benchmark.observations:
        raise ForecastProtocolViolation("Economic benchmark and candidate observations differ.")
    return float(candidate.net_return - benchmark.net_return)
