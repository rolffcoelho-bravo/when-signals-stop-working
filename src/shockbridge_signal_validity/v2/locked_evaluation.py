from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss

from .causal_features import (
    STATE_INPUT_FEATURES,
    build_causal_base_features,
    build_registered_signal_features,
)
from .contracts import HoldoutAccessError, ProtocolViolation
from .filtered_states import CausalFilteredStateEngine
from .pipeline_selection import (
    StructuralPipelineSpecification,
    matched_pipeline_fold,
)
from .predictive_screening import expected_calibration_error
from .registry import V2Registry
from .signals import add_soft_state_interactions
from .targets import forward_log_return


EXPECTED_D3_FAMILY = "bollinger"
EXPECTED_D3_PIPELINE_HASH = "2f85b54f8f178ec59c2bfb8a06cd8dedb3e053e2bec4da40cb446d380def2851"


@dataclass(frozen=True)
class FrozenEvaluationPipeline:
    pipeline_hash: str
    signal_family: str
    horizon_candles: int
    horizon_hours: int
    signal_specification: dict[str, Any]
    structural_pipeline: dict[str, Any]
    calibration_method: str
    decision_probability_distance_threshold: float


def canonical_pipeline_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_single_frozen_pipeline(
    path: Path | str,
    expected_hash: str = EXPECTED_D3_PIPELINE_HASH,
) -> FrozenEvaluationPipeline:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    pipelines = payload.get("frozen_pipelines", [])
    if payload.get("holdout_authorization_enabled") is not False:
        raise ProtocolViolation("D2C registry must still have holdout authorization disabled.")
    if payload.get("family_level_pipeline_freeze_completed") is not True:
        raise ProtocolViolation("D2C family-level pipeline freeze is incomplete.")
    if len(pipelines) != 1:
        raise ProtocolViolation("D3 requires exactly one D2C-frozen pipeline.")
    pipeline = dict(pipelines[0])
    recorded_hash = str(pipeline.pop("pipeline_hash", ""))
    computed_hash = canonical_pipeline_hash(pipeline)
    if recorded_hash != computed_hash:
        raise ProtocolViolation("D2C frozen-pipeline hash does not match its canonical payload.")
    if recorded_hash != expected_hash:
        raise ProtocolViolation("D3 received a pipeline other than the pre-authorized D2C pipeline.")
    if pipeline.get("signal_family") != EXPECTED_D3_FAMILY:
        raise ProtocolViolation("Only the admitted Bollinger family may enter D3.")
    if pipeline.get("holdout_performance_accessed") is not False:
        raise ProtocolViolation("The D2C pipeline already reports holdout access.")
    if pipeline.get("economic_gate_evaluated") is not False:
        raise ProtocolViolation("The D2C pipeline already reports economic-gate evaluation.")
    calibration = str(pipeline["calibration_method"])
    if calibration not in {"none", "sigmoid"}:
        raise ProtocolViolation("D3 cannot use diagnostic-only calibration.")
    return FrozenEvaluationPipeline(
        pipeline_hash=recorded_hash,
        signal_family=str(pipeline["signal_family"]),
        horizon_candles=int(pipeline["horizon_candles"]),
        horizon_hours=int(pipeline["horizon_hours"]),
        signal_specification=dict(pipeline["signal_specification"]),
        structural_pipeline=dict(pipeline["structural_pipeline"]),
        calibration_method=calibration,
        decision_probability_distance_threshold=float(
            pipeline["decision_probability_distance_threshold"]
        ),
    )


def validate_d3_authorization(
    payload: dict[str, Any],
    protocol_lock_id: str,
    d2c_lock_id: str,
    d3_lock_id: str,
    implementation_commit: str,
    pipeline: FrozenEvaluationPipeline,
    registry: V2Registry,
) -> None:
    if payload.get("status") != "APPROVED_FOR_SINGLE_ACCESS":
        raise HoldoutAccessError("D3 authorization status is not approved for single access.")
    if payload.get("authorized") is not True or payload.get("single_access") is not True:
        raise HoldoutAccessError("D3 authorization must explicitly permit one access.")
    expected = {
        "protocol_lock_id": protocol_lock_id,
        "d2c_lock_id": d2c_lock_id,
        "d3_lock_id": d3_lock_id,
        "implementation_commit": implementation_commit,
        "pipeline_hash": pipeline.pipeline_hash,
        "signal_family": pipeline.signal_family,
        "holdout_start_utc": registry.holdout_start.isoformat(),
        "holdout_end_utc": registry.holdout_end.isoformat(),
    }
    for key, value in expected.items():
        if str(payload.get(key)) != str(value):
            raise HoldoutAccessError(f"D3 authorization mismatch: {key}.")
    forbidden = {str(value).lower() for value in payload.get("forbidden_signal_families", [])}
    if "rsi" not in forbidden:
        raise HoldoutAccessError("D3 authorization must explicitly prohibit RSI re-entry.")
    if payload.get("approval_record_created_before_results") is not True:
        raise HoldoutAccessError("D3 approval must be recorded before result access.")


