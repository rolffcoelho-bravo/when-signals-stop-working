from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from .data_contract import stable_frame_hash, stable_mapping_hash


DIAGNOSTICS_SCHEMA_VERSION = "v3.panic-regime-governance.v1"
PANIC_MODEL_IDS = (
    "MONOTONE_MECHANISM_SCORE_V1",
    "CAUSAL_GAUSSIAN_HMM_V1",
)
CHALLENGER_MODEL_ID = "V2_TRANSPARENT_STATE_CHALLENGER_V1"
FAMILY_ORDER = (
    "spectral",
    "network",
    "liquidity",
    "funding",
    "volatility",
    "downside",
)
PANIC_STATES = (
    "LOW_PANIC_CONSISTENCY",
    "STRESS_BUILDING",
    "TRANSMISSION_ESCALATION",
    "PANIC_CONSISTENT_REGIME",
)
CHALLENGER_STATES = ("RANGE", "TREND", "STRESS")
FAMILY_BLOCK = {
    "spectral": "STRUCTURAL",
    "network": "STRUCTURAL",
    "liquidity": "MARKET_PLUMBING",
    "funding": "MARKET_PLUMBING",
    "volatility": "PRICE_RISK",
    "downside": "PRICE_RISK",
}


class PanicRegimeDiagnosticsError(ValueError):
    """Raised when Gate V3-3C cannot satisfy its governance contract."""


