from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_VALIDATION = ROOT / "V3_G5_CONTRACT_VALIDATION.json"
FOUNDATION_VALIDATION = ROOT / "V3_G5_FOUNDATION_VALIDATION.json"

PROTECTED_FOUNDATION_PATHS = (
    "RUN_V3_G5_FOUNDATION.ps1",
    "RUN_V3_G5_FOUNDATION.sh",
    "scripts/verify_v3_g5_foundation.py",
    "src/shockbridge_signal_validity/v3/forecast_contract.py",
    "src/shockbridge_signal_validity/v3/forecast_targets.py",
    "src/shockbridge_signal_validity/v3/forecast_splits.py",
    "src/shockbridge_signal_validity/v3/forecast_benchmark.py",
    "src/shockbridge_signal_validity/v3/forecast_inventory.py",
    "src/shockbridge_signal_validity/v3/forecast_matching.py",
    "tests/test_v3_g5_targets_partitions.py",
    "tests/test_v3_g5_splits_matching.py",
    "tests/test_v3_g5_inventory_benchmark.py",
)


class ValidatedBoundaryError(RuntimeError):
    pass


def read_json(path: Path) -> dict:
    if not path.is_file():
        raise ValidatedBoundaryError(f"Validation record is missing: {path.name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidatedBoundaryError(f"Validation record is not an object: {path.name}")
    return value


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ValidatedBoundaryError(
            f"Git command failed: git {' '.join(arguments)}: {detail}"
        )
    return completed.stdout.strip()


def git_object(commit: str, path: str) -> str:
    return git("rev-parse", f"{commit}:{path}")


def main() -> int:
    contract = read_json(CONTRACT_VALIDATION)
    foundation = read_json(FOUNDATION_VALIDATION)

    if contract.get("status") != "CONTRACT_AUTHORITATIVELY_VALIDATED":
        raise ValidatedBoundaryError("V3-5 contract validation status changed.")
    contract_commit = str(contract.get("validated_contract_commit", ""))
    contract_blob = str(contract.get("contract_blob_sha", ""))
    contract_path = str(contract.get("contract_path", ""))
    if contract_commit != "013d91abc0c3c74a28784aed486edb4c95efc6d7":
        raise ValidatedBoundaryError("Validated contract commit changed.")
    if contract_path != "configs/v3_g5_forecast_contract.json":
        raise ValidatedBoundaryError("Validated contract path changed.")
    if git_object(contract_commit, contract_path) != contract_blob:
        raise ValidatedBoundaryError("Recorded contract blob does not match validation commit.")
    if git_object("HEAD", contract_path) != contract_blob:
        raise ValidatedBoundaryError("Frozen V3-5 contract drifted after validation.")

    if foundation.get("status") != "FOUNDATION_AUTHORITATIVELY_VALIDATED":
        raise ValidatedBoundaryError("V3-5 foundation validation status changed.")
    foundation_commit = str(foundation.get("validated_foundation_commit", ""))
    if foundation_commit != "dd8a8ec5f34f0b8587c8f0cdaaf4f3c0891e944a":
        raise ValidatedBoundaryError("Validated foundation commit changed.")
    subprocess_result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", foundation_commit, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    if subprocess_result.returncode != 0:
        raise ValidatedBoundaryError("Validated foundation commit is not an ancestor of HEAD.")

    for path in PROTECTED_FOUNDATION_PATHS:
        validated = git_object(foundation_commit, path)
        current = git_object("HEAD", path)
        if current != validated:
            raise ValidatedBoundaryError(
                f"Validated V3-5 foundation object drifted: {path}"
            )

    print("Gate V3-5 validated boundaries verified.")
    print(f"Contract validation commit: {contract_commit}")
    print(f"Contract blob preserved: {contract_blob}")
    print(f"Foundation validation commit: {foundation_commit}")
    print(f"Protected foundation objects: {len(PROTECTED_FOUNDATION_PATHS)}")
    print("Validated foundation drift detected: False")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, ValueError, ValidatedBoundaryError) as error:
        print(f"Gate V3-5 validated-boundary verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
