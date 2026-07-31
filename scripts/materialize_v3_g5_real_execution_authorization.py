from __future__ import annotations

import json
from pathlib import Path
import platform
import subprocess
import sys

import pandas as pd
from sklearn import __version__ as SKLEARN_VERSION

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shockbridge_signal_validity.v3.forecast_model_registry import (  # noqa: E402
    build_pipeline_registry,
    load_contracts,
)
from shockbridge_signal_validity.v3.forecast_real_execution_authorization import (  # noqa: E402
    build_authorization_job_plan,
    build_batch_manifest,
    load_authorization_candidate,
    write_authorization_candidate_plan,
)
from shockbridge_signal_validity.v3.forecast_real_execution_stages import (  # noqa: E402
    build_complete_stage_manifest,
)

FORECAST_CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"
MODEL_CONTRACT = ROOT / "configs" / "v3_g5_model_implementation_contract.json"
ENGINE_CONTRACT = ROOT / "configs" / "v3_g5_development_execution_contract.json"
AUTHORIZATION_CONTRACT = (
    ROOT / "configs" / "v3_g5_real_execution_authorization_candidate.json"
)
ENGINE_VALIDATION = ROOT / "V3_G5_DEVELOPMENT_ENGINE_VALIDATION.json"
FOUNDATION_DIR = ROOT / "outputs" / "v3" / "forecast_foundation"
OUTPUT_DIR = ROOT / "outputs" / "v3" / "development_execution_plan"


def _git_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"Unable to resolve Git HEAD: {detail}")
    return completed.stdout.strip()


def main() -> int:
    authorization = load_authorization_candidate(AUTHORIZATION_CONTRACT)
    engine_validation = json.loads(ENGINE_VALIDATION.read_text(encoding="utf-8"))
    if engine_validation.get("status") != (
        "DEVELOPMENT_ENGINE_AUTHORITATIVELY_VALIDATED_AND_PROTECTED"
    ):
        raise RuntimeError("Development engine validation is not final.")
    if engine_validation.get("validated_engine_commit") != (
        "9827d5320d45c4b54a7fe85a24403651f3e239c9"
    ):
        raise RuntimeError("Validated development engine commit changed.")

    matched_coverage_path = FOUNDATION_DIR / "matched_row_coverage.csv"
    candidate_inventory_path = FOUNDATION_DIR / "candidate_inventory.csv"
    materialization_manifest_path = FOUNDATION_DIR / "materialization_manifest.json"
    for path in (
        matched_coverage_path,
        candidate_inventory_path,
        materialization_manifest_path,
    ):
        if not path.is_file():
            raise RuntimeError(f"Validated development foundation input is missing: {path}")

    matched_coverage = pd.read_csv(matched_coverage_path)
    candidate_inventory = pd.read_csv(candidate_inventory_path)
    forecast, implementation = load_contracts(FORECAST_CONTRACT, MODEL_CONTRACT)
    registry = build_pipeline_registry(forecast, implementation)
    plan = build_authorization_job_plan(
        matched_coverage=matched_coverage,
        candidate_inventory=candidate_inventory,
        pipeline_specs=registry,
        authorization_contract=authorization,
    )
    batches = build_batch_manifest(plan, authorization)
    stages = build_complete_stage_manifest(plan, authorization)
    manifest = write_authorization_candidate_plan(
        plan=plan,
        batch_manifest=batches,
        stage_manifest=stages,
        output_dir=OUTPUT_DIR,
        authorization_contract=authorization,
        input_paths={
            "authorization_candidate_contract": AUTHORIZATION_CONTRACT,
            "development_engine_contract": ENGINE_CONTRACT,
            "development_engine_validation": ENGINE_VALIDATION,
            "forecast_contract": FORECAST_CONTRACT,
            "model_implementation_contract": MODEL_CONTRACT,
            "materialization_manifest": materialization_manifest_path,
            "matched_row_coverage": matched_coverage_path,
            "candidate_inventory": candidate_inventory_path,
        },
        git_commit=_git_head(),
        python_version=platform.python_version(),
        sklearn_version=SKLEARN_VERSION,
    )
    print("Gate V3-5 real execution authorization candidate plan materialized.")
    print(f"Outer-fold jobs: {manifest['outer_fold_jobs']}")
    print(f"Candidate-pipeline-target combinations: {manifest['candidate_pipeline_target_combinations']}")
    print(f"Batches: {manifest['batch_count']}")
    print(f"Jobs per full batch: {manifest['jobs_per_batch']}")
    print(f"Final batch jobs: {manifest['final_batch_jobs']}")
    print(f"Stages: {manifest['stage_count']}")
    print("Declared empty stages preserved: True")
    print("All input hashes bound: True")
    print("All batches initially planned-not-started: True")
    print("Real development execution authorized: False")
    print("Real development model fitting performed: False")
    print("Development pipeline selection performed: False")
    print("Signal-establishment segment accessed: False")
    print("V3-9 final-framework reserve accessed: False")
    print(f"Outputs: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(
            f"Gate V3-5 real execution authorization materialization failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
