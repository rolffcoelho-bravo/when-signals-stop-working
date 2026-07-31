from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "V3_G5_MODEL_IMPLEMENTATION_VALIDATION.json"


class ModelImplementationBoundaryError(RuntimeError):
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
        raise ModelImplementationBoundaryError(
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
            raise ModelImplementationBoundaryError(
                f"Validated model implementation paths are modified in the {location}."
            )
        if completed.returncode not in {0, 1}:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise ModelImplementationBoundaryError(
                f"Unable to verify protected path cleanliness: {detail}"
            )


def main() -> int:
    if not VALIDATION.is_file():
        raise ModelImplementationBoundaryError("Model implementation validation is missing.")
    payload = json.loads(VALIDATION.read_text(encoding="utf-8"))
    if payload.get("status") != "MODEL_IMPLEMENTATION_AUTHORITATIVELY_VALIDATED_AND_PROTECTED":
        raise ModelImplementationBoundaryError("Model implementation is not finally validated.")
    commit = str(payload.get("validated_implementation_commit", ""))
    if commit != "37c7360afde61a01ee9f9c5237dcf6bdf42985dd":
        raise ModelImplementationBoundaryError("Validated model implementation commit changed.")
    protected = payload.get("protected_implementation", {})
    paths = tuple(str(value) for value in protected.get("protected_paths", []))
    if len(paths) != 10 or len(set(paths)) != 10:
        raise ModelImplementationBoundaryError("Protected model implementation path identity changed.")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        raise ModelImplementationBoundaryError(
            "Validated model implementation commit is not an ancestor of HEAD."
        )
    for path in paths:
        if _git_object(commit, path) != _git_object("HEAD", path):
            raise ModelImplementationBoundaryError(
                f"Validated model implementation object drifted: {path}"
            )
    _require_clean(paths)
    evidence = payload.get("validation_evidence", {})
    expected = {
        "model_implementation_tests_passed": 26,
        "future_warnings_observed": 0,
        "pipeline_specifications": 162,
        "executable_pipeline_specifications": 153,
        "gated_pipeline_specifications": 9,
    }
    for field, value in expected.items():
        if evidence.get(field) != value:
            raise ModelImplementationBoundaryError(
                f"Validated model implementation evidence changed: {field}"
            )
    execution = payload.get("execution_state", {})
    for field in (
        "real_development_model_fitting_started",
        "development_pipeline_selection_performed",
        "establishment_authorization_created",
        "signal_establishment_segment_accessed",
        "final_framework_reserve_accessed",
    ):
        if execution.get(field) is not False:
            raise ModelImplementationBoundaryError(
                f"Model implementation boundary advanced prematurely: {field}"
            )
    print("Gate V3-5 model implementation boundary verified.")
    print(f"Validated model implementation commit: {commit}")
    print(f"Protected model implementation objects: {len(paths)}")
    print("Model implementation tests: 26")
    print("FutureWarnings observed: 0")
    print("Pipeline specifications: 162")
    print("Executable pipeline specifications: 153")
    print("Gated pipeline specifications: 9")
    print("Real development model fitting started: False")
    print("Development pipeline selection performed: False")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, TypeError, ValueError, ModelImplementationBoundaryError) as error:
        print(f"Gate V3-5 model implementation boundary failed: {error}", file=sys.stderr)
        raise SystemExit(1)
