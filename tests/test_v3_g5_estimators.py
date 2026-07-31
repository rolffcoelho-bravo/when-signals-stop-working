from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v3.forecast_contract import ForecastProtocolViolation
from shockbridge_signal_validity.v3.forecast_estimators import (
    ExponentiallyWeightedGLMClassifier,
    ExponentiallyWeightedGLMRegressor,
    build_estimator,
    build_matched_estimator_pair,
    sklearn_major_minor,
    select_training_window,
)
from shockbridge_signal_validity.v3.forecast_model_registry import (
    build_pipeline_registry,
    load_contracts,
)

ROOT = Path(__file__).resolve().parents[1]
FORECAST_CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"
IMPLEMENTATION_CONTRACT = ROOT / "configs" / "v3_g5_model_implementation_contract.json"


def _contracts_and_registry():
    forecast, implementation = load_contracts(
        FORECAST_CONTRACT,
        IMPLEMENTATION_CONTRACT,
    )
    return forecast, implementation, build_pipeline_registry(forecast, implementation)


def _spec(registry, target: str, family: str, window: str = "EXPANDING"):
    return next(
        value
        for value in registry
        if value.target_name == target
        and value.model_family == family
        and value.window_id == window
        and value.executable
    )


def _classification_data(rows: int = 500) -> tuple[pd.DataFrame, pd.Series]:
    index = pd.date_range("2021-01-01T00:00:00Z", periods=rows, freq="4h")
    phase = np.linspace(0.0, 30.0, rows)
    features = pd.DataFrame(
        {
            "x1": np.sin(phase),
            "x2": np.cos(phase / 2.0),
            "x3": np.linspace(-1.0, 1.0, rows),
        },
        index=index,
    )
    target = pd.Series(
        (features["x1"] + 0.25 * features["x2"] > 0.0).astype(int),
        index=index,
        name="direction",
    )
    return features, target


def _regression_data(rows: int = 500) -> tuple[pd.DataFrame, pd.Series]:
    features, _ = _classification_data(rows)
    target = pd.Series(
        0.4 * features["x1"] - 0.2 * features["x2"] + 0.05 * features["x3"],
        index=features.index,
        name="expected_return",
    )
    return features, target


def _assert_logistic_l2_parameters(parameters: dict[str, object]) -> None:
    if sklearn_major_minor() >= (1, 8):
        assert float(parameters["l1_ratio"]) == 0.0
    else:
        assert parameters["penalty"] == "l2"


def test_all_executable_specs_build_matched_estimators() -> None:
    _, implementation, registry = _contracts_and_registry()
    executable = [spec for spec in registry if spec.executable]
    assert len(executable) == 153
    for spec in executable:
        pair = build_matched_estimator_pair(spec, implementation)
        manifest = pair.manifest()
        assert manifest["same_estimator_class"] is True
        assert manifest["same_hyperparameters"] is True
        assert manifest["real_development_model_fitting_performed"] is False


def test_regularized_linear_classification_fits_synthetic_data() -> None:
    _, implementation, registry = _contracts_and_registry()
    spec = _spec(registry, "direction", "regularized_linear")
    estimator = build_estimator(spec, implementation)
    _assert_logistic_l2_parameters(estimator.get_params(deep=True))
    features, target = _classification_data()
    estimator.fit(features, target)
    probabilities = estimator.predict_proba(features.iloc[-30:])[:, 1]
    assert np.isfinite(probabilities).all()
    assert ((probabilities >= 0.0) & (probabilities <= 1.0)).all()


def test_spline_classification_fits_synthetic_data() -> None:
    _, implementation, registry = _contracts_and_registry()
    spec = _spec(registry, "direction", "spline_regularized")
    estimator = build_estimator(spec, implementation)
    _assert_logistic_l2_parameters(estimator.named_steps["model"].get_params(deep=True))
    features, target = _classification_data()
    estimator.fit(features, target)
    probabilities = estimator.predict_proba(features.iloc[-30:])[:, 1]
    assert np.isfinite(probabilities).all()


