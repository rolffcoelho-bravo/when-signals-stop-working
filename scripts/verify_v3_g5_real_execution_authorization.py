from __future__ import annotations

from hashlib import sha256
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

from shockbridge_signal_validity.v3.forecast_real_execution_authorization import (  # noqa: E402
    load_authorization_candidate,
    verify_authorization_candidate_plan,
)

AUTHORIZATION_CONTRACT = (
    ROOT / "configs" / "v3_g5_real_execution_authorization_candidate.json"
)
ENGINE_CONTRACT = ROOT / "configs" / "v3_g5_development_execution_contract.json"
ENGINE_VALIDATION = ROOT / "V3_G5_DEVELOPMENT_ENGINE_VALIDATION.json"
FORECAST_CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"
MODEL_CONTRACT = ROOT / "configs" / "v3_g5_model_implementation_contract.json"
FOUNDATION_DIR = ROOT / "outputs" / "v3" / "forecast_foundation"
OUTPUT_DIR = ROOT / "outputs" / "v3" / "development_execution_plan"


def _sha256_file(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Authorization input is missing: {path}")
    return sha256(path.read_bytes()).hexdigest()


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
    manifest = verify_authorization_candidate_plan(
        output_dir=OUTPUT_DIR,
        authorization_contract=authorization,
    )
    if manifest.get("git_commit") != _git_head():
        raise RuntimeError("Authorization plan is not bound to the current Git HEAD.")
    if manifest.get("python_version") != platform.python_version():
        raise RuntimeError("Authorization plan Python version binding changed.")
    if manifest.get("scikit_learn_version") != SKLEARN_VERSION:
        raise RuntimeError("Authorization plan scikit-learn version binding changed.")

    input_paths = {
        "authorization_candidate_contract": AUTHORIZATION_CONTRACT,
        "development_engine_contract": ENGINE_CONTRACT,
        "development_engine_validation": ENGINE_VALIDATION,
        "forecast_contract": FORECAST_CONTRACT,
        "model_implementation_contract": MODEL_CONTRACT,
        "materialization_manifest": FOUNDATION_DIR / "materialization_manifest.json",
        "matched_row_coverage": FOUNDATION_DIR / "matched_row_coverage.csv",
        "candidate_inventory": FOUNDATION_DIR / "candidate_inventory.csv",
    }
    observed_input_hashes = manifest.get("input_sha256", {})
    if set(observed_input_hashes) != set(input_paths):
        raise RuntimeError("Authorization input hash identity changed.")
    for name, path in input_paths.items():
        if observed_input_hashes.get(name) != _sha256_file(path):
            raise RuntimeError(f"Authorization input hash mismatch: {name}")

    outputs = authorization["planning_outputs"]
    plan = pd.read_csv(OUTPUT_DIR / str(outputs["job_plan"]))
    batches = pd.read_csv(OUTPUT_DIR / str(outputs["batch_manifest"]))
    stages = pd.read_csv(OUTPUT_DIR / str(outputs["stage_manifest"]))
    false_tokens = {False, "False", "false", 0, "0"}
    for column in (
        "real_execution_authorized",
        "real_development_model_fitting_performed",
        "development_pipeline_selection_performed",
        "signal_establishment_segment_accessed",
        "final_framework_reserve_accessed",
    ):
        if not set(plan[column].unique()).issubset(false_tokens):
            raise RuntimeError(f"Authorization plan advanced execution state: {column}")
    if set(plan["batch_state"].unique()) != {"PLANNED_NOT_STARTED"}:
        raise RuntimeError("Authorization plan contains a started batch.")
    if set(batches["batch_state"].unique()) != {"PLANNED_NOT_STARTED"}:
        raise RuntimeError("Authorization batch manifest contains a started batch.")
    if list(stages["stage_rank"]) != [1, 2, 3, 4, 5, 6]:
        raise RuntimeError("Authorization stage order changed.")
    if int(stages["job_count"].sum()) != 211140:
        raise RuntimeError("Authorization stage workload changed.")

    print("Gate V3-5 real development execution authorization candidate verified.")
    print("Development engine boundary protected: True")
    print("Authorization candidate contract frozen: True")
    print("Outer-fold jobs: 211140")
    print("Candidate-pipeline-target combinations: 42228")
    print("Batches: 845")
    print("Jobs per full batch: 250")
    print("Final batch jobs: 140")
    print("Execution stages: 6")
    print("Input and output hashes verified: True")
    print("Git/environment binding verified: True")
    print("All batches planned-not-started: True")
    print("Real development execution authorized: False")
    print("Real development model fitting performed: False")
    print("Development pipeline selection performed: False")
    print("Signal-establishment segment accessed: False")
    print("V3-9 final-framework reserve accessed: False")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(
            f"Gate V3-5 real execution authorization verification failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
