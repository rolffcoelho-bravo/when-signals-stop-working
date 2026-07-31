from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from .forecast_contract import ForecastProtocolViolation
from .forecast_estimators import logistic_l2_kwargs


class ProbabilityCalibrator:
    method: str

    def fit(self, probability: Any, target: Any) -> "ProbabilityCalibrator":
        raise NotImplementedError

    def transform(self, probability: Any) -> np.ndarray:
        raise NotImplementedError


class IdentityCalibrator(ProbabilityCalibrator):
    method = "none"

    def fit(self, probability: Any, target: Any) -> "IdentityCalibrator":
        estimate, truth = _validated_probability_target(probability, target)
        self.training_rows_ = len(estimate)
        self.target_rate_ = float(truth.mean())
        return self

    def transform(self, probability: Any) -> np.ndarray:
        estimate = _validated_probability(probability)
        return estimate.copy()


class SigmoidCalibrator(ProbabilityCalibrator):
    method = "sigmoid"

    def __init__(self, *, random_state: int = 20260728, max_iter: int = 2000) -> None:
        self.random_state = random_state
        self.max_iter = max_iter

    def fit(self, probability: Any, target: Any) -> "SigmoidCalibrator":
        estimate, truth = _validated_probability_target(probability, target)
        if len(np.unique(truth)) != 2:
            raise ForecastProtocolViolation("Sigmoid calibration requires both binary classes.")
        self.model_ = LogisticRegression(
            C=1.0,
            solver="lbfgs",
            max_iter=int(self.max_iter),
            random_state=int(self.random_state),
            **logistic_l2_kwargs(),
        )
        self.model_.fit(_logit_feature(estimate), truth)
        self.training_rows_ = len(estimate)
        return self

    def transform(self, probability: Any) -> np.ndarray:
        if not hasattr(self, "model_"):
            raise ForecastProtocolViolation("Sigmoid calibrator is not fitted.")
        estimate = _validated_probability(probability)
        return self.model_.predict_proba(_logit_feature(estimate))[:, 1]


class IsotonicDiagnosticCalibrator(ProbabilityCalibrator):
    method = "isotonic"

    def fit(self, probability: Any, target: Any) -> "IsotonicDiagnosticCalibrator":
        estimate, truth = _validated_probability_target(probability, target)
        if len(np.unique(estimate)) < 2:
            raise ForecastProtocolViolation("Isotonic calibration requires varying probabilities.")
        self.model_ = IsotonicRegression(out_of_bounds="clip")
        self.model_.fit(estimate, truth)
        self.training_rows_ = len(estimate)
        return self

    def transform(self, probability: Any) -> np.ndarray:
        if not hasattr(self, "model_"):
            raise ForecastProtocolViolation("Isotonic calibrator is not fitted.")
        return np.asarray(self.model_.predict(_validated_probability(probability)), dtype=float)


@dataclass(frozen=True)
class MatchedCalibrators:
    method: str
    benchmark: ProbabilityCalibrator
    candidate: ProbabilityCalibrator
    training_rows: int

    def transform_pair(
        self,
        benchmark_probability: Any,
        candidate_probability: Any,
    ) -> tuple[np.ndarray, np.ndarray]:
        benchmark = self.benchmark.transform(benchmark_probability)
        candidate = self.candidate.transform(candidate_probability)
        if len(benchmark) != len(candidate):
            raise ForecastProtocolViolation("Calibrated benchmark and candidate rows differ.")
        return benchmark, candidate


@dataclass(frozen=True)
class AbstentionChoice:
    threshold: float
    coverage: float
    nonzero_decisions: int
    eligible: bool


def _validated_probability(value: Any) -> np.ndarray:
    estimate = np.asarray(value, dtype=float).reshape(-1)
    if estimate.size == 0 or not np.isfinite(estimate).all():
        raise ForecastProtocolViolation("Probability input must be finite and nonempty.")
    if ((estimate < 0.0) | (estimate > 1.0)).any():
        raise ForecastProtocolViolation("Probability input must lie in [0,1].")
    return estimate


def _validated_probability_target(probability: Any, target: Any) -> tuple[np.ndarray, np.ndarray]:
    estimate = _validated_probability(probability)
    truth = np.asarray(target, dtype=int).reshape(-1)
    if len(estimate) != len(truth) or not set(np.unique(truth)).issubset({0, 1}):
        raise ForecastProtocolViolation("Calibration target is invalid or misaligned.")
    return estimate, truth


def _logit_feature(probability: np.ndarray) -> np.ndarray:
    clipped = np.clip(probability, 1e-8, 1.0 - 1e-8)
    return np.log(clipped / (1.0 - clipped)).reshape(-1, 1)


def build_calibrator(method: str) -> ProbabilityCalibrator:
    normalized = str(method).lower()
    if normalized == "none":
        return IdentityCalibrator()
    if normalized == "sigmoid":
        return SigmoidCalibrator()
    if normalized == "isotonic":
        return IsotonicDiagnosticCalibrator()
    raise ForecastProtocolViolation(f"Unknown calibration method: {method}")


def fit_matched_calibrators(
    method: str,
    benchmark_probability: Any,
    candidate_probability: Any,
    target: Any,
) -> MatchedCalibrators:
    benchmark_values, truth = _validated_probability_target(benchmark_probability, target)
    candidate_values, candidate_truth = _validated_probability_target(candidate_probability, target)
    if not np.array_equal(truth, candidate_truth) or len(benchmark_values) != len(candidate_values):
        raise ForecastProtocolViolation("Matched calibration rows or targets differ.")
    benchmark = build_calibrator(method).fit(benchmark_values, truth)
    candidate = build_calibrator(method).fit(candidate_values, truth)
    return MatchedCalibrators(
        method=str(method).lower(),
        benchmark=benchmark,
        candidate=candidate,
        training_rows=len(truth),
    )


def evaluate_abstention_thresholds(
    probability: Any,
    thresholds: tuple[float, ...] | list[float],
    *,
    minimum_coverage: float,
    minimum_nonzero_decisions: int,
) -> list[AbstentionChoice]:
    estimate = _validated_probability(probability)
    if not 0.0 <= float(minimum_coverage) <= 1.0 or int(minimum_nonzero_decisions) < 0:
        raise ForecastProtocolViolation("Abstention eligibility requirements are invalid.")
    choices: list[AbstentionChoice] = []
    for threshold in thresholds:
        value = float(threshold)
        if value < 0.0 or value >= 0.5:
            raise ForecastProtocolViolation("Abstention threshold is invalid.")
        decisions = np.abs(estimate - 0.5) >= value
        nonzero = int(decisions.sum())
        coverage = float(decisions.mean())
        choices.append(
            AbstentionChoice(
                threshold=value,
                coverage=coverage,
                nonzero_decisions=nonzero,
                eligible=(
                    coverage >= float(minimum_coverage)
                    and nonzero >= int(minimum_nonzero_decisions)
                ),
            )
        )
    return choices
