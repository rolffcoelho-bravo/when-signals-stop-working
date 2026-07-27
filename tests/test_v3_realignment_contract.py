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


def test_true_v3_g4_is_authoritatively_validated_without_empirical_claims() -> None:
    payload = contract()
    gate = payload["true_next_core_gate"]
    assert gate == {
        "gate": "V3-4",
        "title": "Unified RSI and Bollinger Interpretation Engine",
        "status": "AUTHORITATIVE_VALIDATION_COMPLETE_LOCK_PENDING",
        "implementation_started": True,
        "implementation_complete": True,
        "authoritative_validation_complete": True,
        "validated_implementation_commit": "ff2e7ecba3fa69f22e0b109437d23b52d30fba2b",
        "lock_created": False,
        "predictive_claims_permitted": False,
        "economic_claims_permitted": False,
        "failure_claims_permitted": False,
    }
    evidence = payload["v3_4_implementation"]
    assert evidence["registered_signal_count"] == 48
    assert evidence["canonical_source_rows"] == 12171
    assert evidence["expected_feature_rows"] == 584208
    assert evidence["observed_feature_rows"] == 584208
    assert evidence["row_count_identity_verified"] is True
    assert evidence["current_exact_suite_execution_pending"] is False
    assert evidence["real_data_execution_pending"] is False
    assert evidence["real_data_execution_passed"] is True
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


def test_parent_and_lock_finalization_boundaries_are_explicit() -> None:
    payload = contract()
    parent = payload["v3_1_parent_verification"]
    assert parent["historical_boundary_commit"] == (
        "7a7a5c55184aadfb436774ff1e497ce873a96b6e"
    )
    assert parent["historical_lock_rewritten"] is False
    assert parent["authoritative_windows_rerun_pending"] is False
    assert parent["authoritative_windows_rerun_passed"] is True

    lock = payload["v3_4_lock_finalization"]
    assert lock == {
        "status": "LOCK_MATERIALIZATION_PENDING",
        "validated_implementation_commit": "ff2e7ecba3fa69f22e0b109437d23b52d30fba2b",
        "lock_path": "V3_G4_SIGNAL_ENGINE_LOCK.json",
        "lock_candidate_generator": "scripts/finalize_v3_g4_lock.py",
        "lock_verifier": "scripts/verify_v3_g4_lock.py",
        "windows_runner": "RUN_V3_G4_LOCK.ps1",
        "posix_runner": "RUN_V3_G4_LOCK.sh",
        "large_signal_features_tracked": False,
        "large_signal_features_bound_by_sha256": True,
        "curated_evidence_directory": "evidence/v3/g4_signal_lock",
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


def test_core_sequence_and_v3_g5_approval_remain_governed() -> None:
    payload = contract()
    sequence = payload["core_sequence"]
    assert sequence.index("V3-4_SIGNAL_INTERPRETATION") < sequence.index(
        "V3-5_MATCHED_FORECAST_ESTABLISHMENT"
    )
    assert sequence.index("V3-5_MATCHED_FORECAST_ESTABLISHMENT") < sequence.index(
        "V3-6_PROSPECTIVE_FAILURE_DEFINITION"
    )
    assert payload["stop_rules"]["no_established_signal"] == (
        "FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED"
    )
    approval = payload["v3_5_approval"]
    assert approval == {
        "gate": "V3-5",
        "title": "Matched Benchmark-versus-Signal Forecast Selection",
        "status": "APPROVED_PENDING_V3_4_LOCK",
        "implementation_started": False,
        "parent_gate": "V3-4",
        "parent_authoritative_validation_required": True,
        "parent_authoritative_validation_complete": True,
        "parent_lock_required": True,
        "separate_approval_required_after_parent_lock": False,
        "predictive_evaluation_permitted_before_parent_lock": False,
    }


def test_required_documents_and_implementation_files_exist() -> None:
    payload = contract()
    for relative in payload["required_documents"]:
        assert (ROOT / relative).is_file(), relative
    for relative in payload["required_v3_4_files"]:
        assert (ROOT / relative).is_file(), relative

    checkpoint = (ROOT / "V3_G4_SIGNAL_ENGINE_CHECKPOINT.md").read_text(
        encoding="utf-8"
    )
    assert "AUTHORITATIVE_VALIDATION_COMPLETE_LOCK_PENDING" in checkpoint
    assert "ff2e7ecba3fa69f22e0b109437d23b52d30fba2b" in checkpoint
    assert "584208" in checkpoint


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
    assert (
        "True V3-4 status: AUTHORITATIVE_VALIDATION_COMPLETE_LOCK_PENDING"
        in completed.stdout
    )
    assert (
        "Validated V3-4 implementation commit: "
        "ff2e7ecba3fa69f22e0b109437d23b52d30fba2b"
        in completed.stdout
    )
    assert "Authoritative source rows: 12171" in completed.stdout
    assert "Authoritative feature rows: 584208" in completed.stdout
    assert "Gate V3-5 approval: APPROVED_PENDING_V3_4_LOCK" in completed.stdout
    assert "Gate V3-5 implementation started: False" in completed.stdout
