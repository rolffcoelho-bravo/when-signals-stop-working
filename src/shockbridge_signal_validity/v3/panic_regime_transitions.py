from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd

from .panic_regime_governance_base import (
    CHALLENGER_MODEL_ID,
    DIAGNOSTICS_SCHEMA_VERSION,
    CHALLENGER_STATES,
    PANIC_MODEL_IDS,
    PANIC_STATES,
    PanicRegimeDiagnosticsConfig,
    _stable_seed,
)


def _transition_posterior(
    counts: np.ndarray,
    state_names: Sequence[str],
    *,
    replications: int,
    coverage: float,
    seed: int,
) -> dict[str, Any]:
    row_sums = counts.sum(axis=1, keepdims=True)
    mean = counts / row_sums
    lower = np.empty_like(mean)
    upper = np.empty_like(mean)
    alpha_tail = (1.0 - coverage) / 2.0
    for row in range(len(state_names)):
        rng = np.random.default_rng(_stable_seed(seed, "transition", state_names[row]))
        draws = rng.dirichlet(counts[row], size=replications)
        lower[row] = np.quantile(draws, alpha_tail, axis=0)
        upper[row] = np.quantile(draws, 1.0 - alpha_tail, axis=0)
    return {
        "states": list(state_names),
        "posterior_mean": {
            state_names[row]: {
                state_names[column]: float(mean[row, column])
                for column in range(len(state_names))
            }
            for row in range(len(state_names))
        },
        "lower_95": {
            state_names[row]: {
                state_names[column]: float(lower[row, column])
                for column in range(len(state_names))
            }
            for row in range(len(state_names))
        },
        "upper_95": {
            state_names[row]: {
                state_names[column]: float(upper[row, column])
                for column in range(len(state_names))
            }
            for row in range(len(state_names))
        },
        "rows_sum_to_one": bool(np.allclose(mean.sum(axis=1), 1.0, atol=1e-12)),
        "dirichlet_counts": counts.tolist(),
    }


