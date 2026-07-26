from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from .data_contract import stable_frame_hash, stable_mapping_hash
from ..regimes import FilteredRegimeModel


PANIC_REGIME_SCHEMA_VERSION = "v3.panic-regime-engine.v1"
REGISTERED_MODEL_IDS = (
    "V2_TRANSPARENT_STATE_CHALLENGER_V1",
    "MONOTONE_MECHANISM_SCORE_V1",
    "CAUSAL_GAUSSIAN_HMM_V1",
)
FAMILY_ORDER = (
    "spectral",
    "network",
    "liquidity",
    "funding",
    "volatility",
    "downside",
)
STRUCTURAL_FAMILIES = frozenset({"spectral", "network"})
PLUMBING_FAMILIES = frozenset({"liquidity", "funding"})
PRICE_RISK_FAMILIES = frozenset({"volatility", "downside"})


class PanicRegimeError(ValueError):
    """Raised when Gate V3-3B cannot satisfy its causal regime contract."""


@dataclass(frozen=True)
class PanicRegimeConfig:
    dependence_window: int
    reference_series_id: str
    minimum_prior_observations: int = 250
    scaling_refit_interval: int = 30
    minimum_available_mechanism_families: int = 4
    minimum_valid_feature_fraction: float = 0.50
    minimum_features_per_family: int = 2
    monotone_logistic_slope: float = 6.0
    monotone_ewma_alpha: float = 0.35
    challenger_minimum_history: int = 250
    hmm_minimum_history: int = 500
    hmm_refit_interval: int = 30
    hmm_max_iter: int = 20
    hmm_tolerance: float = 1e-6
    covariance_floor: float = 1e-4
    transition_smoothing: float = 1.0
    minimum_state_occupancy_fraction: float = 0.05
    minimum_state_occupancy_count: int = 20
    random_seed: int = 1729

    def __post_init__(self) -> None:
        if self.dependence_window < 3:
            raise PanicRegimeError("dependence_window must be >= 3.")
        if not str(self.reference_series_id).strip() or "@" not in self.reference_series_id:
            raise PanicRegimeError(
                "reference_series_id must use the stable 'asset@venue' identifier."
            )
        if self.minimum_prior_observations < 5:
            raise PanicRegimeError("minimum_prior_observations must be >= 5.")
        if self.scaling_refit_interval < 1:
            raise PanicRegimeError("scaling_refit_interval must be >= 1.")
        if not 0.0 < self.minimum_valid_feature_fraction <= 1.0:
            raise PanicRegimeError(
                "minimum_valid_feature_fraction must be in (0, 1]."
            )
        if not 1 <= self.minimum_available_mechanism_families <= len(FAMILY_ORDER):
            raise PanicRegimeError(
                "minimum_available_mechanism_families is outside the registered family set."
            )
        if self.minimum_features_per_family < 1:
            raise PanicRegimeError("minimum_features_per_family must be >= 1.")
        if self.monotone_logistic_slope <= 0.0:
            raise PanicRegimeError("monotone_logistic_slope must be positive.")
        if not 0.0 < self.monotone_ewma_alpha <= 1.0:
            raise PanicRegimeError("monotone_ewma_alpha must be in (0, 1].")
        if self.challenger_minimum_history < 20:
            raise PanicRegimeError("challenger_minimum_history must be >= 20.")
        if self.hmm_minimum_history < 20:
            raise PanicRegimeError("hmm_minimum_history must be >= 20.")
        if self.hmm_refit_interval < 1 or self.hmm_max_iter < 1:
            raise PanicRegimeError(
                "hmm_refit_interval and hmm_max_iter must be positive."
            )
        if self.hmm_tolerance <= 0.0 or self.covariance_floor <= 0.0:
            raise PanicRegimeError(
                "hmm_tolerance and covariance_floor must be positive."
            )
        if self.transition_smoothing <= 0.0:
            raise PanicRegimeError("transition_smoothing must be positive.")
        if not 0.0 < self.minimum_state_occupancy_fraction < 0.5:
            raise PanicRegimeError(
                "minimum_state_occupancy_fraction must be in (0, 0.5)."
            )
        if self.minimum_state_occupancy_count < 1:
            raise PanicRegimeError("minimum_state_occupancy_count must be positive.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PanicRegimeManifest:
    schema_version: str
    market_structure_sha256: str
    causal_series_sha256: str
    configuration_sha256: str
    mechanism_scores_sha256: str
    probability_output_sha256: str
    dependence_window: int
    reference_series_id: str
    model_ids: tuple[str, ...]
    rows: int
    timestamps: int
    automatic_model_selection_performed: bool = False
    automatic_ensemble_performed: bool = False
    uncertainty_status: str = "PENDING_V3_3C"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def manifest_sha256(self) -> str:
        payload = json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return sha256(payload).hexdigest()


@dataclass(frozen=True)
class PanicRegimeFeatureFrame:
    probabilities: pd.DataFrame
    mechanism_scores: pd.DataFrame
    manifest: PanicRegimeManifest
    diagnostics: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class _FeatureRule:
    family: str
    output_name: str
    source: str
    column: str
    direction: float = 1.0
    transform: str = "identity"


_FIXED_RULES: tuple[_FeatureRule, ...] = (
    _FeatureRule("spectral", "dominant_eigenvalue_share", "market", "dominant_eigenvalue_share"),
    _FeatureRule("spectral", "normalized_eigenvalue_gap", "market", "eigenvalue_gap"),
    _FeatureRule("spectral", "participation_ratio", "market", "participation_ratio", -1.0),
    _FeatureRule("spectral", "spectral_entropy", "market", "spectral_entropy", -1.0),
    _FeatureRule("spectral", "first_eigenvector_concentration", "market", "first_eigenvector_concentration"),
    _FeatureRule("spectral", "spectral_instability", "market", "eigenvector_instability"),
    _FeatureRule("network", "network_density", "market", "network_density"),
    _FeatureRule("network", "network_average_clustering", "market", "network_average_clustering"),
    _FeatureRule("network", "network_modularity", "market", "network_modularity", -1.0),
    _FeatureRule("network", "network_connectivity_share", "market", "network_connectivity_share"),
    _FeatureRule("network", "betweenness_centrality_concentration", "market", "betweenness_centrality_concentration"),
    _FeatureRule("network", "eigenvector_centrality_concentration", "market", "eigenvector_centrality_concentration"),
    _FeatureRule("network", "mst_total_distance", "market", "mst_total_distance", -1.0),
    _FeatureRule("liquidity", "bid_ask_spread_stress", "series", "bid_ask_spread_z"),
    _FeatureRule("liquidity", "order_book_depth_stress", "series", "order_book_depth_log_change", -1.0),
    _FeatureRule("liquidity", "order_book_imbalance_magnitude", "series", "order_book_imbalance", 1.0, "absolute"),
    _FeatureRule("liquidity", "cross_venue_price_dispersion", "series", "cross_venue_price_dispersion"),
    _FeatureRule("funding", "funding_rate_stress", "series", "funding_stress_z"),
    _FeatureRule("funding", "open_interest_dislocation", "series", "open_interest_log_change", 1.0, "absolute"),
    _FeatureRule("funding", "liquidation_intensity", "series", "liquidation_intensity"),
    _FeatureRule("funding", "net_liquidation_pressure_magnitude", "series", "net_liquidation_pressure", 1.0, "absolute"),
    _FeatureRule("volatility", "downside_semivariance", "series", "downside_semivariance"),
    _FeatureRule("volatility", "abnormal_volume_score", "series", "abnormal_volume_z"),
    _FeatureRule("downside", "drawdown_magnitude", "series", "drawdown", -1.0),
    _FeatureRule("downside", "drawdown_velocity", "series", "drawdown_velocity", -1.0),
    _FeatureRule("downside", "downside_return_acceleration", "series", "downside_return_acceleration", -1.0),
)


def _stable_probability_frame_hash(frame: pd.DataFrame) -> str:
    ordered = frame.sort_values(["timestamp", "model_id"], kind="mergesort")
    return stable_frame_hash(ordered.reset_index(drop=True))


def _validate_market_structure(
    frame: pd.DataFrame,
    dependence_window: int,
) -> pd.DataFrame:
    required = {"timestamp", "window", "eligibility_status"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise PanicRegimeError(
            "Market-structure input is missing columns: " + ", ".join(missing)
        )
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    if data["timestamp"].isna().any():
        raise PanicRegimeError("Market-structure timestamps must be valid UTC values.")
    data["window"] = pd.to_numeric(data["window"], errors="coerce")
    if data["window"].isna().any():
        raise PanicRegimeError("Market-structure window values must be numeric.")
    selected = data.loc[data["window"].astype(int) == int(dependence_window)].copy()
    if selected.empty:
        raise PanicRegimeError(
            f"No market-structure rows exist for dependence_window={dependence_window}."
        )
    if selected["timestamp"].duplicated().any():
        raise PanicRegimeError(
            "Market-structure input contains duplicate timestamps for the selected window."
        )
    return selected.sort_values("timestamp", kind="mergesort").reset_index(drop=True)


def _validate_series_features(
    frame: pd.DataFrame,
    reference_series_id: str,
) -> pd.DataFrame:
    required = {"timestamp", "series_id", "log_return_1"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise PanicRegimeError(
            "Causal-series input is missing columns: " + ", ".join(missing)
        )
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    if data["timestamp"].isna().any():
        raise PanicRegimeError("Causal-series timestamps must be valid UTC values.")
    data["series_id"] = data["series_id"].astype("string").str.strip()
    if data.duplicated(["timestamp", "series_id"]).any():
        raise PanicRegimeError(
            "Causal-series input contains duplicate timestamp/series_id keys."
        )
    if reference_series_id not in set(data["series_id"].dropna().astype(str)):
        raise PanicRegimeError(
            f"Reference series is absent from the causal-series input: {reference_series_id}"
        )
    return data.sort_values(["timestamp", "series_id"], kind="mergesort").reset_index(
        drop=True
    )


def _transform(values: pd.Series, transform: str) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce").astype(float)
    if transform == "identity":
        return numeric
    if transform == "absolute":
        return numeric.abs()
    raise PanicRegimeError(f"Unknown feature transform: {transform}")


def _expanded_rules(
    market_columns: Sequence[str],
    series_columns: Sequence[str],
) -> tuple[_FeatureRule, ...]:
    rules = [
        rule
        for rule in _FIXED_RULES
        if rule.column in (market_columns if rule.source == "market" else series_columns)
    ]
    for column in sorted(
        value for value in series_columns if str(value).startswith("realised_volatility_")
    ):
        rules.append(
            _FeatureRule(
                "volatility",
                str(column),
                "series",
                str(column),
            )
        )
    return tuple(rules)


def _build_directed_raw_features(
    market: pd.DataFrame,
    series: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, list[str]], dict[str, dict[str, Any]]]:
    rules = _expanded_rules(market.columns, series.columns)
    timestamps = market[["timestamp"]].copy()
    output = timestamps.copy()
    family_columns: dict[str, list[str]] = {family: [] for family in FAMILY_ORDER}
    feature_registry: dict[str, dict[str, Any]] = {}

    for rule in rules:
        feature_name = f"{rule.family}__{rule.output_name}"
        if rule.source == "market":
            values = _transform(market[rule.column], rule.transform) * rule.direction
            values = values.where(market["eligibility_status"].eq("ELIGIBLE"))
            output[feature_name] = values.to_numpy(dtype=float)
        else:
            transformed = _transform(series[rule.column], rule.transform) * rule.direction
            aggregated = (
                pd.DataFrame(
                    {
                        "timestamp": series["timestamp"],
                        "value": transformed,
                    }
                )
                .groupby("timestamp", sort=True)["value"]
                .median()
            )
            output[feature_name] = output["timestamp"].map(aggregated).astype(float)
        family_columns[rule.family].append(feature_name)
        feature_registry[feature_name] = {
            "family": rule.family,
            "source": rule.source,
            "source_column": rule.column,
            "direction": rule.direction,
            "transform": rule.transform,
            "cross_sectional_aggregation": (
                None if rule.source == "market" else "median"
            ),
        }

    return output, family_columns, feature_registry


def _expanding_robust_feature_scores(
    directed_raw: pd.DataFrame,
    feature_columns: Sequence[str],
    *,
    minimum_prior_observations: int,
    refit_interval: int,
) -> pd.DataFrame:
    values = directed_raw[list(feature_columns)].to_numpy(dtype=float)
    scores = np.full_like(values, np.nan, dtype=float)
    location = np.full(values.shape[1], np.nan, dtype=float)
    scale = np.full(values.shape[1], np.nan, dtype=float)
    valid_parameter = np.zeros(values.shape[1], dtype=bool)

    for index in range(len(values)):
        if index >= minimum_prior_observations and (
            index == minimum_prior_observations
            or (index - minimum_prior_observations) % refit_interval == 0
        ):
            prefix = values[:index]
            counts = np.isfinite(prefix).sum(axis=0)
            with np.errstate(all="ignore"):
                location = np.nanmedian(prefix, axis=0)
                absolute_deviation = np.abs(prefix - location)
                scale = 1.4826 * np.nanmedian(absolute_deviation, axis=0)
            valid_parameter = (
                (counts >= minimum_prior_observations)
                & np.isfinite(location)
                & np.isfinite(scale)
                & (scale > 1e-12)
            )

        current = values[index]
        eligible = valid_parameter & np.isfinite(current)
        if not eligible.any():
            continue
        z = np.full(values.shape[1], np.nan, dtype=float)
        z[eligible] = (current[eligible] - location[eligible]) / scale[eligible]
        z[eligible] = np.clip(z[eligible], -5.0, 5.0)
        scores[index, eligible] = 1.0 / (1.0 + np.exp(-z[eligible]))

    result = directed_raw[["timestamp"]].copy()
    for position, column in enumerate(feature_columns):
        result[f"{column}__score"] = scores[:, position]
    return result


def _build_mechanism_scores(
    directed_raw: pd.DataFrame,
    family_columns: Mapping[str, Sequence[str]],
    config: PanicRegimeConfig,
) -> pd.DataFrame:
    feature_columns = [
        column
        for family in FAMILY_ORDER
        for column in family_columns.get(family, ())
    ]
    if not feature_columns:
        raise PanicRegimeError("No registered mechanism features are available.")
    scored = _expanding_robust_feature_scores(
        directed_raw,
        feature_columns,
        minimum_prior_observations=config.minimum_prior_observations,
        refit_interval=config.scaling_refit_interval,
    )
    output = scored.copy()
    for family in FAMILY_ORDER:
        columns = [f"{column}__score" for column in family_columns.get(family, ())]
        family_score_column = f"{family}_score"
        family_count_column = f"{family}_valid_feature_count"
        family_registered_column = f"{family}_registered_feature_count"
        if len(columns) < config.minimum_features_per_family:
            output[family_score_column] = np.nan
            output[family_count_column] = 0
            output[family_registered_column] = len(columns)
            continue
        values = output[columns]
        valid_count = values.notna().sum(axis=1)
        required = max(
            config.minimum_features_per_family,
            int(np.ceil(len(columns) * config.minimum_valid_feature_fraction)),
        )
        family_score = values.median(axis=1, skipna=True)
        output[family_score_column] = family_score.where(valid_count >= required)
        output[family_count_column] = valid_count.astype(int)
        output[family_registered_column] = len(columns)

    family_score_columns = [f"{family}_score" for family in FAMILY_ORDER]
    available = output[family_score_columns].notna()
    output["available_mechanism_count"] = available.sum(axis=1).astype(int)
    structural = available[[f"{family}_score" for family in STRUCTURAL_FAMILIES]].any(axis=1)
    plumbing = available[[f"{family}_score" for family in PLUMBING_FAMILIES]].any(axis=1)
    price_risk = available[[f"{family}_score" for family in PRICE_RISK_FAMILIES]].any(axis=1)
    sufficient = (
        (output["available_mechanism_count"] >= config.minimum_available_mechanism_families)
        & structural
        & plumbing
        & price_risk
    )
    output["structural_evidence_available"] = structural
    output["plumbing_evidence_available"] = plumbing
    output["price_risk_evidence_available"] = price_risk
    output["evidence_sufficiency"] = np.where(
        sufficient,
        "SUFFICIENT",
        "INSUFFICIENT_MECHANISM_EVIDENCE",
    )
    output["composite_mechanism_score"] = output[family_score_columns].mean(
        axis=1, skipna=True
    ).where(sufficient)
    return output


def _operational_state(probability: float | None, sufficient: bool) -> str:
    if not sufficient or probability is None or not np.isfinite(probability):
        return "INSUFFICIENT_MECHANISM_EVIDENCE"
    value = float(probability)
    if value < 0.25:
        return "LOW_PANIC_CONSISTENCY"
    if value < 0.50:
        return "STRESS_BUILDING"
    if value < 0.75:
        return "TRANSMISSION_ESCALATION"
    return "PANIC_CONSISTENT_REGIME"


def _monotone_probability_frame(
    mechanism: pd.DataFrame,
    config: PanicRegimeConfig,
) -> pd.DataFrame:
    composite = mechanism["composite_mechanism_score"].to_numpy(dtype=float)
    sufficient = mechanism["evidence_sufficiency"].eq("SUFFICIENT").to_numpy()
    raw = np.full(len(mechanism), np.nan, dtype=float)
    valid = sufficient & np.isfinite(composite)
    raw[valid] = 1.0 / (
        1.0
        + np.exp(
            -config.monotone_logistic_slope
            * (composite[valid] - 0.5)
        )
    )
    filtered = np.full(len(raw), np.nan, dtype=float)
    previous: float | None = None
    for index, value in enumerate(raw):
        if not np.isfinite(value):
            continue
        previous = (
            float(value)
            if previous is None
            else (
                config.monotone_ewma_alpha * float(value)
                + (1.0 - config.monotone_ewma_alpha) * previous
            )
        )
        filtered[index] = previous

    output = pd.DataFrame(
        {
            "timestamp": mechanism["timestamp"],
            "model_id": "MONOTONE_MECHANISM_SCORE_V1",
            "raw_probability": raw,
            "filtered_probability": filtered,
            "lower_95": np.nan,
            "upper_95": np.nan,
            "p_range": np.nan,
            "p_trend": np.nan,
            "p_stress": np.nan,
            "operational_state": [
                _operational_state(
                    None if not np.isfinite(filtered[index]) else float(filtered[index]),
                    bool(sufficient[index]),
                )
                for index in range(len(filtered))
            ],
            "available_mechanism_count": mechanism[
                "available_mechanism_count"
            ].to_numpy(dtype=int),
            "evidence_sufficiency": mechanism[
                "evidence_sufficiency"
            ].astype(str),
            "model_validity": np.where(
                valid,
                "VALID_IMPLEMENTATION_PROBABILITY_UNCERTAINTY_PENDING",
                "INSUFFICIENT_MECHANISM_EVIDENCE",
            ),
            "panic_probability_authorized": True,
            "uncertainty_status": "PENDING_V3_3C",
        }
    )
    return output


def _transparent_challenger_frame(
    series: pd.DataFrame,
    timestamps: pd.Series,
    mechanism: pd.DataFrame,
    config: PanicRegimeConfig,
) -> pd.DataFrame:
    reference = series.loc[
        series["series_id"].astype(str) == config.reference_series_id,
        ["timestamp", "log_return_1"],
    ].copy()
    reference = reference.sort_values("timestamp", kind="mergesort")
    returns = pd.to_numeric(reference["log_return_1"], errors="coerce").astype(float)
    reference["sol_ret_1"] = returns
    reference["vol_20"] = returns.rolling(20, min_periods=20).std(ddof=1)
    reference["trend_12"] = returns.rolling(12, min_periods=12).sum()
    reference = (
        pd.DataFrame({"timestamp": timestamps})
        .merge(
            reference[["timestamp", "sol_ret_1", "vol_20", "trend_12"]],
            on="timestamp",
            how="left",
            sort=True,
        )
        .sort_values("timestamp", kind="mergesort")
        .reset_index(drop=True)
    )

    probabilities = pd.DataFrame(
        {
            "timestamp": reference["timestamp"],
            "model_id": "V2_TRANSPARENT_STATE_CHALLENGER_V1",
            "raw_probability": np.nan,
            "filtered_probability": np.nan,
            "lower_95": np.nan,
            "upper_95": np.nan,
            "p_range": np.nan,
            "p_trend": np.nan,
            "p_stress": np.nan,
            "operational_state": "NOT_AUTHORIZED_FOR_PANIC",
            "available_mechanism_count": mechanism[
                "available_mechanism_count"
            ].to_numpy(dtype=int),
            "evidence_sufficiency": mechanism[
                "evidence_sufficiency"
            ].astype(str),
            "model_validity": "TRAINING_WARMUP",
            "panic_probability_authorized": False,
            "uncertainty_status": "NOT_APPLICABLE",
        }
    )
    complete = reference[["sol_ret_1", "vol_20", "trend_12"]].notna().all(axis=1)
    complete_positions = np.flatnonzero(complete.to_numpy())
    if len(complete_positions) <= config.challenger_minimum_history:
        probabilities["model_validity"] = "INSUFFICIENT_CHALLENGER_HISTORY"
        return probabilities

    train_positions = complete_positions[: config.challenger_minimum_history]
    future_positions = complete_positions[config.challenger_minimum_history :]
    train = reference.loc[
        train_positions,
        ["sol_ret_1", "vol_20", "trend_12"],
    ]
    if len(future_positions):
        model = FilteredRegimeModel(random_state=config.random_seed).fit(train)
        future = reference.loc[
            future_positions,
            ["sol_ret_1", "vol_20", "trend_12"],
        ]
        filtered = model.filter(future)
        probabilities.loc[future_positions, "p_range"] = filtered[
            "latent_prob_range"
        ].to_numpy(dtype=float)
        probabilities.loc[future_positions, "p_trend"] = filtered[
            "latent_prob_trend"
        ].to_numpy(dtype=float)
        probabilities.loc[future_positions, "p_stress"] = filtered[
            "latent_prob_stress"
        ].to_numpy(dtype=float)
        probabilities.loc[future_positions, "model_validity"] = (
            "VALID_TRANSPARENT_CHALLENGER"
        )
    probabilities.loc[train_positions, "model_validity"] = "TRAINING_WARMUP"
    return probabilities


def _emission_likelihood(
    observation: np.ndarray,
    means: np.ndarray,
    variances: np.ndarray,
    *,
    neutral: bool,
) -> np.ndarray:
    if neutral:
        return np.ones(2, dtype=float)
    observed = np.isfinite(observation)
    if not observed.any():
        return np.ones(2, dtype=float)
    log_probabilities = np.empty(2, dtype=float)
    for state in range(2):
        variance = variances[state, observed]
        difference = observation[observed] - means[state, observed]
        log_probabilities[state] = -0.5 * float(
            np.sum(
                np.log(2.0 * np.pi * variance)
                + (difference**2) / variance
            )
        )
    maximum = float(np.max(log_probabilities))
    return np.exp(log_probabilities - maximum)


def _forward_backward(
    values: np.ndarray,
    sufficient: np.ndarray,
    initial: np.ndarray,
    transition: np.ndarray,
    means: np.ndarray,
    variances: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, float]:
    rows = len(values)
    emissions = np.vstack(
        [
            _emission_likelihood(
                values[index],
                means,
                variances,
                neutral=not bool(sufficient[index]),
            )
            for index in range(rows)
        ]
    )
    alpha = np.empty((rows, 2), dtype=float)
    scales = np.empty(rows, dtype=float)
    current = initial * emissions[0]
    scales[0] = max(float(current.sum()), 1e-300)
    alpha[0] = current / scales[0]
    for index in range(1, rows):
        current = (alpha[index - 1] @ transition) * emissions[index]
        scales[index] = max(float(current.sum()), 1e-300)
        alpha[index] = current / scales[index]

    beta = np.ones((rows, 2), dtype=float)
    for index in range(rows - 2, -1, -1):
        beta[index] = (
            transition
            @ (emissions[index + 1] * beta[index + 1])
        ) / scales[index + 1]
    gamma = alpha * beta
    gamma /= np.clip(gamma.sum(axis=1, keepdims=True), 1e-300, None)

    xi_sum = np.zeros((2, 2), dtype=float)
    for index in range(rows - 1):
        numerator = (
            alpha[index, :, None]
            * transition
            * (emissions[index + 1] * beta[index + 1])[None, :]
        )
        denominator = float(numerator.sum())
        if denominator > 0.0:
            xi_sum += numerator / denominator
    log_likelihood = float(np.log(scales).sum())
    return gamma, xi_sum, log_likelihood


def _initialize_hmm(
    values: np.ndarray,
    sufficient: np.ndarray,
    covariance_floor: float,
    transition_smoothing: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    eligible = values[sufficient]
    if len(eligible) < 2:
        raise PanicRegimeError("HMM initialization has insufficient eligible observations.")
    composite = np.nanmean(eligible, axis=1)
    threshold = float(np.nanmedian(composite))
    labels = (composite > threshold).astype(int)
    if len(np.unique(labels)) < 2:
        order = np.argsort(composite, kind="mergesort")
        labels = np.zeros(len(composite), dtype=int)
        labels[order[len(order) // 2 :]] = 1

    dimensions = values.shape[1]
    means = np.empty((2, dimensions), dtype=float)
    variances = np.empty((2, dimensions), dtype=float)
    global_mean = np.nanmean(eligible, axis=0)
    global_variance = np.nanvar(eligible, axis=0)
    global_variance = np.where(
        np.isfinite(global_variance) & (global_variance > covariance_floor),
        global_variance,
        covariance_floor,
    )
    for state in range(2):
        subset = eligible[labels == state]
        for dimension in range(dimensions):
            observed = subset[:, dimension]
            observed = observed[np.isfinite(observed)]
            means[state, dimension] = (
                float(observed.mean())
                if len(observed)
                else float(global_mean[dimension])
            )
            variance = float(observed.var(ddof=0)) if len(observed) else float(
                global_variance[dimension]
            )
            variances[state, dimension] = max(variance, covariance_floor)

    initial_counts = np.bincount(labels, minlength=2).astype(float)
    initial = (initial_counts + transition_smoothing) / (
        initial_counts.sum() + 2.0 * transition_smoothing
    )
    transition = np.full((2, 2), transition_smoothing, dtype=float)
    for previous, current in zip(labels[:-1], labels[1:]):
        transition[int(previous), int(current)] += 1.0
    transition /= transition.sum(axis=1, keepdims=True)
    return initial, transition, means, variances


def _fit_two_state_hmm(
    values: np.ndarray,
    sufficient: np.ndarray,
    config: PanicRegimeConfig,
    warm_start: Mapping[str, np.ndarray] | None = None,
) -> dict[str, Any]:
    if warm_start is None:
        initial, transition, means, variances = _initialize_hmm(
            values,
            sufficient,
            config.covariance_floor,
            config.transition_smoothing,
        )
    else:
        initial = np.asarray(warm_start["initial"], dtype=float).copy()
        transition = np.asarray(warm_start["transition"], dtype=float).copy()
        means = np.asarray(warm_start["means"], dtype=float).copy()
        variances = np.asarray(warm_start["variances"], dtype=float).copy()

    previous_likelihood: float | None = None
    gamma = np.empty((len(values), 2), dtype=float)
    for iteration in range(config.hmm_max_iter):
        gamma, xi_sum, likelihood = _forward_backward(
            values,
            sufficient,
            initial,
            transition,
            means,
            variances,
        )
        initial = (gamma[0] + config.transition_smoothing)
        initial /= initial.sum()
        transition = xi_sum + config.transition_smoothing
        transition /= transition.sum(axis=1, keepdims=True)

        for state in range(2):
            for dimension in range(values.shape[1]):
                observed = sufficient & np.isfinite(values[:, dimension])
                weights = gamma[observed, state]
                data = values[observed, dimension]
                total = float(weights.sum())
                if total <= 1e-12:
                    continue
                mean = float(np.dot(weights, data) / total)
                variance = float(np.dot(weights, (data - mean) ** 2) / total)
                means[state, dimension] = mean
                variances[state, dimension] = max(
                    variance,
                    config.covariance_floor,
                )
        if (
            previous_likelihood is not None
            and abs(likelihood - previous_likelihood) <= config.hmm_tolerance
        ):
            break
        previous_likelihood = likelihood

    composite_means = np.nanmean(means, axis=1)
    panic_state = int(np.argmax(composite_means))
    other_state = 1 - panic_state
    directional_count = int(np.sum(means[panic_state] > means[other_state]))
    occupancy = gamma[sufficient].mean(axis=0)
    minimum_occupancy = max(
        config.minimum_state_occupancy_fraction,
        config.minimum_state_occupancy_count / max(int(sufficient.sum()), 1),
    )
    valid = (
        directional_count >= 4
        and bool(np.all(occupancy >= minimum_occupancy))
    )
    validity_reason = (
        "VALID"
        if valid
        else (
            "FAILED_STATE_ANCHOR"
            if directional_count < 4
            else "FAILED_MINIMUM_STATE_OCCUPANCY"
        )
    )
    return {
        "initial": initial,
        "transition": transition,
        "means": means,
        "variances": variances,
        "gamma": gamma,
        "last_probability": gamma[-1],
        "panic_state": panic_state,
        "directional_family_count": directional_count,
        "occupancy": occupancy,
        "valid": valid,
        "validity_reason": validity_reason,
        "iterations": iteration + 1,
        "log_likelihood": previous_likelihood,
    }


def _hmm_probability_frame(
    mechanism: pd.DataFrame,
    config: PanicRegimeConfig,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    family_columns = [f"{family}_score" for family in FAMILY_ORDER]
    values = mechanism[family_columns].to_numpy(dtype=float)
    sufficient = mechanism["evidence_sufficiency"].eq("SUFFICIENT").to_numpy()
    probabilities = np.full(len(mechanism), np.nan, dtype=float)
    validity = np.full(
        len(mechanism),
        "INSUFFICIENT_HMM_HISTORY",
        dtype=object,
    )
    refits: list[dict[str, Any]] = []
    params: dict[str, Any] | None = None
    previous_probability: np.ndarray | None = None
    eligible_since_refit = 0

    for index in range(len(mechanism)):
        valid_history = int(sufficient[:index].sum())
        should_refit = (
            valid_history >= config.hmm_minimum_history
            and (
                params is None
                or eligible_since_refit >= config.hmm_refit_interval
            )
        )
        if should_refit:
            warm = (
                None
                if params is None
                else {
                    "initial": params["initial"],
                    "transition": params["transition"],
                    "means": params["means"],
                    "variances": params["variances"],
                }
            )
            params = _fit_two_state_hmm(
                values[:index],
                sufficient[:index],
                config,
                warm_start=warm,
            )
            previous_probability = np.asarray(
                params["last_probability"], dtype=float
            )
            eligible_since_refit = 0
            refits.append(
                {
                    "forecast_origin_index": int(index),
                    "forecast_origin_timestamp": mechanism.iloc[index][
                        "timestamp"
                    ].isoformat(),
                    "training_rows": int(index),
                    "eligible_training_rows": valid_history,
                    "panic_state": int(params["panic_state"]),
                    "directional_family_count": int(
                        params["directional_family_count"]
                    ),
                    "occupancy": [
                        float(value) for value in params["occupancy"]
                    ],
                    "valid": bool(params["valid"]),
                    "validity_reason": str(params["validity_reason"]),
                    "iterations": int(params["iterations"]),
                }
            )

        if params is None or previous_probability is None:
            continue

        predicted = previous_probability @ params["transition"]
        if not sufficient[index]:
            previous_probability = predicted / predicted.sum()
            validity[index] = "INSUFFICIENT_MECHANISM_EVIDENCE"
            continue

        emission = _emission_likelihood(
            values[index],
            params["means"],
            params["variances"],
            neutral=False,
        )
        current = predicted * emission
        current /= np.clip(current.sum(), 1e-300, None)
        previous_probability = current
        eligible_since_refit += 1
        if params["valid"]:
            probabilities[index] = float(current[int(params["panic_state"])])
            validity[index] = (
                "VALID_IMPLEMENTATION_PROBABILITY_UNCERTAINTY_PENDING"
            )
        else:
            validity[index] = str(params["validity_reason"])

    output = pd.DataFrame(
        {
            "timestamp": mechanism["timestamp"],
            "model_id": "CAUSAL_GAUSSIAN_HMM_V1",
            "raw_probability": probabilities,
            "filtered_probability": probabilities,
            "lower_95": np.nan,
            "upper_95": np.nan,
            "p_range": np.nan,
            "p_trend": np.nan,
            "p_stress": np.nan,
            "operational_state": [
                _operational_state(
                    None
                    if not np.isfinite(probabilities[index])
                    else float(probabilities[index]),
                    bool(sufficient[index] and str(validity[index]).startswith("VALID")),
                )
                for index in range(len(probabilities))
            ],
            "available_mechanism_count": mechanism[
                "available_mechanism_count"
            ].to_numpy(dtype=int),
            "evidence_sufficiency": mechanism[
                "evidence_sufficiency"
            ].astype(str),
            "model_validity": validity,
            "panic_probability_authorized": True,
            "uncertainty_status": "PENDING_V3_3C",
        }
    )
    return output, refits


def compute_panic_regime_probabilities(
    market_structure_features: pd.DataFrame,
    causal_series_features: pd.DataFrame,
    config: PanicRegimeConfig,
) -> PanicRegimeFeatureFrame:
    market = _validate_market_structure(
        market_structure_features,
        config.dependence_window,
    )
    series = _validate_series_features(
        causal_series_features,
        config.reference_series_id,
    )
    directed_raw, family_columns, feature_registry = _build_directed_raw_features(
        market,
        series,
    )
    mechanism = _build_mechanism_scores(
        directed_raw,
        family_columns,
        config,
    )
    challenger = _transparent_challenger_frame(
        series,
        market["timestamp"],
        mechanism,
        config,
    )
    monotone = _monotone_probability_frame(mechanism, config)
    hmm, hmm_refits = _hmm_probability_frame(mechanism, config)
    probabilities = pd.concat(
        [challenger, monotone, hmm],
        ignore_index=True,
    ).sort_values(["timestamp", "model_id"], kind="mergesort").reset_index(drop=True)

    market_hash_frame = market.sort_values("timestamp", kind="mergesort").reset_index(
        drop=True
    )
    series_hash_frame = series.sort_values(
        ["timestamp", "series_id"], kind="mergesort"
    ).reset_index(drop=True)
    manifest = PanicRegimeManifest(
        schema_version=PANIC_REGIME_SCHEMA_VERSION,
        market_structure_sha256=stable_frame_hash(market_hash_frame),
        causal_series_sha256=stable_frame_hash(series_hash_frame),
        configuration_sha256=stable_mapping_hash(config.to_dict()),
        mechanism_scores_sha256=stable_frame_hash(mechanism),
        probability_output_sha256=_stable_probability_frame_hash(probabilities),
        dependence_window=config.dependence_window,
        reference_series_id=config.reference_series_id,
        model_ids=REGISTERED_MODEL_IDS,
        rows=int(len(probabilities)),
        timestamps=int(probabilities["timestamp"].nunique()),
    )
    diagnostics = {
        "schema_version": PANIC_REGIME_SCHEMA_VERSION,
        "registered_models": list(REGISTERED_MODEL_IDS),
        "automatic_model_selection_performed": False,
        "automatic_ensemble_performed": False,
        "consensus_probability_produced": False,
        "uncertainty_status": "PENDING_V3_3C",
        "feature_registry": feature_registry,
        "family_registered_features": {
            family: list(columns)
            for family, columns in family_columns.items()
        },
        "evidence_sufficiency_counts": {
            str(key): int(value)
            for key, value in mechanism["evidence_sufficiency"]
            .value_counts(dropna=False)
            .sort_index()
            .items()
        },
        "model_validity_counts": {
            str(model_id): {
                str(key): int(value)
                for key, value in group["model_validity"]
                .value_counts(dropna=False)
                .sort_index()
                .items()
            }
            for model_id, group in probabilities.groupby("model_id", sort=True)
        },
        "hmm_refits": hmm_refits,
        "excluded_ambiguous_features": {
            "contagion_radius": (
                "The upstream metric is a radius in correlation-distance space. "
                "Its panic direction is not monotone without a separately frozen "
                "transformation, so V3-3B excludes it rather than assigning a silent sign."
            )
        },
        "selection_performed": False,
    }
    return PanicRegimeFeatureFrame(
        probabilities=probabilities,
        mechanism_scores=mechanism,
        manifest=manifest,
        diagnostics=diagnostics,
    )
