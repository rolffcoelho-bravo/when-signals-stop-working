from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
CONTRACT = ROOT / "configs" / "v3_realignment_contract.json"

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


def require_equal(observed: object, expected: object, label: str) -> None:
    if observed != expected:
        fail(f"{label} changed")


def main() -> int:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require_equal(payload.get("schema_version"), "v3.repository-realignment.v1", "Schema")
    require_equal(payload.get("gate"), "V3-REALIGNMENT", "Gate identifier")
    require_equal(
        payload.get("status"),
        "RESEARCH_QUESTION_AND_GATE_SEQUENCE_REALIGNED",
        "Realignment status",
    )
    require_equal(
        payload.get("baseline_commit"),
        "5a07299367b80c3940e652e7bbdd208ce86ba5ef",
        "Frozen Version 2 baseline",
    )

    anchor = payload.get("research_anchor", {})
    require_equal(anchor.get("original_question"), "When will RSI stop working?", "Richard question")
    require_equal(anchor.get("corrected_practical_indicator"), "Bollinger Bands", "Corrected indicator")
    require_equal(anchor.get("establishment_precedes_deterioration"), True, "Establishment rule")
    require_equal(anchor.get("establishment_precedes_failure_probability"), True, "Failure rule")

    frozen = payload.get("frozen_determinations", {})
    require_equal(frozen.get("modified_by_realignment"), False, "Frozen determinations")
    require_equal(frozen.get("version_2", {}).get("rsi"), "NO_PIPELINE_ADMITTED", "V2 RSI")
    require_equal(
        frozen.get("version_2", {}).get("bollinger"),
        "NO_INCREMENTAL_EVIDENCE",
        "V2 Bollinger",
    )
    require_equal(
        frozen.get("version_2", {}).get("primary_case_established"),
        False,
        "V2 establishment",
    )

    current = payload.get("true_next_core_gate", {})
    expected_current = {
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
    require_equal(current, expected_current, "Current V3-4 boundary")

    parent = payload.get("v3_1_parent_verification", {})
    expected_parent = {
        "historical_boundary_commit": "7a7a5c55184aadfb436774ff1e497ce873a96b6e",
        "historical_lock_rewritten": False,
        "historical_objects_verified_at_boundary": True,
        "current_direct_objects_verified_as_git_objects": True,
        "current_direct_worktree_mutations_fail_closed": True,
        "shared_export_surface": "src/shockbridge_signal_validity/v3/__init__.py",
        "shared_export_surface_may_have_later_owner": True,
        "v3_1_export_compatibility_required": True,
        "checkout_eol_invariant": True,
        "authoritative_windows_rerun_pending": False,
        "authoritative_windows_rerun_passed": True,
    }
    require_equal(parent, expected_parent, "V3-1 parent verification")

    implementation = payload.get("v3_4_implementation", {})
    expected_implementation = {
        "registered_signal_count": 48,
        "base_signal_count": 44,
        "interaction_signal_count": 4,
        "adaptive_template_count": 2,
        "identifier_scheme": "v3sig:<feature_key>:<sha256(canonical_specification)>",
        "prior_development_suite_passed": 19,
        "exact_hardened_suite_passed": 19,
        "final_hardening_applied_after_prior_suite": True,
        "current_exact_suite_execution_pending": False,
        "canonical_input_materialization": "FROZEN_SOL_SNAPSHOT_VIA_LOCKED_V3_G1_ADAPTER",
        "canonical_source_path": "data/raw/sol_usdt_4h.csv",
        "canonical_adapter_config": "configs/v3_adapter_frozen_sol.json",
        "canonical_output_path": "outputs/v3/data_adapter/canonical_market_data.csv",
        "canonical_source_rows": 12171,
        "canonical_data_sha256": "3c49bfcab5fdf3aba9ada614873fa424e97c1f66e2690b790204fc29fdb5109c",
        "real_data_execution_pending": False,
        "real_data_execution_passed": True,
        "expected_feature_rows": 584208,
        "observed_feature_rows": 584208,
        "row_count_identity_verified": True,
        "automatic_selection_performed": False,
        "target_accessed": False,
        "chronology_accessed": False,
        "predictive_claims_produced": False,
        "economic_claims_produced": False,
        "deterioration_claims_produced": False,
        "failure_claims_produced": False,
    }
    require_equal(implementation, expected_implementation, "V3-4 implementation evidence")

    lock_finalization = payload.get("v3_4_lock_finalization", {})
    expected_lock_finalization = {
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
    require_equal(lock_finalization, expected_lock_finalization, "V3-4 lock finalization")

    v3_5 = payload.get("v3_5_approval", {})
    expected_v3_5 = {
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
    require_equal(v3_5, expected_v3_5, "V3-5 approval boundary")

    mappings = payload.get("regime_validation_reclassification", [])
    expected_mappings = {
        "V3-4A": ("V3-RV1", "COMPLETE_AND_HISTORICALLY_LOCKED"),
        "V3-4B": (
            "V3-RV2",
            "COMPLETE_AND_HISTORICALLY_LOCKED_WITH_PORTABILITY_REVISION_OPEN",
        ),
        "V3-4C": ("V3-RV3", "PAUSED_NOT_STARTED"),
    }
    observed_mappings = {
        item.get("historical_identifier"): (
            item.get("realigned_identifier"),
            item.get("status"),
        )
        for item in mappings
    }
    require_equal(observed_mappings, expected_mappings, "Regime-validation reclassification")
    if any(item.get("historical_files_renamed") is not False for item in mappings):
        fail("Historical chronology files may not be renamed")

    controls = payload.get("governance_controls", {})
    expected_controls = {
        "historical_locks_rewritten": False,
        "chronology_may_tune_signal_registry": False,
        "panic_regime_may_rescue_v2_signal": False,
        "automatic_signal_selection_in_v3_4": False,
        "each_future_gate_must_state_richard_question_link": True,
        "governance_must_be_proportional_to_scientific_gate": True,
    }
    require_equal(controls, expected_controls, "Governance controls")

    for relative in payload.get("required_documents", []):
        require_file(relative)
    for relative in payload.get("required_v3_4_files", []):
        require_file(relative)

    registry = json.loads(
        require_file("configs/v3_signal_interpretation_registry.json").read_text(
            encoding="utf-8"
        )
    )
    specs = validate_registry(registry)
    if len(specs) != 48:
        fail("Committed V3-4 registry does not expand to 48 specifications")

    required_phrases = {
        "RICHARD_QUESTION.md": (
            "When will RSI stop working?",
            "NO_PIPELINE_ADMITTED",
            "NO_INCREMENTAL_EVIDENCE",
        ),
        "DIRECT_ANSWER_LOGIC.md": (
            "ESTABLISHMENT",
            "FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED",
        ),
        "V3_REALIGNMENT_DECISION.md": (
            "V3-RV3",
            "Unified RSI and Bollinger Interpretation Engine",
        ),
        "docs/V3_REALIGNED_GATE_MAP.md": (
            "V3-4_SIGNAL_INTERPRETATION",
            "Regime-validation extension",
        ),
        "docs/V3_G4_SIGNAL_ENGINE_SCOPE.md": (
            "APPROVED_AND_REOPENED",
            "Gate V3-5",
        ),
        "docs/V3_G4_SIGNAL_ENGINE.md": (
            "IMPLEMENTATION_COMPLETE",
            "Gate V3-5",
        ),
        "V3_G4_SIGNAL_ENGINE_CHECKPOINT.md": (
            "AUTHORITATIVE_VALIDATION_COMPLETE_LOCK_PENDING",
            "ff2e7ecba3fa69f22e0b109437d23b52d30fba2b",
        ),
    }
    for relative, phrases in required_phrases.items():
        text = require_file(relative).read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                fail(f"Required phrase missing from {relative}: {phrase}")

    print("Version 3 repository realignment verification passed.")
    print("Richard question restored: True")
    print("Frozen V1/V2 determinations modified: False")
    print("Historical chronology work reclassified: V3-RV1/V3-RV2")
    print("Event alignment: V3-RV3 PAUSED_NOT_STARTED")
    print("Current core gate: V3-4 — Unified RSI and Bollinger Interpretation Engine")
    print("True V3-4 status: AUTHORITATIVE_VALIDATION_COMPLETE_LOCK_PENDING")
    print("Validated V3-4 implementation commit: ff2e7ecba3fa69f22e0b109437d23b52d30fba2b")
    print("V3-1 historical-owner boundary preserved: True")
    print("Registered signal specifications: 48")
    print("Authoritative source rows: 12171")
    print("Authoritative feature rows: 584208")
    print("Gate V3-5 approval: APPROVED_PENDING_V3_4_LOCK")
    print("Gate V3-5 implementation started: False")
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
