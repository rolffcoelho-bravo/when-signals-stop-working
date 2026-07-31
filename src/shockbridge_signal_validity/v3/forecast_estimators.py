from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
from typing import Any

import numpy as np
import pandas as pd
from sklearn import __version__ as SKLEARN_VERSION
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import SplineTransformer

from .forecast_contract import ForecastProtocolViolation, require_utc_index
from .forecast_model_registry import ForecastPipelineSpec


def sklearn_major_minor() -> tuple[int, int]:
    match = re.match(r"^(\d+)\.(\d+)", str(SKLEARN_VERSION))
    if match is None:
        raise ForecastProtocolViolation(
            f"Unable to parse scikit-learn version: {SKLEARN_VERSION!r}"
        )
    return int(match.group(1)), int(match.group(2))


def version_compatible_logistic_l2_arguments(
    *,
    penalty_before_sklearn_1_8: str,
    l1_ratio_from_sklearn_1_8: float,
) -> dict[str, object]:
    if str(penalty_before_sklearn_1_8) != "l2":
        raise ForecastProtocolViolation("Pre-1.8 logistic policy must preserve L2.")
    if float(l1_ratio_from_sklearn_1_8) != 0.0:
        raise ForecastProtocolViolation("Scikit-learn 1.8+ logistic policy must preserve L2.")
    if sklearn_major_minor() >= (1, 8):
        return {"l1_ratio": 0.0}
    return {"penalty": "l2"}


class ExponentiallyWeightedGLMClassifier(ClassifierMixin, BaseEstimator):
    def __init__(
        self,
        *,
        forgetting_factor: float,
        minimum_training_observations: int,
        C: float = 1.0,
        max_iter: int = 2000,
        random_state: int = 20260728,
        penalty_before_sklearn_1_8: str = "l2",
        l1_ratio_from_sklearn_1_8: float = 0.0,
    ) -> None:
        self.forgetting_factor = forgetting_factor
        self.minimum_training_observations = minimum_training_observations
        self.C = C
        self.max_iter = max_iter
        self.random_state = random_state
        self.penalty_before_sklearn_1_8 = penalty_before_sklearn_1_8
        self.l1_ratio_from_sklearn_1_8 = l1_ratio_from_sklearn_1_8

    def fit(self, X: Any, y: Any) -> "ExponentiallyWeightedGLMClassifier":
        values = np.asarray(X, dtype=float)
        target = np.asarray(y)
        if values.ndim != 2 or len(values) != len(target):
            raise ForecastProtocolViolation("Dynamic classifier training arrays are invalid.")
        if len(values) < int(self.minimum_training_observations):
            raise ForecastProtocolViolation(
                "Dynamic classifier has insufficient training observations."
            )
        if not np.isfinite(values).all():
            raise ForecastProtocolViolation("Dynamic classifier features are not finite.")
        classes = np.unique(target)
        if not np.array_equal(classes, np.array([0, 1])):
            raise ForecastProtocolViolation(
                "Dynamic classifier requires both binary classes in training."
            )
        if not 0.0 < float(self.forgetting_factor) < 1.0:
            raise ForecastProtocolViolation("Dynamic classifier forgetting factor is invalid.")
        age = np.arange(len(values) - 1, -1, -1, dtype=float)
        weights = np.power(float(self.forgetting_factor), age)
        weights = np.maximum(weights, np.finfo(float).tiny)
        regularization = version_compatible_logistic_l2_arguments(
            penalty_before_sklearn_1_8=str(self.penalty_before_sklearn_1_8),
            l1_ratio_from_sklearn_1_8=float(self.l1_ratio_from_sklearn_1_8),
        )
        self.model_ = LogisticRegression(
            C=float(self.C),
            solver="lbfgs",
            max_iter=int(self.max_iter),
            random_state=int(self.random_state),
            **regularization,
        )
        self.model_.fit(values, target, sample_weight=weights)
        self.classes_ = self.model_.classes_
        self.n_features_in_ = values.shape[1]
        self.training_rows_ = len(values)
        self.effective_weight_ = float(weights.sum())
        return self

    def predict_proba(self, X: Any) -> np.ndarray:
        if not hasattr(self, "model_"):
            raise ForecastProtocolViolation("Dynamic classifier is not fitted.")
        return self.model_.predict_proba(np.asarray(X, dtype=float))

    def predict(self, X: Any) -> np.ndarray:
        if not hasattr(self, "model_"):
            raise ForecastProtocolViolation("Dynamic classifier is not fitted.")
        return self.model_.predict(np.asarray(X, dtype=float))


