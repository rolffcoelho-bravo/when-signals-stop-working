from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .forecast_calibration import fit_matched_calibrators
from .forecast_contract import ForecastProtocolViolation, require_utc_index
from .forecast_development_metrics import (
    EconomicBundle,
    MetricBundle,
    classification_metrics,
    direction_positions,
    economic_metrics,
    expected_return_positions,
    incremental_economic_gain,
    regression_metrics,
)
from .forecast_development_selection import build_fold_large_move_target
from .forecast_estimators import build_matched_estimator_pair, select_training_window
from .forecast_model_registry import ForecastPipelineSpec
from .forecast_preprocessing import fit_matched_fold_preprocessors


@dataclass(frozen=True)
class ExecutionPlanIdentity:
    matched_candidate_horizon_records: int
    executable_pipeline_specifications: int
    outer_folds: int
    candidate_pipeline_target_combinations: int
    outer_fold_jobs: int
    real_execution_authorized: bool


@dataclass(frozen=True)
class MatchedOuterFoldResult:
    pipeline_spec_id: str
    target_name: str
    calibration_method: str
    abstention_threshold: float
    training_rows: int
    calibration_rows: int
    test_rows: int
    benchmark_metrics: MetricBundle
    candidate_metrics: MetricBundle
    incremental_primary_gain: float
    benchmark_economic: EconomicBundle | None
    candidate_economic: EconomicBundle | None
    incremental_economic_gain: float | None
    large_move_threshold: float | None
    benchmark_prediction: np.ndarray
    candidate_prediction: np.ndarray
    synthetic_validation_only: bool
    real_development_model_fitting_performed: bool


def build_execution_plan_identity(
    *,
    matched_candidate_horizon_records: int,
    executable_pipeline_specifications: int,
    outer_folds: int,
    real_execution_authorized: bool,
) -> ExecutionPlanIdentity:
    matched = int(matched_candidate_horizon_records)
    executable = int(executable_pipeline_specifications)
    folds = int(outer_folds)
    if matched < 1 or executable < 1 or folds < 1:
        raise ForecastProtocolViolation("Execution-plan counts must be positive.")
    combinations = matched * executable
    return ExecutionPlanIdentity(
        matched_candidate_horizon_records=matched,
        executable_pipeline_specifications=executable,
        outer_folds=folds,
        candidate_pipeline_target_combinations=combinations,
        outer_fold_jobs=combinations * folds,
        real_execution_authorized=bool(real_execution_authorized),
    )


def build_execution_plan_frame(
    matched_coverage: pd.DataFrame,
    pipeline_specs: Iterable[ForecastPipelineSpec],
    *,
    outer_folds: int = 5,
    real_execution_authorized: bool = False,
) -> pd.DataFrame:
    required = {"candidate_id", "horizon_candles", "coverage_status"}
    if not required.issubset(matched_coverage.columns):
        raise ForecastProtocolViolation("Matched coverage lacks execution-plan columns.")
    available = matched_coverage.loc[
        matched_coverage["coverage_status"] == "MATCHED_ROWS_AVAILABLE",
        ["candidate_id", "horizon_candles"],
    ].drop_duplicates()
    specs = [value for value in pipeline_specs if value.executable]
    records: list[dict[str, object]] = []
    for coverage_row in available.itertuples(index=False):
        for spec in specs:
            for outer_fold in range(1, int(outer_folds) + 1):
                records.append(
                    {
                        "candidate_id": str(coverage_row.candidate_id),
                        "horizon_candles": int(coverage_row.horizon_candles),
                        "target_name": spec.target_name,
                        "pipeline_spec_id": spec.pipeline_spec_id,
                        "model_family": spec.model_family,
                        "window_id": spec.window_id,
                        "outer_fold": outer_fold,
                        "real_execution_authorized": bool(real_execution_authorized),
                        "real_development_model_fitting_performed": False,
                    }
                )
    frame = pd.DataFrame.from_records(records)
    if frame.empty or frame.duplicated(
        ["candidate_id", "horizon_candles", "pipeline_spec_id", "outer_fold"]
    ).any():
        raise ForecastProtocolViolation("Execution plan is empty or not uniquely identified.")
    return frame.sort_values(
        ["horizon_candles", "candidate_id", "target_name", "pipeline_spec_id", "outer_fold"],
        kind="mergesort",
    ).reset_index(drop=True)


def _validate_partition(
    benchmark: pd.DataFrame,
    candidate: pd.DataFrame,
    target: pd.Series,
    label: str,
) -> None:
    benchmark_index = require_utc_index(benchmark.index, f"{label} benchmark timestamps")
    candidate_index = require_utc_index(candidate.index, f"{label} candidate timestamps")
    target_index = require_utc_index(target.index, f"{label} target timestamps")
    if not benchmark_index.equals(candidate_index) or not benchmark_index.equals(target_index):
        raise ForecastProtocolViolation(f"{label} matched rows differ.")
    if list(candidate.columns[: len(benchmark.columns)]) != list(benchmark.columns):
        raise ForecastProtocolViolation(
            f"{label} candidate does not preserve benchmark columns first."
        )
    if benchmark.isna().any().any() or candidate.isna().any().any() or target.isna().any():
        raise ForecastProtocolViolation(f"{label} matched rows must be complete.")


