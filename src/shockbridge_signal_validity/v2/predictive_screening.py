from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .causal_features import BASELINE_FEATURES, build_registered_signal_features
from .contracts import ProtocolViolation
from .filtered_states import CausalFilteredStateEngine
from .signals import add_soft_state_interactions

STATE_PROBABILITY_COLUMNS = ("state_p_range", "state_p_trend", "state_p_stress")


@dataclass(frozen=True)
class ScreeningSpecification:
    signal_spec_id: str
    signal_family: str
    interpretation: str
    period: int
    lower_threshold: float | None = None
    upper_threshold: float | None = None
    standard_deviations: float | None = None


@dataclass(frozen=True)
class MatchedFoldResult:
    benchmark_log_loss: float
    candidate_log_loss: float
    incremental_log_loss: float
    benchmark_brier: float
    candidate_brier: float
    test_rows: int
    train_rows: int
    benchmark_probability: np.ndarray
    candidate_probability: np.ndarray
    realised: np.ndarray
    timestamps: pd.DatetimeIndex


def _require_chronological(frame: pd.DataFrame | pd.Series) -> None:
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise ProtocolViolation("D2 screening requires timezone-aware timestamps.")
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ProtocolViolation("D2 screening timestamps must be unique and chronological.")


def specification_from_row(row: pd.Series) -> ScreeningSpecification:
    family = str(row["signal_family"])
    if family == "rsi":
        identifier = (
            f"rsi-p{int(row['period'])}-l{int(float(row['lower_threshold']))}"
            f"-u{int(float(row['upper_threshold']))}-{row['interpretation']}"
        )
    elif family == "bollinger":
        identifier = (
            f"bollinger-p{int(row['period'])}-k{float(row['standard_deviations']):g}"
            f"-{row['interpretation']}"
        )
    else:
        raise ProtocolViolation(f"Unsupported D2 screening family: {family}")
    return ScreeningSpecification(
        signal_spec_id=identifier,
        signal_family=family,
        interpretation=str(row["interpretation"]),
        period=int(row["period"]),
        lower_threshold=None if pd.isna(row.get("lower_threshold")) else float(row["lower_threshold"]),
        upper_threshold=None if pd.isna(row.get("upper_threshold")) else float(row["upper_threshold"]),
        standard_deviations=None if pd.isna(row.get("standard_deviations")) else float(row["standard_deviations"]),
    )


def unique_signal_specifications(candidate_inventory: pd.DataFrame) -> list[ScreeningSpecification]:
    required = {
        "signal_family",
        "interpretation",
        "period",
        "lower_threshold",
        "upper_threshold",
        "standard_deviations",
    }
    missing = sorted(required.difference(candidate_inventory.columns))
    if missing:
        raise ProtocolViolation("Candidate inventory is missing: " + ", ".join(missing))
    columns = sorted(required)
    rows = candidate_inventory[columns].drop_duplicates().sort_values(columns, na_position="last")
    specs = [specification_from_row(row) for _, row in rows.iterrows()]
    identifiers = [spec.signal_spec_id for spec in specs]
    if len(identifiers) != len(set(identifiers)):
        raise ProtocolViolation("Signal specification identifiers are not unique.")
    return specs


def build_signal_block(
    close: pd.Series,
    specification: ScreeningSpecification,
    states: pd.DataFrame,
) -> pd.DataFrame:
    _require_chronological(close)
    _require_chronological(states)
    if not close.index.equals(states.index):
        raise ProtocolViolation("Signal and state frames must share the same timestamps.")
    features = build_registered_signal_features(
        close=close,
        signal_family=specification.signal_family,
        interpretation=specification.interpretation,
        period=specification.period,
        lower_threshold=specification.lower_threshold,
        upper_threshold=specification.upper_threshold,
        standard_deviations=specification.standard_deviations,
    )
    score_column = "rsi_signal_score" if specification.signal_family == "rsi" else "bb_signal_score"
    interactions = add_soft_state_interactions(features[score_column], states)
    renamed = features.add_prefix(f"{specification.signal_family}_")
    return renamed.join(interactions, how="left")


