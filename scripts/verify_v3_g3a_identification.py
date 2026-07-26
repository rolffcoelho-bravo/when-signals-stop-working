from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "V3_G3A_PANIC_REGIME_IDENTIFICATION_LOCK.json"
PARENT_LOCK = ROOT / "V3_G2B_MARKET_STRUCTURE_LOCK.json"


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
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    if payload.get("gate") != "V3-3A":
        fail("Unexpected gate identifier.")
    if payload.get("status") != "IDENTIFICATION_CONTRACT_COMPLETE_AND_LOCKED":
        fail("Identification lock is not complete.")
    if payload.get("parent_lock") != PARENT_LOCK.name:
        fail("Parent lock path changed.")
    if object_id("HEAD", PARENT_LOCK.name) != payload.get("parent_lock_blob_sha"):
        fail("V3-2B parent lock object changed.")

    protected = payload.get("protected_files")
    if not isinstance(protected, dict) or not protected:
        fail("Protected-file inventory is missing.")
    for path, expected in protected.items():
        observed = object_id("HEAD", path)
        if observed != expected:
            fail(f"Protected Git object changed: {path}")

    acceptance = payload.get("acceptance_evidence", {})
    if acceptance.get("contract_tests_passed") != 8:
        fail("Recorded contract-test count is invalid.")
    if acceptance.get("automatic_model_selection_performed") is not False:
        fail("Automatic model selection was incorrectly recorded.")
    if acceptance.get("engine_implementation_started") is not False:
        fail("V3-3A must not claim implementation.")
    if acceptance.get("final_v3_3_lock_permitted") is not False:
        fail("V3-3A cannot authorize the final V3-3 lock.")

    print("Gate V3-3A identification lock verification passed.")
    print("Status: IDENTIFICATION_CONTRACT_COMPLETE_AND_LOCKED")
    print(f"Protected files verified: {len(protected)}")
    print("Probabilistic engine implemented: False")
    print("Next subgate: V3-3B")
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
        print(
            f"Gate V3-3A identification lock verification failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
