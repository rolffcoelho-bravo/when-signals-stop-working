from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v3.forecast_contract import ForecastProtocolViolation
from shockbridge_signal_validity.v3.forecast_development_execution import (
    build_execution_plan_frame,
    build_execution_plan_identity,
    build_large_move_targets_for_partitions,
    execute_matched_outer_fold,
)
from shockbridge_signal_validity.v3.forecast_model_registry import (
    build_pipeline_registry,
    load_contracts,
)

ROOT = Path(__file__).resolve().parents[1]
FORECAST_CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"
IMPLEMENTATION_CONTRACT = ROOT / "configs" / "v3_g5_model_implementation_contract.json"


def _registry():
    forecast, implementation = load_contracts(FORECAST_CONTRACT, IMPLEMENTATION_CONTRACT)
    return implementation, build_pipeline_registry(forecast, implementation)


def _spec(target: str):
    implementation, registry = _registry()
    spec = next(
        value
        for value in registry
        if value.target_name == target
        and value.model_family == "regularized_linear"
        and value.window_id == "EXPANDING"
        and value.executable
    )
    return implementation, spec


def _partitions():
    index = pd.date_range("2021-01-01T00:00:00Z", periods=900, freq="4h")
    phase = np.linspace(0.0, 35.0, len(index))
    benchmark = pd.DataFrame(
        {
            "sol_ret_1": np.sin(phase),
            "btc_ret_1": np.cos(phase / 2.0),
            "vol_20": 1.0 + np.sin(phase / 3.0) ** 2,
        },
        index=index,
    )
    candidate = benchmark.copy()
    candidate["registered_signal"] = np.cos(phase / 5.0)
    direction = pd.Series(
        (
            benchmark["sol_ret_1"]
            + 0.35 * candidate["registered_signal"]
            > 0.0
        ).astype(int),
        index=index,
        name="direction",
    )
    expected_return = pd.Series(
        0.01 * benchmark["sol_ret_1"]
        - 0.005 * benchmark["btc_ret_1"]
        + 0.004 * candidate["registered_signal"],
        index=index,
        name="expected_return",
    )
    realized = expected_return + 0.001 * np.sin(phase / 7.0)
    slices = (slice(0, 600), slice(600, 750), slice(750, 900))
    return benchmark, candidate, direction, expected_return, realized, slices


def test_execution_plan_identity_matches_frozen_workload() -> None:
    identity = build_execution_plan_identity(
        matched_candidate_horizon_records=300,
        executable_pipeline_specifications=153,
        outer_folds=5,
        real_execution_authorized=False,
    )
    assert identity.candidate_pipeline_target_combinations == 42228
    assert identity.outer_fold_jobs == 211140
    assert identity.real_execution_authorized is False


def test_execution_plan_frame_is_unique_and_execution_disabled() -> None:
    _, registry = _registry()
    coverage = pd.DataFrame(
        {
            "candidate_id": ["candidate-a", "candidate-b", "candidate-c"],
            "horizon_candles": [1, 2, 3],
            "coverage_status": [
                "MATCHED_ROWS_AVAILABLE",
                "MATCHED_ROWS_AVAILABLE",
                "INELIGIBLE_NO_COMPLETE_MATCHED_ROWS",
            ],
        }
    )
    frame = build_execution_plan_frame(
        coverage,
        [value for value in registry if value.executable][:2],
        outer_folds=2,
        real_execution_authorized=False,
    )
    assert len(frame) == 8
    assert frame["real_execution_authorized"].eq(False).all()
    assert frame["real_development_model_fitting_performed"].eq(False).all()


def test_real_execution_is_rejected_before_fit() -> None:
    implementation, spec = _spec("direction")
    benchmark, candidate, direction, _, realized, slices = _partitions()
    train, calibration, test = slices
    with pytest.raises(ForecastProtocolViolation, match="NOT_AUTHORIZED"):
        execute_matched_outer_fold(
            spec=spec,
            implementation_contract=implementation,
            benchmark_training=benchmark.iloc[train],
            candidate_training=candidate.iloc[train],
            training_target=direction.iloc[train],
            benchmark_calibration=benchmark.iloc[calibration],
            candidate_calibration=candidate.iloc[calibration],
            calibration_target=direction.iloc[calibration],
            benchmark_test=benchmark.iloc[test],
            candidate_test=candidate.iloc[test],
            test_target=direction.iloc[test],
            test_future_log_return=realized.iloc[test],
            horizon_candles=1,
            synthetic_validation_only=False,
        )


