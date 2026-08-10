from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
import pandas as pd
from sklearn import __version__ as SKLEARN_VERSION

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shockbridge_signal_validity.v3.forecast_real_execution_batching import (  # noqa: E402
    load_stage_aligned_authorization_candidate,
)
from shockbridge_signal_validity.v3.forecast_real_execution_verification import (  # noqa: E402
    verify_authorization_candidate_plan_strict,
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
    authorization = load_stage_aligned_authorization_candidate(AUTHORIZATION_CONTRACT)
    manifest = verify_authorization_candidate_plan_strict(
        output_dir=OUTPUT_DIR,
        authorization_contract=authorization,
    )
    git_head = _git_head()
    if manifest.get("git_commit") != git_head:
        raise RuntimeError("Authorization plan is not bound to the current Git HEAD.")
    expected_environment = {
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "scikit_learn_version": SKLEARN_VERSION,
        "platform": platform.platform(),
    }
    if manifest.get("environment") != expected_environment:
        raise RuntimeError("Authorization plan serialization environment binding changed.")

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
    input_manifest_path = OUTPUT_DIR / str(outputs["input_hash_manifest"])
    input_manifest = json.loads(input_manifest_path.read_text(encoding="utf-8"))
    if input_manifest.get("all_inputs_bound") is not True:
        raise RuntimeError("Authorization input manifest is not fully bound.")
    if input_manifest.get("input_sha256") != observed_input_hashes:
        raise RuntimeError("Authorization input manifests disagree.")

    batches = pd.read_csv(OUTPUT_DIR / str(outputs["batch_manifest"]))
    stages = pd.read_csv(OUTPUT_DIR / str(outputs["stage_manifest"]))
    if set(batches["batch_state"].unique()) != {"PLANNED_NOT_STARTED"}:
        raise RuntimeError("Authorization batch manifest contains a started batch.")
    if list(stages["stage_rank"].astype(int)) != [1, 2, 3, 4, 5, 6]:
        raise RuntimeError("Authorization stage order changed.")
    if int(stages["job_count"].sum()) != 229500:
        raise RuntimeError("Authorization stage workload changed.")
    if batches.groupby("batch_ordinal")["stage_rank"].nunique().max() != 1:
        raise RuntimeError("Authorization batch manifest mixes scientific stages.")

    manifest_path = OUTPUT_DIR / str(outputs["authorization_candidate_manifest"])
    manifest_sha256 = _sha256_file(manifest_path)
    output_hashes = manifest["output_sha256"]
    batch_count = int(manifest["batch_count"])

    print("Gate V3-5 real development execution authorization candidate verified.")
    print("Development engine boundary protected: True")
    print("Authorization candidate contract frozen: True")
    print(f"Plan Git commit: {git_head}")
    print("Outer-fold jobs: 229500")
    print("Candidate-pipeline-target combinations: 45900")
    print(f"Stage-aligned batches: {batch_count}")
    print("Valid stage-aligned batch range: 918-919")
    print("Jobs per full batch: 250")
    print("Final batch jobs: 130")
    print("Execution stages: 6")
    print("No batch crosses a stage boundary: True")
    print(f"Python version: {expected_environment['python_version']}")
    print(f"pandas version: {expected_environment['pandas_version']}")
    print(f"NumPy version: {expected_environment['numpy_version']}")
    print(f"scikit-learn version: {expected_environment['scikit_learn_version']}")
    print(f"Platform: {expected_environment['platform']}")
    print(f"Authorization candidate manifest SHA-256: {manifest_sha256}")
    print(f"Execution job plan SHA-256: {output_hashes[str(outputs['job_plan'])]}")
    print(f"Execution batch manifest SHA-256: {output_hashes[str(outputs['batch_manifest'])]}")
    print(f"Execution stage manifest SHA-256: {output_hashes[str(outputs['stage_manifest'])]}")
    print(f"Authorization input manifest SHA-256: {output_hashes[str(outputs['input_hash_manifest'])]}")
    print("Input and output hashes verified: True")
    print("Input hash manifests agree: True")
    print("Strict false-state parsing verified: True")
    print("Git and serialization environment binding verified: True")
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
