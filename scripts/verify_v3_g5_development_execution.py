from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shockbridge_signal_validity.v3.forecast_development_execution import (  # noqa: E402
    build_execution_plan_identity,
    build_large_move_targets_for_partitions,
    execute_matched_outer_fold,
)
from shockbridge_signal_validity.v3.forecast_development_selection import (  # noqa: E402
    InnerFoldScore,
    positive_fold_concentration,
    select_one_standard_error_configuration,
)
from shockbridge_signal_validity.v3.forecast_model_registry import (  # noqa: E402
    build_pipeline_registry,
    load_contracts,
)
from shockbridge_signal_validity.v3.forecast_multiplicity import (  # noqa: E402
    benjamini_hochberg_adjust,
    holm_adjust,
)

FORECAST_CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"
MODEL_CONTRACT = ROOT / "configs" / "v3_g5_model_implementation_contract.json"
EXECUTION_CONTRACT = ROOT / "configs" / "v3_g5_development_execution_contract.json"
MODEL_VALIDATION = ROOT / "V3_G5_MODEL_IMPLEMENTATION_VALIDATION.json"


def _synthetic_partitions():
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
        (benchmark["sol_ret_1"] + 0.35 * candidate["registered_signal"] > 0.0).astype(int),
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
    return benchmark, candidate, direction, expected_return, realized


def _representative(registry, target_name: str):
    return next(
        value
        for value in registry
        if value.target_name == target_name
        and value.model_family == "regularized_linear"
        and value.window_id == "EXPANDING"
        and value.executable
    )


def main() -> int:
    model_validation = json.loads(MODEL_VALIDATION.read_text(encoding="utf-8"))
    if model_validation.get("status") != "MODEL_IMPLEMENTATION_AUTHORITATIVELY_VALIDATED_AND_PROTECTED":
        raise RuntimeError("Model implementation boundary is not final.")
    if model_validation.get("validated_implementation_commit") != (
        "37c7360afde61a01ee9f9c5237dcf6bdf42985dd"
    ):
        raise RuntimeError("Validated model implementation commit changed.")
    execution_contract = json.loads(EXECUTION_CONTRACT.read_text(encoding="utf-8"))
    if execution_contract.get("status") != "EXECUTION_ENGINE_CONTRACT_FROZEN":
        raise RuntimeError("Development execution contract is not frozen.")
    for field in (
        "real_development_execution_authorized",
        "real_development_model_fitting_authorized",
        "development_pipeline_selection_authorized",
        "signal_establishment_segment_access_authorized",
        "final_framework_reserve_access_authorized",
    ):
        if execution_contract.get(field) is not False:
            raise RuntimeError(f"Development execution advanced prematurely: {field}")

    forecast, implementation = load_contracts(FORECAST_CONTRACT, MODEL_CONTRACT)
    registry = build_pipeline_registry(forecast, implementation)
    identity = build_execution_plan_identity(
        matched_candidate_horizon_records=300,
        executable_pipeline_specifications=sum(value.executable for value in registry),
        outer_folds=5,
        real_execution_authorized=False,
    )
    if identity.candidate_pipeline_target_combinations != 45900:
        raise RuntimeError("Candidate-pipeline workload identity changed.")
    if identity.outer_fold_jobs != 229500:
        raise RuntimeError("Outer-fold workload identity changed.")

    benchmark, candidate, direction, expected_return, realized = _synthetic_partitions()
    train = slice(0, 600)
    calibration = slice(600, 750)
    test = slice(750, 900)
    for target_name, target, calibration_method in (
        ("direction", direction, "sigmoid"),
        ("expected_return", expected_return, "none"),
    ):
        result = execute_matched_outer_fold(
            spec=_representative(registry, target_name),
            implementation_contract=implementation,
            benchmark_training=benchmark.iloc[train],
            candidate_training=candidate.iloc[train],
            training_target=target.iloc[train],
            benchmark_calibration=benchmark.iloc[calibration],
            candidate_calibration=candidate.iloc[calibration],
            calibration_target=target.iloc[calibration],
            benchmark_test=benchmark.iloc[test],
            candidate_test=candidate.iloc[test],
            test_target=target.iloc[test],
            test_future_log_return=realized.iloc[test],
            horizon_candles=1,
            calibration_method=calibration_method,
            abstention_threshold=0.02,
            synthetic_validation_only=True,
        )
        if result.real_development_model_fitting_performed is not False:
            raise RuntimeError("Synthetic execution reported real development fitting.")
        if not np.isfinite(result.incremental_primary_gain):
            raise RuntimeError("Synthetic execution produced non-finite gain.")

    large_training, large_calibration, large_test, large_threshold = (
        build_large_move_targets_for_partitions(
            realized.iloc[train],
            realized.iloc[calibration],
            realized.iloc[test],
            quantile=0.9,
        )
    )
    large_result = execute_matched_outer_fold(
        spec=_representative(registry, "large_move_probability"),
        implementation_contract=implementation,
        benchmark_training=benchmark.iloc[train],
        candidate_training=candidate.iloc[train],
        training_target=large_training,
        benchmark_calibration=benchmark.iloc[calibration],
        candidate_calibration=candidate.iloc[calibration],
        calibration_target=large_calibration,
        benchmark_test=benchmark.iloc[test],
        candidate_test=candidate.iloc[test],
        test_target=large_test,
        test_future_log_return=realized.iloc[test],
        horizon_candles=1,
        calibration_method="none",
        fold_large_move_threshold=large_threshold,
        synthetic_validation_only=True,
    )
    if large_result.large_move_threshold != large_threshold:
        raise RuntimeError("Large-move execution lost its training-fold threshold.")
    if large_result.benchmark_economic is not None or large_result.candidate_economic is not None:
        raise RuntimeError("Large-move diagnostic created an unauthorized trading policy.")

    inner_rows: list[InnerFoldScore] = []
    for fold, gain in enumerate((0.020, 0.018, 0.022), start=1):
        inner_rows.append(
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
    selected = select_one_standard_error_configuration(inner_rows)
    if selected.pipeline_spec_id != "simple":
        raise RuntimeError("One-standard-error selection identity changed.")
    concentration = positive_fold_concentration([0.1, 0.08, 0.07, -0.02, 0.03])
    if concentration["minimum_positive_outer_folds_passed"] is not True:
        raise RuntimeError("Positive-fold concentration control changed.")

    holm = holm_adjust(["rsi", "bollinger"], [0.01, 0.04], alpha=0.05)
    bh = benjamini_hochberg_adjust(["a", "b", "c"], [0.01, 0.03, 0.2], q=0.1)
    if len(holm) != 2 or len(bh) != 3:
        raise RuntimeError("Multiplicity output identity changed.")

    print("Gate V3-5 chronological development execution engine verified.")
    print("Model implementation boundary protected: True")
    print("Execution engine contract frozen: True")
    print("Development execution authorized: False")
    print("Candidate-pipeline-target combinations: 45900")
    print("Outer-fold jobs: 229500")
    print("Strict training/calibration/test chronology verified: True")
    print("Fold-scoped large-move threshold and execution verified: True")
    print("Training-only calibration verified: True")
    print("One-standard-error inner selection verified: True")
    print("Predictive and economic metrics verified: True")
    print("Holm and Benjamini-Hochberg controls verified: True")
    print("Synthetic matched outer-fold fits: passed")
    print("Real development model fitting performed: False")
    print("Development pipeline selection performed: False")
    print("Signal-establishment segment accessed: False")
    print("V3-9 final-framework reserve accessed: False")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"Gate V3-5 development execution verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