class ExponentiallyWeightedGLMRegressor(RegressorMixin, BaseEstimator):
    def __init__(
        self,
        *,
        forgetting_factor: float,
        minimum_training_observations: int,
        alpha: float = 1.0,
    ) -> None:
        self.forgetting_factor = forgetting_factor
        self.minimum_training_observations = minimum_training_observations
        self.alpha = alpha

    def fit(self, X: Any, y: Any) -> "ExponentiallyWeightedGLMRegressor":
        values = np.asarray(X, dtype=float)
        target = np.asarray(y, dtype=float)
        if values.ndim != 2 or len(values) != len(target):
            raise ForecastProtocolViolation("Dynamic regressor training arrays are invalid.")
        if len(values) < int(self.minimum_training_observations):
            raise ForecastProtocolViolation(
                "Dynamic regressor has insufficient training observations."
            )
        if not np.isfinite(values).all() or not np.isfinite(target).all():
            raise ForecastProtocolViolation("Dynamic regressor training values are not finite.")
        if not 0.0 < float(self.forgetting_factor) < 1.0:
            raise ForecastProtocolViolation("Dynamic regressor forgetting factor is invalid.")
        age = np.arange(len(values) - 1, -1, -1, dtype=float)
        weights = np.power(float(self.forgetting_factor), age)
        weights = np.maximum(weights, np.finfo(float).tiny)
        self.model_ = Ridge(alpha=float(self.alpha))
        self.model_.fit(values, target, sample_weight=weights)
        self.n_features_in_ = values.shape[1]
        self.training_rows_ = len(values)
        self.effective_weight_ = float(weights.sum())
        return self

    def predict(self, X: Any) -> np.ndarray:
        if not hasattr(self, "model_"):
            raise ForecastProtocolViolation("Dynamic regressor is not fitted.")
        return self.model_.predict(np.asarray(X, dtype=float))


def estimator_signature(estimator: BaseEstimator) -> str:
    material = (
        f"{estimator.__class__.__module__}.{estimator.__class__.__qualname__}|"
        f"{repr(estimator)}"
    )
    return sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MatchedEstimatorPair:
    pipeline_spec_id: str
    benchmark_estimator: BaseEstimator
    candidate_estimator: BaseEstimator
    target_name: str
    task_type: str
    model_family: str
    window_id: str
    window_observations: int | None

    def manifest(self) -> dict[str, object]:
        benchmark_signature = estimator_signature(self.benchmark_estimator)
        candidate_signature = estimator_signature(self.candidate_estimator)
        return {
            "schema_version": "v3.g5-matched-estimator-pair.v1",
            "pipeline_spec_id": self.pipeline_spec_id,
            "target_name": self.target_name,
            "task_type": self.task_type,
            "model_family": self.model_family,
            "window_id": self.window_id,
            "window_observations": self.window_observations,
            "benchmark_estimator_signature": benchmark_signature,
            "candidate_estimator_signature": candidate_signature,
            "same_estimator_class": type(self.benchmark_estimator)
            is type(self.candidate_estimator),
            "same_hyperparameters": benchmark_signature == candidate_signature,
            "real_development_model_fitting_performed": False,
        }


def _logistic_estimator(
    *,
    C: float,
    defaults: dict[str, object],
) -> LogisticRegression:
    regularization = version_compatible_logistic_l2_arguments(
        penalty_before_sklearn_1_8=str(
            defaults["logistic_penalty_before_sklearn_1_8"]
        ),
        l1_ratio_from_sklearn_1_8=float(
            defaults["logistic_l1_ratio_from_sklearn_1_8"]
        ),
    )
    return LogisticRegression(
        C=float(C),
        solver=str(defaults["logistic_solver"]),
        max_iter=int(defaults["logistic_max_iter"]),
        random_state=int(defaults["random_state"]),
        **regularization,
    )


def _spline_pipeline(
    *,
    task_type: str,
    parameters: dict[str, object],
    defaults: dict[str, object],
) -> Pipeline:
    spline = SplineTransformer(
        degree=int(parameters["degree"]),
        n_knots=int(parameters["n_knots"]),
        knots=str(defaults["spline_knots"]),
        extrapolation=str(defaults["spline_extrapolation"]),
        include_bias=bool(defaults["spline_include_bias"]),
    )
    if task_type == "CLASSIFICATION":
        model: BaseEstimator = _logistic_estimator(
            C=float(parameters["C"]),
            defaults=defaults,
        )
    else:
        model = Ridge(alpha=float(parameters["alpha"]))
    return Pipeline([("spline", spline), ("model", model)])


