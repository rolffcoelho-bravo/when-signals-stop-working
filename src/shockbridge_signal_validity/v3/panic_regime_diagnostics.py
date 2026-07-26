from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping, Sequence

import pandas as pd

from .data_contract import stable_frame_hash, stable_mapping_hash
from .panic_regime_governance_base import (
    DIAGNOSTICS_SCHEMA_VERSION,
    PanicRegimeDiagnosticsConfig,
    PanicRegimeDiagnosticsManifest,
    PanicRegimeDiagnosticsResult,
    _apply_confirmed_states,
    _canonical_json_hash,
    _validate_mechanism_scores,
    _validate_probabilities,
    add_prefix_probability_intervals,
)
from .panic_regime_transitions import (
    add_transition_risk,
    build_state_duration_and_occupancy,
)
from .panic_regime_explainability import (
    build_cross_model_disagreement,
    build_mechanism_contributions,
    build_mechanism_coverage,
)
from .panic_regime_sensitivity import build_sensitivity_diagnostics


def _dataframe_hash(frame: pd.DataFrame, sort_columns: Sequence[str]) -> str:
    ordered = frame.sort_values(list(sort_columns), kind="mergesort").reset_index(
        drop=True
    )
    return stable_frame_hash(ordered)


def compute_panic_regime_governance(
    probabilities: pd.DataFrame,
    mechanism_scores: pd.DataFrame,
    market_structure: pd.DataFrame,
    causal_series: pd.DataFrame,
    engine_diagnostics: Mapping[str, Any],
    parent_engine_manifest: Mapping[str, Any],
    config: PanicRegimeDiagnosticsConfig,
) -> PanicRegimeDiagnosticsResult:
    probability_input = _validate_probabilities(probabilities)
    mechanism = _validate_mechanism_scores(mechanism_scores)
    probability_input_hash = _dataframe_hash(
        probability_input, ("timestamp", "model_id")
    )
    mechanism_input_hash = _dataframe_hash(mechanism, ("timestamp",))

    with_intervals, interval_diagnostics = add_prefix_probability_intervals(
        probability_input, config
    )
    confirmed = _apply_confirmed_states(with_intervals, config)
    finalized_probability, transition_matrix = add_transition_risk(confirmed, config)
    state_duration, occupancy = build_state_duration_and_occupancy(
        finalized_probability, config
    )
    contributions, contribution_diagnostics = build_mechanism_contributions(
        finalized_probability, mechanism, config
    )
    disagreement = build_cross_model_disagreement(finalized_probability, config)
    dependence_window = int(parent_engine_manifest["dependence_window"])
    coverage, coverage_summary = build_mechanism_coverage(
        market_structure,
        causal_series,
        engine_diagnostics,
        dependence_window,
    )
    sensitivity = build_sensitivity_diagnostics(
        finalized_probability,
        mechanism,
        engine_diagnostics,
        config,
    )

    point_probabilities = finalized_probability.loc[
        finalized_probability["panic_probability_authorized"].astype(bool)
        & finalized_probability["filtered_probability"].notna()
    ]
    all_point_estimates_publishable = bool(
        point_probabilities.empty
        or point_probabilities["probability_publishable"].astype(bool).all()
    )
    transition_rows_valid = all(
        model_payload["rows_sum_to_one"]
        for model_payload in transition_matrix["operational_state_models"].values()
    ) and bool(transition_matrix["hmm_filtered_posterior_binary"]["rows_sum_to_one"])
    disagreement_counts = {
        str(key): int(value)
        for key, value in disagreement["disagreement_class"]
        .value_counts(dropna=False)
        .sort_index()
        .items()
    }
    diagnostics = {
        "schema_version": DIAGNOSTICS_SCHEMA_VERSION,
        "interval_diagnostics": interval_diagnostics,
        "contribution_diagnostics": contribution_diagnostics,
        "cross_model_disagreement_counts": disagreement_counts,
        "high_disagreement_is_model_risk_not_model_selection": True,
        "transition_rows_sum_to_one": transition_rows_valid,
        "occupancy_model_boundaries": occupancy["hmm_binary_latent_state"],
        "automatic_model_selection_performed": False,
        "automatic_ensemble_performed": False,
        "consensus_probability_produced": False,
        "external_chronology_used": False,
    }
    validation = {
        "schema_version": DIAGNOSTICS_SCHEMA_VERSION,
        "status": "GOVERNANCE_AND_DIAGNOSTICS_COMPLETE_FINAL_ACCEPTANCE_PENDING",
        "probability_rows": int(len(finalized_probability)),
        "timestamps": int(finalized_probability["timestamp"].nunique()),
        "all_valid_point_probabilities_have_complete_intervals": (
            all_point_estimates_publishable
        ),
        "nonpublishable_point_estimates_remain_visible": bool(
            (~point_probabilities["probability_publishable"].astype(bool)).any()
            if not point_probabilities.empty
            else False
        ),
        "transition_diagnostics_complete": True,
        "transition_rows_sum_to_one": transition_rows_valid,
        "duration_and_occupancy_outputs_complete": True,
        "mechanism_contribution_decomposition_complete": True,
        "cross_model_disagreement_index_complete": True,
        "mechanism_coverage_map_complete": True,
        "sensitivity_diagnostics_complete": True,
        "external_chronology_validation_complete": False,
        "external_chronology_deferred_to_later_robustness": True,
        "automatic_model_selection_performed": False,
        "automatic_ensemble_performed": False,
        "final_v3_3_lock_permitted": False,
        "next_subgate": "V3-3D — Final Acceptance, Protected-Object Audit, and Lock",
    }

    output_hashes = {
        "panic_regime_probability.csv": _dataframe_hash(
            finalized_probability, ("timestamp", "model_id")
        ),
        "state_duration.csv": (
            stable_frame_hash(state_duration)
            if not state_duration.empty
            else sha256(b"EMPTY_STATE_DURATION").hexdigest()
        ),
        "mechanism_contributions.csv": (
            _dataframe_hash(contributions, ("timestamp", "model_id", "family"))
            if not contributions.empty
            else sha256(b"EMPTY_MECHANISM_CONTRIBUTIONS").hexdigest()
        ),
        "cross_model_disagreement.csv": _dataframe_hash(
            disagreement, ("timestamp",)
        ),
        "mechanism_coverage.csv": _dataframe_hash(
            coverage, ("timestamp", "family", "feature", "series_id")
        ),
        "transition_matrix.json": _canonical_json_hash(transition_matrix),
        "occupancy_statistics.json": _canonical_json_hash(occupancy),
        "mechanism_coverage_summary.json": _canonical_json_hash(coverage_summary),
        "sensitivity_diagnostics.json": _canonical_json_hash(sensitivity),
        "probability_diagnostics.json": _canonical_json_hash(diagnostics),
        "regime_validation_report.json": _canonical_json_hash(validation),
    }
    parent_manifest_hash = str(
        parent_engine_manifest.get("manifest_sha256")
        or _canonical_json_hash(
            {
                key: value
                for key, value in parent_engine_manifest.items()
                if key != "manifest_sha256"
            }
        )
    )
    market = market_structure.copy()
    market["timestamp"] = pd.to_datetime(
        market["timestamp"], utc=True, errors="coerce"
    )
    market = market.sort_values(
        ["timestamp", "window"], kind="mergesort"
    ).reset_index(drop=True)
    series = causal_series.copy()
    series["timestamp"] = pd.to_datetime(
        series["timestamp"], utc=True, errors="coerce"
    )
    series = series.sort_values(
        ["timestamp", "series_id"], kind="mergesort"
    ).reset_index(drop=True)
    manifest = PanicRegimeDiagnosticsManifest(
        schema_version=DIAGNOSTICS_SCHEMA_VERSION,
        parent_engine_manifest_sha256=parent_manifest_hash,
        probability_input_sha256=probability_input_hash,
        mechanism_input_sha256=mechanism_input_hash,
        market_structure_input_sha256=stable_frame_hash(market),
        causal_series_input_sha256=stable_frame_hash(series),
        engine_diagnostics_sha256=_canonical_json_hash(engine_diagnostics),
        configuration_sha256=stable_mapping_hash(config.to_dict()),
        output_hashes=output_hashes,
        probability_rows=int(len(finalized_probability)),
        timestamps=int(finalized_probability["timestamp"].nunique()),
    )
    return PanicRegimeDiagnosticsResult(
        probabilities=finalized_probability,
        transition_matrix=transition_matrix,
        state_duration=state_duration,
        occupancy_statistics=occupancy,
        mechanism_contributions=contributions,
        disagreement=disagreement,
        coverage=coverage,
        coverage_summary=coverage_summary,
        sensitivity=sensitivity,
        diagnostics=diagnostics,
        validation_report=validation,
        manifest=manifest,
    )
