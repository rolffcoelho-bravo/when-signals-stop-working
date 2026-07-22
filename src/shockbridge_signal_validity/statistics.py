from __future__ import annotations

from collections.abc import Iterable

import numpy as np


RANDOM_SEED = 42


def moving_block_bootstrap_mean_ci(
    values: Iterable[float],
    samples: int = 2000,
    block_size: int = 10,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    x = np.asarray(list(values), dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        raise ValueError("Cannot bootstrap an empty series.")

    block_size = max(1, min(int(block_size), len(x)))
    starts = np.arange(0, len(x) - block_size + 1)
    rng = np.random.default_rng(RANDOM_SEED)
    means = np.empty(samples)

    for index in range(samples):
        draw: list[float] = []
        while len(draw) < len(x):
            start = int(rng.choice(starts))
            draw.extend(x[start : start + block_size].tolist())
        means[index] = float(np.mean(draw[: len(x)]))

    return (
        float(np.mean(x)),
        float(np.quantile(means, alpha / 2.0)),
        float(np.quantile(means, 1.0 - alpha / 2.0)),
    )


def matched_random_event_pvalue(
    future_returns: np.ndarray,
    event_positions: np.ndarray,
    observed_mean: float,
    cost_rate: float,
    samples: int = 2000,
) -> float:
    """Exploratory matched random-event comparison."""
    valid_returns = np.asarray(future_returns, dtype=float)
    positions = np.asarray(event_positions, dtype=float)
    positions = positions[positions != 0.0]

    if len(positions) == 0:
        return float("nan")

    rng = np.random.default_rng(RANDOM_SEED)
    simulated = np.empty(samples)

    for index in range(samples):
        sampled_returns = rng.choice(
            valid_returns,
            size=len(positions),
            replace=True,
        )
        sampled_positions = rng.permutation(positions)
        simulated[index] = np.mean(
            sampled_positions * sampled_returns - 2.0 * cost_rate
        )

    return float((1.0 + np.sum(simulated >= observed_mean)) / (samples + 1.0))
