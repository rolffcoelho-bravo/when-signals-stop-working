from __future__ import annotations

import copy
from pathlib import Path

import pytest

from shockbridge_signal_validity.v3.chronology_signal_use_contract import (
    ChronologySignalUseContractError,
    EXPECTED_OUTPUTS,
    load_contract,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "v3_external_chronology_signal_use_contract.json"


def contract() -> dict:
    return load_contract(CONTRACT)


def test_frozen_contract_validates() -> None:
    validate_contract(contract())


def test_parent_lock_and_frozen_determinations_are_exact() -> None:
    value = contract()["upstream_contract"]
    assert value["parent_lock"] == "V3_G3_PANIC_REGIME_LOCK.json"
    assert (
        value["parent_lock_blob_sha"]
        == "0e35908c03e36d8caeb832a078ff0566ef4e2ea4"
    )
    assert value["version_1_and_version_2_determinations_immutable"] is True
    assert value["v3_3_models_thresholds_and_protected_objects_immutable"] is True


def test_chronology_is_compiled_independently_before_overlay() -> None:
    value = contract()["chronology_registry"]
    assert (
        value["construction_order"]
        == "chronology_registry_locked_before_model_output_overlay"
    )
    assert value["model_outputs_hidden_during_compilation"] is True
    assert value["model_derived_events_prohibited"] is True
    assert value["retrospective_event_deletion_prohibited"] is True
    assert value["retrospective_event_boundary_tuning_prohibited"] is True


def test_chronology_is_not_treated_as_complete_ground_truth() -> None:
    value = contract()
    assert value["scientific_question"]["chronology_is_ground_truth_label"] is False
    alignment = value["event_alignment_evaluation"]
    assert alignment["chronology_completeness_adjustment_required"] is True
    assert (
        alignment["classification_metrics_prohibited_without_complete_event_registry"]
        is True
    )


def test_alignment_metrics_horizons_and_models_are_frozen() -> None:
    value = contract()["event_alignment_evaluation"]
    assert value["registered_models"] == [
        "MONOTONE_MECHANISM_SCORE_V1",
        "CAUSAL_GAUSSIAN_HMM_V1",
    ]
    assert value["lead_horizons_observations"] == [1, 3, 6, 12]
    assert value["decay_horizons_observations"] == [1, 3, 6, 12]
    assert value["threshold_selection_against_chronology_prohibited"] is True
    assert value["model_ranking_or_selection_prohibited"] is True


def test_rsi_and_bollinger_remain_ineligible_for_rescue() -> None:
    value = contract()["signal_use_eligibility"]
    frozen = value["frozen_signal_statuses"]
    assert frozen["RSI"]["version_2_status"] == "NO_PIPELINE_ADMITTED"
    assert frozen["BOLLINGER"]["version_2_status"] == "NO_INCREMENTAL_EVIDENCE"
    assert frozen["RSI"]["eligibility"] == "INELIGIBLE_BASELINE_NOT_ESTABLISHED"
    assert (
        frozen["BOLLINGER"]["eligibility"]
        == "INELIGIBLE_BASELINE_NOT_ESTABLISHED"
    )
    assert value["regime_conditioning_cannot_promote_signal"] is True
    assert value["regime_conditioning_cannot_change_frozen_unconditional_verdict"] is True


def test_conditional_diagnostics_are_frozen_and_descriptive() -> None:
    value = contract()["conditional_diagnostic_design"]
    assert value["signal_parameters_frozen"] is True
    assert value["signal_retraining_or_retuning_prohibited"] is True
    assert value["regime_threshold_retuning_prohibited"] is True
    assert value["descriptive_only_for_current_rsi_and_bollinger"] is True
    assert value["minimum_regime_observations"] >= 50
    assert value["minimum_regime_episodes"] >= 5


def test_multiplicity_and_negative_result_retention_are_frozen() -> None:
    value = contract()["multiplicity_and_reporting"]
    assert value["familywise_method"] == "holm"
    assert value["primary_hypotheses_predeclared_before_overlay"] is True
    assert value["raw_and_adjusted_results_reported"] is True
    assert value["negative_and_insufficient_results_retained"] is True
    assert value["favourable_subgroup_suppression_prohibited"] is True


def test_required_outputs_and_subgate_sequence_are_frozen() -> None:
    value = contract()
    assert set(value["required_outputs"]) == EXPECTED_OUTPUTS
    assert [item["gate"] for item in value["subgate_sequence"]] == [
        "V3-4A",
        "V3-4B",
        "V3-4C",
        "V3-4D",
    ]
    assert value["subgate_sequence"][0]["may_access_model_outputs"] is False
    assert value["subgate_sequence"][1]["may_access_model_outputs"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        ("upstream_contract", "parent_lock_blob_sha", "invalid"),
        ("chronology_registry", "model_outputs_hidden_during_compilation", False),
        (
            "event_alignment_evaluation",
            "threshold_selection_against_chronology_prohibited",
            False,
        ),
        ("signal_use_eligibility", "regime_conditioning_cannot_promote_signal", False),
        (
            "conditional_diagnostic_design",
            "signal_retraining_or_retuning_prohibited",
            False,
        ),
    ],
)
def test_contract_mutations_fail_closed(
    mutation: tuple[str, str, object],
) -> None:
    value = copy.deepcopy(contract())
    section, field, replacement = mutation
    value[section][field] = replacement
    with pytest.raises(ChronologySignalUseContractError):
        validate_contract(value)
