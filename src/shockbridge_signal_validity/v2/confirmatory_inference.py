
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BootstrapInterval:
    mean: float
    lower: float
    upper: float
    probability_nonpositive: float
    block_length: int


@dataclass(frozen=True)
class PredictiveComparison:
    mean_loss_differential: float
    standard_error: float
    statistic: float
    one_sided_p_value: float
    hac_lag: int


def _finite(values: Iterable[float]) -> np.ndarray:
    array = np.asarray(list(values), dtype=float)
    array = array[np.isfinite(array)]
    if len(array) == 0:
        raise ValueError("The inference series is empty after removing non-finite values.")
    return array


def normal_survival(value: float) -> float:
    return 0.5 * math.erfc(float(value) / math.sqrt(2.0))


def newey_west_variance_of_mean(values: Iterable[float], max_lag: int) -> float:
    x = _finite(values)
    n = len(x)
    lag = max(0, min(int(max_lag), n - 1))
    centered = x - float(np.mean(x))
    gamma0 = float(np.dot(centered, centered) / n)
    long_run_variance = gamma0
    for order in range(1, lag + 1):
        covariance = float(np.dot(centered[order:], centered[:-order]) / n)
        weight = 1.0 - order / (lag + 1.0)
        long_run_variance += 2.0 * weight * covariance
    return max(long_run_variance / n, 0.0)


def one_sided_predictive_comparison(
    loss_differentials: Iterable[float],
    horizon_candles: int,
) -> PredictiveComparison:
    x = _finite(loss_differentials)
    hac_lag = max(int(horizon_candles) - 1, 0)
    variance = newey_west_variance_of_mean(x, hac_lag)
    standard_error = math.sqrt(variance)
    mean_value = float(np.mean(x))
    if standard_error <= 0.0:
        statistic = math.inf if mean_value > 0.0 else -math.inf
    else:
        statistic = mean_value / standard_error
    return PredictiveComparison(
        mean_loss_differential=mean_value,
        standard_error=standard_error,
        statistic=float(statistic),
        one_sided_p_value=float(normal_survival(statistic)),
        hac_lag=hac_lag,
    )


def holm_adjusted_pvalues(pvalues: dict[str, float]) -> dict[str, float]:
    if not pvalues:
        raise ValueError("Holm adjustment requires at least one p-value.")
    ordered = sorted((name, min(max(float(value), 0.0), 1.0)) for name, value in pvalues.items())
    ordered.sort(key=lambda item: item[1])
    total = len(ordered)
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, (name, value) in enumerate(ordered):
        candidate = min(1.0, (total - rank) * value)
        running = max(running, candidate)
        adjusted[name] = running
    return adjusted


def moving_block_bootstrap_mean_interval(
    values: Iterable[float],
    samples: int,
    block_length: int,
    confidence_level: float,
    random_seed: int,
) -> BootstrapInterval:
    x = _finite(values)
    n = len(x)
    block = max(1, min(int(block_length), n))
    starts = np.arange(0, n - block + 1)
    rng = np.random.default_rng(int(random_seed))
    means = np.empty(int(samples), dtype=float)
    for index in range(int(samples)):
        draw: list[float] = []
        while len(draw) < n:
            start = int(rng.choice(starts))
            draw.extend(x[start : start + block].tolist())
        means[index] = float(np.mean(draw[:n]))
    alpha = 1.0 - float(confidence_level)
    return BootstrapInterval(
        mean=float(np.mean(x)),
        lower=float(np.quantile(means, alpha / 2.0)),
        upper=float(np.quantile(means, 1.0 - alpha / 2.0)),
        probability_nonpositive=float(np.mean(means <= 0.0)),
        block_length=block,
    )


