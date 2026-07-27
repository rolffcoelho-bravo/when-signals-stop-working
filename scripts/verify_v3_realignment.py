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


def main() -> int:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "v3.repository-realignment.v1":
        fail("Unexpected realignment schema version")
    if payload.get("gate") != "V3-REALIGNMENT":
        fail("Unexpected gate identifier")
    if payload.get("status") != "RESEARCH_QUESTION_AND_GATE_SEQUENCE_REALIGNED":
        fail("Repository realignment is not complete")
    if payload.get("baseline_commit") != "5a07299367b80c3940e652e7bbdd208ce86ba5ef":
        fail("Frozen Version 2 baseline changed")

    anchor = payload.get("research_anchor", {})
    if anchor.get("original_question") != "When will RSI stop working?":
        fail("Richard's original question is not preserved")
    if anchor.get("corrected_practical_indicator") != "Bollinger Bands":
        fail("Richard's corrected practical indicator is not preserved")
    if anchor.get("establishment_precedes_deterioration") is not True:
        fail("Establishment-before-deterioration rule changed")
    if anchor.get("establishment_precedes_failure_probability") is not True:
        fail("Establishment-before-failure-probability rule changed")

    frozen = payload.get("frozen_determinations", {})
    if frozen.get("modified_by_realignment") is not False:
        fail("Realignment may not modify frozen determinations")
    if frozen.get("version_2", {}).get("rsi") != "NO_PIPELINE_ADMITTED":
        fail("Frozen Version 2 RSI status changed")
    if frozen.get("version_2", {}).get("bollinger") != "NO_INCREMENTAL_EVIDENCE":
        fail("Frozen Version 2 Bollinger status changed")
    if frozen.get("version_2", {}).get("primary_case_established") is not False:
        fail("Frozen Version 2 establishment status changed")

    next_gate = payload.get("true_next_core_gate", {})
    if next_gate.get("gate") != "V3-4":
        fail("True current core gate is not V3-4")
    if next_gate.get("title") != "Unified RSI and Bollinger Interpretation Engine":
        fail("True V3-4 title changed")
    if next_gate.get("status") != "IMPLEMENTATION_COMPLETE_VALIDATION_PENDING":
        fail("True V3-4 implementation status changed")
    if next_gate.get("implementation_started") is not True:
        fail("Realignment contract does not record approved V3-4 implementation")
    if next_gate.get("implementation_complete") is not True:
        fail("V3-4 implementation is not recorded complete")
    if next_gate.get("authoritative_validation_complete") is not False:
        fail("V3-4 validation is claimed prematurely")
    if next_gate.get("lock_created") is not False:
        fail("V3-4 lock is claimed prematurely")
    for field in (
        "predictive_claims_permitted",
        "economic_claims_permitted",
        "failure_claims_permitted",
    ):
        if next_gate.get(field) is not False:
            fail(f"True V3-4 boundary changed: {field}")

    implementation = payload.get("v3_4_implementation", {})
    expected_counts = {
        "registered_signal_count": 48,
        "base_signal_count": 44,
        "interaction_signal_count": 4,
        "adaptive_template_count": 2,
        "prior_development_suite_passed": 19,
    }
    for field, expected in expected_counts.items():
        if implementation.get(field) != expected:
            fail(f"V3-4 implementation evidence changed: {field}")
    if implementation.get("identifier_scheme") != (
        "v3sig:<feature_key>:<sha256(canonical_specification)>"
    ):
        fail("V3-4 identifier scheme changed")
    if implementation.get("final_hardening_applied_after_prior_suite") is not True:
        fail("V3-4 final hardening boundary is not recorded")
    if implementation.get("current_exact_suite_execution_pending") is not True:
        fail("V3-4 current exact suite is claimed prematurely")
    for field in (
        "automatic_selection_performed",
        "target_accessed",
        "chronology_accessed",
        "predictive_claims_produced",
        "economic_claims_produced",
        "deterioration_claims_produced",
        "failure_claims_produced",
    ):
        if implementation.get(field) is not False:
            fail(f"V3-4 prohibited action changed: {field}")

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
    for field in (
        "historical_locks_rewritten",
        "chronology_may_tune_signal_registry",
        "panic_regime_may_rescue_v2_signal",
        "automatic_signal_selection_in_v3_4",
    ):
        if controls.get(field) is not False:
            fail(f"Governance control changed: {field}")
    if controls.get("each_future_gate_must_state_richard_question_link") is not True:
        fail("Future gates are not linked to Richard's question")
    if controls.get("governance_must_be_proportional_to_scientific_gate") is not True:
        fail("Governance proportionality rule changed")

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

    texts = {
        "RICHARD_QUESTION.md": require_file("RICHARD_QUESTION.md").read_text(
            encoding="utf-8"
        ),
        "DIRECT_ANSWER_LOGIC.md": require_file("DIRECT_ANSWER_LOGIC.md").read_text(
            encoding="utf-8"
        ),
        "V3_REALIGNMENT_DECISION.md": require_file(
            "V3_REALIGNMENT_DECISION.md"
        ).read_text(encoding="utf-8"),
        "docs/V3_REALIGNED_GATE_MAP.md": require_file(
            "docs/V3_REALIGNED_GATE_MAP.md"
        ).read_text(encoding="utf-8"),
        "docs/V3_G4_SIGNAL_ENGINE_SCOPE.md": require_file(
            "docs/V3_G4_SIGNAL_ENGINE_SCOPE.md"
        ).read_text(encoding="utf-8"),
        "docs/V3_G4_SIGNAL_ENGINE.md": require_file(
            "docs/V3_G4_SIGNAL_ENGINE.md"
        ).read_text(encoding="utf-8"),
    }
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
            "CURRENT_HARDENED_SUITE_EXECUTION_PENDING",
            "Gate V3-5",
        ),
    }
    for path, phrases in required_phrases.items():
        for phrase in phrases:
            if phrase not in texts[path]:
                fail(f"Required phrase missing from {path}: {phrase}")

    print("Version 3 repository realignment verification passed.")
    print("Richard question restored: True")
    print("Frozen V1/V2 determinations modified: False")
    print("Historical chronology work reclassified: V3-RV1/V3-RV2")
    print("Event alignment: V3-RV3 PAUSED_NOT_STARTED")
    print("Current core gate: V3-4 — Unified RSI and Bollinger Interpretation Engine")
    print("True V3-4 implementation started: True")
    print("True V3-4 status: IMPLEMENTATION_COMPLETE_VALIDATION_PENDING")
    print("Registered signal specifications: 48")
    print("Current hardened V3-4 suite execution pending: True")
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
