from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from .panic_regime_governance_base import (
    DIAGNOSTICS_SCHEMA_VERSION,
    PANIC_MODEL_IDS,
    PANIC_STATES,
    PanicRegimeDiagnosticsConfig,
)


def _state_from_thresholds(probability: float, thresholds: Sequence[float]) -> str:
    if probability < thresholds[0]:
        return PANIC_STATES[0]
    if probability < thresholds[1]:
        return PANIC_STATES[1]
    if probability < thresholds[2]:
        return PANIC_STATES[2]
    return PANIC_STATES[3]


def _causal_ewma(values: np.ndarray, alpha: float) -> np.ndarray:
    output = np.full(len(values), np.nan, dtype=float)
    previous: float | None = None
    for index, value in enumerate(values):
        if not np.isfinite(value):
            continue
        previous = (
            float(value)
            if previous is None
            else alpha * float(value) + (1.0 - alpha) * previous
        )
        output[index] = previous
    return output


def build_sensitivity_diagnostics(
    probabilities: pd.DataFrame,
    mechanism: pd.DataFrame,
    engine_diagnostics: Mapping[str, Any],
    config: PanicRegimeDiagnosticsConfig,
) -> dict[str, Any]:
    threshold_payload: dict[str, Any] = {}
    for model_id in PANIC_MODEL_IDS:
        group = probabilities.loc[
            probabilities["model_id"].eq(model_id)
        ].sort_values("timestamp")
        valid = group["filtered_probability"].dropna().to_numpy(dtype=float)
        model_sets = {}
        for thresholds in config.threshold_sensitivity:
            states = [_state_from_thresholds(value, thresholds) for value in valid]
            model_sets["|".join(format(value, ".2f") for value in thresholds)] = {
                state: int(states.count(state)) for state in PANIC_STATES
            }
        threshold_payload[model_id] = model_sets

    monotone = probabilities.loc[
        probabilities["model_id"].eq("MONOTONE_MECHANISM_SCORE_V1")
    ].sort_values("timestamp")
    raw = monotone["raw_probability"].to_numpy(dtype=float)
    central = monotone["filtered_probability"].to_numpy(dtype=float)
    ewma_payload = {}
    for alpha in config.ewma_alpha_sensitivity:
        alternative = _causal_ewma(raw, alpha)
        valid = np.isfinite(alternative) & np.isfinite(central)
        ewma_payload[format(alpha, ".2f")] = {
            "valid_rows": int(valid.sum()),
            "mean_absolute_difference_from_central": (
                None
                if not valid.any()
                else float(np.mean(np.abs(alternative[valid] - central[valid])))
            ),
            "maximum_absolute_difference_from_central": (
                None
                if not valid.any()
                else float(np.max(np.abs(alternative[valid] - central[valid])))
            ),
        }

    mono_raw = monotone["raw_probability"].to_numpy(dtype=float)
    mono_jumps = np.abs(np.diff(mono_raw, prepend=np.nan))
    boundary = np.zeros(len(monotone), dtype=bool)
    start = config.scaling_minimum_prior_observations
    if start < len(boundary):
        boundary[np.arange(start, len(boundary), config.scaling_refit_interval)] = True
    boundary_valid = boundary & np.isfinite(mono_jumps)
    nonboundary_valid = (~boundary) & np.isfinite(mono_jumps)
    scaling_payload = {
        "registered_refit_interval": config.scaling_refit_interval,
        "boundary_observations": int(boundary_valid.sum()),
        "mean_absolute_probability_jump_at_boundary": (
            None
            if not boundary_valid.any()
            else float(np.mean(mono_jumps[boundary_valid]))
        ),
        "mean_absolute_probability_jump_elsewhere": (
            None
            if not nonboundary_valid.any()
            else float(np.mean(mono_jumps[nonboundary_valid]))
        ),
        "selection_performed": False,
    }

    hmm = probabilities.loc[
        probabilities["model_id"].eq("CAUSAL_GAUSSIAN_HMM_V1")
    ].sort_values("timestamp").reset_index(drop=True)
    hmm_values = hmm["filtered_probability"].to_numpy(dtype=float)
    hmm_jumps = np.abs(np.diff(hmm_values, prepend=np.nan))
    refit_indices = {
        int(record["forecast_origin_index"])
        for record in engine_diagnostics.get("hmm_refits", [])
        if isinstance(record, Mapping) and "forecast_origin_index" in record
    }
    refit_mask = np.asarray([index in refit_indices for index in range(len(hmm))])
    refit_valid = refit_mask & np.isfinite(hmm_jumps)
    nonrefit_valid = (~refit_mask) & np.isfinite(hmm_jumps)
    valid_refits = [
        record
        for record in engine_diagnostics.get("hmm_refits", [])
        if isinstance(record, Mapping) and bool(record.get("valid"))
    ]
    total_refits = len(engine_diagnostics.get("hmm_refits", []))
    hmm_payload = {
        "refit_origins": total_refits,
        "valid_refits": len(valid_refits),
        "invalid_refits": total_refits - len(valid_refits),
        "mean_absolute_probability_jump_at_refit": (
            None
            if not refit_valid.any()
            else float(np.mean(hmm_jumps[refit_valid]))
        ),
        "mean_absolute_probability_jump_elsewhere": (
            None
            if not nonrefit_valid.any()
            else float(np.mean(hmm_jumps[nonrefit_valid]))
        ),
        "saturation_share_below_0_01_or_above_0_99": (
            None
            if not np.isfinite(hmm_values).any()
            else float(
                np.mean(
                    (hmm_values[np.isfinite(hmm_values)] < 0.01)
                    | (hmm_values[np.isfinite(hmm_values)] > 0.99)
                )
            )
        ),
        "retrospective_smoothing_performed": False,
    }
    return {
        "schema_version": DIAGNOSTICS_SCHEMA_VERSION,
        "threshold_sensitivity": threshold_payload,
        "ewma_alpha_sensitivity": ewma_payload,
        "scaling_refit_boundary_sensitivity": scaling_payload,
        "hmm_refit_and_saturation_sensitivity": hmm_payload,
        "automatic_selection_performed": False,
    }
