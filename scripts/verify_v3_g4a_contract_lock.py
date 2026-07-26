from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "V3_G4A_CHRONOLOGY_SIGNAL_USE_CONTRACT_LOCK.json"
PARENT_LOCK = ROOT / "V3_G3_PANIC_REGIME_LOCK.json"
CHECKPOINT = ROOT / "V3_G4A_CHRONOLOGY_SIGNAL_USE_CONTRACT_CHECKPOINT.md"
EXPECTED_PARENT_BLOB = "0e35908c03e36d8caeb832a078ff0566ef4e2ea4"


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def fail(message: str) -> None:
    raise RuntimeError(message)


def object_id(reference: str, path: str) -> str:
    return git("rev-parse", f"{reference}:{path}")


def main() -> int:
    if not LOCK.exists():
        fail(f"Missing Gate V3-4A lock: {LOCK.name}")
    if not CHECKPOINT.exists():
        fail(f"Missing Gate V3-4A checkpoint: {CHECKPOINT.name}")

    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    if payload.get("gate") != "V3-4A":
        fail("Unexpected Gate V3-4A identifier.")
    if payload.get("status") != "INDEPENDENT_CHRONOLOGY_AND_SIGNAL_USE_CONTRACT_COMPLETE_AND_LOCKED":
        fail("Gate V3-4A contract is not complete and locked.")
    if payload.get("parent_lock") != PARENT_LOCK.name:
        fail("Gate V3-4A parent lock path changed.")
    if payload.get("parent_lock_blob_sha") != EXPECTED_PARENT_BLOB:
        fail("Recorded Gate V3-3 parent lock blob is invalid.")
    if object_id("HEAD", PARENT_LOCK.name) != EXPECTED_PARENT_BLOB:
        fail("Gate V3-3 parent lock object changed.")

    protected = payload.get("protected_files")
    if not isinstance(protected, dict) or not protected:
        fail("Gate V3-4A protected-file inventory is missing.")
    for path, expected in protected.items():
        observed = object_id("HEAD", str(path))
        if observed != expected:
            fail(f"Gate V3-4A protected Git object changed: {path}")

    evidence = payload.get("acceptance_evidence")
    if not isinstance(evidence, dict):
        fail("Gate V3-4A acceptance evidence is missing.")

    expected_values = {
        "isolated_contract_tests_passed": 15,
        "tested_contract_blob_matches_repository": True,
        "tested_validator_blob_matches_repository": True,
        "tested_test_blob_matches_repository": True,
        "launcher_user_site_compatibility_verified": True,
        "parent_v3_3_lock_verified": True,
        "model_outputs_accessed": False,
        "chronology_compiled": False,
        "rsi_rescue_permitted": False,
        "bollinger_rescue_permitted": False,
        "version_1_and_version_2_determinations_modified": False,
    }
    for field, expected in expected_values.items():
        if evidence.get(field) != expected:
            fail(
                f"Gate V3-4A acceptance evidence is invalid: {field} "
                f"expected={expected!r} observed={evidence.get(field)!r}"
            )

    if evidence.get("next_subgate") != "V3-4B":
        fail("Unexpected next Gate V3-4 subgate.")

    lock_blob = object_id("HEAD", LOCK.name)
    checkpoint_text = CHECKPOINT.read_text(encoding="utf-8")
    if lock_blob not in checkpoint_text:
        fail("Gate V3-4A checkpoint does not reference the current lock blob.")

    print("Gate V3-4A chronology and signal-use contract lock verification passed.")
    print("Status: INDEPENDENT_CHRONOLOGY_AND_SIGNAL_USE_CONTRACT_COMPLETE_AND_LOCKED")
    print(f"Protected files verified: {len(protected)}")
    print("Isolated contract tests: 15 passed")
    print("Launcher user-site compatibility verified: True")
    print("Model outputs accessed: False")
    print("Chronology compiled: False")
    print("RSI rescue permitted: False")
    print("Bollinger rescue permitted: False")
    print("Next subgate: V3-4B")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        KeyError,
        OSError,
        RuntimeError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"Gate V3-4A lock verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
