import argparse
import json
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shockbridge_signal_validity.v3.forecast_contract import ForecastProtocolViolation
from shockbridge_signal_validity.v3.forecast_development_execution import execute_matched_outer_fold

def load_batch_manifest(batch_id: str) -> pd.DataFrame:
    manifest_path = ROOT / "outputs/v3/development_execution_plan/execution_batch_manifest.csv"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing batch manifest at {manifest_path}")
    
    df = pd.read_csv(manifest_path)
    batch_record = df[df["batch_id"] == batch_id]
    if batch_record.empty:
        raise ValueError(f"Batch {batch_id} not found in manifest.")
    return batch_record

def load_job_plan(batch_id: str) -> pd.DataFrame:
    plan_path = ROOT / "outputs/v3/development_execution_plan/execution_job_plan.csv"
    if not plan_path.exists():
        raise FileNotFoundError(f"Missing execution job plan at {plan_path}")
    
    # In production, use chunking to load only the specific batch if memory is extremely tight
    df = pd.read_csv(plan_path)
    batch_jobs = df[df["batch_id"] == batch_id]
    return batch_jobs

def verify_authorization() -> None:
    lock_path = ROOT / "V3_G5_REAL_EXECUTION_AUTHORIZATION_LOCK.json"
    if not lock_path.exists():
        raise ForecastProtocolViolation("Execution authorization lock is missing.")
    
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("status") != "AUTHORIZATION_GRANTED":
        raise ForecastProtocolViolation(f"Execution not granted. Status: {lock.get('status')}")
    if not lock.get("real_development_execution_authorized"):
        raise ForecastProtocolViolation("Real development execution is explicitly unauthorized.")

def main():
    parser = argparse.ArgumentParser(description="Worker node script for V3-5 batch execution")
    parser.add_argument("--batch-id", required=True, help="The batch ID to execute (e.g. v3g5batch:0001)")
    parser.add_argument("--format", default="csv", choices=["csv", "parquet"], help="Output format for results")
    args = parser.parse_args()

    batch_id = args.batch_id

    try:
        verify_authorization()
    except Exception as e:
        print(f"Authorization Error: {e}")
        sys.exit(1)
        
    print(f"Initializing execution worker for batch: {batch_id}")
    
    try:
        batch_record = load_batch_manifest(batch_id)
        job_plan = load_job_plan(batch_id)
    except Exception as e:
        print(f"Failed to load planning data: {e}")
        sys.exit(1)
        
    job_count = len(job_plan)
    print(f"Loaded {job_count} jobs for {batch_id}.")
    
    # ---------------------------------------------------------
    # TODO: Load canonical source data, matched rows, and targets
    # ---------------------------------------------------------
    print("WARNING: Data loading and execute_matched_outer_fold are currently stubbed.")
    print("Connect the data adapter outputs to the worker execution loop.")
    
    # ---------------------------------------------------------
    # Example Execution Loop:
    # ---------------------------------------------------------
    results = []
    for _, job in job_plan.iterrows():
        # spec = load_spec(job["pipeline_spec_id"])
        # result = execute_matched_outer_fold(
        #     spec=spec,
        #     implementation_contract=...,
        #     benchmark_training=...,
        #     ...
        # )
        # results.append(result)
        pass
        
    print(f"Batch {batch_id} execution complete.")
    
    # ---------------------------------------------------------
    # Save Results
    # ---------------------------------------------------------
    output_dir = ROOT / "outputs/v3/development_execution_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # output_df = pd.DataFrame(results)
    output_df = pd.DataFrame([{"job_id": job["job_id"], "status": "STUBBED"} for _, job in job_plan.iterrows()])
    
    out_path = output_dir / f"{batch_id.replace(':', '_')}.{args.format}"
    if args.format == "parquet":
        output_df.to_parquet(out_path, index=False)
    else:
        output_df.to_csv(out_path, index=False)
        
    print(f"Results saved to {out_path}")

if __name__ == "__main__":
    main()