def add_transition_risk(
    probabilities: pd.DataFrame,
    config: PanicRegimeDiagnosticsConfig,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    output = probabilities.copy()
    output["one_step_panic_transition_probability"] = np.nan
    output["one_step_latent_panic_probability"] = np.nan
    payload: dict[str, Any] = {
        "schema_version": DIAGNOSTICS_SCHEMA_VERSION,
        "operational_state_models": {},
        "hmm_filtered_posterior_binary": None,
        "automatic_model_selection_performed": False,
    }

    for model_id, group in output.groupby("model_id", sort=True):
        group = group.sort_values("timestamp", kind="mergesort")
        states = CHALLENGER_STATES if model_id == CHALLENGER_MODEL_ID else PANIC_STATES
        state_index = {state: index for index, state in enumerate(states)}
        counts = np.full(
            (len(states), len(states)),
            config.transition_dirichlet_alpha,
            dtype=float,
        )
        previous: str | None = None
        for global_index, state in zip(group.index, group["confirmed_state"].astype(str)):
            if state not in state_index:
                previous = None
                continue
            if previous in state_index:
                counts[state_index[previous], state_index[state]] += 1.0
            previous = state
            mean = counts / counts.sum(axis=1, keepdims=True)
            if model_id in PANIC_MODEL_IDS:
                output.loc[global_index, "one_step_panic_transition_probability"] = float(
                    mean[state_index[state], state_index["PANIC_CONSISTENT_REGIME"]]
                )
        payload["operational_state_models"][model_id] = _transition_posterior(
            counts,
            states,
            replications=config.bootstrap_replications,
            coverage=config.interval_coverage,
            seed=_stable_seed(config.random_seed, model_id, "operational_transition"),
        )

    hmm = output.loc[
        output["model_id"].eq("CAUSAL_GAUSSIAN_HMM_V1")
    ].sort_values("timestamp", kind="mergesort")
    binary_counts = np.full((2, 2), config.transition_dirichlet_alpha, dtype=float)
    previous_probability: float | None = None
    for global_index, probability in zip(hmm.index, hmm["filtered_probability"].to_numpy(dtype=float)):
        if not np.isfinite(probability):
            previous_probability = None
            continue
        if previous_probability is not None:
            previous_vector = np.asarray([1.0 - previous_probability, previous_probability])
            current_vector = np.asarray([1.0 - probability, probability])
            binary_counts += np.outer(previous_vector, current_vector)
        mean = binary_counts / binary_counts.sum(axis=1, keepdims=True)
        current_vector = np.asarray([1.0 - probability, probability])
        output.loc[global_index, "one_step_latent_panic_probability"] = float(
            current_vector @ mean[:, 1]
        )
        previous_probability = float(probability)
    payload["hmm_filtered_posterior_binary"] = _transition_posterior(
        binary_counts,
        ("NON_PANIC_CONSISTENT", "PANIC_CONSISTENT"),
        replications=config.bootstrap_replications,
        coverage=config.interval_coverage,
        seed=_stable_seed(config.random_seed, "hmm_binary_transition"),
    )
    payload["hmm_filtered_posterior_binary"]["estimation_semantics"] = (
        "Forward-filtered posterior-implied expected transition counts; no retrospective smoothing."
    )
    return output, payload


def build_state_duration_and_occupancy(
    probabilities: pd.DataFrame,
    config: PanicRegimeDiagnosticsConfig,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    occupancy: dict[str, Any] = {
        "schema_version": DIAGNOSTICS_SCHEMA_VERSION,
        "models": {},
        "hmm_binary_latent_state": {},
    }
    invalid_prefixes = ("INSUFFICIENT", "UNCONFIRMED", "NOT_AUTHORIZED")

    for model_id, group in probabilities.groupby("model_id", sort=True):
        group = group.sort_values("timestamp", kind="mergesort").reset_index(drop=True)
        current_state: str | None = None
        start_index: int | None = None
        model_episodes: list[dict[str, Any]] = []
        for index, state in enumerate(group["confirmed_state"].astype(str)):
            valid_state = not state.startswith(invalid_prefixes)
            if not valid_state:
                if current_state is not None and start_index is not None:
                    model_episodes.append(
                        _episode_record(model_id, group, current_state, start_index, index - 1, False, config)
                    )
                current_state = None
                start_index = None
                continue
            if current_state is None:
                current_state = state
                start_index = index
            elif state != current_state:
                model_episodes.append(
                    _episode_record(model_id, group, current_state, int(start_index), index - 1, False, config)
                )
                current_state = state
                start_index = index
        if current_state is not None and start_index is not None:
            model_episodes.append(
                _episode_record(model_id, group, current_state, int(start_index), len(group) - 1, True, config)
            )
        episodes.extend(model_episodes)

        valid_states = group.loc[
            ~group["confirmed_state"].astype(str).str.startswith(invalid_prefixes),
            "confirmed_state",
        ].astype(str)
        total = int(len(valid_states))
        state_payload: dict[str, Any] = {}
        state_universe = CHALLENGER_STATES if model_id == CHALLENGER_MODEL_ID else PANIC_STATES
        for state in state_universe:
            count = int(valid_states.eq(state).sum())
            state_episodes = [record for record in model_episodes if record["state"] == state]
            durations = [int(record["duration_observations"]) for record in state_episodes]
            state_payload[state] = {
                "observations": count,
                "fraction": float(count / total) if total else 0.0,
                "episodes": len(state_episodes),
                "median_duration": None if not durations else float(np.median(durations)),
                "maximum_duration": None if not durations else int(max(durations)),
            }
        occupancy["models"][model_id] = {
            "valid_state_observations": total,
            "states": state_payload,
        }

    hmm = probabilities.loc[
        probabilities["model_id"].eq("CAUSAL_GAUSSIAN_HMM_V1")
        & probabilities["filtered_probability"].notna()
    ].sort_values("timestamp", kind="mergesort")
    panic_count = int((hmm["filtered_probability"] >= 0.5).sum())
    nonpanic_count = int(len(hmm) - panic_count)
    total = int(len(hmm))
    minimum_count = max(
        config.minimum_state_occupancy_count,
        int(np.ceil(config.minimum_state_occupancy_fraction * max(total, 1))),
    )
    collapsed = bool(total == 0 or panic_count < minimum_count or nonpanic_count < minimum_count)
    occupancy["hmm_binary_latent_state"] = {
        "observations": total,
        "panic_consistent_observations": panic_count,
        "non_panic_consistent_observations": nonpanic_count,
        "panic_consistent_fraction": float(panic_count / total) if total else 0.0,
        "minimum_required_count": minimum_count,
        "minimum_required_fraction": config.minimum_state_occupancy_fraction,
        "collapsed_state": collapsed,
        "model_validity": "MODEL_INVALID_COLLAPSED_STATE" if collapsed else "VALID_OCCUPANCY",
    }
    frame = pd.DataFrame(episodes)
    if not frame.empty:
        frame = frame.sort_values(["model_id", "start_timestamp"], kind="mergesort").reset_index(drop=True)
    return frame, occupancy


def _episode_record(
    model_id: str,
    group: pd.DataFrame,
    state: str,
    start_index: int,
    end_index: int,
    censored: bool,
    config: PanicRegimeDiagnosticsConfig,
) -> dict[str, Any]:
    duration = int(end_index - start_index + 1)
    return {
        "model_id": model_id,
        "state": state,
        "start_timestamp": group.iloc[start_index]["timestamp"],
        "end_timestamp": group.iloc[end_index]["timestamp"],
        "duration_observations": duration,
        "right_censored": bool(censored),
        "episode_valid": bool(duration >= config.minimum_episode_observations),
        "retroactive_backfill_performed": False,
    }
