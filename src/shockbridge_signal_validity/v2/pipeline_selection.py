from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

from .causal_features import BASELINE_FEATURES
from .contracts import ProtocolViolation
from .predictive_screening import STATE_PROBABILITY_COLUMNS, expected_calibration_error


CALIBRATION_METHODS = ("none", "sigmoid", "isotonic")
ELIGIBLE_CALIBRATION_METHODS = ("none", "sigmoid")
ABSTENTION_THRESHOLDS = (0.0, 0.02, 0.05, 0.10)


@dataclass(frozen=True)
class StructuralPipelineSpecification:
    pipeline_id: str
    model_family: str
    window_scheme: str
    regime_conditioned: bool
    parameters: dict[str, Any]
    complexity_rank: int


@dataclass(frozen=True)
class MatchedPipelineFoldResult:
    benchmark_probability: np.ndarray
    candidate_probability: np.ndarray
    realised: np.ndarray
    timestamps: pd.DatetimeIndex
    future_return: np.ndarray
    benchmark_log_loss: float
    candidate_log_loss: float
    incremental_log_loss: float
    benchmark_brier: float
    candidate_brier: float
    benchmark_ece: float
    candidate_ece: float
    train_rows: int
    fit_rows: int
    calibration_rows: int
    test_rows: int


def _json_parameters(parameters: dict[str, Any]) -> str:
    return json.dumps(parameters, sort_keys=True, separators=(",", ":"))


def _pipeline_id(
    model_family: str,
    parameters: dict[str, Any],
    window_scheme: str,
    regime_conditioned: bool,
) -> str:
    parameter_text = "-".join(
        f"{key}{str(value).replace('.', 'p')}" for key, value in sorted(parameters.items())
    )
    regime = "softstate" if regime_conditioned else "unconditioned"
    return f"{model_family}-{parameter_text}-{window_scheme}-{regime}"


def build_structural_pipeline_inventory(registry_payload: dict[str, Any]) -> pd.DataFrame:
    """Build the frozen D2B structural grid without calibration multiplication.

    Calibration is selected after structural-model selection so that the model,
    window, and state-conditioning grid remains fully evaluated while avoiding
    redundant fitting of the same base estimator.
    """
    model_families = registry_payload["model_families"]
    windows = registry_payload["window_schemes"]
    records: list[dict[str, Any]] = []
    complexity_rank = 0

    model_records: list[tuple[str, dict[str, Any]]] = []
    for c_value in model_families["regularized_linear"]["classification_C"]:
        model_records.append(("regularized_linear", {"C": float(c_value)}))

    spline = model_families["spline_regularized"]
    for knots in spline["n_knots"]:
        for c_value in spline["classification_C"]:
            model_records.append(
                (
                    "spline_regularized",
                    {"degree": int(spline["degree"]), "n_knots": int(knots), "C": float(c_value)},
                )
            )

    boosting = model_families["shallow_hist_gradient_boosting"]
    for leaf_nodes in boosting["max_leaf_nodes"]:
        for max_iter in boosting["max_iter"]:
            for l2 in boosting["l2_regularization"]:
                model_records.append(
                    (
                        "shallow_hist_gradient_boosting",
                        {
                            "learning_rate": float(boosting["learning_rate"][0]),
                            "max_leaf_nodes": int(leaf_nodes),
                            "max_iter": int(max_iter),
                            "min_samples_leaf": int(boosting["min_samples_leaf"][0]),
                            "l2_regularization": float(l2),
                        },
                    )
                )

    window_records = [
        ("expanding", None),
        ("rolling_two_year", int(windows["rolling_two_year_observations"])),
        ("rolling_one_year", int(windows["rolling_one_year_observations"])),
    ]

    for model_family, parameters in model_records:
        for window_scheme, observations in window_records:
            for regime_conditioned in (False, True):
                complexity_rank += 1
                values = dict(parameters)
                if observations is not None:
                    values["window_observations"] = observations
                records.append(
                    {
                        "pipeline_id": _pipeline_id(
                            model_family,
                            values,
                            window_scheme,
                            regime_conditioned,
                        ),
                        "model_family": model_family,
                        "window_scheme": window_scheme,
                        "window_observations": observations,
                        "regime_conditioned": regime_conditioned,
                        "parameters_json": _json_parameters(values),
                        "complexity_rank": complexity_rank,
                    }
                )

    frame = pd.DataFrame.from_records(records)
    if len(frame) != 90:
        raise ProtocolViolation(f"D2B structural inventory must contain 90 rows, found {len(frame)}.")
    if frame["pipeline_id"].duplicated().any():
        raise ProtocolViolation("D2B structural pipeline identifiers are not unique.")
    return frame


