from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "V3_G3_PANIC_REGIME_LOCK.json"
PARENT_LOCK = ROOT / "V3_G3C_GOVERNANCE_LOCK.json"
CHECKPOINT = ROOT / "V3_G3_PANIC_REGIME_CHECKPOINT.md"
EXPECTED_PARENT_BLOB = "30553882746296d34114eef271fde6c64ae5e471"
EXPECTED_ACCEPTANCE_COMMIT = "78504fab90599cd0227991268536dc09bca542eb"


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
        fail(f"Missing final Gate V3-3 lock: {LOCK.name}")
    if not CHECKPOINT.exists():
        fail(f"Missing final Gate V3-3 checkpoint: {CHECKPOINT.name}")

    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    if payload.get("gate") != "V3-3":
        fail("Unexpected final gate identifier.")
    if payload.get("subgate") != "V3-3D":
        fail("Unexpected final acceptance subgate.")
    if payload.get("status") != "V3_G3_PANIC_REGIME_COMPLETE_VALIDATED_AND_LOCKED":
        fail("Gate V3-3 final lock is not complete and locked.")
    if payload.get("parent_lock") != PARENT_LOCK.name:
        fail("Final Gate V3-3 parent lock path changed.")
    if payload.get("parent_lock_blob_sha") != EXPECTED_PARENT_BLOB:
        fail("Recorded V3-3C parent lock blob is invalid.")
    if object_id("HEAD", PARENT_LOCK.name) != EXPECTED_PARENT_BLOB:
        fail("V3-3C parent lock object changed.")
    if payload.get("acceptance_boundary_commit") != EXPECTED_ACCEPTANCE_COMMIT:
        fail("Final acceptance boundary commit changed.")

    protected = payload.get("protected_files")
    if not isinstance(protected, dict) or not protected:
        fail("Final protected-file inventory is missing.")
    for path, expected in protected.items():
        observed = object_id("HEAD", str(path))
        if observed != expected:
            fail(f"Final protected Git object changed: {path}")

    evidence = payload.get("acceptance_evidence")
    if not isinstance(evidence, dict):
        fail("Final acceptance evidence is missing.")

    expected_values = {
        "integrated_tests_passed": 46,
        "historical_protected_objects_verified": 59,
        "current_latest_owner_objects_verified": 58,
        "governed_superseded_paths": 1,
        "lock_finalization_anchors_verified": True,
        "required_output_contract_verified": True,
        "automatic_model_selection_performed": False,
        "automatic_ensemble_performed": False,
        "consensus_probability_produced": False,
        "external_chronology_validation_complete": False,
        "external_chronology_deferred_to_later_robustness": True,
        "external_chronology_used": False,
        "version_1_and_version_2_determinations_modified": False,
        "final_lock_created_by_acceptance_runner": False,
    }
    for field, expected in expected_values.items():
        if evidence.get(field) != expected:
            fail(
                f"Final acceptance evidence is invalid: {field} "
                f"expected={expected!r} observed={evidence.get(field)!r}"
            )

    verifiers = evidence.get("subgate_verifiers_passed")
    expected_verifiers = [
        "scripts/verify_v3_g3a_identification.py",
        "scripts/verify_v3_g3b_probabilistic_engine.py",
        "scripts/verify_v3_g3c_governance.py",
    ]
    if verifiers != expected_verifiers:
        fail("Final subgate-verifier inventory changed.")

    superseded = evidence.get("superseded_paths")
    expected_superseded = {
        "src/shockbridge_signal_validity/v3/__init__.py": [
            "V3_G1_DATA_ADAPTER_LOCK.json",
            "V3_G2_SPECTRAL_ENGINE_LOCK.json",
        ]
    }
    if superseded != expected_superseded:
        fail("Final governed-supersession evidence changed.")

    lock_blob = object_id("HEAD", LOCK.name)
    checkpoint_text = CHECKPOINT.read_text(encoding="utf-8")
    if lock_blob not in checkpoint_text:
        fail("Final checkpoint does not reference the current lock blob.")

    print("Gate V3-3 final panic-regime lock verification passed.")
    print("Status: V3_G3_PANIC_REGIME_COMPLETE_VALIDATED_AND_LOCKED")
    print(f"Protected files verified: {len(protected)}")
    print("Integrated acceptance tests: 46 passed")
    print("Historical protected objects verified: 59")
    print("Current latest-owner objects verified: 58")
    print("Automatic model selection performed: False")
    print("External chronology used: False")
    print("Version 1 and Version 2 determinations modified: False")
    print("Next gate: V3-4")
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
            f"Gate V3-3 final lock verification failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
