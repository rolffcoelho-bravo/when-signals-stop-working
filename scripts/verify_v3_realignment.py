from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

CONTRACT = ROOT / "configs" / "v3_realignment_contract.json"
V3_G4_LOCK = ROOT / "V3_G4_SIGNAL_ENGINE_LOCK.json"
V3_G5_CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"

from shockbridge_signal_validity.v3.signal_registry import validate_registry


class RealignmentVerificationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise RealignmentVerificationError(message)


def require_file(relative: str) -> Path:
    path = ROOT / relative
    if not path.is_file():
        fail(f"Required realignment file is missing: {relative}")
    return path


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"Expected JSON object: {path.relative_to(ROOT)}")
    return value


def verify_parent_lock() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "scripts/verify_v3_g4_lock.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        fail(f"Gate V3-4 final lock verification failed: {detail}")
    lock = read_json(V3_G4_LOCK)
    if lock.get("status") != "IMPLEMENTATION_VALIDATED_AND_LOCKED":
        fail("Gate V3-4 is not finally locked")
    if lock.get("validated_implementation_commit") != (
        "a422db066e4a2f8b50f682df6a17b07c9ce0534c"
    ):
        fail("Gate V3-4 validated implementation commit changed")
    if lock.get("evidence_materialization_commit") != (
        "705511de9e8ee22a9f8aff34506aebb6c26223e7"
    ):
        fail("Gate V3-4 evidence materialization commit changed")
    return lock