def test_synthetic_direction_outer_fold_executes_matched_pair() -> None:
    implementation, spec = _spec("direction")
    benchmark, candidate, direction, _, realized, slices = _partitions()
    train, calibration, test = slices
    result = execute_matched_outer_fold(
        spec=spec,
        implementation_contract=implementation,
        benchmark_training=benchmark.iloc[train],
        candidate_training=candidate.iloc[train],
        training_target=direction.iloc[train],
        benchmark_calibration=benchmark.iloc[calibration],
        candidate_calibration=candidate.iloc[calibration],
        calibration_target=direction.iloc[calibration],
        benchmark_test=benchmark.iloc[test],
        candidate_test=candidate.iloc[test],
        test_target=direction.iloc[test],
        test_future_log_return=realized.iloc[test],
        horizon_candles=1,
        calibration_method="sigmoid",
        abstention_threshold=0.02,
        synthetic_validation_only=True,
    )
    assert result.test_rows == 150
    assert result.synthetic_validation_only is True
    assert result.real_development_model_fitting_performed is False
    assert result.benchmark_economic is not None
    assert result.candidate_economic is not None
    assert np.isfinite(result.incremental_primary_gain)


def test_synthetic_regression_outer_fold_executes_matched_pair() -> None:
    implementation, spec = _spec("expected_return")
    benchmark, candidate, _, expected_return, realized, slices = _partitions()
    train, calibration, test = slices
    result = execute_matched_outer_fold(
        spec=spec,
        implementation_contract=implementation,
        benchmark_training=benchmark.iloc[train],
        candidate_training=candidate.iloc[train],
        training_target=expected_return.iloc[train],
        benchmark_calibration=benchmark.iloc[calibration],
        candidate_calibration=candidate.iloc[calibration],
        calibration_target=expected_return.iloc[calibration],
        benchmark_test=benchmark.iloc[test],
        candidate_test=candidate.iloc[test],
        test_target=expected_return.iloc[test],
        test_future_log_return=realized.iloc[test],
        horizon_candles=2,
        synthetic_validation_only=True,
    )
    assert result.target_name == "expected_return"
    assert result.benchmark_metrics.primary_metric_name == "mean_squared_error"
    assert result.incremental_economic_gain is not None


def test_large_move_partition_threshold_is_training_only() -> None:
    index = pd.date_range("2021-01-01T00:00:00Z", periods=1000, freq="4h")
    returns = pd.Series(np.sin(np.linspace(0, 30, 1000)) * 0.05, index=index)
    training, calibration, test, threshold = build_large_move_targets_for_partitions(
        returns.iloc[:700], returns.iloc[700:850], returns.iloc[850:], quantile=0.9
    )
    changed_test = returns.iloc[850:] * 100.0
    _, _, _, second_threshold = build_large_move_targets_for_partitions(
        returns.iloc[:700], returns.iloc[700:850], changed_test, quantile=0.9
    )
    assert threshold == pytest.approx(second_threshold)
    assert set(training.unique()).issubset({0, 1})
    assert len(calibration) == len(test) == 150


