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
    gate = contract()["true_next_core_gate"]
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
    evidence = contract()["v3_4_implementation"]
    assert evidence["registered_signal_count"] == 48
    assert evidence["base_signal_count"] == 44
    assert evidence["interaction_signal_count"] == 4
    assert evidence["adaptive_template_count"] == 2
    assert evidence["development_tests_passed"] == 19
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
    assert "V3-4_SIGNAL_INTERPRETATION" in gate_map
    assert "APPROVED_AND_REOPENED" in scope
    assert "IMPLEMENTATION_COMPLETE_VALIDATION_PENDING" in scope
    assert "IMPLEMENTATION_COMPLETE" in implementation
    assert "DEVELOPMENT_TESTS_19_PASSED" in implementation


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
    assert "Registered signal specifications: 48" in completed.stdout