def structural_specification_from_row(row: pd.Series) -> StructuralPipelineSpecification:
    return StructuralPipelineSpecification(
        pipeline_id=str(row["pipeline_id"]),
        model_family=str(row["model_family"]),
        window_scheme=str(row["window_scheme"]),
        regime_conditioned=bool(row["regime_conditioned"]),
        parameters=json.loads(str(row["parameters_json"])),
        complexity_rank=int(row["complexity_rank"]),
    )


def _require_chronological(frame: pd.DataFrame | pd.Series) -> None:
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise ProtocolViolation("D2B inputs require timezone-aware timestamps.")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ProtocolViolation("D2B timestamps must be unique and chronological.")


def apply_training_window(
    frame: pd.DataFrame,
    window_scheme: str,
    registry_payload: dict[str, Any],
) -> pd.DataFrame:
    _require_chronological(frame)
    if window_scheme == "expanding":
        return frame
    windows = registry_payload["window_schemes"]
    if window_scheme == "rolling_one_year":
        observations = int(windows["rolling_one_year_observations"])
    elif window_scheme == "rolling_two_year":
        observations = int(windows["rolling_two_year_observations"])
    else:
        raise ProtocolViolation(f"Unsupported D2B training window: {window_scheme}")
    if len(frame) <= observations:
        return frame
    return frame.iloc[-observations:]


def signal_feature_columns(signal_frame: pd.DataFrame, regime_conditioned: bool) -> list[str]:
    interaction_columns = ["signal_x_range", "signal_x_trend", "signal_x_stress"]
    raw_columns = [
        column
        for column in signal_frame.columns
        if column not in interaction_columns and pd.api.types.is_numeric_dtype(signal_frame[column])
    ]
    if not raw_columns:
        raise ProtocolViolation("D2B signal block contains no numeric registered features.")
    columns = list(raw_columns)
    if regime_conditioned:
        missing = [column for column in interaction_columns if column not in signal_frame]
        if missing:
            raise ProtocolViolation("D2B signal-state interactions are missing: " + ", ".join(missing))
        columns.extend(interaction_columns)
    return columns


def _make_model(
    specification: StructuralPipelineSpecification,
    feature_columns: list[str],
    signal_columns: list[str],
    random_state: int,
) -> Any:
    parameters = specification.parameters
    if specification.model_family == "regularized_linear":
        return Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        C=float(parameters["C"]),
                        solver="lbfgs",
                        max_iter=2000,
                        random_state=random_state,
                    ),
                ),
            ]
        )

    if specification.model_family == "spline_regularized":
        nonlinear = [column for column in feature_columns if column in signal_columns]
        linear = [column for column in feature_columns if column not in nonlinear]
        transformers: list[tuple[str, Any, list[str]]] = []
        if linear:
            transformers.append(("linear", StandardScaler(), linear))
        if nonlinear:
            transformers.append(
                (
                    "spline",
                    Pipeline(
                        [
                            (
                                "basis",
                                SplineTransformer(
                                    degree=int(parameters["degree"]),
                                    n_knots=int(parameters["n_knots"]),
                                    include_bias=False,
                                ),
                            ),
                            ("scale", StandardScaler()),
                        ]
                    ),
                    nonlinear,
                )
            )
        preprocessor = ColumnTransformer(transformers, remainder="drop")
        return Pipeline(
            [
                ("features", preprocessor),
                (
                    "model",
                    LogisticRegression(
                        C=float(parameters["C"]),
                        solver="lbfgs",
                        max_iter=2000,
                        random_state=random_state,
                    ),
                ),
            ]
        )

    if specification.model_family == "shallow_hist_gradient_boosting":
        return HistGradientBoostingClassifier(
            learning_rate=float(parameters["learning_rate"]),
            max_leaf_nodes=int(parameters["max_leaf_nodes"]),
            max_iter=int(parameters["max_iter"]),
            min_samples_leaf=int(parameters["min_samples_leaf"]),
            l2_regularization=float(parameters["l2_regularization"]),
            early_stopping=True,
            validation_fraction=0.10,
            n_iter_no_change=10,
            random_state=random_state,
        )

    raise ProtocolViolation(f"Unsupported D2B model family: {specification.model_family}")