def verify_research_anchor(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "v3.repository-realignment.v1":
        fail("Unexpected realignment schema version")
    if payload.get("gate") != "V3-REALIGNMENT":
        fail("Unexpected realignment gate identifier")
    if payload.get("status") != "RESEARCH_QUESTION_AND_GATE_SEQUENCE_REALIGNED":
        fail("Repository realignment is not complete")
    if payload.get("baseline_commit") != "5a07299367b80c3940e652e7bbdd208ce86ba5ef":
        fail("Frozen Version 2 baseline changed")

    anchor = payload.get("research_anchor", {})
    if anchor.get("original_question") != "When will RSI stop working?":
        fail("the practitioner's original question is not preserved")
    if anchor.get("corrected_practical_indicator") != "Bollinger Bands":
        fail("the practitioner's corrected practical indicator is not preserved")
    if anchor.get("establishment_precedes_deterioration") is not True:
        fail("Establishment-before-deterioration rule changed")
    if anchor.get("establishment_precedes_failure_probability") is not True:
        fail("Establishment-before-failure-probability rule changed")

    frozen = payload.get("frozen_determinations", {})
    if frozen.get("modified_by_realignment") is not False:
        fail("Realignment may not modify frozen determinations")
    if frozen.get("version_1") != {
        "rsi": "NOT_ESTABLISHED",
        "bollinger": "NOT_ESTABLISHED",
        "combined": "NOT_ESTABLISHED",
    }:
        fail("Frozen Version 1 determination changed")
    if frozen.get("version_2") != {
        "rsi": "NO_PIPELINE_ADMITTED",
        "bollinger": "NO_INCREMENTAL_EVIDENCE",
        "primary_case_established": False,
    }:
        fail("Frozen Version 2 determination changed")


def verify_v3_g4(payload: dict[str, Any], lock: dict[str, Any]) -> None:
    if "V3-4" not in payload.get("completed_core_gates", []):
        fail("Gate V3-4 is not recorded as completed")
    implementation = payload.get("v3_4_implementation", {})
    expected = {
        "status": "IMPLEMENTATION_VALIDATED_AND_LOCKED",
        "registered_signal_count": 54,
        "base_signal_count": 50,
        "interaction_signal_count": 4,
        "adaptive_template_count": 2,
        "validated_implementation_commit": (
            "a422db066e4a2f8b50f682df6a17b07c9ce0534c"
        ),
        "evidence_materialization_commit": (
            "705511de9e8ee22a9f8aff34506aebb6c26223e7"
        ),
        "lock_promotion_commit": "4150d73ff1e12d5b022e591f0a6ee700c29b5ce1",
        "lock_path": "V3_G4_SIGNAL_ENGINE_LOCK.json",
        "canonical_source_rows": 12171,
        "expected_feature_rows": 584208,
        "observed_feature_rows": 584208,
        "row_count_identity_verified": True,
        "large_signal_features_tracked": False,
        "large_signal_features_bound_by_sha256": True,
        "automatic_selection_performed": False,
        "target_accessed": False,
        "chronology_accessed": False,
        "predictive_claims_produced": False,
        "economic_claims_produced": False,
        "deterioration_claims_produced": False,
        "failure_claims_produced": False,
    }
    for field, value in expected.items():
        if implementation.get(field) != value:
            fail(f"Gate V3-4 locked evidence changed: {field}")
    if implementation.get("lock_blob_sha") != "721c559553f492427ca1f8792030c4bf32076a39":
        fail("Gate V3-4 promoted lock blob identity changed")
    if lock.get("acceptance_evidence", {}).get("registered_signal_count") != 54:
        fail("Gate V3-4 lock signal count changed")


def verify_v3_g5(payload: dict[str, Any]) -> None:
    current = payload.get("true_next_core_gate", {})
    expected_current = {
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
    if current != expected_current:
        fail("True current core gate is not the frozen V3-5 contract boundary")

    recorded = payload.get("v3_5_implementation", {})
    expected_recorded = {
        "gate": "V3-5",
        "title": "Matched Benchmark-versus-Signal Forecast Selection",
        "approval": "APPROVED",
        "status": "APPROVED_IMPLEMENTATION_STARTED_CONTRACT_FROZEN",
        "implementation_started": True,
        "contract_path": "configs/v3_g5_forecast_contract.json",
        "scope_path": "docs/V3_G5_MATCHED_FORECAST_SCOPE.md",
        "checkpoint_path": "V3_G5_MATCHED_FORECAST_CHECKPOINT.md",
        "contract_verifier": "scripts/verify_v3_g5_contract.py",
        "contract_tests": "tests/test_v3_g5_contract.py",
        "windows_runner": "RUN_V3_G5_CONTRACT.ps1",
        "posix_runner": "RUN_V3_G5_CONTRACT.sh",
        "target_accessed": False,
        "development_model_fitting_started": False,
        "signal_establishment_segment_accessed": False,
        "final_framework_reserve_accessed": False,
        "separate_approval_required": False,
        "next_action": "IMPLEMENT_TARGET_FOLD_BENCHMARK_AND_MATCHED_SELECTION_ENGINES",
    }
    if recorded != expected_recorded:
        fail("Gate V3-5 implementation boundary changed")

    for relative in payload.get("required_v3_5_contract_files", []):
        require_file(relative)
    contract = read_json(V3_G5_CONTRACT)
    if contract.get("status") != "APPROVED_IMPLEMENTATION_STARTED_CONTRACT_FROZEN":
        fail("Gate V3-5 forecast contract is not frozen")
    if contract.get("target_accessed") is not False:
        fail("Gate V3-5 target access advanced prematurely")
    if contract.get("final_framework_reserve_accessed") is not False:
        fail("Gate V3-5 final-framework reserve was accessed")
    if contract.get("forecast_horizons", {}).get("hours") != [4, 8, 12, 24, 48, 72]:
        fail("Gate V3-5 horizon set changed")


def verify_reclassification_and_controls(payload: dict[str, Any]) -> None:
    mappings = payload.get("regime_validation_reclassification", [])
    expected = {
        "V3-4A": ("V3-RV1", "COMPLETE_AND_HISTORICALLY_LOCKED"),
        "V3-4B": (
            "V3-RV2",
            "COMPLETE_AND_HISTORICALLY_LOCKED_WITH_PORTABILITY_REVISION_OPEN",
        ),
        "V3-4C": ("V3-RV3", "PAUSED_NOT_STARTED"),
    }
    observed = {
        item.get("historical_identifier"): (
            item.get("realigned_identifier"),
            item.get("status"),
        )
        for item in mappings
    }
    if observed != expected:
        fail("Regime-validation reclassification changed")
    if any(item.get("historical_files_renamed") is not False for item in mappings):
        fail("Historical chronology files may not be renamed")

    controls = payload.get("governance_controls", {})
    expected_false = (
        "historical_locks_rewritten",
        "chronology_may_tune_signal_registry",
        "panic_regime_may_rescue_v2_signal",
        "automatic_signal_selection_in_v3_4",
        "v3_4_protected_objects_may_change_in_v3_5",
        "v3_5_may_access_v3_9_final_reserve",
    )
    for field in expected_false:
        if controls.get(field) is not False:
            fail(f"Governance control changed: {field}")
    if controls.get("each_future_gate_must_state_richard_question_link") is not True:
        fail("Future gates are not linked to the practitioner's question")
    if controls.get("governance_must_be_proportional_to_scientific_gate") is not True:
        fail("Governance proportionality rule changed")

    stop_rules = payload.get("stop_rules", {})
    if stop_rules.get("no_established_signal") != (
        "FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED"
    ):
        fail("Establishment stop rule changed")
    if stop_rules.get("v3_5_final_reserve_access") != (
        "PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED"
    ):
        fail("V3-5 final reserve stop rule changed")


def verify_documents_and_registry(payload: dict[str, Any]) -> None:
    for relative in payload.get("required_documents", []):
        require_file(relative)

    registry = read_json(require_file("configs/v3_signal_interpretation_registry.json"))
    if len(validate_registry(registry)) != 54:
        fail("Committed V3-4 registry does not expand to 54 specifications")

    required_phrases = {
        "PRACTITIONER_QUESTION.md": (
            "When will RSI stop working?",
            "NO_PIPELINE_ADMITTED",
            "NO_INCREMENTAL_EVIDENCE",
        ),
        "DIRECT_ANSWER_LOGIC.md": (
            "ESTABLISHMENT",
            "FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED",
        ),
        "docs/V3_G5_MATCHED_FORECAST_SCOPE.md": (
            "PARENT_V3_4_VALIDATED_AND_LOCKED",
            "PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED",
            "4 hours",
            "72 hours",
        ),
        "V3_G5_MATCHED_FORECAST_CHECKPOINT.md": (
            "CONTRACT_FROZEN",
            "TARGET_ACCESS_NOT_STARTED",
            "failure modelling admissible: false",
        ),
    }
    for relative, phrases in required_phrases.items():
        text = require_file(relative).read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                fail(f"Required phrase missing from {relative}: {phrase}")


def main() -> int:
    payload = read_json(CONTRACT)
    verify_research_anchor(payload)
    lock = verify_parent_lock()
    verify_v3_g4(payload, lock)
    verify_v3_g5(payload)
    verify_reclassification_and_controls(payload)
    verify_documents_and_registry(payload)

    print("Version 3 repository realignment verification passed.")
    print("the practitioner question restored: True")
    print("Frozen V1/V2 determinations modified: False")
    print("Historical chronology work reclassified: V3-RV1/V3-RV2")
    print("Event alignment: V3-RV3 PAUSED_NOT_STARTED")
    print("Gate V3-4 status: IMPLEMENTATION_VALIDATED_AND_LOCKED")
    print("Validated V3-4 implementation commit: a422db066e4a2f8b50f682df6a17b07c9ce0534c")
    print("V3-4 evidence materialization commit: 705511de9e8ee22a9f8aff34506aebb6c26223e7")
    print("Current core gate: V3-5 — Matched Benchmark-versus-Signal Forecast Selection")
    print("Gate V3-5 status: APPROVED_IMPLEMENTATION_STARTED_CONTRACT_FROZEN")
    print("Gate V3-5 target access: False")
    print("Gate V3-5 model fitting started: False")
    print("Gate V3-5 establishment segment accessed: False")
    print("V3-9 final-framework reserve accessed: False")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, RealignmentVerificationError) as error:
        print(
            f"Version 3 repository realignment verification failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