def test_large_move_execution_requires_and_records_fold_threshold() -> None:
    implementation, spec = _spec("large_move_probability")
    benchmark, candidate, _, _, realized, slices = _partitions()
    train, calibration, test = slices
    training_target, calibration_target, test_target, threshold = (
        build_large_move_targets_for_partitions(
            realized.iloc[train],
            realized.iloc[calibration],
            realized.iloc[test],
            quantile=0.9,
        )
    )
    with pytest.raises(ForecastProtocolViolation, match="training-fold threshold"):
        execute_matched_outer_fold(
            spec=spec,
            implementation_contract=implementation,
            benchmark_training=benchmark.iloc[train],
            candidate_training=candidate.iloc[train],
            training_target=training_target,
            benchmark_calibration=benchmark.iloc[calibration],
            candidate_calibration=candidate.iloc[calibration],
            calibration_target=calibration_target,
            benchmark_test=benchmark.iloc[test],
            candidate_test=candidate.iloc[test],
            test_target=test_target,
            test_future_log_return=realized.iloc[test],
            horizon_candles=1,
            synthetic_validation_only=True,
        )
    result = execute_matched_outer_fold(
        spec=spec,
        implementation_contract=implementation,
        benchmark_training=benchmark.iloc[train],
        candidate_training=candidate.iloc[train],
        training_target=training_target,
        benchmark_calibration=benchmark.iloc[calibration],
        candidate_calibration=candidate.iloc[calibration],
        calibration_target=calibration_target,
        benchmark_test=benchmark.iloc[test],
        candidate_test=candidate.iloc[test],
        test_target=test_target,
        test_future_log_return=realized.iloc[test],
        horizon_candles=1,
        calibration_method="none",
        fold_large_move_threshold=threshold,
        synthetic_validation_only=True,
    )
    assert result.large_move_threshold == pytest.approx(threshold)
    assert result.benchmark_economic is None
    assert result.candidate_economic is None


def test_execution_rejects_mismatched_target_rows() -> None:
    implementation, spec = _spec("direction")
    benchmark, candidate, direction, _, realized, slices = _partitions()
    train, calibration, test = slices
    with pytest.raises(ForecastProtocolViolation, match="matched rows differ"):
        execute_matched_outer_fold(
            spec=spec,
            implementation_contract=implementation,
            benchmark_training=benchmark.iloc[train],
            candidate_training=candidate.iloc[train],
            training_target=direction.iloc[train].iloc[1:],
            benchmark_calibration=benchmark.iloc[calibration],
            candidate_calibration=candidate.iloc[calibration],
            calibration_target=direction.iloc[calibration],
            benchmark_test=benchmark.iloc[test],
            candidate_test=candidate.iloc[test],
            test_target=direction.iloc[test],
            test_future_log_return=realized.iloc[test],
            horizon_candles=1,
            synthetic_validation_only=True,
        )


def test_execution_rejects_candidate_without_benchmark_prefix() -> None:
    implementation, spec = _spec("direction")
    benchmark, candidate, direction, _, realized, slices = _partitions()
    candidate = candidate[["registered_signal", "sol_ret_1", "btc_ret_1", "vol_20"]]
    train, calibration, test = slices
    with pytest.raises(ForecastProtocolViolation, match="benchmark columns first"):
        execute_matched_outer_fold(
            spec=spec,
            implementation_contract=implementation,
            benchmark_training=benchmark.iloc[train],
            candidate_training=candidate.iloc[train],
            training_target=direction.iloc[train],
            benchmark_calibration=benchmark.iloc[calibration],
            candidate_calibration=candidate.iloc[calibration],
            calibration_target=direction.iloc[calibration],
            benchmark_test=benchmark.iloc[test],
            candidate_test=candidate.iloc[test],
            test_target=direction.iloc[test],
            test_future_log_return=realized.iloc[test],
            horizon_candles=1,
            synthetic_validation_only=True,
        )


def test_execution_rejects_nonchronological_partitions() -> None:
    implementation, spec = _spec("direction")
    benchmark, candidate, direction, _, realized, _ = _partitions()
    train = slice(0, 600)
    calibration = slice(500, 650)
    test = slice(750, 900)
    with pytest.raises(ForecastProtocolViolation, match="Training observations must end"):
        execute_matched_outer_fold(
            spec=spec,
            implementation_contract=implementation,
            benchmark_training=benchmark.iloc[train],
            candidate_training=candidate.iloc[train],
            training_target=direction.iloc[train],
            benchmark_calibration=benchmark.iloc[calibration],
            candidate_calibration=candidate.iloc[calibration],
            calibration_target=direction.iloc[calibration],
            benchmark_test=benchmark.iloc[test],
            candidate_test=candidate.iloc[test],
            test_target=direction.iloc[test],
            test_future_log_return=realized.iloc[test],
            horizon_candles=1,
            synthetic_validation_only=True,
        )
