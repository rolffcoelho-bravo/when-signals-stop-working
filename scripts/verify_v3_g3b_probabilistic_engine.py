from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "V3_G3B_PROBABILISTIC_ENGINE_LOCK.json"
PARENT_LOCK = ROOT / "V3_G3A_PANIC_REGIME_IDENTIFICATION_LOCK.json"


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
    if payload.get("gate") != "V3-3B":
        fail("Unexpected gate identifier.")
    if payload.get("status") != "IMPLEMENTATION_COMPLETE_AND_LOCKED":
        fail("Probabilistic-engine implementation lock is incomplete.")
    if payload.get("parent_lock") != PARENT_LOCK.name:
        fail("Parent identification lock path changed.")
    if object_id("HEAD", PARENT_LOCK.name) != payload.get("parent_lock_blob_sha"):
        fail("V3-3A parent lock object changed.")

    protected = payload.get("protected_files")
    if not isinstance(protected, dict) or not protected:
        fail("Protected-file inventory is missing.")
    for path, expected in protected.items():
        observed = object_id("HEAD", str(path))
        if observed != expected:
            fail(f"Protected Git object changed: {path}")

    acceptance = payload.get("acceptance_evidence", {})
    if acceptance.get("isolated_engine_tests_passed") != 11:
        fail("Recorded engine-test count is invalid.")
    if acceptance.get("all_registered_models_reported") is not True:
        fail("Registered-model reporting evidence is incomplete.")
    if acceptance.get("future_append_invariance") is not True:
        fail("Future-append invariance evidence is incomplete.")
    if acceptance.get("automatic_model_selection_performed") is not False:
        fail("Automatic model selection was incorrectly recorded.")
    if acceptance.get("automatic_ensemble_performed") is not False:
        fail("Automatic ensemble use was incorrectly recorded.")
    if acceptance.get("uncertainty_intervals_complete") is not False:
        fail("V3-3B must not claim final uncertainty intervals.")
    if acceptance.get("final_v3_3_lock_permitted") is not False:
        fail("V3-3B cannot authorize the final V3-3 lock.")

    print("Gate V3-3B probabilistic-engine lock verification passed.")
    print("Status: IMPLEMENTATION_COMPLETE_AND_LOCKED")
    print(f"Protected files verified: {len(protected)}")
    print("Registered models reported: 3")
    print("Automatic model selection performed: False")
    print("Uncertainty status: PENDING_V3_3C")
    print("Next subgate: V3-3C")
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
            f"Gate V3-3B probabilistic-engine lock verification failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