def _logit(probability: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(probability, dtype=float), 1e-9, 1.0 - 1e-9)
    return np.log(values / (1.0 - values))


def _chronological_calibration_split(
    frame: pd.DataFrame,
    horizon_candles: int,
    calibration_fraction: float,
    minimum_fit_rows: int,
    minimum_calibration_rows: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    n_rows = len(frame)
    calibration_rows = max(minimum_calibration_rows, int(np.floor(n_rows * calibration_fraction)))
    calibration_start = n_rows - calibration_rows
    fit_end = calibration_start - int(horizon_candles)
    if fit_end < minimum_fit_rows or calibration_start >= n_rows:
        raise ProtocolViolation("Insufficient rows for chronological training-only calibration.")
    return frame.iloc[:fit_end], frame.iloc[calibration_start:]


def _fit_calibrator(method: str, y: np.ndarray, probability: np.ndarray) -> Any:
    if method == "sigmoid":
        model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
        model.fit(_logit(probability).reshape(-1, 1), y.astype(int))
        return model
    if method == "isotonic":
        model = IsotonicRegression(out_of_bounds="clip")
        model.fit(np.asarray(probability, dtype=float), y.astype(float))
        return model
    if method == "none":
        return None
    raise ProtocolViolation(f"Unsupported calibration method: {method}")


def _apply_calibrator(method: str, calibrator: Any, probability: np.ndarray) -> np.ndarray:
    if method == "none":
        output = probability
    elif method == "sigmoid":
        output = calibrator.predict_proba(_logit(probability).reshape(-1, 1))[:, 1]
    elif method == "isotonic":
        output = calibrator.predict(np.asarray(probability, dtype=float))
    else:
        raise ProtocolViolation(f"Unsupported calibration method: {method}")
    return np.clip(np.asarray(output, dtype=float), 1e-9, 1.0 - 1e-9)


def _fit_probability_model(
    train: pd.DataFrame,
    test: pd.DataFrame,
    target_column: str,
    feature_columns: list[str],
    signal_columns: list[str],
    specification: StructuralPipelineSpecification,
    calibration_method: str,
    horizon_candles: int,
    calibration_fraction: float,
    minimum_fit_rows: int,
    minimum_calibration_rows: int,
    random_state: int,
) -> tuple[np.ndarray, int, int]:
    if train[target_column].nunique(dropna=True) < 2:
        raise ProtocolViolation("D2B direction target contains one class in training data.")

    if calibration_method == "none":
        model = _make_model(specification, feature_columns, signal_columns, random_state)
        model.fit(train[feature_columns], train[target_column].astype(int))
        probability = model.predict_proba(test[feature_columns])[:, 1]
        return np.clip(probability, 1e-9, 1.0 - 1e-9), len(train), 0

    fit_frame, calibration_frame = _chronological_calibration_split(
        train,
        horizon_candles=horizon_candles,
        calibration_fraction=calibration_fraction,
        minimum_fit_rows=minimum_fit_rows,
        minimum_calibration_rows=minimum_calibration_rows,
    )
    if fit_frame[target_column].nunique(dropna=True) < 2 or calibration_frame[target_column].nunique(dropna=True) < 2:
        raise ProtocolViolation("D2B calibration partitions require both direction classes.")
    model = _make_model(specification, feature_columns, signal_columns, random_state)
    model.fit(fit_frame[feature_columns], fit_frame[target_column].astype(int))
    calibration_probability = model.predict_proba(calibration_frame[feature_columns])[:, 1]
    calibrator = _fit_calibrator(
        calibration_method,
        calibration_frame[target_column].astype(int).to_numpy(),
        calibration_probability,
    )
    test_probability = model.predict_proba(test[feature_columns])[:, 1]
    return (
        _apply_calibrator(calibration_method, calibrator, test_probability),
        len(fit_frame),
        len(calibration_frame),
    )


def matched_pipeline_fold(
    baseline_features: pd.DataFrame,
    states: pd.DataFrame,
    signal_features: pd.DataFrame,
    target: pd.Series,
    future_return: pd.Series,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
    specification: StructuralPipelineSpecification,
    registry_payload: dict[str, Any],
    calibration_method: str = "none",
    horizon_candles: int = 1,
    calibration_fraction: float = 0.20,
    minimum_fit_rows: int = 120,
    minimum_calibration_rows: int = 60,
    random_state: int = 42,
) -> MatchedPipelineFoldResult:
    for frame in (baseline_features, states, signal_features, target, future_return):
        _require_chronological(frame)
    if calibration_method not in CALIBRATION_METHODS:
        raise ProtocolViolation(f"Unsupported D2B calibration method: {calibration_method}")

    benchmark_columns = [*BASELINE_FEATURES, *STATE_PROBABILITY_COLUMNS]
    selected_signal_columns = signal_feature_columns(signal_features, specification.regime_conditioned)
    candidate_columns = [*benchmark_columns, *selected_signal_columns]

    frame = (
        baseline_features.loc[:, BASELINE_FEATURES]
        .join(states[list(STATE_PROBABILITY_COLUMNS)], how="left")
        .join(signal_features[selected_signal_columns], how="left")
        .join(target.rename("target"), how="left")
        .join(future_return.rename("future_return"), how="left")
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    train = frame.loc[train_start:train_end]
    test = frame.loc[test_start:test_end]
    train = apply_training_window(train, specification.window_scheme, registry_payload)
    if len(train) < minimum_fit_rows + (minimum_calibration_rows if calibration_method != "none" else 0):
        raise ProtocolViolation("Insufficient complete D2B training observations.")
    if len(test) < 20:
        raise ProtocolViolation("Insufficient complete D2B test observations.")

    benchmark_probability, benchmark_fit_rows, benchmark_calibration_rows = _fit_probability_model(
        train=train,
        test=test,
        target_column="target",
        feature_columns=benchmark_columns,
        signal_columns=[],
        specification=specification,
        calibration_method=calibration_method,
        horizon_candles=horizon_candles,
        calibration_fraction=calibration_fraction,
        minimum_fit_rows=minimum_fit_rows,
        minimum_calibration_rows=minimum_calibration_rows,
        random_state=random_state,
    )
    candidate_probability, candidate_fit_rows, candidate_calibration_rows = _fit_probability_model(
        train=train,
        test=test,
        target_column="target",
        feature_columns=candidate_columns,
        signal_columns=selected_signal_columns,
        specification=specification,
        calibration_method=calibration_method,
        horizon_candles=horizon_candles,
        calibration_fraction=calibration_fraction,
        minimum_fit_rows=minimum_fit_rows,
        minimum_calibration_rows=minimum_calibration_rows,
        random_state=random_state,
    )
    realised = test["target"].astype(int).to_numpy()
    return MatchedPipelineFoldResult(
        benchmark_probability=benchmark_probability,
        candidate_probability=candidate_probability,
        realised=realised,
        timestamps=pd.DatetimeIndex(test.index),
        future_return=test["future_return"].to_numpy(dtype=float),
        benchmark_log_loss=float(log_loss(realised, benchmark_probability, labels=[0, 1])),
        candidate_log_loss=float(log_loss(realised, candidate_probability, labels=[0, 1])),
        incremental_log_loss=float(
            log_loss(realised, benchmark_probability, labels=[0, 1])
            - log_loss(realised, candidate_probability, labels=[0, 1])
        ),
        benchmark_brier=float(brier_score_loss(realised, benchmark_probability)),
        candidate_brier=float(brier_score_loss(realised, candidate_probability)),
        benchmark_ece=float(expected_calibration_error(realised, benchmark_probability)),
        candidate_ece=float(expected_calibration_error(realised, candidate_probability)),
        train_rows=int(len(train)),
        fit_rows=int(min(benchmark_fit_rows, candidate_fit_rows)),
        calibration_rows=int(min(benchmark_calibration_rows, candidate_calibration_rows)),
        test_rows=int(len(test)),
    )


def select_structural_pipeline(inner_results: pd.DataFrame) -> pd.Series:
    required = {
        "pipeline_id",
        "inner_fold",
        "incremental_log_loss",
        "benchmark_brier",
        "candidate_brier",
        "benchmark_ece",
        "candidate_ece",
        "complexity_rank",
    }
    missing = sorted(required.difference(inner_results.columns))
    if missing:
        raise ProtocolViolation("D2B structural results are missing: " + ", ".join(missing))
    grouped = (
        inner_results.groupby("pipeline_id", as_index=False)
        .agg(
            mean_incremental_log_loss=("incremental_log_loss", "mean"),
            standard_error_incremental_log_loss=(
                "incremental_log_loss",
                lambda values: float(pd.Series(values).std(ddof=1) / np.sqrt(len(values)))
                if len(values) > 1
                else 0.0,
            ),
            positive_inner_folds=("incremental_log_loss", lambda values: int((pd.Series(values) > 0.0).sum())),
            mean_brier_gap=("candidate_brier", "mean"),
            mean_benchmark_brier=("benchmark_brier", "mean"),
            mean_ece_gap=("candidate_ece", "mean"),
            mean_benchmark_ece=("benchmark_ece", "mean"),
            complexity_rank=("complexity_rank", "min"),
            inner_folds=("inner_fold", "nunique"),
        )
    )
    grouped["calibration_not_dominated"] = (
        grouped["mean_brier_gap"] <= grouped["mean_benchmark_brier"] + 0.0025
    ) & (grouped["mean_ece_gap"] <= grouped["mean_benchmark_ece"] + 0.01)
    eligible = grouped.loc[grouped["calibration_not_dominated"]].copy()
    if eligible.empty:
        eligible = grouped.copy()
    eligible = eligible.sort_values(
        [
            "mean_incremental_log_loss",
            "positive_inner_folds",
            "standard_error_incremental_log_loss",
            "complexity_rank",
            "pipeline_id",
        ],
        ascending=[False, False, True, True, True],
    )
    return eligible.iloc[0]


def select_calibration_method(calibration_results: pd.DataFrame) -> pd.Series:
    required = {
        "calibration_method",
        "inner_fold",
        "incremental_log_loss",
        "candidate_brier",
        "candidate_ece",
        "eligible_for_selection",
    }
    missing = sorted(required.difference(calibration_results.columns))
    if missing:
        raise ProtocolViolation("D2B calibration results are missing: " + ", ".join(missing))
    grouped = (
        calibration_results.groupby("calibration_method", as_index=False)
        .agg(
            mean_incremental_log_loss=("incremental_log_loss", "mean"),
            mean_candidate_brier=("candidate_brier", "mean"),
            mean_candidate_ece=("candidate_ece", "mean"),
            positive_inner_folds=("incremental_log_loss", lambda values: int((pd.Series(values) > 0.0).sum())),
            eligible_for_selection=("eligible_for_selection", "all"),
        )
    )
    eligible = grouped.loc[grouped["eligible_for_selection"]].copy()
    if eligible.empty:
        raise ProtocolViolation("D2B has no confirmatory calibration method eligible for selection.")
    # Predictive loss remains primary. Brier, ECE, and simpler no-calibration are tie breakers.
    eligible["calibration_complexity"] = eligible["calibration_method"].map({"none": 0, "sigmoid": 1}).fillna(9)
    eligible = eligible.sort_values(
        [
            "mean_incremental_log_loss",
            "positive_inner_folds",
            "mean_candidate_brier",
            "mean_candidate_ece",
            "calibration_complexity",
        ],
        ascending=[False, False, True, True, True],
    )
    return eligible.iloc[0]


def directional_policy_metrics(
    probability: Iterable[float],
    future_return: Iterable[float],
    threshold: float,
    one_way_cost_bps: float = 10.0,
) -> dict[str, float | int]:
    probability_array = np.asarray(list(probability), dtype=float)
    return_array = np.asarray(list(future_return), dtype=float)
    if len(probability_array) != len(return_array):
        raise ProtocolViolation("D2B probability and return arrays must align.")
    if threshold < 0.0 or threshold >= 0.5:
        raise ProtocolViolation("D2B abstention threshold must lie in [0, 0.5).")
    active = np.abs(probability_array - 0.5) > threshold
    position = np.where(active, np.where(probability_array > 0.5, 1.0, -1.0), 0.0)
    prior = np.concatenate([[0.0], position[:-1]])
    turnover = np.abs(position - prior)
    cost = turnover * (float(one_way_cost_bps) / 10000.0)
    net = position * return_array - cost
    active_net = net[active]
    return {
        "threshold": float(threshold),
        "coverage": float(active.mean()) if len(active) else 0.0,
        "nonzero_decisions": int(active.sum()),
        "mean_net_edge": float(active_net.mean()) if len(active_net) else 0.0,
        "cumulative_net_return": float(net.sum()),
        "turnover_units": float(turnover.sum()),
    }


def select_abstention_policy(policy_results: pd.DataFrame) -> pd.Series:
    required = {"threshold", "inner_fold", "coverage", "nonzero_decisions", "mean_net_edge"}
    missing = sorted(required.difference(policy_results.columns))
    if missing:
        raise ProtocolViolation("D2B policy results are missing: " + ", ".join(missing))
    grouped = (
        policy_results.groupby("threshold", as_index=False)
        .agg(
            mean_coverage=("coverage", "mean"),
            total_nonzero_decisions=("nonzero_decisions", "sum"),
            mean_net_edge=("mean_net_edge", "mean"),
            positive_inner_folds=("mean_net_edge", lambda values: int((pd.Series(values) > 0.0).sum())),
        )
    )
    eligible = grouped.loc[
        (grouped["mean_coverage"] >= 0.10) & (grouped["total_nonzero_decisions"] >= 100)
    ].copy()
    if eligible.empty:
        eligible = grouped.loc[grouped["threshold"] == 0.0].copy()
    eligible = eligible.sort_values(
        ["mean_net_edge", "positive_inner_folds", "mean_coverage", "threshold"],
        ascending=[False, False, False, True],
    )
    selected = eligible.iloc[0].copy()
    selected["governance_interpretation"] = "DEVELOPMENT_POLICY_SELECTION_NOT_ECONOMIC_GATE"
    return selected


def development_stability_summary(outer_results: pd.DataFrame) -> pd.DataFrame:
    required = {
        "signal_family",
        "horizon_candles",
        "outer_fold",
        "incremental_log_loss",
        "candidate_brier",
        "benchmark_brier",
    }
    missing = sorted(required.difference(outer_results.columns))
    if missing:
        raise ProtocolViolation("D2B outer results are missing: " + ", ".join(missing))
    records: list[dict[str, Any]] = []
    for (family, horizon), group in outer_results.groupby(["signal_family", "horizon_candles"]):
        gains = group["incremental_log_loss"].astype(float)
        positive = gains.clip(lower=0.0)
        total_positive = float(positive.sum())
        concentration = float(positive.max() / total_positive) if total_positive > 0.0 else 1.0
        records.append(
            {
                "signal_family": str(family),
                "horizon_candles": int(horizon),
                "horizon_hours": int(horizon) * 4,
                "outer_folds": int(group["outer_fold"].nunique()),
                "mean_incremental_log_loss": float(gains.mean()),
                "positive_outer_folds": int((gains > 0.0).sum()),
                "maximum_single_fold_share_of_positive_gain": concentration,
                "mean_candidate_brier": float(group["candidate_brier"].mean()),
                "mean_benchmark_brier": float(group["benchmark_brier"].mean()),
                "development_stability_pass": bool(
                    gains.mean() > 0.0
                    and int((gains > 0.0).sum()) >= 3
                    and concentration <= 0.60
                    and float(group["candidate_brier"].mean())
                    <= float(group["benchmark_brier"].mean()) + 0.0025
                ),
                "governance_interpretation": "DEVELOPMENT_GATE_ONLY_NO_HOLDOUT_EVIDENCE",
            }
        )
    return pd.DataFrame.from_records(records).sort_values(
        ["signal_family", "horizon_candles"]
    ).reset_index(drop=True)
