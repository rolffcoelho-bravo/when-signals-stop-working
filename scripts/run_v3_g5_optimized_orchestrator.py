import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shockbridge_signal_validity.v3.forecast_contract import ForecastProtocolViolation
from shockbridge_signal_validity.v3.forecast_development_execution import execute_matched_outer_fold
from shockbridge_signal_validity.v3.forecast_model_registry import load_contracts, build_pipeline_registry

def load_batch_manifest() -> pd.DataFrame:
    manifest_path = ROOT / "outputs/v3/development_execution_plan/execution_batch_manifest.csv"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing batch manifest at {manifest_path}")
    return pd.read_csv(manifest_path)

def run_worker_chunk(chunk_file: str, format_arg: str):
    """The function executed by the worker process for a list of batches"""
    # Force single threading for internal math libraries to prevent CPU thrashing
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"
    
    with open(chunk_file, "r") as f:
        batches = json.load(f)
        
    print(f"[Worker {os.getpid()}] Processing {len(batches)} batches. Loading global datasets into memory once...")
    
    FORECAST_CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"
    MODEL_CONTRACT = ROOT / "configs" / "v3_g5_model_implementation_contract.json"
    _forecast, _implementation = load_contracts(FORECAST_CONTRACT, MODEL_CONTRACT)
    _registry = build_pipeline_registry(_forecast, _implementation)
    _spec_map = {spec.pipeline_spec_id: spec for spec in _registry}
    import csv
    
    plan_path = ROOT / "outputs/v3/development_execution_plan/execution_job_plan.csv"
    if not plan_path.exists():
        raise FileNotFoundError(f"Missing execution job plan at {plan_path}")
        
    batch_set = set(batches)
    my_jobs = {b: [] for b in batches}
    
    print(f"[Worker {os.getpid()}] Reading job plan sequentially to conserve memory...")
    with open(plan_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            b_id = row["batch_id"]
            if b_id in batch_set:
                row["horizon_candles"] = int(row["horizon_candles"])
                row["outer_fold"] = int(row["outer_fold"])
                my_jobs[b_id].append(row)
    
    print(f"[Worker {os.getpid()}] Loading global datasets...")
    benchmark_df = pd.read_csv(ROOT / "outputs/v3/forecast_foundation/continuity_benchmark.csv", index_col="timestamp", parse_dates=True)
    target_df = pd.read_csv(ROOT / "outputs/v3/forecast_foundation/development_targets.csv", index_col="timestamp", parse_dates=True)
    
    candidate_pivoted_path = ROOT / "outputs/v3/signal_engine/signal_features_pivoted.parquet"
    if candidate_pivoted_path.exists():
        candidate_pivoted = pd.read_parquet(candidate_pivoted_path)
    else:
        candidate_raw = pd.read_csv(ROOT / "outputs/v3/signal_engine/signal_features.csv")
        candidate_pivoted = candidate_raw.pivot(index="timestamp", columns="feature_key", values="feature_value")
        candidate_pivoted.index = pd.to_datetime(candidate_pivoted.index)
    
    candidate_df = pd.concat([benchmark_df, candidate_pivoted], axis=1)
    
    valid_idx = benchmark_df.dropna().index.intersection(target_df.index)
    benchmark_df = benchmark_df.loc[valid_idx]
    candidate_df = candidate_df.loc[valid_idx]
    target_df = target_df.loc[valid_idx]
    
    candidate_df = candidate_df.ffill().fillna(0)
    
    fold_plan = pd.read_csv(ROOT / "outputs/v3/forecast_foundation/nested_fold_plan.csv")
    outer_folds = fold_plan[fold_plan["level"] == "outer"]
    
    print(f"[Worker {os.getpid()}] Ready. Beginning execution loop.")
    
    out_dir = ROOT / "outputs/v3/development_execution_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for batch_id in batches:
        try:
            job_plan = my_jobs[batch_id]
            if not job_plan:
                print(f"[Worker {os.getpid()}] FAILED: {batch_id} (No jobs found)")
                continue
                
            results = []
            for job in job_plan:
                try:
                    spec = _spec_map[job["pipeline_spec_id"]]
                    fold_id = job["outer_fold"]
                    fold_matches = outer_folds[(outer_folds["outer_fold"] == fold_id) & (outer_folds["horizon_candles"] == job["horizon_candles"])]
                    if len(fold_matches) == 0:
                        raise ValueError(f"Fold {fold_id} not found in fold_plan")
                    fold_def = fold_matches.iloc[0]
                    
                    target_df_horizon = target_df[target_df["horizon_candles"] == job["horizon_candles"]]
                    target_name = spec.target_name
                    realized_series = target_df_horizon["future_log_return"]

                    train_start = pd.to_datetime(fold_def["train_start_utc"])
                    train_end = pd.to_datetime(fold_def["train_end_utc"])
                    test_start = pd.to_datetime(fold_def["test_start_utc"])
                    test_end = pd.to_datetime(fold_def["test_end_utc"])
                    
                    if target_name == "direction":
                        target_series = target_df_horizon["direction"]
                    elif target_name == "expected_return":
                        target_series = target_df_horizon["future_log_return"]
                    elif target_name == "large_move_probability":
                        train_returns = target_df_horizon["future_log_return"][train_start:train_end]
                        q90 = train_returns.abs().quantile(0.90)
                        target_series = (target_df_horizon["future_log_return"].abs() > q90).astype(int)
                    else:
                        raise ValueError(f"Unknown target {target_name}")
                    
                    train_slice_raw = benchmark_df[train_start:train_end]
                    train_len = len(train_slice_raw)
                    if train_len == 0:
                        raise ValueError("Training slice is empty.")
                        
                    calib_start_idx = int(train_len * 0.8)
                    if calib_start_idx == 0:
                        calib_start_idx = 1
                    
                    valid_target_idx = target_series.dropna().index.intersection(realized_series.dropna().index)
                    
                    train_slice_df = train_slice_raw.loc[:train_slice_raw.index[calib_start_idx - 1]]
                    calib_slice_df = train_slice_raw.loc[train_slice_raw.index[calib_start_idx]:]
                    
                    train_idx = train_slice_df.index.intersection(valid_target_idx)
                    calib_idx = calib_slice_df.index.intersection(valid_target_idx)
                    test_idx = benchmark_df[test_start:test_end].index.intersection(valid_target_idx)
                    
                    result = execute_matched_outer_fold(
                        spec=spec,
                        implementation_contract=_implementation,
                        benchmark_training=benchmark_df.loc[train_idx],
                        candidate_training=candidate_df.loc[train_idx],
                        training_target=target_series.loc[train_idx],
                        benchmark_calibration=benchmark_df.loc[calib_idx],
                        candidate_calibration=candidate_df.loc[calib_idx],
                        calibration_target=target_series.loc[calib_idx],
                        benchmark_test=benchmark_df.loc[test_idx],
                        candidate_test=candidate_df.loc[test_idx],
                        test_target=target_series.loc[test_idx],
                        test_future_log_return=realized_series.loc[test_idx],
                        horizon_candles=job["horizon_candles"],
                        calibration_method="sigmoid" if target_name in ["direction", "large_move_probability"] else "none",
                        abstention_threshold=0.02,
                        synthetic_validation_only=False,
                    )
                    
                    res_dict = {
                        "job_id": job["job_id"],
                        "status": "SUCCESS",
                        "real_development_model_fitting_performed": result.real_development_model_fitting_performed,
                    }
                    if result.candidate_economic is not None:
                        res_dict["coverage_fraction"] = result.candidate_economic.coverage
                        
                    if target_name in ["direction", "large_move_probability"]:
                        res_dict["brier_score"] = result.candidate_metrics.secondary_metrics.get("brier_score")
                        res_dict["log_loss"] = result.candidate_metrics.primary_loss
                    elif target_name == "expected_return":
                        res_dict["mse"] = result.candidate_metrics.primary_loss
                    
                    results.append(res_dict)
                    
                except Exception as e:
                    results.append({
                        "job_id": job["job_id"],
                        "status": f"FAILED: {str(e)}"
                    })
                    
            out_df = pd.DataFrame(results)
            out_path = out_dir / f"{batch_id.replace(':', '_')}.csv"
            out_df.to_csv(out_path, index=False)
            print(f"[Worker {os.getpid()}] SUCCESS: {batch_id}")
            
        except Exception as e:
            print(f"[Worker {os.getpid()}] FAILED: {batch_id} with exception: {e}")

def verify_authorization() -> None:
    lock_path = ROOT / "V3_G5_REAL_EXECUTION_AUTHORIZATION_LOCK.json"
    if not lock_path.exists():
        raise RuntimeError("Execution authorization lock is missing.")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if not lock.get("real_development_execution_authorized"):
        raise RuntimeError("Real development execution is explicitly unauthorized.")

def main():
    parser = argparse.ArgumentParser(description="Fully Decoupled Local Multiprocessing Orchestrator")
    parser.add_argument("--workers", type=int, default=6, help="Number of parallel worker processes to spawn.")
    parser.add_argument("--format", default="csv", choices=["csv", "parquet"], help="Output format for batch results")
    parser.add_argument("--worker-chunk", type=str, default=None, help="Internal use only: path to JSON file containing list of batches")
    args = parser.parse_args()

    if args.worker_chunk:
        run_worker_chunk(args.worker_chunk, args.format)
        sys.exit(0)

    try:
        verify_authorization()
    except Exception as e:
        print(f"Authorization Error: {e}")
        sys.exit(1)
        
    print("Loading batch manifest...")
    manifest = load_batch_manifest()
    
    pending_batches = manifest[manifest["batch_state"].isin(["PLANNED_NOT_STARTED", "RUNNING"])]["batch_id"].tolist()
    
    output_dir = ROOT / "outputs/v3/development_execution_results"
    filtered_pending = []
    for bid in pending_batches:
        csv_path = output_dir / f"{bid.replace(':', '_')}.csv"
        parquet_path = output_dir / f"{bid.replace(':', '_')}.parquet"
        skip = False
        if csv_path.exists():
            with open(csv_path, 'r') as f:
                content = f.read()
                if "STUBBED" not in content and "FAILED" not in content:
                    skip = True
        elif parquet_path.exists():
            skip = True
            
        if not skip:
            filtered_pending.append(bid)
    
    pending_batches = filtered_pending

    if not pending_batches:
        print("All batches are complete!")
        sys.exit(0)
        
    print(f"Found {len(pending_batches)} batches pending execution.")
    print(f"Spawning {args.workers} decoupled worker processes...")
    
    # Split into chunks
    import math
    chunk_size = math.ceil(len(pending_batches) / args.workers)
    chunks = [pending_batches[i:i + chunk_size] for i in range(0, len(pending_batches), chunk_size)]
    
    processes = []
    temp_files = []
    
    scratch_dir = ROOT / "outputs" / "temp_chunks"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    
    for i, chunk in enumerate(chunks):
        if not chunk:
            continue
        chunk_file = scratch_dir / f"chunk_{i}.json"
        with open(chunk_file, "w") as f:
            json.dump(chunk, f)
        temp_files.append(chunk_file)
        
        cmd = [sys.executable, "-u", __file__, "--worker-chunk", str(chunk_file), "--format", args.format]
        p = subprocess.Popen(cmd)
        processes.append(p)
        
    print(f"Waiting for {len(processes)} processes to finish...")
    for p in processes:
        p.wait()
        
    # Cleanup
    for f in temp_files:
        try:
            os.remove(f)
        except:
            pass
            
    print("\n--- Execution Summary ---")
    print(f"All worker processes have completed. Check output directory for results.")

if __name__ == "__main__":
    main()
