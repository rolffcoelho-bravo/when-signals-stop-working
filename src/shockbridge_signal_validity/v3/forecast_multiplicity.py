from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .forecast_contract import ForecastProtocolViolation


@dataclass(frozen=True)
class AdjustedPValue:
    hypothesis_id: str
    raw_p_value: float
    adjusted_p_value: float
    rejected: bool
    method: str


def _validated_pairs(
    hypothesis_ids: Iterable[str],
    p_values: Iterable[float],
) -> tuple[list[str], np.ndarray]:
    identifiers = [str(value) for value in hypothesis_ids]
    probabilities = np.asarray(list(p_values), dtype=float)
    if not identifiers or len(identifiers) != len(probabilities):
        raise ForecastProtocolViolation("Multiplicity inputs must be nonempty and aligned.")
    if len(set(identifiers)) != len(identifiers):
        raise ForecastProtocolViolation("Multiplicity hypothesis identifiers must be unique.")
    if not np.isfinite(probabilities).all() or ((probabilities < 0.0) | (probabilities > 1.0)).any():
        raise ForecastProtocolViolation("Multiplicity p-values must lie in [0,1].")
    return identifiers, probabilities


def holm_adjust(
    hypothesis_ids: Iterable[str],
    p_values: Iterable[float],
    *,
    alpha: float = 0.05,
) -> list[AdjustedPValue]:
    identifiers, probabilities = _validated_pairs(hypothesis_ids, p_values)
    if not 0.0 < float(alpha) < 1.0:
        raise ForecastProtocolViolation("Holm alpha must lie in (0,1).")
    order = np.argsort(probabilities, kind="mergesort")
    sorted_values = probabilities[order]
    m = len(sorted_values)
    adjusted_sorted = np.maximum.accumulate(
        np.minimum(1.0, (m - np.arange(m)) * sorted_values)
    )
    rejected_sorted = np.zeros(m, dtype=bool)
    active = True
    for position, value in enumerate(sorted_values):
        threshold = float(alpha) / float(m - position)
        if active and value <= threshold:
            rejected_sorted[position] = True
        else:
            active = False
    adjusted = np.empty(m, dtype=float)
    rejected = np.empty(m, dtype=bool)
    adjusted[order] = adjusted_sorted
    rejected[order] = rejected_sorted
    return [
        AdjustedPValue(
            hypothesis_id=identifier,
            raw_p_value=float(raw),
            adjusted_p_value=float(adj),
            rejected=bool(flag),
            method="HOLM",
        )
        for identifier, raw, adj, flag in zip(
            identifiers, probabilities, adjusted, rejected, strict=True
        )
    ]


def benjamini_hochberg_adjust(
    hypothesis_ids: Iterable[str],
    p_values: Iterable[float],
    *,
    q: float = 0.10,
) -> list[AdjustedPValue]:
    identifiers, probabilities = _validated_pairs(hypothesis_ids, p_values)
    if not 0.0 < float(q) < 1.0:
        raise ForecastProtocolViolation("Benjamini-Hochberg q must lie in (0,1).")
    order = np.argsort(probabilities, kind="mergesort")
    sorted_values = probabilities[order]
    m = len(sorted_values)
    raw_adjusted = sorted_values * float(m) / np.arange(1, m + 1)
    adjusted_sorted = np.minimum.accumulate(raw_adjusted[::-1])[::-1]
    adjusted_sorted = np.minimum(1.0, adjusted_sorted)
    critical = float(q) * np.arange(1, m + 1) / float(m)
    eligible = np.flatnonzero(sorted_values <= critical)
    rejected_sorted = np.zeros(m, dtype=bool)
    if len(eligible):
        rejected_sorted[: int(eligible.max()) + 1] = True
    adjusted = np.empty(m, dtype=float)
    rejected = np.empty(m, dtype=bool)
    adjusted[order] = adjusted_sorted
    rejected[order] = rejected_sorted
    return [
        AdjustedPValue(
            hypothesis_id=identifier,
            raw_p_value=float(raw),
            adjusted_p_value=float(adj),
            rejected=bool(flag),
            method="BENJAMINI_HOCHBERG",
        )
        for identifier, raw, adj, flag in zip(
            identifiers, probabilities, adjusted, rejected, strict=True
        )
    ]
