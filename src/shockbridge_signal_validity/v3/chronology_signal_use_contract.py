from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


EXPECTED_PARENT_LOCK = "V3_G3_PANIC_REGIME_LOCK.json"
EXPECTED_PARENT_BLOB = "0e35908c03e36d8caeb832a078ff0566ef4e2ea4"
EXPECTED_MODELS = {
    "MONOTONE_MECHANISM_SCORE_V1",
    "CAUSAL_GAUSSIAN_HMM_V1",
}
EXPECTED_EVENT_TYPES = {
    "LIQUIDITY_DISLOCATION",
    "FUNDING_STRESS",
    "LIQUIDATION_CASCADE",
    "VOLATILITY_SHOCK",
    "DOWNSIDE_DISLOCATION",
    "MARKET_STRUCTURE_BREAK",
    "EXCHANGE_OR_VENUE_DISRUPTION",
    "CROSS_MARKET_CONTAGION",
}
EXPECTED_OUTPUTS = {
    "external_chronology.csv",
    "chronology_manifest.json",
    "chronology_provenance.json",
    "chronology_merge_log.csv",
    "event_alignment.csv",
    "lead_lag_diagnostics.json",
    "false_alert_burden.json",
    "chronology_validation_report.json",
    "signal_use_eligibility.json",
    "conditional_signal_diagnostics.csv",
    "v3_g4_decision_report.json",
}


class ChronologySignalUseContractError(ValueError):
    """Raised when the frozen Gate V3-4A contract is invalid."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ChronologySignalUseContractError(message)


def load_contract(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_contract(contract: Mapping[str, Any]) -> None:
    _require(contract.get("gate") == "V3-4A", "Unexpected gate identifier")
    _require(
        contract.get("status")
        == "INDEPENDENT_CHRONOLOGY_AND_SIGNAL_USE_CONTRACT_FROZEN",
        "Contract is not frozen",
    )

    upstream = contract.get("upstream_contract", {})
    _require(upstream.get("parent_lock") == EXPECTED_PARENT_LOCK, "Parent lock changed")
    _require(
        upstream.get("parent_lock_blob_sha") == EXPECTED_PARENT_BLOB,
        "Parent lock blob changed",
    )
    _require(
        upstream.get("version_1_and_version_2_determinations_immutable") is True,
        "Frozen V1/V2 determinations are not protected",
    )
    _require(
        upstream.get("v3_3_models_thresholds_and_protected_objects_immutable") is True,
        "Gate V3-3 is not protected",
    )

    question = contract.get("scientific_question", {})
    _require(
        question.get("chronology_is_ground_truth_label") is False,
        "Chronology cannot be ground truth",
    )
    prohibited_claims = set(question.get("prohibited_claims", []))
    _require(
        "RSI rescue through regime conditioning" in prohibited_claims,
        "RSI rescue prohibition missing",
    )
    _require(
        "Bollinger rescue through regime conditioning" in prohibited_claims,
        "Bollinger rescue prohibition missing",
    )

    chronology = contract.get("chronology_registry", {})
    _require(
        chronology.get("construction_order")
        == "chronology_registry_locked_before_model_output_overlay",
        "Chronology must be locked before model overlay",
    )
    for field in (
        "model_outputs_hidden_during_compilation",
        "model_derived_events_prohibited",
        "retrospective_event_deletion_prohibited",
        "retrospective_event_boundary_tuning_prohibited",
    ):
        _require(chronology.get(field) is True, f"Chronology control missing: {field}")
    _require(
        set(chronology.get("event_taxonomy", [])) == EXPECTED_EVENT_TYPES,
        "Event taxonomy changed",
    )
    _require(
        len(chronology.get("required_event_fields", [])) >= 12,
        "Event provenance fields are incomplete",
    )

    alignment = contract.get("event_alignment_evaluation", {})
    _require(
        set(alignment.get("registered_models", [])) == EXPECTED_MODELS,
        "Registered models changed",
    )
    _require(
        alignment.get("central_operational_thresholds_inherited_from_v3_3") is True,
        "V3-3 thresholds not inherited",
    )
    _require(
        alignment.get("threshold_selection_against_chronology_prohibited") is True,
        "Chronology threshold selection permitted",
    )
    _require(
        alignment.get("model_ranking_or_selection_prohibited") is True,
        "Model selection permitted",
    )
    _require(
        alignment.get(
            "classification_metrics_prohibited_without_complete_event_registry"
        )
        is True,
        "Incomplete chronology classification risk not controlled",
    )
    _require(
        alignment.get("lead_horizons_observations") == [1, 3, 6, 12],
        "Lead horizons changed",
    )
    _require(
        alignment.get("decay_horizons_observations") == [1, 3, 6, 12],
        "Decay horizons changed",
    )

    eligibility = contract.get("signal_use_eligibility", {})
    frozen = eligibility.get("frozen_signal_statuses", {})
    _require(
        frozen.get("RSI", {}).get("version_2_status") == "NO_PIPELINE_ADMITTED",
        "RSI status changed",
    )
    _require(
        frozen.get("BOLLINGER", {}).get("version_2_status")
        == "NO_INCREMENTAL_EVIDENCE",
        "Bollinger status changed",
    )
    for signal in ("RSI", "BOLLINGER"):
        _require(
            frozen.get(signal, {}).get("eligibility")
            == "INELIGIBLE_BASELINE_NOT_ESTABLISHED",
            f"{signal} conditional eligibility is invalid",
        )
    _require(
        eligibility.get("regime_conditioning_cannot_promote_signal") is True,
        "Signal promotion is permitted",
    )
    _require(
        eligibility.get("regime_conditioning_cannot_change_frozen_unconditional_verdict")
        is True,
        "Frozen verdict can change",
    )

    diagnostic = contract.get("conditional_diagnostic_design", {})
    for field in (
        "signal_parameters_frozen",
        "signal_retraining_or_retuning_prohibited",
        "regime_threshold_retuning_prohibited",
        "descriptive_only_for_current_rsi_and_bollinger",
        "dependence_aware_inference_required",
        "chronological_evaluation_required",
    ):
        _require(
            diagnostic.get(field) is True,
            f"Conditional diagnostic control missing: {field}",
        )
    _require(
        diagnostic.get("minimum_regime_observations", 0) >= 50,
        "Regime sample boundary too weak",
    )
    _require(
        diagnostic.get("minimum_regime_episodes", 0) >= 5,
        "Episode boundary too weak",
    )

    reporting = contract.get("multiplicity_and_reporting", {})
    _require(reporting.get("familywise_method") == "holm", "Multiplicity method changed")
    _require(
        reporting.get("primary_hypotheses_predeclared_before_overlay") is True,
        "Hypotheses not predeclared",
    )
    _require(
        reporting.get("negative_and_insufficient_results_retained") is True,
        "Negative results may be suppressed",
    )

    _require(
        set(contract.get("required_outputs", [])) == EXPECTED_OUTPUTS,
        "Required output contract changed",
    )
    sequence = contract.get("subgate_sequence", [])
    _require(
        [item.get("gate") for item in sequence]
        == ["V3-4A", "V3-4B", "V3-4C", "V3-4D"],
        "Subgate sequence changed",
    )
    _require(
        sequence[0].get("may_access_model_outputs") is False,
        "V3-4A may not access model outputs",
    )
    _require(
        sequence[1].get("may_access_model_outputs") is False,
        "V3-4B may not access model outputs",
    )
