from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "V3_G5_DEVELOPMENT_ENGINE_VALIDATION.json"


class DevelopmentEngineBoundaryError(RuntimeError):
    pass


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise DevelopmentEngineBoundaryError(
            f"Git command failed: git {' '.join(arguments)}: {detail}"
        )
    return completed.stdout.strip()


def _git_object(commit: str, path: str) -> str:
    return _git("rev-parse", f"{commit}:{path}")


def _require_clean(paths: tuple[str, ...]) -> None:
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
            raise DevelopmentEngineBoundaryError(
                f"Validated development engine paths are modified in the {location}."
            )
        if completed.returncode not in {0, 1}:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise DevelopmentEngineBoundaryError(
                f"Unable to verify protected path cleanliness: {detail}"
            )


def main() -> int:
    if not VALIDATION.is_file():
        raise DevelopmentEngineBoundaryError(
            "Development engine validation record is missing."
        )
    payload = json.loads(VALIDATION.read_text(encoding="utf-8"))
    if payload.get("status") != (
        "DEVELOPMENT_ENGINE_AUTHORITATIVELY_VALIDATED_AND_PROTECTED"
    ):
        raise DevelopmentEngineBoundaryError(
            "Development engine is not authoritatively validated."
        )
    commit = str(payload.get("validated_engine_commit", ""))
    if commit != "9827d5320d45c4b54a7fe85a24403651f3e239c9":
        raise DevelopmentEngineBoundaryError(
            "Validated development engine commit changed."
        )
    protected = payload.get("protected_engine", {})
    paths = tuple(str(value) for value in protected.get("protected_paths", []))
    if len(paths) != 14 or len(set(paths)) != 14:
        raise DevelopmentEngineBoundaryError(
            "Protected development engine path identity changed."
        )
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        raise DevelopmentEngineBoundaryError(
            "Validated development engine commit is not an ancestor of HEAD."
        )
    for path in paths:
        if _git_object(commit, path) != _git_object("HEAD", path):
            raise DevelopmentEngineBoundaryError(
                f"Validated development engine object drifted: {path}"
            )
    _require_clean(paths)

    evidence = payload.get("validation_evidence", {})
    expected = {
        "development_engine_tests_passed": 33,
        "development_engine_tests_failed": 0,
        "future_warnings_observed": 0,
        "candidate_pipeline_target_combinations": 45900,
        "outer_fold_jobs": 229500,
        "strict_training_calibration_test_chronology_verified": True,
        "fold_scoped_large_move_threshold_verified": True,
        "training_only_calibration_verified": True,
        "one_standard_error_inner_selection_verified": True,
        "predictive_and_economic_metrics_verified": True,
        "holm_and_benjamini_hochberg_verified": True,
    }
    for field, expected_value in expected.items():
        if evidence.get(field) != expected_value:
            raise DevelopmentEngineBoundaryError(
                f"Validated development engine evidence changed: {field}"
            )

    execution = payload.get("execution_state", {})
    for field in (
        "real_development_target_consumption_started",
        "real_development_model_fitting_started",
        "real_development_predictions_generated",
        "development_pipeline_selection_performed",
        "development_pipeline_admission_performed",
        "establishment_authorization_created",
        "signal_establishment_segment_accessed",
        "final_framework_reserve_accessed",
    ):
        if execution.get(field) is not False:
            raise DevelopmentEngineBoundaryError(
                f"Development engine boundary advanced prematurely: {field}"
            )

    print("Gate V3-5 development engine boundary verified.")
    print(f"Validated development engine commit: {commit}")
    print(f"Protected development engine objects: {len(paths)}")
    print("Development engine tests: 33")
    print("FutureWarnings observed: 0")
    print("Candidate-pipeline-target combinations: 45900")
    print("Outer-fold jobs: 229500")
    print("Real development model fitting started: False")
    print("Development pipeline selection performed: False")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        DevelopmentEngineBoundaryError,
    ) as error:
        print(f"Gate V3-5 development engine boundary failed: {error}", file=sys.stderr)
        raise SystemExit(1)