def fit_fold_state_probabilities(
    causal_features: pd.DataFrame,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    _require_chronological(causal_features)
    train = causal_features.loc[train_start:train_end].dropna()
    test = causal_features.loc[test_start:test_end].dropna()
    engine = CausalFilteredStateEngine().fit(train)
    train_probabilities = engine.training_probabilities_.copy()
    test_probabilities = engine.filter_forward(test)
    return train_probabilities, test_probabilities


def _fit_logistic(x: pd.DataFrame, y: pd.Series, random_state: int) -> Pipeline:
    if y.nunique(dropna=True) < 2:
        raise ProtocolViolation("Direction target contains only one class in training data.")
    model = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            (
                "logistic",
                LogisticRegression(
                    C=1.0,
                    solver="lbfgs",
                    max_iter=1000,
                    random_state=random_state,
                ),
            ),
        ]
    )
    model.fit(x, y.astype(int))
    return model


def expected_calibration_error(y_true: np.ndarray, probability: np.ndarray, bins: int = 10) -> float:
    if bins < 2:
        raise ProtocolViolation("At least two calibration bins are required.")
    probability = np.clip(np.asarray(probability, dtype=float), 1e-9, 1.0 - 1e-9)
    y_true = np.asarray(y_true, dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    value = 0.0
    for lower, upper in zip(edges[:-1], edges[1:]):
        mask = (probability >= lower) & (probability < upper if upper < 1.0 else probability <= upper)
        if mask.any():
            value += float(mask.mean()) * abs(float(y_true[mask].mean()) - float(probability[mask].mean()))
    return value


def matched_logistic_fold(
    baseline_features: pd.DataFrame,
    signal_features: pd.DataFrame,
    train_states: pd.DataFrame,
    test_states: pd.DataFrame,
    target: pd.Series,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
    random_state: int = 42,
) -> MatchedFoldResult:
    for frame in (baseline_features, signal_features, train_states, test_states, target):
        _require_chronological(frame)

    state_frame = pd.concat([train_states, test_states]).sort_index()
    combined = baseline_features.loc[:, BASELINE_FEATURES].join(state_frame[list(STATE_PROBABILITY_COLUMNS)])
    combined = combined.join(signal_features, how="left").join(target.rename("target"), how="left")
    candidate_columns = [column for column in combined.columns if column != "target"]
    benchmark_columns = [*BASELINE_FEATURES, *STATE_PROBABILITY_COLUMNS]
    matched = combined.loc[:, [*candidate_columns, "target"]].dropna()
    train = matched.loc[train_start:train_end]
    test = matched.loc[test_start:test_end]
    if len(train) < 120 or len(test) < 20:
        raise ProtocolViolation("Insufficient complete matched observations for D2 screening.")

    benchmark_model = _fit_logistic(train[benchmark_columns], train["target"], random_state)
    candidate_model = _fit_logistic(train[candidate_columns], train["target"], random_state)
    benchmark_probability = benchmark_model.predict_proba(test[benchmark_columns])[:, 1]
    candidate_probability = candidate_model.predict_proba(test[candidate_columns])[:, 1]
    realised = test["target"].astype(int).to_numpy()
    benchmark_loss = float(log_loss(realised, benchmark_probability, labels=[0, 1]))
    candidate_loss = float(log_loss(realised, candidate_probability, labels=[0, 1]))
    return MatchedFoldResult(
        benchmark_log_loss=benchmark_loss,
        candidate_log_loss=candidate_loss,
        incremental_log_loss=benchmark_loss - candidate_loss,
        benchmark_brier=float(brier_score_loss(realised, benchmark_probability)),
        candidate_brier=float(brier_score_loss(realised, candidate_probability)),
        test_rows=int(len(test)),
        train_rows=int(len(train)),
        benchmark_probability=benchmark_probability,
        candidate_probability=candidate_probability,
        realised=realised,
        timestamps=pd.DatetimeIndex(test.index),
    )


def select_screening_specification(inner_results: pd.DataFrame) -> pd.Series:
    required = {"signal_spec_id", "incremental_log_loss", "candidate_brier", "benchmark_brier", "inner_fold"}
    missing = sorted(required.difference(inner_results.columns))
    if missing:
        raise ProtocolViolation("Inner screening results are missing: " + ", ".join(missing))
    grouped = (
        inner_results.groupby("signal_spec_id", as_index=False)
        .agg(
            mean_incremental_log_loss=("incremental_log_loss", "mean"),
            standard_error_incremental_log_loss=("incremental_log_loss", lambda values: float(pd.Series(values).std(ddof=1) / np.sqrt(len(values))) if len(values) > 1 else 0.0),
            positive_inner_folds=("incremental_log_loss", lambda values: int((pd.Series(values) > 0.0).sum())),
            mean_candidate_brier=("candidate_brier", "mean"),
            mean_benchmark_brier=("benchmark_brier", "mean"),
            inner_folds=("inner_fold", "nunique"),
        )
    )
    grouped["calibration_not_dominated"] = grouped["mean_candidate_brier"] <= grouped["mean_benchmark_brier"] + 0.0025
    eligible = grouped.loc[grouped["calibration_not_dominated"]].copy()
    if eligible.empty:
        eligible = grouped.copy()
    eligible = eligible.sort_values(
        ["mean_incremental_log_loss", "positive_inner_folds", "standard_error_incremental_log_loss", "signal_spec_id"],
        ascending=[False, False, True, True],
    )
    return eligible.iloc[0]


def preliminary_gate_summary(outer_results: pd.DataFrame) -> pd.DataFrame:
    required = {"signal_family", "horizon_candles", "outer_fold", "incremental_log_loss"}
    missing = sorted(required.difference(outer_results.columns))
    if missing:
        raise ProtocolViolation("Outer screening results are missing: " + ", ".join(missing))
    records: list[dict[str, object]] = []
    for (family, horizon), group in outer_results.groupby(["signal_family", "horizon_candles"]):
        gains = group["incremental_log_loss"].astype(float)
        positive = gains.clip(lower=0.0)
        total_positive = float(positive.sum())
        concentration = float(positive.max() / total_positive) if total_positive > 0.0 else 1.0
        records.append(
            {
                "signal_family": family,
                "horizon_candles": int(horizon),
                "horizon_hours": int(horizon) * 4,
                "outer_folds": int(group["outer_fold"].nunique()),
                "mean_incremental_log_loss": float(gains.mean()),
                "positive_outer_folds": int((gains > 0.0).sum()),
                "maximum_single_fold_share_of_positive_gain": concentration,
                "screening_gate_pass": bool(gains.mean() > 0.0 and (gains > 0.0).sum() >= 3 and concentration <= 0.60),
                "governance_interpretation": "PRELIMINARY_SCREENING_ONLY_NOT_FINAL_GATE_2",
            }
        )
    return pd.DataFrame.from_records(records).sort_values(["signal_family", "horizon_candles"]).reset_index(drop=True)

@dataclass(frozen=True)
class BenchmarkScreeningFold:
    train_index: pd.DatetimeIndex
    test_index: pd.DatetimeIndex
    train_target: np.ndarray
    test_target: np.ndarray
    train_logit: np.ndarray
    test_logit: np.ndarray
    benchmark_probability: np.ndarray
    benchmark_log_loss: float
    benchmark_brier: float
    train_rows: int
    test_rows: int


def _logit(probability: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(probability, dtype=float), 1e-9, 1.0 - 1e-9)
    return np.log(values / (1.0 - values))


def _sigmoid(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    output = np.empty_like(values)
    positive = values >= 0.0
    output[positive] = 1.0 / (1.0 + np.exp(-values[positive]))
    exp_values = np.exp(values[~positive])
    output[~positive] = exp_values / (1.0 + exp_values)
    return output


def fit_benchmark_screening_fold(
    baseline_features: pd.DataFrame,
    train_states: pd.DataFrame,
    test_states: pd.DataFrame,
    target: pd.Series,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
    random_state: int = 42,
) -> BenchmarkScreeningFold:
    state_frame = pd.concat([train_states, test_states]).sort_index()
    frame = baseline_features.loc[:, BASELINE_FEATURES].join(
        state_frame[list(STATE_PROBABILITY_COLUMNS)]
    ).join(target.rename("target"), how="left").dropna()
    train = frame.loc[train_start:train_end]
    test = frame.loc[test_start:test_end]
    if len(train) < 120 or len(test) < 20:
        raise ProtocolViolation("Insufficient complete benchmark observations for D2A screening.")
    columns = [*BASELINE_FEATURES, *STATE_PROBABILITY_COLUMNS]
    model = _fit_logistic(train[columns], train["target"], random_state)
    train_probability = model.predict_proba(train[columns])[:, 1]
    test_probability = model.predict_proba(test[columns])[:, 1]
    train_target = train["target"].astype(int).to_numpy()
    test_target = test["target"].astype(int).to_numpy()
    return BenchmarkScreeningFold(
        train_index=pd.DatetimeIndex(train.index),
        test_index=pd.DatetimeIndex(test.index),
        train_target=train_target,
        test_target=test_target,
        train_logit=_logit(train_probability),
        test_logit=_logit(test_probability),
        benchmark_probability=test_probability,
        benchmark_log_loss=float(log_loss(test_target, test_probability, labels=[0, 1])),
        benchmark_brier=float(brier_score_loss(test_target, test_probability)),
        train_rows=int(len(train)),
        test_rows=int(len(test)),
    )


def screening_signal_columns(signal_features: pd.DataFrame, family: str) -> list[str]:
    if family == "rsi":
        preferred = [
            "rsi_rsi_signal_score",
            "rsi_rsi_signal_event",
            "rsi_rsi_extreme",
            "rsi_rsi_event_persistence",
        ]
    elif family == "bollinger":
        preferred = [
            "bollinger_bb_signal_score",
            "bollinger_bb_signal_event",
            "bollinger_bb_extreme",
            "bollinger_bb_event_persistence",
        ]
    else:
        raise ProtocolViolation(f"Unsupported screening family: {family}")
    preferred.extend(["signal_x_range", "signal_x_trend", "signal_x_stress"])
    columns = [column for column in preferred if column in signal_features]
    if len(columns) < 4:
        raise ProtocolViolation("D2A signal block is incomplete.")
    return columns


def _fit_offset_ridge_logistic(
    x: np.ndarray,
    y: np.ndarray,
    offset: np.ndarray,
    ridge: float = 1.0,
    max_iter: int = 1,
    tolerance: float = 1e-8,
) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    offset = np.asarray(offset, dtype=float)
    design = np.column_stack([np.ones(len(x)), x])
    beta = np.zeros(design.shape[1], dtype=float)
    penalty = np.eye(design.shape[1], dtype=float) * float(ridge)
    penalty[0, 0] = 0.0
    for _ in range(max_iter):
        probability = _sigmoid(offset + design @ beta)
        weights = np.clip(probability * (1.0 - probability), 1e-6, None)
        gradient = design.T @ (y - probability) - penalty @ beta
        hessian = (design.T * weights) @ design + penalty
        step = np.linalg.solve(hessian, gradient)
        beta += step
        if float(np.max(np.abs(step))) <= tolerance:
            break
    return beta


def offset_signal_screening_fold(
    benchmark: BenchmarkScreeningFold,
    signal_features: pd.DataFrame,
    family: str,
    ridge: float = 1.0,
) -> MatchedFoldResult:
    columns = screening_signal_columns(signal_features, family)
    train = signal_features.reindex(benchmark.train_index)[columns]
    test = signal_features.reindex(benchmark.test_index)[columns]
    if train.isna().any().any() or test.isna().any().any():
        raise ProtocolViolation("Signal block is incomplete on the common D2A benchmark sample.")
    location = train.mean(axis=0)
    scale = train.std(axis=0, ddof=0).replace(0.0, 1.0)
    x_train = ((train - location) / scale).to_numpy(dtype=float)
    x_test = ((test - location) / scale).to_numpy(dtype=float)
    beta = _fit_offset_ridge_logistic(
        x=x_train,
        y=benchmark.train_target,
        offset=benchmark.train_logit,
        ridge=ridge,
    )
    candidate_probability = _sigmoid(
        benchmark.test_logit
        + np.column_stack([np.ones(len(x_test)), x_test]) @ beta
    )
    candidate_loss = float(
        log_loss(benchmark.test_target, candidate_probability, labels=[0, 1])
    )
    return MatchedFoldResult(
        benchmark_log_loss=benchmark.benchmark_log_loss,
        candidate_log_loss=candidate_loss,
        incremental_log_loss=benchmark.benchmark_log_loss - candidate_loss,
        benchmark_brier=benchmark.benchmark_brier,
        candidate_brier=float(
            brier_score_loss(benchmark.test_target, candidate_probability)
        ),
        test_rows=benchmark.test_rows,
        train_rows=benchmark.train_rows,
        benchmark_probability=benchmark.benchmark_probability,
        candidate_probability=candidate_probability,
        realised=benchmark.test_target,
        timestamps=benchmark.test_index,
    )


def fit_common_benchmark_screening_fold(
    baseline_features: pd.DataFrame,
    train_states: pd.DataFrame,
    test_states: pd.DataFrame,
    target: pd.Series,
    signal_scores: pd.DataFrame,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
    random_state: int = 42,
) -> BenchmarkScreeningFold:
    state_frame = pd.concat([train_states, test_states]).sort_index()
    frame = (
        baseline_features.loc[:, BASELINE_FEATURES]
        .join(state_frame[list(STATE_PROBABILITY_COLUMNS)])
        .join(target.rename("target"), how="left")
        .join(signal_scores, how="left")
        .dropna()
    )
    train = frame.loc[train_start:train_end]
    test = frame.loc[test_start:test_end]
    if len(train) < 120 or len(test) < 20:
        raise ProtocolViolation("Insufficient common complete observations for D2A screening.")
    columns = [*BASELINE_FEATURES, *STATE_PROBABILITY_COLUMNS]
    model = _fit_logistic(train[columns], train["target"], random_state)
    train_probability = model.predict_proba(train[columns])[:, 1]
    test_probability = model.predict_proba(test[columns])[:, 1]
    train_target = train["target"].astype(int).to_numpy()
    test_target = test["target"].astype(int).to_numpy()
    return BenchmarkScreeningFold(
        train_index=pd.DatetimeIndex(train.index),
        test_index=pd.DatetimeIndex(test.index),
        train_target=train_target,
        test_target=test_target,
        train_logit=_logit(train_probability),
        test_logit=_logit(test_probability),
        benchmark_probability=test_probability,
        benchmark_log_loss=float(log_loss(test_target, test_probability, labels=[0, 1])),
        benchmark_brier=float(brier_score_loss(test_target, test_probability)),
        train_rows=int(len(train)),
        test_rows=int(len(test)),
    )


def scalar_state_score_screening_fold(
    benchmark: BenchmarkScreeningFold,
    signal_score: pd.Series,
    states: pd.DataFrame,
    ridge: float = 1.0,
) -> MatchedFoldResult:
    train_score = pd.to_numeric(signal_score.reindex(benchmark.train_index), errors="coerce")
    test_score = pd.to_numeric(signal_score.reindex(benchmark.test_index), errors="coerce")
    train_states = states.reindex(benchmark.train_index)[list(STATE_PROBABILITY_COLUMNS)]
    test_states = states.reindex(benchmark.test_index)[list(STATE_PROBABILITY_COLUMNS)]
    if train_score.isna().any() or test_score.isna().any() or train_states.isna().any().any() or test_states.isna().any().any():
        raise ProtocolViolation("D2A score or state inputs are incomplete on the common sample.")
    train_score_values = train_score.to_numpy(dtype=float)
    test_score_values = test_score.to_numpy(dtype=float)
    train_x = np.column_stack(
        [
            train_score_values,
            train_score_values * train_states["state_p_range"].to_numpy(dtype=float),
            train_score_values * train_states["state_p_trend"].to_numpy(dtype=float),
            train_score_values * train_states["state_p_stress"].to_numpy(dtype=float),
        ]
    )
    test_x = np.column_stack(
        [
            test_score_values,
            test_score_values * test_states["state_p_range"].to_numpy(dtype=float),
            test_score_values * test_states["state_p_trend"].to_numpy(dtype=float),
            test_score_values * test_states["state_p_stress"].to_numpy(dtype=float),
        ]
    )
    location = train_x.mean(axis=0)
    scale = train_x.std(axis=0, ddof=0)
    scale[scale == 0.0] = 1.0
    train_x = (train_x - location) / scale
    test_x = (test_x - location) / scale
    beta = _fit_offset_ridge_logistic(
        x=train_x,
        y=benchmark.train_target,
        offset=benchmark.train_logit,
        ridge=ridge,
        max_iter=1,
    )
    candidate_probability = _sigmoid(
        benchmark.test_logit
        + np.column_stack([np.ones(len(test_x)), test_x]) @ beta
    )
    candidate_loss = float(log_loss(benchmark.test_target, candidate_probability, labels=[0, 1]))
    return MatchedFoldResult(
        benchmark_log_loss=benchmark.benchmark_log_loss,
        candidate_log_loss=candidate_loss,
        incremental_log_loss=benchmark.benchmark_log_loss - candidate_loss,
        benchmark_brier=benchmark.benchmark_brier,
        candidate_brier=float(brier_score_loss(benchmark.test_target, candidate_probability)),
        test_rows=benchmark.test_rows,
        train_rows=benchmark.train_rows,
        benchmark_probability=benchmark.benchmark_probability,
        candidate_probability=candidate_probability,
        realised=benchmark.test_target,
        timestamps=benchmark.test_index,
    )
