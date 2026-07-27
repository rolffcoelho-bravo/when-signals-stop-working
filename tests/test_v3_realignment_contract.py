from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "v3_realignment_contract.json"


def contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_richard_question_and_frozen_answer_are_restored() -> None:
    payload = contract()
    anchor = payload["research_anchor"]
    frozen = payload["frozen_determinations"]
    assert anchor["original_question"] == "When will RSI stop working?"
    assert anchor["corrected_practical_indicator"] == "Bollinger Bands"
    assert anchor["establishment_precedes_deterioration"] is True
    assert anchor["establishment_precedes_failure_probability"] is True
    assert frozen["version_1"] == {
        "rsi": "NOT_ESTABLISHED",
        "bollinger": "NOT_ESTABLISHED",
        "combined": "NOT_ESTABLISHED",
    }
    assert frozen["version_2"]["rsi"] == "NO_PIPELINE_ADMITTED"
    assert frozen["version_2"]["bollinger"] == "NO_INCREMENTAL_EVIDENCE"
    assert frozen["version_2"]["primary_case_established"] is False
    assert frozen["modified_by_realignment"] is False


def test_true_v3_g4_is_implemented_without_empirical_claims() -> None:
    payload = contract()
    gate = payload["true_next_core_gate"]
    assert gate == {
        "gate": "V3-4",
        "title": "Unified RSI and Bollinger Interpretation Engine",
        "status": "IMPLEMENTATION_COMPLETE_VALIDATION_PENDING",
        "implementation_started": True,
        "implementation_complete": True,
        "authoritative_validation_complete": False,
        "lock_created": False,
        "predictive_claims_permitted": False,
        "economic_claims_permitted": False,
        "failure_claims_permitted": False,
    }

    parent = payload["v3_1_parent_verification"]
    assert parent == {
        "historical_boundary_commit": "7a7a5c55184aadfb436774ff1e497ce873a96b6e",
        "historical_lock_rewritten": False,
        "historical_objects_verified_at_boundary": True,
        "current_direct_objects_verified_as_git_objects": True,
        "current_direct_worktree_mutations_fail_closed": True,
        "shared_export_surface": "src/shockbridge_signal_validity/v3/__init__.py",
        "shared_export_surface_may_have_later_owner": True,
        "v3_1_export_compatibility_required": True,
        "checkout_eol_invariant": True,
        "authoritative_windows_rerun_pending": True,
    }

    evidence = payload["v3_4_implementation"]
    assert evidence["registered_signal_count"] == 48
    assert evidence["base_signal_count"] == 44
    assert evidence["interaction_signal_count"] == 4
    assert evidence["adaptive_template_count"] == 2
    assert evidence["identifier_scheme"] == (
        "v3sig:<feature_key>:<sha256(canonical_specification)>"
    )
    assert evidence["prior_development_suite_passed"] == 19
    assert evidence["exact_hardened_suite_passed"] == 19
    assert evidence["final_hardening_applied_after_prior_suite"] is True
    assert evidence["current_exact_suite_execution_pending"] is True
    assert evidence["canonical_input_materialization"] == (
        "FROZEN_SOL_SNAPSHOT_VIA_LOCKED_V3_G1_ADAPTER"
    )
    assert evidence["canonical_source_path"] == "data/raw/sol_usdt_4h.csv"
    assert evidence["canonical_adapter_config"] == (
        "configs/v3_adapter_frozen_sol.json"
    )
    assert evidence["canonical_output_path"] == (
        "outputs/v3/data_adapter/canonical_market_data.csv"
    )
    assert evidence["real_data_execution_pending"] is True
    for field in (
        "automatic_selection_performed",
        "target_accessed",
        "chronology_accessed",
        "predictive_claims_produced",
        "economic_claims_produced",
        "deterioration_claims_produced",
        "failure_claims_produced",
    ):
        assert evidence[field] is False

    approval = payload["v3_5_approval"]
    assert approval == {
        "gate": "V3-5",
        "title": "Matched Benchmark-versus-Signal Forecast Selection",
        "status": "APPROVED_PENDING_V3_4_VALIDATION_AND_LOCK",
        "implementation_started": False,
        "parent_gate": "V3-4",
        "parent_authoritative_validation_required": True,
        "parent_lock_required": True,
        "separate_approval_required_after_parent_lock": False,
        "predictive_evaluation_permitted_before_parent_lock": False,
    }