def matched_policy_returns(
    frame: pd.DataFrame,
    probability_distance_threshold: float,
    one_way_cost_bps: float,
) -> pd.DataFrame:
    required = {
        "candidate_probability",
        "benchmark_probability",
        "future_return",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError("Missing policy columns: " + ", ".join(missing))
    result = frame.copy()
    threshold = float(probability_distance_threshold)
    candidate_probability = result["candidate_probability"].to_numpy(float)
    benchmark_probability = result["benchmark_probability"].to_numpy(float)
    future_return = result["future_return"].to_numpy(float)

    candidate_active = np.abs(candidate_probability - 0.5) > threshold
    benchmark_active = np.abs(benchmark_probability - 0.5) > threshold
    candidate_position = np.where(
        candidate_active,
        np.where(candidate_probability > 0.5, 1.0, -1.0),
        0.0,
    )
    benchmark_position = np.where(
        benchmark_active,
        np.where(benchmark_probability > 0.5, 1.0, -1.0),
        0.0,
    )
    candidate_prior = np.concatenate([[0.0], candidate_position[:-1]])
    benchmark_prior = np.concatenate([[0.0], benchmark_position[:-1]])
    candidate_turnover = np.abs(candidate_position - candidate_prior)
    benchmark_turnover = np.abs(benchmark_position - benchmark_prior)
    cost = float(one_way_cost_bps) / 10000.0

    result["candidate_decision_active"] = candidate_active
    result["benchmark_decision_active"] = benchmark_active
    result["candidate_position"] = candidate_position
    result["benchmark_position"] = benchmark_position
    result["candidate_turnover_units"] = candidate_turnover
    result["benchmark_turnover_units"] = benchmark_turnover
    result["candidate_gross_return"] = candidate_position * future_return
    result["benchmark_gross_return"] = benchmark_position * future_return
    result["candidate_net_return"] = result["candidate_gross_return"] - candidate_turnover * cost
    result["benchmark_net_return"] = result["benchmark_gross_return"] - benchmark_turnover * cost
    result["incremental_gross_return"] = result["candidate_gross_return"] - result["benchmark_gross_return"]
    result["incremental_net_return"] = result["candidate_net_return"] - result["benchmark_net_return"]
    return result


def expected_calibration_error(
    realised: Iterable[int], probabilities: Iterable[float], bins: int = 10
) -> float:
    y = _finite(realised).astype(int)
    p = _finite(probabilities)
    if len(y) != len(p):
        raise ValueError("Calibration inputs have different lengths.")
    edges = np.linspace(0.0, 1.0, int(bins) + 1)
    assignments = np.clip(np.digitize(p, edges[1:-1], right=False), 0, bins - 1)
    error = 0.0
    for bucket in range(int(bins)):
        mask = assignments == bucket
        if not np.any(mask):
            continue
        error += float(np.mean(mask)) * abs(float(np.mean(y[mask])) - float(np.mean(p[mask])))
    return float(error)


def brier_score(realised: Iterable[int], probabilities: Iterable[float]) -> float:
    y = _finite(realised).astype(float)
    p = _finite(probabilities)
    if len(y) != len(p):
        raise ValueError("Brier inputs have different lengths.")
    return float(np.mean((p - y) ** 2))


def monthly_positive_concentration(frame: pd.DataFrame) -> tuple[pd.DataFrame, float, str | None]:
    if "Timestamp" not in frame.columns or "incremental_net_return" not in frame.columns:
        raise ValueError("Monthly concentration requires Timestamp and incremental_net_return.")
    monthly = frame.copy()
    monthly["Timestamp"] = pd.to_datetime(monthly["Timestamp"], utc=True, errors="raise")
    monthly["calendar_month"] = monthly["Timestamp"].dt.strftime("%Y-%m")
    table = (
        monthly.groupby("calendar_month", sort=True)["incremental_net_return"]
        .agg(["size", "mean", "sum"])
        .reset_index()
        .rename(
            columns={
                "size": "rows",
                "mean": "mean_incremental_net_return",
                "sum": "cumulative_incremental_net_return",
            }
        )
    )
    positive = table.loc[table["cumulative_incremental_net_return"] > 0.0].copy()
    total_positive = float(positive["cumulative_incremental_net_return"].sum())
    table["share_of_total_positive_contribution"] = 0.0
    if total_positive <= 0.0 or positive.empty:
        return table, 0.0, None
    mask = table["cumulative_incremental_net_return"] > 0.0
    table.loc[mask, "share_of_total_positive_contribution"] = (
        table.loc[mask, "cumulative_incremental_net_return"] / total_positive
    )
    maximum_row = table.loc[table["share_of_total_positive_contribution"].idxmax()]
    return (
        table,
        float(maximum_row["share_of_total_positive_contribution"]),
        str(maximum_row["calendar_month"]),
    )


def select_development_block_length(
    close: pd.Series,
    maximum_lag: int = 48,
    threshold: float = 0.10,
    consecutive_lags: int = 3,
) -> tuple[int, list[float]]:
    returns = np.log(close.astype(float)).diff().dropna()
    squared = returns.pow(2)
    acf = [float(squared.autocorr(lag=lag)) for lag in range(1, int(maximum_lag) + 1)]
    run = int(consecutive_lags)
    for lag in range(1, int(maximum_lag) - run + 2):
        values = acf[lag - 1 : lag - 1 + run]
        if all(np.isfinite(values)) and all(abs(value) <= float(threshold) for value in values):
            return lag, acf
    raise ValueError("The deterministic development-only block-length rule did not resolve.")