def test_shallow_boosting_classification_fits_synthetic_data() -> None:
    _, implementation, registry = _contracts_and_registry()
    spec = _spec(registry, "direction", "shallow_hist_gradient_boosting")
    estimator = build_estimator(spec, implementation)
    features, target = _classification_data()
    estimator.fit(features, target)
    probabilities = estimator.predict_proba(features.iloc[-30:])[:, 1]
    assert np.isfinite(probabilities).all()


def test_regularized_spline_and_boosting_regressors_are_finite() -> None:
    _, implementation, registry = _contracts_and_registry()
    features, target = _regression_data()
    for family in (
        "regularized_linear",
        "spline_regularized",
        "shallow_hist_gradient_boosting",
    ):
        spec = _spec(registry, "expected_return", family)
        estimator = build_estimator(spec, implementation)
        estimator.fit(features, target)
        prediction = estimator.predict(features.iloc[-30:])
        assert np.isfinite(prediction).all()


def test_dynamic_classifier_enforces_minimum_training_history() -> None:
    _, implementation, registry = _contracts_and_registry()
    spec = _spec(registry, "direction", "time_varying_regularized_glm")
    estimator = build_estimator(spec, implementation)
    assert isinstance(estimator, ExponentiallyWeightedGLMClassifier)
    features, target = _classification_data(2189)
    with pytest.raises(ForecastProtocolViolation, match="insufficient"):
        estimator.fit(features, target)


def test_dynamic_classifier_fits_at_registered_minimum() -> None:
    _, implementation, registry = _contracts_and_registry()
    spec = _spec(registry, "direction", "time_varying_regularized_glm")
    estimator = build_estimator(spec, implementation)
    features, target = _classification_data(2190)
    estimator.fit(features, target)
    _assert_logistic_l2_parameters(estimator.model_.get_params(deep=True))
    probabilities = estimator.predict_proba(features.iloc[-20:])[:, 1]
    assert np.isfinite(probabilities).all()
    assert estimator.training_rows_ == 2190
    assert estimator.effective_weight_ > 0.0


def test_dynamic_regressor_fits_at_registered_minimum() -> None:
    _, implementation, registry = _contracts_and_registry()
    spec = _spec(registry, "expected_return", "time_varying_regularized_glm")
    estimator = build_estimator(spec, implementation)
    assert isinstance(estimator, ExponentiallyWeightedGLMRegressor)
    features, target = _regression_data(2190)
    estimator.fit(features, target)
    prediction = estimator.predict(features.iloc[-20:])
    assert np.isfinite(prediction).all()
    assert estimator.training_rows_ == 2190


def test_gated_state_space_spec_cannot_build_estimator() -> None:
    _, implementation, registry = _contracts_and_registry()
    gated = next(spec for spec in registry if not spec.executable)
    with pytest.raises(
        ForecastProtocolViolation,
        match="INELIGIBLE_IMPLEMENTATION_NOT_AUTHORIZED",
    ):
        build_estimator(gated, implementation)


def test_rolling_windows_use_only_registered_trailing_history() -> None:
    _, _, registry = _contracts_and_registry()
    features, target = _classification_data(5000)
    one_year = _spec(
        registry,
        "direction",
        "regularized_linear",
        "ROLLING_ONE_YEAR",
    )
    selected_features, selected_target = select_training_window(
        features, target, one_year
    )
    assert len(selected_features) == 2190
    assert len(selected_target) == 2190
    assert selected_features.index.equals(features.index[-2190:])

    two_year = _spec(
        registry,
        "direction",
        "regularized_linear",
        "ROLLING_TWO_YEARS",
    )
    selected_features, selected_target = select_training_window(
        features, target, two_year
    )
    assert len(selected_features) == 4380
    assert len(selected_target) == 4380


def test_rolling_window_rejects_insufficient_fold_history() -> None:
    _, _, registry = _contracts_and_registry()
    features, target = _classification_data(2000)
    one_year = _spec(
        registry,
        "direction",
        "regularized_linear",
        "ROLLING_ONE_YEAR",
    )
    with pytest.raises(ForecastProtocolViolation, match="shorter"):
        select_training_window(features, target, one_year)
