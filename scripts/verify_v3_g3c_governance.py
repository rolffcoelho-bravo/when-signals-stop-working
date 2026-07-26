from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "V3_G3C_GOVERNANCE_LOCK.json"
PARENT_LOCK = ROOT / "V3_G3B_PROBABILISTIC_ENGINE_LOCK.json"


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
        fail(f"Missing Gate V3-3C lock: {LOCK.name}")
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    if payload.get("gate") != "V3-3C":
        fail("Unexpected gate identifier.")
    if payload.get("status") != "GOVERNANCE_AND_DIAGNOSTICS_COMPLETE_AND_LOCKED":
        fail("Gate V3-3C lock is not complete.")
    if payload.get("parent_lock") != PARENT_LOCK.name:
        fail("Parent lock path changed.")
    if object_id("HEAD", PARENT_LOCK.name) != payload.get("parent_lock_blob_sha"):
        fail("V3-3B parent lock object changed.")

    protected = payload.get("protected_files")
    if not isinstance(protected, dict) or not protected:
        fail("Protected-file inventory is missing.")
    for path, expected in protected.items():
        observed = object_id("HEAD", str(path))
        if observed != expected:
            fail(f"Protected Git object changed: {path}")

    evidence = payload.get("acceptance_evidence", {})
    expected_true = (
        "prefix_probability_intervals_complete",
        "transition_outputs_complete",
        "transition_rows_sum_to_one",
        "duration_and_occupancy_outputs_complete",
        "mechanism_contribution_decomposition_complete",
        "cross_model_disagreement_index_complete",
        "mechanism_coverage_map_complete",
        "sensitivity_diagnostics_complete",
        "future_append_invariance",
        "shuffled_input_determinism",
        "causal_confirmation_without_backfill",
        "ambiguous_contagion_radius_exclusion_preserved",
    )
    for field in expected_true:
        if evidence.get(field) is not True:
            fail(f"Acceptance evidence is incomplete: {field}")
    if evidence.get("isolated_governance_tests_passed") != 15:
        fail("Recorded Gate V3-3C test count is invalid.")
    for field in (
        "automatic_model_selection_performed",
        "automatic_ensemble_performed",
        "consensus_probability_produced",
        "external_chronology_validation_complete",
        "final_v3_3_lock_permitted",
    ):
        if evidence.get(field) is not False:
            fail(f"Gate boundary is invalid: {field}")

    print("Gate V3-3C governance lock verification passed.")
    print("Status: GOVERNANCE_AND_DIAGNOSTICS_COMPLETE_AND_LOCKED")
    print(f"Protected files verified: {len(protected)}")
    print("Isolated governance tests: 15 passed")
    print("Automatic model selection performed: False")
    print("External chronology validation: DEFERRED")
    print("Final V3-3 lock permitted: False")
    print("Next subgate: V3-3D")
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
            f"Gate V3-3C governance lock verification failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