def build_dual_boundary_targets(
    close: pd.Series,
    horizon_candles: int,
    registry: V2Registry,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    future = forward_log_return(close, horizon_candles)
    target_timestamp = close.index.to_series().shift(-int(horizon_candles))
    origins = pd.Series(close.index, index=close.index)
    development_valid = origins.le(registry.development_end) & target_timestamp.le(
        registry.development_end
    )
    holdout_valid = (
        origins.ge(registry.holdout_start)
        & origins.le(registry.holdout_end)
        & target_timestamp.le(registry.holdout_end)
    )
    valid = development_valid | holdout_valid
    future = future.where(valid).rename("future_return")
    direction = future.gt(0.0).astype("Int64").where(valid).rename("target")
    return direction, future, target_timestamp.where(valid).rename("target_timestamp")


def assign_equal_chronological_subperiods(
    index: pd.DatetimeIndex,
    periods: int = 3,
) -> pd.Series:
    if periods < 2:
        raise ProtocolViolation("D3 requires at least two chronological subperiods.")
    if len(index) < periods:
        raise ProtocolViolation("Insufficient observations for D3 subperiod assignment.")
    labels = np.empty(len(index), dtype=object)
    for number, positions in enumerate(np.array_split(np.arange(len(index)), periods), start=1):
        labels[positions] = f"P{number}"
    return pd.Series(labels, index=index, name="holdout_subperiod")


def structural_specification(pipeline: FrozenEvaluationPipeline) -> StructuralPipelineSpecification:
    structural = pipeline.structural_pipeline
    return StructuralPipelineSpecification(
        pipeline_id=str(structural["pipeline_id"]),
        model_family=str(structural["model_family"]),
        window_scheme=str(structural["window_scheme"]),
        regime_conditioned=bool(structural["regime_conditioned"]),
        parameters=dict(structural["parameters"]),
        complexity_rank=0,
    )


def build_signal_features(
    close: pd.Series,
    states: pd.DataFrame,
    pipeline: FrozenEvaluationPipeline,
) -> pd.DataFrame:
    spec = pipeline.signal_specification
    raw = build_registered_signal_features(
        close,
        signal_family=str(spec["signal_family"]),
        interpretation=str(spec["interpretation"]),
        period=int(spec["period"]),
        lower_threshold=spec.get("lower_threshold"),
        upper_threshold=spec.get("upper_threshold"),
        standard_deviations=spec.get("standard_deviations"),
    ).add_prefix(f"{pipeline.signal_family}_")
    score_column = f"{pipeline.signal_family}_bb_signal_score"
    score = raw[score_column].reindex(states.index)
    return raw.reindex(states.index).join(add_soft_state_interactions(score, states))


def locked_evaluation(
    aligned: pd.DataFrame,
    pipeline: FrozenEvaluationPipeline,
    registry: V2Registry,
    d2b_config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    if not isinstance(aligned.index, pd.DatetimeIndex) or aligned.index.tz is None:
        raise ProtocolViolation("D3 aligned data require timezone-aware timestamps.")
    aligned = aligned.sort_index()
    if aligned.index.has_duplicates:
        raise ProtocolViolation("D3 aligned data contain duplicate timestamps.")
    expected = aligned.loc[registry.holdout_start : registry.holdout_end]
    if expected.empty or expected.index.min() != registry.holdout_start:
        raise ProtocolViolation("D3 methodology-locked partition is incomplete at its start.")
    if expected.index.max() != registry.holdout_end:
        raise ProtocolViolation("D3 methodology-locked partition is incomplete at its end.")

    causal = build_causal_base_features(aligned)
    development_state_input = causal.loc[
        registry.development_start : registry.development_end,
        STATE_INPUT_FEATURES,
    ].dropna()
    holdout_state_input = causal.loc[
        registry.holdout_start : registry.holdout_end,
        STATE_INPUT_FEATURES,
    ].dropna()
    state_engine = CausalFilteredStateEngine().fit(development_state_input)
    training_states = state_engine.training_probabilities_.copy()
    holdout_states = state_engine.filter_forward(holdout_state_input)
    all_states = pd.concat([training_states, holdout_states]).sort_index()

    signal = build_signal_features(aligned["sol_Close"], all_states, pipeline)
    target, future_return, target_timestamp = build_dual_boundary_targets(
        aligned["sol_Close"], pipeline.horizon_candles, registry
    )
    result = matched_pipeline_fold(
        baseline_features=causal,
        states=all_states,
        signal_features=signal,
        target=target,
        future_return=future_return,
        train_start=registry.development_start,
        train_end=registry.development_end,
        test_start=registry.holdout_start,
        test_end=registry.holdout_end,
        specification=structural_specification(pipeline),
        registry_payload=registry.payload,
        calibration_method=pipeline.calibration_method,
        horizon_candles=pipeline.horizon_candles,
        calibration_fraction=float(d2b_config["calibration"]["chronological_fraction"]),
        minimum_fit_rows=int(d2b_config["calibration"]["minimum_fit_rows"]),
        minimum_calibration_rows=int(d2b_config["calibration"]["minimum_calibration_rows"]),
        random_state=int(d2b_config["random_state"]),
    )

    predictions = pd.DataFrame(
        {
            "Timestamp": result.timestamps,
            "target_timestamp": target_timestamp.reindex(result.timestamps).to_numpy(),
            "realised_direction": result.realised,
            "future_return": result.future_return,
            "benchmark_probability": result.benchmark_probability,
            "candidate_probability": result.candidate_probability,
        }
    ).set_index("Timestamp")
    benchmark = np.clip(predictions["benchmark_probability"].to_numpy(float), 1e-9, 1 - 1e-9)
    candidate = np.clip(predictions["candidate_probability"].to_numpy(float), 1e-9, 1 - 1e-9)
    realised = predictions["realised_direction"].to_numpy(float)
    predictions["benchmark_observation_log_loss"] = -(
        realised * np.log(benchmark) + (1.0 - realised) * np.log(1.0 - benchmark)
    )
    predictions["candidate_observation_log_loss"] = -(
        realised * np.log(candidate) + (1.0 - realised) * np.log(1.0 - candidate)
    )
    predictions["incremental_observation_log_loss"] = (
        predictions["benchmark_observation_log_loss"]
        - predictions["candidate_observation_log_loss"]
    )
    threshold = pipeline.decision_probability_distance_threshold
    active = np.abs(candidate - 0.5) > threshold
    position = np.where(active, np.where(candidate > 0.5, 1.0, -1.0), 0.0)
    prior = np.concatenate([[0.0], position[:-1]])
    turnover = np.abs(position - prior)
    one_way_cost = float(d2b_config["decision_policy"]["primary_one_way_cost_bps"]) / 10000.0
    predictions["decision_active"] = active
    predictions["position"] = position
    predictions["turnover_units"] = turnover
    predictions["gross_strategy_return"] = position * predictions["future_return"].to_numpy(float)
    predictions["transaction_cost"] = turnover * one_way_cost
    predictions["net_strategy_return"] = (
        predictions["gross_strategy_return"] - predictions["transaction_cost"]
    )
    predictions = predictions.join(
        holdout_states[["state_p_range", "state_p_trend", "state_p_stress", "state_label"]],
        how="left",
    )
    predictions["holdout_subperiod"] = assign_equal_chronological_subperiods(predictions.index)
    predictions["signal_family"] = pipeline.signal_family
    predictions["pipeline_hash"] = pipeline.pipeline_hash

    def metrics(frame: pd.DataFrame) -> dict[str, Any]:
        y = frame["realised_direction"].astype(int).to_numpy()
        bp = frame["benchmark_probability"].to_numpy(float)
        cp = frame["candidate_probability"].to_numpy(float)
        active_frame = frame.loc[frame["decision_active"].astype(bool)]
        return {
            "rows": int(len(frame)),
            "benchmark_log_loss": float(log_loss(y, bp, labels=[0, 1])),
            "candidate_log_loss": float(log_loss(y, cp, labels=[0, 1])),
            "incremental_log_loss": float(log_loss(y, bp, labels=[0, 1]) - log_loss(y, cp, labels=[0, 1])),
            "benchmark_brier": float(brier_score_loss(y, bp)),
            "candidate_brier": float(brier_score_loss(y, cp)),
            "benchmark_ece": float(expected_calibration_error(y, bp)),
            "candidate_ece": float(expected_calibration_error(y, cp)),
            "decision_coverage": float(frame["decision_active"].mean()),
            "nonzero_decisions": int(frame["decision_active"].sum()),
            "mean_net_edge_active": float(active_frame["net_strategy_return"].mean()) if len(active_frame) else 0.0,
            "cumulative_net_return": float(frame["net_strategy_return"].sum()),
        }

    summary = {
        "overall": metrics(predictions),
        "subperiods": {
            label: metrics(group)
            for label, group in predictions.groupby("holdout_subperiod", sort=True)
        },
        "statistical_gate_evaluated": False,
        "economic_gate_evaluated": False,
        "multiplicity_adjustment_applied": False,
        "robustness_gate_evaluated": False,
        "interpretation": "RAW_METHODOLOGY_LOCKED_EVALUATION_EVIDENCE_NO_VERDICT",
    }
    state_record = state_engine.parameter_record()
    return predictions, summary, state_record
