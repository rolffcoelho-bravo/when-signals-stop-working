from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "v3_realignment_contract.json"


class RealignmentVerificationError(RuntimeError):
    """Raised when the repository realignment contract is incomplete or inconsistent."""


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
        fail("True next core gate is not V3-4")
    if next_gate.get("title") != "Unified RSI and Bollinger Interpretation Engine":
        fail("True V3-4 title changed")
    if next_gate.get("status") != "APPROVED_AND_REOPENED":
        fail("True V3-4 is not reopened")
    if next_gate.get("implementation_started") is not False:
        fail("Realignment contract incorrectly claims V3-4 implementation")
    for field in (
        "predictive_claims_permitted",
        "economic_claims_permitted",
        "failure_claims_permitted",
    ):
        if next_gate.get(field) is not False:
            fail(f"True V3-4 boundary changed: {field}")

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
    required_false = (
        "historical_locks_rewritten",
        "chronology_may_tune_signal_registry",
        "panic_regime_may_rescue_v2_signal",
        "automatic_signal_selection_in_v3_4",
    )
    for field in required_false:
        if controls.get(field) is not False:
            fail(f"Governance control changed: {field}")
    if controls.get("each_future_gate_must_state_richard_question_link") is not True:
        fail("Future gates are not linked to Richard's question")
    if controls.get("governance_must_be_proportional_to_scientific_gate") is not True:
        fail("Governance proportionality rule changed")

    for relative in payload.get("required_documents", []):
        require_file(relative)

    richard = require_file("RICHARD_QUESTION.md").read_text(encoding="utf-8")
    direct = require_file("DIRECT_ANSWER_LOGIC.md").read_text(encoding="utf-8")
    decision = require_file("V3_REALIGNMENT_DECISION.md").read_text(encoding="utf-8")
    gate_map = require_file("docs/V3_REALIGNED_GATE_MAP.md").read_text(encoding="utf-8")
    g4_scope = require_file("docs/V3_G4_SIGNAL_ENGINE_SCOPE.md").read_text(encoding="utf-8")

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
            "IMPLEMENTATION_NOT_STARTED",
            "Gate V3-5",
        ),
    }
    texts = {
        "RICHARD_QUESTION.md": richard,
        "DIRECT_ANSWER_LOGIC.md": direct,
        "V3_REALIGNMENT_DECISION.md": decision,
        "docs/V3_REALIGNED_GATE_MAP.md": gate_map,
        "docs/V3_G4_SIGNAL_ENGINE_SCOPE.md": g4_scope,
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
    print("True next core gate: V3-4 — Unified RSI and Bollinger Interpretation Engine")
    print("True V3-4 implementation started: False")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, RealignmentVerificationError) as error:
        print(f"Version 3 repository realignment verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
