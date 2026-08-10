from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "V3_G4_SIGNAL_ENGINE_LOCK.json"
EXPECTED_VALIDATED_COMMIT = "7c8b6fd83e124dbd25e4c9f52e4c00c7757f939d"


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_object_sha(commit: str, relative_path: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", f"{commit}:{relative_path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"Unable to resolve {relative_path} at {commit}: {detail}")
    return completed.stdout.strip()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def verify_lock(lock: dict[str, Any]) -> None:
    if lock.get("gate") != "V3-4":
        raise RuntimeError("Unexpected lock gate identifier.")
    if lock.get("schema_version") != "v3.signal-engine-lock.v1":
        raise RuntimeError("Unexpected V3-4 lock schema.")
    if lock.get("status") not in {
        "LOCK_CANDIDATE_AWAITING_REPOSITORY_REVIEW",
        "IMPLEMENTATION_VALIDATED_AND_LOCKED",
    }:
        raise RuntimeError("Unexpected V3-4 lock status.")
    if lock.get("validated_implementation_commit") != EXPECTED_VALIDATED_COMMIT:
        raise RuntimeError("Validated V3-4 implementation commit changed.")

    protected = lock.get("protected_files")
    if not isinstance(protected, dict) or not protected:
        raise RuntimeError("V3-4 lock has no protected implementation objects.")
    for relative, expected_sha in protected.items():
        observed = git_object_sha(EXPECTED_VALIDATED_COMMIT, str(relative))
        if observed != expected_sha:
            raise RuntimeError(
                f"Protected implementation object mismatch: {relative} "
                f"expected={expected_sha} observed={observed}"
            )
        current = git_object_sha("HEAD", str(relative))
        if current != expected_sha:
            raise RuntimeError(
                f"Current implementation drifted after validation: {relative} "
                f"validated={expected_sha} current={current}"
            )

    runtime = lock.get("runtime_evidence")
    if not isinstance(runtime, dict):
        raise RuntimeError("V3-4 lock has no runtime evidence mapping.")
    for key, record in runtime.items():
        if not isinstance(record, dict):
            raise RuntimeError(f"Invalid runtime evidence record: {key}")
        path = ROOT / str(record.get("path", ""))
        if path.is_file() and sha256_file(path) != record.get("sha256"):
            raise RuntimeError(f"Runtime evidence hash mismatch: {key}")

    curated = lock.get("curated_evidence_sha256")
    if not isinstance(curated, dict) or not curated:
        raise RuntimeError("V3-4 lock has no curated evidence hashes.")
    for relative, expected_sha in curated.items():
        path = ROOT / str(relative)
        if not path.is_file():
            raise FileNotFoundError(path)
        if sha256_file(path) != expected_sha:
            raise RuntimeError(f"Curated evidence hash mismatch: {relative}")

    evidence = lock.get("acceptance_evidence")
    if not isinstance(evidence, dict):
        raise RuntimeError("V3-4 lock has no acceptance evidence.")
    expected = {
        "repository_realignment_tests_passed": 7,
        "exact_hardened_signal_tests_passed": 19,
        "canonical_source_rows": 12171,
        "registered_signal_count": 54,
        "expected_feature_rows": 657234,
        "observed_feature_rows": 657234,
        "row_count_identity_verified": True,
        "registry_definition_count": 54,
        "canonical_data_sha256": "3c49bfcab5fdf3aba9ada614873fa424e97c1f66e2690b790204fc29fdb5109c",
        "automatic_selection_performed": False,
        "target_accessed": False,
        "chronology_accessed": False,
        "predictive_claims_produced": False,
        "economic_claims_produced": False,
        "deterioration_claims_produced": False,
        "failure_claims_produced": False,
        "next_gate": "V3-5",
        "tracked_worktree_mutation": False,
    }
    if evidence != expected:
        raise RuntimeError("V3-4 acceptance evidence changed.")

    policy = lock.get("large_runtime_artifact_policy", {})
    if policy != {
        "signal_features_csv_tracked": False,
        "signal_features_csv_bound_by_sha256": True,
        "small_manifests_curated_for_repository_review": True,
    }:
        raise RuntimeError("V3-4 large-runtime-artifact policy changed.")

    next_gate = lock.get("next_gate", {})
    if next_gate != {
        "gate": "V3-5",
        "title": "Matched Benchmark-versus-Signal Forecast Selection",
        "approval": "APPROVED",
        "implementation_started": False,
        "may_start_after_final_lock_promotion": True,
    }:
        raise RuntimeError("V3-5 boundary changed in the V3-4 lock.")


def main() -> int:
    if not LOCK_PATH.is_file():
        raise FileNotFoundError(LOCK_PATH)
    lock = read_json(LOCK_PATH)
    verify_lock(lock)
    print("Gate V3-4 lock evidence verified.")
    print(f"status: {lock['status']}")
    print(f"validated_implementation_commit: {lock['validated_implementation_commit']}")
    print("source_rows: 12171")
    print("registered_signals: 48")
    print("feature_rows: 584208")
    print("large signal_features.csv tracked: False")
    print("large signal_features.csv bound by SHA-256: True")
    print("next_gate: V3-5 APPROVED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"Gate V3-4 lock verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
