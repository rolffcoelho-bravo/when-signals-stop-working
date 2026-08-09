from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "v3_realignment_contract.json"


def contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_richard_question_and_frozen_answers_remain_unchanged() -> None:
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
    assert frozen["version_2"] == {
        "rsi": "NO_PIPELINE_ADMITTED",
        "bollinger": "NO_INCREMENTAL_EVIDENCE",
        "primary_case_established": False,
    }
    assert frozen["modified_by_realignment"] is False


def test_v3_g4_is_completed_validated_and_finally_locked() -> None:
    payload = contract()
    assert "V3-4" in payload["completed_core_gates"]
    evidence = payload["v3_4_implementation"]
    assert evidence["status"] == "IMPLEMENTATION_VALIDATED_AND_LOCKED"
    assert evidence["validated_implementation_commit"] == (
        "ff2e7ecba3fa69f22e0b109437d23b52d30fba2b"
    )
    assert evidence["evidence_materialization_commit"] == (
        "705511de9e8ee22a9f8aff34506aebb6c26223e7"
    )
    assert evidence["lock_promotion_commit"] == (
        "4150d73ff1e12d5b022e591f0a6ee700c29b5ce1"
    )
    assert evidence["registered_signal_count"] == 48
    assert evidence["canonical_source_rows"] == 12171
    assert evidence["expected_feature_rows"] == 584208
    assert evidence["observed_feature_rows"] == 584208
    assert evidence["row_count_identity_verified"] is True
    assert evidence["large_signal_features_tracked"] is False
    assert evidence["large_signal_features_bound_by_sha256"] is True

    lock = json.loads((ROOT / "V3_G4_SIGNAL_ENGINE_LOCK.json").read_text())
    assert lock["status"] == "IMPLEMENTATION_VALIDATED_AND_LOCKED"
    assert lock["evidence_materialization_commit"] == (
        "705511de9e8ee22a9f8aff34506aebb6c26223e7"
    )


def test_v3_g5_is_the_current_frozen_contract_boundary() -> None:
    payload = contract()
    assert payload["true_next_core_gate"] == {
        "gate": "V3-5",
        "title": "Matched Benchmark-versus-Signal Forecast Selection",
        "status": "APPROVED_IMPLEMENTATION_STARTED_CONTRACT_FROZEN",
        "implementation_started": True,
        "implementation_complete": False,
        "contract_frozen": True,
        "target_accessed": False,
        "development_model_fitting_started": False,
        "signal_establishment_segment_accessed": False,
        "final_framework_reserve_accessed": False,
        "predictive_claims_permitted": False,
        "economic_claims_permitted": False,
        "failure_claims_permitted": False,
    }
    implementation = payload["v3_5_implementation"]
    assert implementation["approval"] == "APPROVED"
    assert implementation["implementation_started"] is True
    assert implementation["status"] == (
        "APPROVED_IMPLEMENTATION_STARTED_CONTRACT_FROZEN"
    )
    assert implementation["target_accessed"] is False
    assert implementation["development_model_fitting_started"] is False
    assert implementation["signal_establishment_segment_accessed"] is False
    assert implementation["final_framework_reserve_accessed"] is False
    assert implementation["separate_approval_required"] is False


def test_v3_g5_contract_files_and_final_reserve_controls_exist() -> None:
    payload = contract()
    for relative in payload["required_documents"]:
        assert (ROOT / relative).is_file(), relative
    for relative in payload["required_v3_5_contract_files"]:
        assert (ROOT / relative).is_file(), relative

    forecast = json.loads(
        (ROOT / "configs" / "v3_g5_forecast_contract.json").read_text(
            encoding="utf-8"
        )
    )
    assert forecast["forecast_horizons"]["hours"] == [4, 8, 12, 24, 48, 72]
    assert forecast["data_partition"]["final_framework_reserve_start_utc"] == (
        "2026-01-01T00:00:00Z"
    )
    assert forecast["data_partition"]["v3_5_may_access_final_framework_reserve"] is False
    assert forecast["final_framework_reserve"]["reserved_for_gate"] == "V3-9"
    assert forecast["final_framework_reserve"]["v3_5_access_prohibited"] is True
    assert forecast["final_framework_reserve_accessed"] is False


def test_chronology_reclassification_and_establishment_sequence_remain_intact() -> None:
    payload = contract()
    mappings = payload["regime_validation_reclassification"]
    assert [item["realigned_identifier"] for item in mappings] == [
        "V3-RV1",
        "V3-RV2",
        "V3-RV3",
    ]
    assert mappings[2]["status"] == "PAUSED_NOT_STARTED"
    assert all(item["historical_files_renamed"] is False for item in mappings)

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
    assert payload["stop_rules"]["v3_5_final_reserve_access"] == (
        "PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED"
    )


def test_governance_controls_prohibit_rescue_drift_and_reserve_access() -> None:
    controls = contract()["governance_controls"]
    for field in (
        "historical_locks_rewritten",
        "chronology_may_tune_signal_registry",
        "panic_regime_may_rescue_v2_signal",
        "automatic_signal_selection_in_v3_4",
        "v3_4_protected_objects_may_change_in_v3_5",
        "v3_5_may_access_v3_9_final_reserve",
    ):
        assert controls[field] is False
    assert controls["each_future_gate_must_state_richard_question_link"] is True
    assert controls["governance_must_be_proportional_to_scientific_gate"] is True


def test_realignment_verifier_passes_at_active_v3_g5_boundary() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/verify_v3_realignment.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "the practitioner question restored: True" in completed.stdout
    assert "Gate V3-4 status: IMPLEMENTATION_VALIDATED_AND_LOCKED" in completed.stdout
    assert (
        "Current core gate: V3-5 — Matched Benchmark-versus-Signal Forecast Selection"
        in completed.stdout
    )
    assert (
        "Gate V3-5 status: APPROVED_IMPLEMENTATION_STARTED_CONTRACT_FROZEN"
        in completed.stdout
    )
    assert "Gate V3-5 target access: False" in completed.stdout
    assert "V3-9 final-framework reserve accessed: False" in completed.stdout
