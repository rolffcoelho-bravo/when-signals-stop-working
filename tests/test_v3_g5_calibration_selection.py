from __future__ import annotations

import numpy as np
import pytest

from shockbridge_signal_validity.v3.forecast_calibration import (
    build_calibrator,
    evaluate_abstention_thresholds,
    fit_matched_calibrators,
)
from shockbridge_signal_validity.v3.forecast_contract import ForecastProtocolViolation
from shockbridge_signal_validity.v3.forecast_development_selection import (
    InnerFoldScore,
    build_fold_large_move_target,
    positive_fold_concentration,
    select_one_standard_error_configuration,
)


def test_identity_calibrator_preserves_probabilities() -> None:
    probability = np.array([0.1, 0.4, 0.7, 0.9])
    target = np.array([0, 0, 1, 1])
    calibrator = build_calibrator("none").fit(probability, target)
    np.testing.assert_allclose(calibrator.transform(probability), probability)


def test_sigmoid_calibrator_is_bounded() -> None:
    probability = np.linspace(0.05, 0.95, 100)
    target = (probability > 0.5).astype(int)
    calibrator = build_calibrator("sigmoid").fit(probability, target)
    transformed = calibrator.transform(probability)
    assert np.isfinite(transformed).all()
    assert ((transformed >= 0.0) & (transformed <= 1.0)).all()


def test_matched_calibrators_preserve_row_identity() -> None:
    benchmark = np.linspace(0.1, 0.8, 60)
    candidate = np.linspace(0.15, 0.9, 60)
    target = np.tile([0, 1], 30)
    calibrators = fit_matched_calibrators("sigmoid", benchmark, candidate, target)
    first, second = calibrators.transform_pair(benchmark, candidate)
    assert len(first) == len(second) == 60
    assert calibrators.method == "sigmoid"


def test_isotonic_remains_diagnostic_and_bounded() -> None:
    probability = np.linspace(0.01, 0.99, 80)
    target = (probability > 0.6).astype(int)
    calibrator = build_calibrator("isotonic").fit(probability, target)
    transformed = calibrator.transform(probability)
    assert ((transformed >= 0.0) & (transformed <= 1.0)).all()


def test_abstention_thresholds_report_eligibility() -> None:
    probability = np.concatenate([np.full(120, 0.9), np.full(80, 0.5)])
    choices = evaluate_abstention_thresholds(
        probability,
        [0.02, 0.05, 0.1],
        minimum_coverage=0.1,
        minimum_nonzero_decisions=100,
    )
    assert len(choices) == 3
    assert all(choice.eligible for choice in choices)
    assert all(choice.nonzero_decisions == 120 for choice in choices)


def test_invalid_abstention_threshold_fails_closed() -> None:
    with pytest.raises(ForecastProtocolViolation, match="invalid"):
        evaluate_abstention_thresholds(
            [0.2, 0.8],
            [0.5],
            minimum_coverage=0.1,
            minimum_nonzero_decisions=1,
        )


def test_large_move_threshold_uses_training_only() -> None:
    training = np.linspace(-0.2, 0.2, 1000)
    evaluation = np.array([0.01, 0.03, 1.0])
    first = build_fold_large_move_target(training, evaluation, quantile=0.9)
    second = build_fold_large_move_target(training, evaluation * 100.0, quantile=0.9)
    assert first.threshold == pytest.approx(second.threshold)
    assert first.training_rows == 1000


def _scores() -> list[InnerFoldScore]:
    rows: list[InnerFoldScore] = []
    for fold, gain in enumerate([0.020, 0.018, 0.022], start=1):
        rows.append(
            InnerFoldScore(
                pipeline_spec_id="simple",
                calibration_method="none",
                abstention_threshold=0.02,
                complexity_rank=1,
                inner_fold=fold,
                benchmark_primary_loss=0.70,
                candidate_primary_loss=0.70 - gain,
                coverage=0.8,
                nonzero_decisions=200,
            )
        )
    for fold, gain in enumerate([0.021, 0.023, 0.024], start=1):
        rows.append(
            InnerFoldScore(
                pipeline_spec_id="complex",
                calibration_method="sigmoid",
                abstention_threshold=0.02,
                complexity_rank=3,
                inner_fold=fold,
                benchmark_primary_loss=0.70,
                candidate_primary_loss=0.70 - gain,
                coverage=0.8,
                nonzero_decisions=200,
            )
        )
    return rows


def test_one_standard_error_prefers_simpler_eligible_configuration() -> None:
    selected = select_one_standard_error_configuration(_scores())
    assert selected.pipeline_spec_id == "simple"
    assert selected.complexity_rank == 1
    assert selected.valid_inner_folds == 3


def test_one_standard_error_rejects_ineligible_coverage() -> None:
    rows = [
        InnerFoldScore(
            pipeline_spec_id="only",
            calibration_method="none",
            abstention_threshold=0.1,
            complexity_rank=1,
            inner_fold=fold,
            benchmark_primary_loss=0.7,
            candidate_primary_loss=0.6,
            coverage=0.01,
            nonzero_decisions=5,
        )
        for fold in (1, 2, 3)
    ]
    with pytest.raises(ForecastProtocolViolation, match="No inner configuration"):
        select_one_standard_error_configuration(rows)


def test_positive_fold_concentration_enforces_both_controls() -> None:
    result = positive_fold_concentration([0.1, 0.08, 0.07, -0.02, 0.03])
    assert result["positive_outer_folds"] == 4
    assert result["minimum_positive_outer_folds_passed"] is True
    assert result["maximum_single_fold_share_passed"] is True
