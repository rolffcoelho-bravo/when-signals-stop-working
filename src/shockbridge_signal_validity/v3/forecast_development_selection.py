from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .forecast_contract import ForecastProtocolViolation


@dataclass(frozen=True)
class InnerFoldScore:
    pipeline_spec_id: str
    calibration_method: str
    abstention_threshold: float
    complexity_rank: int
    inner_fold: int
    benchmark_primary_loss: float
    candidate_primary_loss: float
    coverage: float
    nonzero_decisions: int

    @property
    def incremental_gain(self) -> float:
        return float(self.benchmark_primary_loss - self.candidate_primary_loss)


@dataclass(frozen=True)
class SelectedDevelopmentConfiguration:
    pipeline_spec_id: str
    calibration_method: str
    abstention_threshold: float
    complexity_rank: int
    mean_incremental_gain: float
    standard_error: float
    valid_inner_folds: int
    selection_rule: str


@dataclass(frozen=True)
class FoldLargeMoveTarget:
    threshold: float
    quantile: float
    training_rows: int
    training_positive_rows: int
    evaluation_rows: int
    evaluation_positive_rows: int
    evaluation_labels: np.ndarray


def build_fold_large_move_target(
    training_future_returns: Iterable[float],
    evaluation_future_returns: Iterable[float],
    *,
    quantile: float = 0.9,
) -> FoldLargeMoveTarget:
    training = np.asarray(list(training_future_returns), dtype=float).reshape(-1)
    evaluation = np.asarray(list(evaluation_future_returns), dtype=float).reshape(-1)
    if training.size == 0 or evaluation.size == 0:
        raise ForecastProtocolViolation(
            "Large-move target requires training and evaluation rows."
        )
    if not np.isfinite(training).all() or not np.isfinite(evaluation).all():
        raise ForecastProtocolViolation("Large-move returns must be finite.")
    if not 0.0 < float(quantile) < 1.0:
        raise ForecastProtocolViolation("Large-move quantile must lie in (0,1).")
    threshold = float(np.quantile(np.abs(training), float(quantile)))
    training_labels = (np.abs(training) >= threshold).astype(int)
    training_positive = int(training_labels.sum())
    if training_positive == 0 or training_positive == len(training_labels):
        raise ForecastProtocolViolation(
            "Training-fold large-move threshold must produce both binary classes."
        )
    evaluation_labels = (np.abs(evaluation) >= threshold).astype(int)
    return FoldLargeMoveTarget(
        threshold=threshold,
        quantile=float(quantile),
        training_rows=int(len(training)),
        training_positive_rows=training_positive,
        evaluation_rows=int(len(evaluation)),
        evaluation_positive_rows=int(evaluation_labels.sum()),
        evaluation_labels=evaluation_labels,
    )


def select_one_standard_error_configuration(
    scores: Iterable[InnerFoldScore],
    *,
    minimum_valid_inner_folds: int = 3,
    minimum_coverage: float = 0.1,
    minimum_nonzero_decisions: int = 100,
) -> SelectedDevelopmentConfiguration:
    rows = list(scores)
    if not rows:
        raise ForecastProtocolViolation("Inner selection requires score rows.")
    if int(minimum_valid_inner_folds) < 1:
        raise ForecastProtocolViolation("Minimum valid inner folds must be positive.")
    if not 0.0 <= float(minimum_coverage) <= 1.0:
        raise ForecastProtocolViolation("Minimum coverage must lie in [0,1].")
    if int(minimum_nonzero_decisions) < 0:
        raise ForecastProtocolViolation("Minimum nonzero decisions cannot be negative.")
    groups: dict[tuple[str, str, float, int], list[InnerFoldScore]] = {}
    for row in rows:
        if not np.isfinite(
            [
                row.benchmark_primary_loss,
                row.candidate_primary_loss,
                row.coverage,
            ]
        ).all():
            raise ForecastProtocolViolation("Inner selection contains non-finite values.")
        if not 0.0 <= float(row.coverage) <= 1.0 or int(row.nonzero_decisions) < 0:
            raise ForecastProtocolViolation(
                "Inner selection coverage or decision count is invalid."
            )
        key = (
            str(row.pipeline_spec_id),
            str(row.calibration_method),
            float(row.abstention_threshold),
            int(row.complexity_rank),
        )
        groups.setdefault(key, []).append(row)
    summaries: list[SelectedDevelopmentConfiguration] = []
    for key, group in groups.items():
        folds = {int(row.inner_fold) for row in group}
        if len(group) != len(folds) or len(group) < int(minimum_valid_inner_folds):
            continue
        if any(
            row.coverage < float(minimum_coverage)
            or row.nonzero_decisions < int(minimum_nonzero_decisions)
            for row in group
        ):
            continue
        gains = np.asarray([row.incremental_gain for row in group], dtype=float)
        standard_error = (
            float(gains.std(ddof=1) / np.sqrt(len(gains)))
            if len(gains) > 1
            else 0.0
        )
        summaries.append(
            SelectedDevelopmentConfiguration(
                pipeline_spec_id=key[0],
                calibration_method=key[1],
                abstention_threshold=key[2],
                complexity_rank=key[3],
                mean_incremental_gain=float(gains.mean()),
                standard_error=standard_error,
                valid_inner_folds=len(group),
                selection_rule="ONE_STANDARD_ERROR_COMPLEXITY_PREFERENCE",
            )
        )
    if not summaries:
        raise ForecastProtocolViolation(
            "No inner configuration satisfies eligibility requirements."
        )
    best = max(
        summaries,
        key=lambda value: (
            value.mean_incremental_gain,
            -value.complexity_rank,
            value.pipeline_spec_id,
            value.calibration_method,
            -value.abstention_threshold,
        ),
    )
    lower_bound = best.mean_incremental_gain - best.standard_error
    eligible = [
        value for value in summaries if value.mean_incremental_gain >= lower_bound
    ]
    return min(
        eligible,
        key=lambda value: (
            value.complexity_rank,
            -value.mean_incremental_gain,
            value.pipeline_spec_id,
            value.calibration_method,
            value.abstention_threshold,
        ),
    )


def positive_fold_concentration(
    incremental_gains: Iterable[float],
) -> dict[str, float | int | bool]:
    gains = np.asarray(list(incremental_gains), dtype=float).reshape(-1)
    if gains.size == 0 or not np.isfinite(gains).all():
        raise ForecastProtocolViolation("Outer-fold gains must be finite and nonempty.")
    positive = np.maximum(gains, 0.0)
    positive_folds = int(np.count_nonzero(positive))
    total_positive = float(positive.sum())
    maximum_share = (
        float(positive.max() / total_positive) if total_positive > 0.0 else 1.0
    )
    return {
        "outer_folds": int(len(gains)),
        "positive_outer_folds": positive_folds,
        "total_positive_gain": total_positive,
        "maximum_single_fold_share_of_positive_gain": maximum_share,
        "minimum_positive_outer_folds_passed": positive_folds >= 3,
        "maximum_single_fold_share_passed": maximum_share <= 0.6,
    }
