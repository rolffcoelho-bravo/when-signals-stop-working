from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "V3_G4B_CHRONOLOGY_PROVENANCE_LOCK.json"
CHECKPOINT = ROOT / "V3_G4B_CHRONOLOGY_PROVENANCE_CHECKPOINT.md"
PARENT_LOCK = ROOT / "V3_G4A_CHRONOLOGY_SIGNAL_USE_CONTRACT_LOCK.json"
EXPECTED_PARENT_BLOB = "d3c4ce27808e60b001e7d58e0c5e36be8d8cac6a"
EXPECTED_HASHES = {
    "chronology_manifest.json": "3e968b1432cf9e95dd26984d1dd80297825b3c94e676c70982cb5c68ef357a00",
    "chronology_merge_log.csv": "93c64dc662f788eb4634921f6060402e71156ce81fbed033d5f38ba7bd153c44",
    "chronology_provenance.json": "c7d23a74ccacae2be7bce5827205ee8285e547bac96553f1e23c144f1056c67f",
    "external_chronology.csv": "7eb99d1e1492685bfc8efee04b0cec9dbd776f8f176358f5b6d5d89ba0e53f53",
}


def git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> int:
    if not LOCK.exists() or not CHECKPOINT.exists():
        fail("Final V3-4B lock or checkpoint is missing")
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    if payload.get("gate") != "V3-4B":
        fail("Unexpected gate identifier")
    if payload.get("status") != "CHRONOLOGY_COMPILATION_AND_PROVENANCE_COMPLETE_AND_LOCKED":
        fail("V3-4B lock is not complete")
    if payload.get("parent_lock") != PARENT_LOCK.name:
        fail("Parent lock path changed")
    if payload.get("parent_lock_blob_sha") != EXPECTED_PARENT_BLOB:
        fail("Parent lock blob changed")
    if git("rev-parse", f"HEAD:{PARENT_LOCK.name}") != EXPECTED_PARENT_BLOB:
        fail("Current V3-4A lock object changed")

    protected = payload.get("protected_files")
    if not isinstance(protected, dict) or not protected:
        fail("Protected-file inventory is missing")
    for path, expected in protected.items():
        observed = git("rev-parse", f"HEAD:{path}")
        if observed != expected:
            fail(f"Protected Git object changed: {path}")

    evidence = payload.get("acceptance_evidence", {})
    expected_evidence = {
        "isolated_tests_passed": 19,
        "canonical_event_count": 17,
        "provenance_source_count": 27,
        "confirmed_event_count": 12,
        "boundary_uncertain_event_count": 5,
        "source_conflict_event_count": 0,
        "model_outputs_accessed": False,
        "chronology_completeness_claimed": False,
        "event_alignment_executed": False,
        "cross_gate_lineage_verified": True,
    }
    for field, expected in expected_evidence.items():
        if evidence.get(field) != expected:
            fail(f"Acceptance evidence changed: {field}")
    if evidence.get("output_sha256") != EXPECTED_HASHES:
        fail("Chronology output hashes changed")

    lock_blob = git("rev-parse", f"HEAD:{LOCK.name}")
    if lock_blob not in CHECKPOINT.read_text(encoding="utf-8"):
        fail("Checkpoint does not bind the current lock blob")

    print("Gate V3-4B chronology and provenance lock verification passed.")
    print("Status: CHRONOLOGY_COMPILATION_AND_PROVENANCE_COMPLETE_AND_LOCKED")
    print(f"Protected files verified: {len(protected)}")
    print("Isolated tests: 19 passed")
    print("Canonical events: 17")
    print("Provenance sources: 27")
    print("Confirmed timing events: 12")
    print("Boundary-uncertain events: 5")
    print("Model outputs accessed: False")
    print("Event alignment executed: False")
    print("Next subgate: V3-4C")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Gate V3-4B lock verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
