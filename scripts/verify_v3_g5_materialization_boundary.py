from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VALIDATION_PATH = ROOT / "V3_G5_MATERIALIZATION_VALIDATION.json"
VALIDATED_COMMIT = "91606edf50a2c0aee9bcb94a93350936ee53f81a"
PROTECTED_PATHS = (
    "RUN_V3_G5_MATERIALIZATION.ps1",
    "RUN_V3_G5_MATERIALIZATION.sh",
    "scripts/run_v3_g5_materialization.py",
    "scripts/verify_v3_g5_materialization.py",
    "scripts/verify_v3_g5_validated_boundaries.py",
    "src/shockbridge_signal_validity/v3/forecast_materialization.py",
    "tests/test_v3_g5_materialization.py",
)


class MaterializationBoundaryError(RuntimeError):
    pass


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
        raise MaterializationBoundaryError(
            f"Git command failed: git {' '.join(arguments)}: {detail}"
        )
    return completed.stdout.strip()


def git_object(commit: str, path: str) -> str:
    return git("rev-parse", f"{commit}:{path}")


def require_clean_paths(paths: tuple[str, ...]) -> None:
    for staged in (False, True):
        arguments = ["diff", "--quiet"]
        if staged:
            arguments.append("--cached")
        arguments.extend(["--", *paths])
        completed = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 1:
            location = "staged index" if staged else "working tree"
            raise MaterializationBoundaryError(
                f"Validated materialization paths are modified in the {location}."
            )
        if completed.returncode not in {0, 1}:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise MaterializationBoundaryError(
                f"Unable to verify materialization path cleanliness: {detail}"
            )


def main() -> int:
    if not VALIDATION_PATH.is_file():
        raise MaterializationBoundaryError("Materialization validation record is missing.")
    validation = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
    if validation.get("status") != "MATERIALIZATION_AUTHORITATIVELY_VALIDATED":
        raise MaterializationBoundaryError("Materialization validation status changed.")
    if validation.get("validated_materialization_commit") != VALIDATED_COMMIT:
        raise MaterializationBoundaryError("Validated materialization commit changed.")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", VALIDATED_COMMIT, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    if ancestry.returncode != 0:
        raise MaterializationBoundaryError(
            "Validated materialization commit is not an ancestor of HEAD."
        )
    for path in PROTECTED_PATHS:
        validated = git_object(VALIDATED_COMMIT, path)
        current = git_object("HEAD", path)
        if current != validated:
            raise MaterializationBoundaryError(
                f"Validated materialization object drifted: {path}"
            )
    require_clean_paths(PROTECTED_PATHS)

    identities = validation.get("real_data_identities", {})
    expected = {
        "development_rows": 9852,
        "target_primitive_rows": 59070,
        "nested_fold_records": 120,
        "bounded_candidates": 57,
        "candidate_horizon_records": 342,
        "matched_rows_available_records": 276,
        "explicitly_ineligible_candidate_horizon_records": 66,
    }
    if identities != expected:
        raise MaterializationBoundaryError("Materialization validation identities changed.")
    execution = validation.get("execution_state", {})
    for field in (
        "development_model_fitting_started",
        "development_pipeline_selection_performed",
        "establishment_authorization_created",
        "signal_establishment_segment_accessed",
        "final_framework_reserve_accessed",
    ):
        if execution.get(field) is not False:
            raise MaterializationBoundaryError(
                f"Materialization boundary advanced prematurely: {field}"
            )

    print("Gate V3-5 materialization boundary verified.")
    print(f"Validated materialization commit: {VALIDATED_COMMIT}")
    print(f"Protected materialization objects: {len(PROTECTED_PATHS)}")
    print("Development rows: 9852")
    print("Target primitive rows: 59070")
    print("Candidate-horizon records: 342")
    print("Matched records: 276")
    print("Explicitly ineligible records: 66")
    print("Real development model fitting started: False")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, ValueError, MaterializationBoundaryError) as error:
        print(f"Gate V3-5 materialization-boundary verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