def _assert_partition_chronology(
    training_index: pd.Index,
    calibration_index: pd.Index,
    test_index: pd.Index,
) -> None:
    training = require_utc_index(training_index, "training chronology")
    calibration = require_utc_index(calibration_index, "calibration chronology")
    test = require_utc_index(test_index, "test chronology")
    if training.max() >= calibration.min():
        raise ForecastProtocolViolation(
            "Training observations must end before calibration begins."
        )
    if calibration.max() >= test.min():
        raise ForecastProtocolViolation(
            "Calibration observations must end before outer testing begins."
        )


def _classification_prediction(estimator: Any, features: pd.DataFrame) -> np.ndarray:
    if not hasattr(estimator, "predict_proba"):
        raise ForecastProtocolViolation("Classification estimator lacks predict_proba.")
    values = np.asarray(estimator.predict_proba(features)[:, 1], dtype=float)
    if not np.isfinite(values).all():
        raise ForecastProtocolViolation(
            "Classification estimator produced non-finite probabilities."
        )
    return values


def execute_matched_outer_fold(
    *,
    spec: ForecastPipelineSpec,
    implementation_contract: dict[str, Any],
    benchmark_training: pd.DataFrame,
    candidate_training: pd.DataFrame,
    training_target: pd.Series,
    benchmark_calibration: pd.DataFrame,
    candidate_calibration: pd.DataFrame,
    calibration_target: pd.Series,
    benchmark_test: pd.DataFrame,
    candidate_test: pd.DataFrame,
    test_target: pd.Series,
    test_future_log_return: pd.Series,
    horizon_candles: int,
    calibration_method: str = "none",
    abstention_threshold: float = 0.02,
    one_way_cost_bps: float = 10.0,
    fold_large_move_threshold: float | None = None,
    synthetic_validation_only: bool = False,
) -> MatchedOuterFoldResult:
    if not synthetic_validation_only:
        raise ForecastProtocolViolation(
            "REAL_DEVELOPMENT_EXECUTION_NOT_AUTHORIZED_IMPLEMENTATION_VALIDATION_ONLY"
        )
    for label, benchmark, candidate, target in (
        ("training", benchmark_training, candidate_training, training_target),
        ("calibration", benchmark_calibration, candidate_calibration, calibration_target),
        ("test", benchmark_test, candidate_test, test_target),
    ):
        _validate_partition(benchmark, candidate, target, label)
    _assert_partition_chronology(
        benchmark_training.index,
        benchmark_calibration.index,
        benchmark_test.index,
    )
    if not require_utc_index(test_target.index, "test target timestamps").equals(
        require_utc_index(test_future_log_return.index, "test return timestamps")
    ):
        raise ForecastProtocolViolation("Test target and realized-return rows differ.")
    if test_future_log_return.isna().any() or not np.isfinite(
        test_future_log_return.to_numpy(dtype=float)
    ).all():
        raise ForecastProtocolViolation("Test realized returns must be finite and complete.")

    large_move_threshold: float | None = None
    if spec.target_name == "large_move_probability":
        if fold_large_move_threshold is None or not np.isfinite(
            float(fold_large_move_threshold)
        ) or float(fold_large_move_threshold) < 0.0:
            raise ForecastProtocolViolation(
                "Large-move execution requires a valid training-fold threshold."
            )
        large_move_threshold = float(fold_large_move_threshold)
    elif fold_large_move_threshold is not None:
        raise ForecastProtocolViolation(
            "A large-move threshold was supplied for a different target."
        )

    selected_benchmark, selected_target = select_training_window(
        benchmark_training, training_target, spec
    )
    selected_candidate, candidate_target = select_training_window(
        candidate_training, training_target, spec
    )
    if not selected_benchmark.index.equals(selected_candidate.index) or not selected_target.equals(
        candidate_target
    ):
        raise ForecastProtocolViolation("Matched training-window selection differs.")

    preprocessors = fit_matched_fold_preprocessors(
        selected_benchmark, selected_candidate
    )
    transformed_benchmark_train, transformed_candidate_train = (
        preprocessors.transform_pair(selected_benchmark, selected_candidate)
    )
    transformed_benchmark_calibration, transformed_candidate_calibration = (
        preprocessors.transform_pair(benchmark_calibration, candidate_calibration)
    )
    transformed_benchmark_test, transformed_candidate_test = (
        preprocessors.transform_pair(benchmark_test, candidate_test)
    )
    pair = build_matched_estimator_pair(spec, implementation_contract)
    pair.benchmark_estimator.fit(transformed_benchmark_train, selected_target)
    pair.candidate_estimator.fit(transformed_candidate_train, selected_target)

    benchmark_economic: EconomicBundle | None = None
    candidate_economic: EconomicBundle | None = None
    economic_gain: float | None = None

    if spec.task_type == "CLASSIFICATION":
        benchmark_calibration_raw = _classification_prediction(
            pair.benchmark_estimator, transformed_benchmark_calibration
        )
        candidate_calibration_raw = _classification_prediction(
            pair.candidate_estimator, transformed_candidate_calibration
        )
        calibrators = fit_matched_calibrators(
            calibration_method,
            benchmark_calibration_raw,
            candidate_calibration_raw,
            calibration_target,
        )
        benchmark_raw = _classification_prediction(
            pair.benchmark_estimator, transformed_benchmark_test
        )
        candidate_raw = _classification_prediction(
            pair.candidate_estimator, transformed_candidate_test
        )
        benchmark_prediction, candidate_prediction = calibrators.transform_pair(
            benchmark_raw, candidate_raw
        )
        benchmark_metrics = classification_metrics(
            spec.target_name, test_target, benchmark_prediction
        )
        candidate_metrics = classification_metrics(
            spec.target_name, test_target, candidate_prediction
        )
        if spec.target_name == "direction":
            benchmark_position = direction_positions(
                benchmark_prediction, abstention_threshold
            )
            candidate_position = direction_positions(
                candidate_prediction, abstention_threshold
            )
            benchmark_economic = economic_metrics(
                test_future_log_return,
                benchmark_position,
                one_way_cost_bps=one_way_cost_bps,
                horizon_candles=horizon_candles,
            )
            candidate_economic = economic_metrics(
                test_future_log_return,
                candidate_position,
                one_way_cost_bps=one_way_cost_bps,
                horizon_candles=horizon_candles,
            )
            economic_gain = incremental_economic_gain(
                candidate_economic, benchmark_economic
            )
    else:
        benchmark_prediction = np.asarray(
            pair.benchmark_estimator.predict(transformed_benchmark_test), dtype=float
        )
        candidate_prediction = np.asarray(
            pair.candidate_estimator.predict(transformed_candidate_test), dtype=float
        )
        benchmark_metrics = regression_metrics(test_target, benchmark_prediction)
        candidate_metrics = regression_metrics(test_target, candidate_prediction)
        benchmark_economic = economic_metrics(
            test_future_log_return,
            expected_return_positions(benchmark_prediction),
            one_way_cost_bps=one_way_cost_bps,
            horizon_candles=horizon_candles,
        )
        candidate_economic = economic_metrics(
            test_future_log_return,
            expected_return_positions(candidate_prediction),
            one_way_cost_bps=one_way_cost_bps,
            horizon_candles=horizon_candles,
        )
        economic_gain = incremental_economic_gain(
            candidate_economic, benchmark_economic
        )

    return MatchedOuterFoldResult(
        pipeline_spec_id=spec.pipeline_spec_id,
        target_name=spec.target_name,
        calibration_method=str(calibration_method),
        abstention_threshold=float(abstention_threshold),
        training_rows=len(selected_target),
        calibration_rows=len(calibration_target),
        test_rows=len(test_target),
        benchmark_metrics=benchmark_metrics,
        candidate_metrics=candidate_metrics,
        incremental_primary_gain=float(
            benchmark_metrics.primary_loss - candidate_metrics.primary_loss
        ),
        benchmark_economic=benchmark_economic,
        candidate_economic=candidate_economic,
        incremental_economic_gain=economic_gain,
        large_move_threshold=large_move_threshold,
        benchmark_prediction=benchmark_prediction,
        candidate_prediction=candidate_prediction,
        synthetic_validation_only=True,
        real_development_model_fitting_performed=False,
    )