@dataclass(frozen=True)
class PanicRegimeDiagnosticsConfig:
    bootstrap_replications: int = 250
    minimum_valid_bootstrap_replications: int = 200
    minimum_interval_history: int = 30
    bootstrap_history_window: int = 500
    interval_coverage: float = 0.95
    innovation_location_alpha: float = 0.20
    transition_dirichlet_alpha: float = 1.0
    state_confirmation_observations: int = 2
    minimum_episode_observations: int = 2
    minimum_state_occupancy_fraction: float = 0.05
    minimum_state_occupancy_count: int = 20
    monotone_logistic_slope: float = 6.0
    central_monotone_ewma_alpha: float = 0.35
    ewma_alpha_sensitivity: tuple[float, ...] = (0.20, 0.35, 0.50)
    threshold_sensitivity: tuple[tuple[float, float, float], ...] = (
        (0.20, 0.45, 0.70),
        (0.25, 0.50, 0.75),
        (0.30, 0.55, 0.80),
    )
    disagreement_moderate_threshold: float = 0.15
    disagreement_high_threshold: float = 0.30
    contribution_minimum_history: int = 60
    contribution_refit_interval: int = 30
    contribution_ridge_penalty: float = 1.0
    scaling_refit_interval: int = 30
    scaling_minimum_prior_observations: int = 250
    random_seed: int = 1729

    def __post_init__(self) -> None:
        if self.bootstrap_replications < 1:
            raise PanicRegimeDiagnosticsError("bootstrap_replications must be positive.")
        if not 1 <= self.minimum_valid_bootstrap_replications <= self.bootstrap_replications:
            raise PanicRegimeDiagnosticsError(
                "minimum_valid_bootstrap_replications must be in [1, bootstrap_replications]."
            )
        if self.minimum_interval_history < 5 or self.bootstrap_history_window < self.minimum_interval_history:
            raise PanicRegimeDiagnosticsError(
                "bootstrap_history_window must be at least minimum_interval_history >= 5."
            )
        if not 0.0 < self.interval_coverage < 1.0:
            raise PanicRegimeDiagnosticsError("interval_coverage must be in (0, 1).")
        if not 0.0 < self.innovation_location_alpha <= 1.0:
            raise PanicRegimeDiagnosticsError("innovation_location_alpha must be in (0, 1].")
        if self.transition_dirichlet_alpha <= 0.0:
            raise PanicRegimeDiagnosticsError("transition_dirichlet_alpha must be positive.")
        if self.state_confirmation_observations < 2:
            raise PanicRegimeDiagnosticsError(
                "state_confirmation_observations must be at least two."
            )
        if self.minimum_episode_observations < 2:
            raise PanicRegimeDiagnosticsError("minimum_episode_observations must be at least two.")
        if not 0.0 < self.minimum_state_occupancy_fraction < 0.5:
            raise PanicRegimeDiagnosticsError(
                "minimum_state_occupancy_fraction must be in (0, 0.5)."
            )
        if self.minimum_state_occupancy_count < 1:
            raise PanicRegimeDiagnosticsError("minimum_state_occupancy_count must be positive.")
        if self.monotone_logistic_slope <= 0.0:
            raise PanicRegimeDiagnosticsError("monotone_logistic_slope must be positive.")
        if not 0.0 < self.central_monotone_ewma_alpha <= 1.0:
            raise PanicRegimeDiagnosticsError("central_monotone_ewma_alpha must be in (0, 1].")
        if any(not 0.0 < alpha <= 1.0 for alpha in self.ewma_alpha_sensitivity):
            raise PanicRegimeDiagnosticsError("EWMA sensitivity alphas must be in (0, 1].")
        for thresholds in self.threshold_sensitivity:
            if len(thresholds) != 3 or not 0.0 < thresholds[0] < thresholds[1] < thresholds[2] < 1.0:
                raise PanicRegimeDiagnosticsError(
                    "Every threshold sensitivity set must contain three increasing values in (0, 1)."
                )
        if not 0.0 < self.disagreement_moderate_threshold < self.disagreement_high_threshold < 1.0:
            raise PanicRegimeDiagnosticsError("Disagreement thresholds are invalid.")
        if self.contribution_minimum_history < 10 or self.contribution_refit_interval < 1:
            raise PanicRegimeDiagnosticsError("Contribution history/refit controls are invalid.")
        if self.contribution_ridge_penalty <= 0.0:
            raise PanicRegimeDiagnosticsError("contribution_ridge_penalty must be positive.")
        if self.scaling_refit_interval < 1 or self.scaling_minimum_prior_observations < 5:
            raise PanicRegimeDiagnosticsError("Scaling-boundary controls are invalid.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PanicRegimeDiagnosticsManifest:
    schema_version: str
    parent_engine_manifest_sha256: str
    probability_input_sha256: str
    mechanism_input_sha256: str
    market_structure_input_sha256: str
    causal_series_input_sha256: str
    engine_diagnostics_sha256: str
    configuration_sha256: str
    output_hashes: Mapping[str, str]
    probability_rows: int
    timestamps: int
    automatic_model_selection_performed: bool = False
    automatic_ensemble_performed: bool = False
    consensus_probability_produced: bool = False
    final_v3_3_lock_permitted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def manifest_sha256(self) -> str:
        payload = json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")
        return sha256(payload).hexdigest()


@dataclass(frozen=True)
class PanicRegimeDiagnosticsResult:
    probabilities: pd.DataFrame
    transition_matrix: Mapping[str, Any]
    state_duration: pd.DataFrame
    occupancy_statistics: Mapping[str, Any]
    mechanism_contributions: pd.DataFrame
    disagreement: pd.DataFrame
    coverage: pd.DataFrame
    coverage_summary: Mapping[str, Any]
    sensitivity: Mapping[str, Any]
    diagnostics: Mapping[str, Any]
    validation_report: Mapping[str, Any]
    manifest: PanicRegimeDiagnosticsManifest


def _canonical_json_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def _stable_seed(base_seed: int, *parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    digest = sha256(payload).digest()
    return int((base_seed + int.from_bytes(digest[:8], "big")) % (2**32 - 1))


def _logit(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(np.asarray(values, dtype=float), 1e-8, 1.0 - 1e-8)
    return np.log(clipped / (1.0 - clipped))


def _logistic(values: np.ndarray | float) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    return 1.0 / (1.0 + np.exp(-np.clip(array, -40.0, 40.0)))


def _validate_probabilities(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "timestamp",
        "model_id",
        "raw_probability",
        "filtered_probability",
        "operational_state",
        "evidence_sufficiency",
        "model_validity",
        "panic_probability_authorized",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise PanicRegimeDiagnosticsError(
            "Probability input is missing columns: " + ", ".join(missing)
        )
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    if data["timestamp"].isna().any():
        raise PanicRegimeDiagnosticsError("Probability timestamps must be valid UTC values.")
    data["model_id"] = data["model_id"].astype("string").str.strip()
    if data.duplicated(["timestamp", "model_id"]).any():
        raise PanicRegimeDiagnosticsError("Probability input contains duplicate timestamp/model rows.")
    observed = set(data["model_id"].astype(str))
    required_models = {CHALLENGER_MODEL_ID, *PANIC_MODEL_IDS}
    if observed != required_models:
        raise PanicRegimeDiagnosticsError(
            f"Probability input model registry mismatch: observed={sorted(observed)}"
        )
    for column in ("raw_probability", "filtered_probability", "p_range", "p_trend", "p_stress"):
        if column not in data:
            data[column] = np.nan
        data[column] = pd.to_numeric(data[column], errors="coerce")
    for model_id in PANIC_MODEL_IDS:
        values = data.loc[data["model_id"].eq(model_id), "filtered_probability"].dropna()
        if not values.between(0.0, 1.0).all():
            raise PanicRegimeDiagnosticsError(f"Out-of-bound probability for {model_id}.")
    return data.sort_values(["timestamp", "model_id"], kind="mergesort").reset_index(drop=True)


def _validate_mechanism_scores(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"timestamp", "evidence_sufficiency", "available_mechanism_count"}
    required.update(f"{family}_score" for family in FAMILY_ORDER)
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise PanicRegimeDiagnosticsError(
            "Mechanism input is missing columns: " + ", ".join(missing)
        )
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    if data["timestamp"].isna().any() or data["timestamp"].duplicated().any():
        raise PanicRegimeDiagnosticsError(
            "Mechanism input requires unique valid UTC timestamps."
        )
    for family in FAMILY_ORDER:
        data[f"{family}_score"] = pd.to_numeric(
            data[f"{family}_score"], errors="coerce"
        )
    return data.sort_values("timestamp", kind="mergesort").reset_index(drop=True)


def _causal_innovations(values: np.ndarray, alpha: float) -> np.ndarray:
    output = np.full(len(values), np.nan, dtype=float)
    location: float | None = None
    for index, value in enumerate(values):
        if not np.isfinite(value):
            continue
        transformed = float(_logit(np.array([value]))[0])
        if location is not None:
            output[index] = transformed - location
        location = transformed if location is None else alpha * transformed + (1.0 - alpha) * location
    return output


def _valid_moving_blocks(values: np.ndarray, block_length: int) -> np.ndarray:
    if len(values) < block_length:
        return np.empty((0, block_length), dtype=float)
    blocks = []
    for start in range(0, len(values) - block_length + 1):
        block = values[start : start + block_length]
        if np.isfinite(block).all():
            blocks.append(block)
    if not blocks:
        return np.empty((0, block_length), dtype=float)
    return np.vstack(blocks)


def add_prefix_probability_intervals(
    probabilities: pd.DataFrame,
    config: PanicRegimeDiagnosticsConfig,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    output = probabilities.copy()
    output["lower_95"] = np.nan
    output["upper_95"] = np.nan
    output["interval_method"] = "NOT_APPLICABLE"
    output["probability_publishable"] = False
    output["uncertainty_status"] = np.where(
        output["panic_probability_authorized"].astype(bool),
        "INSUFFICIENT_INTERVAL_HISTORY",
        "NOT_APPLICABLE",
    )
    alpha_tail = (1.0 - config.interval_coverage) / 2.0
    summary: dict[str, Any] = {}

    for model_id in PANIC_MODEL_IDS:
        positions = output.index[output["model_id"].eq(model_id)].to_numpy()
        group = output.loc[positions].sort_values("timestamp", kind="mergesort")
        positions = group.index.to_numpy()
        values = group["filtered_probability"].to_numpy(dtype=float)
        innovations = _causal_innovations(values, config.innovation_location_alpha)
        completed = 0
        unavailable = 0
        block_lengths: list[int] = []

        for local_index, global_index in enumerate(positions):
            probability = values[local_index]
            if not np.isfinite(probability):
                output.loc[global_index, "uncertainty_status"] = "NOT_APPLICABLE_INVALID_POINT_PROBABILITY"
                continue
            start = max(0, local_index - config.bootstrap_history_window)
            prior = innovations[start:local_index]
            finite_count = int(np.isfinite(prior).sum())
            if finite_count < config.minimum_interval_history:
                unavailable += 1
                output.loc[global_index, "model_validity"] = (
                    "VALID_POINT_ESTIMATE_INTERVAL_UNAVAILABLE"
                )
                continue
            block_length = max(2, int(np.ceil(1.5 * finite_count ** (1.0 / 3.0))))
            blocks = _valid_moving_blocks(prior, block_length)
            if len(blocks) == 0:
                unavailable += 1
                output.loc[global_index, "model_validity"] = (
                    "VALID_POINT_ESTIMATE_INTERVAL_UNAVAILABLE"
                )
                continue
            centered_means = blocks.mean(axis=1)
            centered_means = centered_means - float(centered_means.mean())
            rng = np.random.default_rng(
                _stable_seed(
                    config.random_seed,
                    model_id,
                    group.loc[global_index, "timestamp"].isoformat(),
                    "probability_interval",
                )
            )
            sampled = rng.choice(
                centered_means,
                size=config.bootstrap_replications,
                replace=True,
            )
            sampled = sampled[np.isfinite(sampled)]
            if len(sampled) < config.minimum_valid_bootstrap_replications:
                unavailable += 1
                output.loc[global_index, "uncertainty_status"] = (
                    "INSUFFICIENT_VALID_BOOTSTRAP_REPLICATIONS"
                )
                output.loc[global_index, "model_validity"] = (
                    "VALID_POINT_ESTIMATE_INTERVAL_UNAVAILABLE"
                )
                continue
            center = float(_logit(np.array([probability]))[0])
            draws = _logistic(center + sampled)
            lower = min(float(np.quantile(draws, alpha_tail)), float(probability))
            upper = max(float(np.quantile(draws, 1.0 - alpha_tail)), float(probability))
            output.loc[global_index, ["lower_95", "upper_95"]] = [lower, upper]
            output.loc[global_index, "interval_method"] = (
                "PREFIX_MOVING_BLOCK_LOGIT_INNOVATION"
            )
            output.loc[global_index, "probability_publishable"] = True
            output.loc[global_index, "uncertainty_status"] = "COMPLETE"
            output.loc[global_index, "model_validity"] = "VALID_PUBLISHABLE_PROBABILITY"
            completed += 1
            block_lengths.append(block_length)

        summary[model_id] = {
            "completed_intervals": completed,
            "unavailable_intervals": unavailable,
            "bootstrap_replications": config.bootstrap_replications,
            "minimum_valid_replications": config.minimum_valid_bootstrap_replications,
            "mean_block_length": (
                None if not block_lengths else float(np.mean(block_lengths))
            ),
            "method": "PREFIX_MOVING_BLOCK_LOGIT_INNOVATION",
            "semantic_boundary": (
                "Dependence-aware probability-path innovation interval. "
                "It is not an externally calibrated event-frequency confidence interval."
            ),
        }
    return output, summary


def _raw_state_for_challenger(group: pd.DataFrame) -> list[str]:
    states = []
    for row in group.itertuples(index=False):
        values = np.asarray([row.p_range, row.p_trend, row.p_stress], dtype=float)
        if not np.isfinite(values).all():
            states.append("INSUFFICIENT_CHALLENGER_EVIDENCE")
        else:
            states.append(CHALLENGER_STATES[int(np.argmax(values))])
    return states


def causal_confirm_states(
    raw_states: Sequence[str],
    *,
    confirmation_observations: int,
) -> list[str]:
    confirmed: list[str] = []
    current: str | None = None
    candidate: str | None = None
    candidate_count = 0
    insufficient_prefixes = ("INSUFFICIENT", "NOT_AUTHORIZED", "UNCONFIRMED")

    for raw in (str(value) for value in raw_states):
        if raw.startswith(insufficient_prefixes):
            confirmed.append(raw)
            current = None
            candidate = None
            candidate_count = 0
            continue
        if current is None:
            if candidate == raw:
                candidate_count += 1
            else:
                candidate = raw
                candidate_count = 1
            if candidate_count >= confirmation_observations:
                current = raw
                candidate = None
                candidate_count = 0
                confirmed.append(current)
            else:
                confirmed.append("UNCONFIRMED_STATE")
            continue
        if raw == current:
            candidate = None
            candidate_count = 0
            confirmed.append(current)
            continue
        if candidate == raw:
            candidate_count += 1
        else:
            candidate = raw
            candidate_count = 1
        if candidate_count >= confirmation_observations:
            current = raw
            candidate = None
            candidate_count = 0
        confirmed.append(current)
    return confirmed


def _apply_confirmed_states(
    probabilities: pd.DataFrame,
    config: PanicRegimeDiagnosticsConfig,
) -> pd.DataFrame:
    output = probabilities.copy()
    output["confirmed_state"] = "UNCONFIRMED_STATE"
    for model_id, group in output.groupby("model_id", sort=True):
        group = group.sort_values("timestamp", kind="mergesort")
        if model_id == CHALLENGER_MODEL_ID:
            raw_states = _raw_state_for_challenger(group)
        else:
            raw_states = group["operational_state"].astype(str).tolist()
        confirmed = causal_confirm_states(
            raw_states,
            confirmation_observations=config.state_confirmation_observations,
        )
        output.loc[group.index, "confirmed_state"] = confirmed
    return output.sort_values(["timestamp", "model_id"], kind="mergesort").reset_index(drop=True)