def build_estimator(
    spec: ForecastPipelineSpec,
    implementation_contract: dict[str, Any],
) -> BaseEstimator:
    if not spec.executable:
        raise ForecastProtocolViolation(
            spec.ineligibility_status or "Pipeline specification is not executable."
        )
    defaults = implementation_contract["estimator_defaults"]
    parameters = spec.parameter_dict()
    family = spec.model_family

    if defaults.get("logistic_l2_compatibility_policy") != (
        "VERSION_AWARE_EQUIVALENT_L2"
    ):
        raise ForecastProtocolViolation("Logistic L2 compatibility policy changed.")

    if family == "regularized_linear":
        if spec.task_type == "CLASSIFICATION":
            return _logistic_estimator(
                C=float(parameters["C"]),
                defaults=defaults,
            )
        return Ridge(alpha=float(parameters["alpha"]))

    if family == "spline_regularized":
        return _spline_pipeline(
            task_type=spec.task_type,
            parameters=parameters,
            defaults=defaults,
        )

    if family == "shallow_hist_gradient_boosting":
        common = {
            "learning_rate": float(parameters["learning_rate"]),
            "max_leaf_nodes": int(parameters["max_leaf_nodes"]),
            "max_iter": int(parameters["max_iter"]),
            "min_samples_leaf": int(parameters["min_samples_leaf"]),
            "l2_regularization": float(parameters["l2_regularization"]),
            "random_state": int(defaults["random_state"]),
        }
        if spec.task_type == "CLASSIFICATION":
            return HistGradientBoostingClassifier(**common)
        return HistGradientBoostingRegressor(**common)

    if family == "time_varying_regularized_glm":
        if spec.task_type == "CLASSIFICATION":
            return ExponentiallyWeightedGLMClassifier(
                forgetting_factor=float(parameters["forgetting_factor"]),
                minimum_training_observations=int(
                    parameters["minimum_training_observations"]
                ),
                C=float(defaults["logistic_C_for_dynamic_glm"]),
                max_iter=int(defaults["logistic_max_iter"]),
                random_state=int(defaults["random_state"]),
                penalty_before_sklearn_1_8=str(
                    defaults["logistic_penalty_before_sklearn_1_8"]
                ),
                l1_ratio_from_sklearn_1_8=float(
                    defaults["logistic_l1_ratio_from_sklearn_1_8"]
                ),
            )
        return ExponentiallyWeightedGLMRegressor(
            forgetting_factor=float(parameters["forgetting_factor"]),
            minimum_training_observations=int(
                parameters["minimum_training_observations"]
            ),
            alpha=float(defaults["ridge_alpha_for_dynamic_glm"]),
        )

    raise ForecastProtocolViolation(f"Unsupported executable model family: {family}")


def build_matched_estimator_pair(
    spec: ForecastPipelineSpec,
    implementation_contract: dict[str, Any],
) -> MatchedEstimatorPair:
    benchmark = build_estimator(spec, implementation_contract)
    candidate = build_estimator(spec, implementation_contract)
    if type(benchmark) is not type(candidate):
        raise ForecastProtocolViolation("Matched estimator classes differ.")
    if estimator_signature(benchmark) != estimator_signature(candidate):
        raise ForecastProtocolViolation("Matched estimator hyperparameters differ.")
    return MatchedEstimatorPair(
        pipeline_spec_id=spec.pipeline_spec_id,
        benchmark_estimator=benchmark,
        candidate_estimator=candidate,
        target_name=spec.target_name,
        task_type=spec.task_type,
        model_family=spec.model_family,
        window_id=spec.window_id,
        window_observations=spec.window_observations,
    )


def select_training_window(
    features: pd.DataFrame,
    target: pd.Series,
    spec: ForecastPipelineSpec,
) -> tuple[pd.DataFrame, pd.Series]:
    index = require_utc_index(features.index, "model training timestamps")
    if not index.equals(require_utc_index(target.index, "model target timestamps")):
        raise ForecastProtocolViolation("Training feature and target rows differ.")
    if features.isna().any().any() or target.isna().any():
        raise ForecastProtocolViolation("Model training rows must be complete.")
    if not np.isfinite(features.to_numpy(dtype=float)).all():
        raise ForecastProtocolViolation("Model training features must be finite.")
    if not np.isfinite(pd.to_numeric(target, errors="coerce").to_numpy(dtype=float)).all():
        raise ForecastProtocolViolation("Model training targets must be finite.")
    if spec.window_id == "EXPANDING":
        return features.copy(), target.copy()
    if spec.window_observations is None or int(spec.window_observations) < 1:
        raise ForecastProtocolViolation("Rolling pipeline window is invalid.")
    if len(features) < int(spec.window_observations):
        raise ForecastProtocolViolation(
            "Training fold is shorter than the registered rolling window."
        )
    return (
        features.iloc[-int(spec.window_observations) :].copy(),
        target.iloc[-int(spec.window_observations) :].copy(),
    )