def build_large_move_targets_for_partitions(
    training_future_log_return: pd.Series,
    calibration_future_log_return: pd.Series,
    test_future_log_return: pd.Series,
    *,
    quantile: float = 0.9,
) -> tuple[pd.Series, pd.Series, pd.Series, float]:
    training_index = require_utc_index(
        training_future_log_return.index, "large-move training chronology"
    )
    calibration_index = require_utc_index(
        calibration_future_log_return.index, "large-move calibration chronology"
    )
    test_index = require_utc_index(
        test_future_log_return.index, "large-move test chronology"
    )
    _assert_partition_chronology(training_index, calibration_index, test_index)
    calibration = build_fold_large_move_target(
        training_future_log_return,
        calibration_future_log_return,
        quantile=quantile,
    )
    test = build_fold_large_move_target(
        training_future_log_return,
        test_future_log_return,
        quantile=quantile,
    )
    threshold = calibration.threshold
    if not np.isclose(test.threshold, threshold, rtol=0.0, atol=0.0):
        raise ForecastProtocolViolation(
            "Fold large-move threshold is not training-only deterministic."
        )
    training_labels = (
        np.abs(training_future_log_return.to_numpy(dtype=float)) >= threshold
    ).astype(int)
    return (
        pd.Series(
            training_labels,
            index=training_future_log_return.index,
            name="large_move_probability",
        ),
        pd.Series(
            calibration.evaluation_labels,
            index=calibration_future_log_return.index,
            name="large_move_probability",
        ),
        pd.Series(
            test.evaluation_labels,
            index=test_future_log_return.index,
            name="large_move_probability",
        ),
        threshold,
    )