def test_chronology_work_is_reclassified_without_rewriting_history() -> None:
    mappings = contract()["regime_validation_reclassification"]
    assert [item["historical_identifier"] for item in mappings] == [
        "V3-4A",
        "V3-4B",
        "V3-4C",
    ]
    assert [item["realigned_identifier"] for item in mappings] == [
        "V3-RV1",
        "V3-RV2",
        "V3-RV3",
    ]
    assert mappings[2]["status"] == "PAUSED_NOT_STARTED"
    assert all(item["historical_files_renamed"] is False for item in mappings)


def test_core_sequence_places_signal_establishment_before_failure_model() -> None:
    sequence = contract()["core_sequence"]
    assert sequence.index("V3-4_SIGNAL_INTERPRETATION") < sequence.index(
        "V3-5_MATCHED_FORECAST_ESTABLISHMENT"
    )
    assert sequence.index("V3-5_MATCHED_FORECAST_ESTABLISHMENT") < sequence.index(
        "V3-6_PROSPECTIVE_FAILURE_DEFINITION"
    )
    assert sequence.index("V3-6_PROSPECTIVE_FAILURE_DEFINITION") < sequence.index(
        "V3-7_FAILURE_PROBABILITY"
    )
    assert contract()["stop_rules"]["no_established_signal"] == (
        "FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED"
    )


def test_required_documents_and_v3_g4_implementation_files_exist() -> None:
    payload = contract()
    for relative in payload["required_documents"]:
        assert (ROOT / relative).is_file(), relative
    for relative in payload["required_v3_4_files"]:
        assert (ROOT / relative).is_file(), relative

    richard = (ROOT / "RICHARD_QUESTION.md").read_text(encoding="utf-8")
    direct = (ROOT / "DIRECT_ANSWER_LOGIC.md").read_text(encoding="utf-8")
    decision = (ROOT / "V3_REALIGNMENT_DECISION.md").read_text(encoding="utf-8")
    gate_map = (ROOT / "docs" / "V3_REALIGNED_GATE_MAP.md").read_text(
        encoding="utf-8"
    )
    scope = (ROOT / "docs" / "V3_G4_SIGNAL_ENGINE_SCOPE.md").read_text(
        encoding="utf-8"
    )
    implementation = (ROOT / "docs" / "V3_G4_SIGNAL_ENGINE.md").read_text(
        encoding="utf-8"
    )

    assert "When will RSI stop working?" in richard
    assert "NO_PIPELINE_ADMITTED" in richard
    assert "NO_INCREMENTAL_EVIDENCE" in richard
    assert "ESTABLISHMENT" in direct
    assert "FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED" in direct
    assert "V3-RV3" in decision
    assert "Unified RSI and Bollinger Interpretation Engine" in decision
    assert "APPROVED / BLOCKED BY V3-4 VALIDATION AND LOCK" in decision
    assert "V3-4_SIGNAL_INTERPRETATION" in gate_map
    assert "APPROVED_AND_REOPENED" in scope
    assert "IMPLEMENTATION_COMPLETE_VALIDATION_PENDING" in scope
    assert "IMPLEMENTATION_COMPLETE" in implementation
    assert "PRIOR_DEVELOPMENT_SUITE_19_PASSED" in implementation
    assert "CURRENT_HARDENED_SUITE_EXECUTION_PENDING" in implementation


def test_governance_controls_fail_closed() -> None:
    controls = contract()["governance_controls"]
    assert controls == {
        "historical_locks_rewritten": False,
        "chronology_may_tune_signal_registry": False,
        "panic_regime_may_rescue_v2_signal": False,
        "automatic_signal_selection_in_v3_4": False,
        "each_future_gate_must_state_richard_question_link": True,
        "governance_must_be_proportional_to_scientific_gate": True,
    }


def test_realignment_verifier_passes() -> None:
    completed = subprocess.run(
        ["python", "scripts/verify_v3_realignment.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "Richard question restored: True" in completed.stdout
    assert "True V3-4 implementation started: True" in completed.stdout
    assert (
        "True V3-4 status: IMPLEMENTATION_COMPLETE_VALIDATION_PENDING"
        in completed.stdout
    )
    assert "V3-1 historical-owner boundary preserved: True" in completed.stdout
    assert "Registered signal specifications: 48" in completed.stdout
    assert "Current hardened V3-4 suite execution pending: True" in completed.stdout
    assert (
        "Gate V3-5 approval: APPROVED_PENDING_V3_4_VALIDATION_AND_LOCK"
        in completed.stdout
    )
    assert "Gate V3-5 implementation started: False" in completed.stdout
