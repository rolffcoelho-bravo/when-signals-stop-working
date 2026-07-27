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

from shockbridge_signal_validity.v3.forecast_contract import (  # noqa: E402
    ForecastProtocolViolation,
)
from shockbridge_signal_validity.v3.forecast_estimators import (  # noqa: E402
    build_estimator,
    build_matched_estimator_pair,
)
from shockbridge_signal_validity.v3.forecast_model_registry import (  # noqa: E402
    build_pipeline_registry,
    load_contracts,
    pipeline_registry_manifest,
)
from shockbridge_signal_validity.v3.forecast_preprocessing import (  # noqa: E402
    fit_matched_fold_preprocessors,
)

FORECAST_CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"
IMPLEMENTATION_CONTRACT = (
    ROOT / "configs" / "v3_g5_model_implementation_contract.json"
)
MATERIALIZATION_VALIDATION = ROOT / "V3_G5_MATERIALIZATION_VALIDATION.json"


def synthetic_pair(rows: int = 2300) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    index = pd.date_range("2021-01-01T00:00:00Z", periods=rows, freq="4h")
    phase = np.linspace(0.0, 40.0, rows)
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
        (benchmark["sol_ret_1"] + 0.2 * candidate["registered_signal"] > 0.0).astype(int),
        index=index,
        name="direction",
    )
    expected_return = pd.Series(
        0.3 * benchmark["sol_ret_1"]
        - 0.1 * benchmark["btc_ret_1"]
        + 0.05 * candidate["registered_signal"],
        index=index,
        name="expected_return",
    )
    return benchmark, candidate, direction, expected_return


def representative(registry, target: str, family: str):
    return next(
        spec
        for spec in registry
        if spec.target_name == target
        and spec.model_family == family
        and spec.window_id == "EXPANDING"
        and spec.executable
    )


def main() -> int:
    validation = json.loads(MATERIALIZATION_VALIDATION.read_text(encoding="utf-8"))
    if validation.get("status") != "MATERIALIZATION_AUTHORITATIVELY_VALIDATED":
        raise RuntimeError("V3-5 materialization validation is not authoritative.")
    if validation.get("validated_materialization_commit") != (
        "91606edf50a2c0aee9bcb94a93350936ee53f81a"
    ):
        raise RuntimeError("Validated materialization commit changed.")
    if validation.get("execution_state") != {
        "development_model_fitting_started": False,
        "development_pipeline_selection_performed": False,
        "establishment_authorization_created": False,
        "signal_establishment_segment_accessed": False,
        "final_framework_reserve_accessed": False,
    }:
        raise RuntimeError("Materialization execution state advanced prematurely.")

    forecast, implementation = load_contracts(
        FORECAST_CONTRACT,
        IMPLEMENTATION_CONTRACT,
    )
    if implementation.get("real_development_model_fitting_authorized") is not False:
        raise RuntimeError("Real development model fitting is authorized prematurely.")
    registry = build_pipeline_registry(forecast, implementation)
    manifest = pipeline_registry_manifest(registry)
    if manifest["pipeline_specifications"] != 162:
        raise RuntimeError("Pipeline registry does not contain 162 specifications.")
    if manifest["executable_pipeline_specifications"] != 153:
        raise RuntimeError("Executable pipeline count changed.")
    if manifest["gated_pipeline_specifications"] != 9:
        raise RuntimeError("Gated pipeline count changed.")

    benchmark, candidate, direction, expected_return = synthetic_pair()
    training_rows = 2190
    preprocessors = fit_matched_fold_preprocessors(
        benchmark.iloc[:training_rows],
        candidate.iloc[:training_rows],
    )
    benchmark_test, candidate_test = preprocessors.transform_pair(
        benchmark.iloc[training_rows:],
        candidate.iloc[training_rows:],
    )
    pd.testing.assert_frame_equal(
        benchmark_test,
        candidate_test.loc[:, list(benchmark.columns)],
        check_exact=True,
    )

    for family in (
        "regularized_linear",
        "spline_regularized",
        "shallow_hist_gradient_boosting",
        "time_varying_regularized_glm",
    ):
        classification_spec = representative(registry, "direction", family)
        matched = build_matched_estimator_pair(classification_spec, implementation)
        pair_manifest = matched.manifest()
        if pair_manifest["same_estimator_class"] is not True:
            raise RuntimeError(f"Matched estimator class differs for {family}.")
        if pair_manifest["same_hyperparameters"] is not True:
            raise RuntimeError(f"Matched estimator parameters differ for {family}.")

        classifier = build_estimator(classification_spec, implementation)
        classifier.fit(
            preprocessors.benchmark.transform(
                benchmark.iloc[:training_rows], "benchmark training verifier"
            ),
            direction.iloc[:training_rows],
        )
        probabilities = classifier.predict_proba(benchmark_test)[:, 1]
        if not np.isfinite(probabilities).all():
            raise RuntimeError(f"Non-finite classifier probability for {family}.")

        regression_spec = representative(registry, "expected_return", family)
        regressor = build_estimator(regression_spec, implementation)
        regressor.fit(
            preprocessors.benchmark.transform(
                benchmark.iloc[:training_rows], "benchmark training verifier"
            ),
            expected_return.iloc[:training_rows],
        )
        prediction = regressor.predict(benchmark_test)
        if not np.isfinite(prediction).all():
            raise RuntimeError(f"Non-finite regression prediction for {family}.")

    gated = [spec for spec in registry if not spec.executable]
    if len(gated) != 9:
        raise RuntimeError("State-space gated specification identity changed.")
    try:
        build_estimator(gated[0], implementation)
    except ForecastProtocolViolation as error:
        if str(error) != "INELIGIBLE_IMPLEMENTATION_NOT_AUTHORIZED":
            raise
    else:
        raise RuntimeError("Gated state-space specification became executable.")

    print("Gate V3-5 model implementation verified.")
    print("Materialization authoritatively validated: True")
    print("Training-only matched preprocessing verified: True")
    print("Exact benchmark transformation reuse verified: True")
    print("Pipeline specifications: 162")
    print("Executable pipeline specifications: 153")
    print("Gated pipeline specifications: 9")
    print("Executable model families: 4")
    print("Window schemes: 3")
    print("Synthetic classification and regression fits: passed")
    print("Real development model fitting performed: False")
    print("Development pipeline selection performed: False")
    print("Signal-establishment segment accessed: False")
    print("V3-9 final-framework reserve accessed: False")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"Gate V3-5 model implementation verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
