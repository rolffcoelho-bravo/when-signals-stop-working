import argparse
import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
import multiprocessing

ROOT = Path(__file__).resolve().parents[1]

def load_batch_manifest() -> pd.DataFrame:
    manifest_path = ROOT / "outputs/v3/development_execution_plan/execution_batch_manifest.csv"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing batch manifest at {manifest_path}")
    return pd.read_csv(manifest_path)

def verify_authorization() -> None:
    lock_path = ROOT / "V3_G5_REAL_EXECUTION_AUTHORIZATION_LOCK.json"
    if not lock_path.exists():
        raise RuntimeError("Execution authorization lock is missing. Run finalize_v3_g5_real_execution_authorization.py first.")
    
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if not lock.get("real_development_execution_authorized"):
        raise RuntimeError("Real development execution is explicitly unauthorized.")

def run_worker(batch_id: str, format_arg: str) -> str:
    # Path to the worker script
    worker_script = ROOT / "scripts/run_v3_g5_execution_worker.py"
    
    cmd = [
        sys.executable, 
        str(worker_script), 
        "--batch-id", batch_id,
        "--format", format_arg
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return f"FAILED: {batch_id}\n{result.stderr}"
    return f"SUCCESS: {batch_id}"

def main():
    parser = argparse.ArgumentParser(description="Local Multi-Processing Orchestrator for V3-5")
    parser.add_argument("--workers", type=int, default=max(1, multiprocessing.cpu_count() - 1),
                        help="Number of parallel worker processes to spawn.")
    parser.add_argument("--format", default="csv", choices=["csv", "parquet"], help="Output format for batch results")
    args = parser.parse_args()

    try:
        verify_authorization()
    except Exception as e:
        print(f"Authorization Error: {e}")
        sys.exit(1)
        
    print("Loading batch manifest...")
    try:
        manifest = load_batch_manifest()
    except Exception as e:
        print(f"Error loading manifest: {e}")
        sys.exit(1)
        
    # Find batches that are not yet COMPLETE
    pending_batches = manifest[manifest["batch_state"].isin(["PLANNED_NOT_STARTED", "RUNNING"])]["batch_id"].tolist()
    
    if not pending_batches:
        print("All batches are complete!")
        sys.exit(0)
        
    print(f"Found {len(pending_batches)} batches pending execution.")
    print(f"Starting ProcessPoolExecutor with {args.workers} workers...")
    
    success_count = 0
    failure_count = 0
    
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(run_worker, bid, args.format): bid for bid in pending_batches}
        
        for future in as_completed(futures):
            batch_id = futures[future]
            try:
                res = future.result()
                print(res)
                if res.startswith("SUCCESS"):
                    success_count += 1
                else:
                    failure_count += 1
            except Exception as e:
                print(f"FAILED: {batch_id} with exception: {e}")
                failure_count += 1
                
    print("\n--- Execution Summary ---")
    print(f"Total Batches Processed: {len(pending_batches)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")

if __name__ == "__main__":
    main()
