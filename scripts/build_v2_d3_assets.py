from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

import pandas as pd

from shockbridge_signal_validity.data import read_ohlcv_csv
from shockbridge_signal_validity.v2.locked_evaluation import (
    load_single_frozen_pipeline,
    locked_evaluation,
    validate_d3_authorization,
)
from shockbridge_signal_validity.v2.manifests import file_record, sha256_file, write_json
from shockbridge_signal_validity.v2.partitions import authorize_holdout_access
from shockbridge_signal_validity.v2.registry import load_v2_registry


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute the single-access Version 2 D3 methodology-locked evaluation."
    )
    parser.add_argument("--sol-csv", type=Path, default=Path("data/raw/sol_usdt_4h.csv"))
    parser.add_argument("--btc-csv", type=Path, default=Path("data/raw/btc_usdt_4h.csv"))
    parser.add_argument("--registry", type=Path, default=Path("configs/v2_experiment_registry.json"))
    parser.add_argument("--d2b-config", type=Path, default=Path("configs/v2_d2b_selection.json"))
    parser.add_argument("--d3-config", type=Path, default=Path("configs/v2_d3_locked_evaluation.json"))
    parser.add_argument("--protocol-lock", type=Path, default=Path("V2_PROTOCOL_LOCK.json"))
    parser.add_argument("--d2c-lock", type=Path, default=Path("V2_D2C_ADMISSION_LOCK.json"))
    parser.add_argument("--d3-lock", type=Path, default=Path("V2_D3_EVALUATION_LOCK.json"))
    parser.add_argument(
        "--pipeline-registry",
        type=Path,
        default=Path("data/processed/v2/development/d2c_frozen_pipeline_registry.json"),
    )
    parser.add_argument(
        "--authorization",
        type=Path,
        default=Path("outputs/v2/development/d3_holdout_authorization.json"),
    )
    parser.add_argument("--processed-root", type=Path, default=Path("data/processed/v2/holdout"))
    parser.add_argument("--output-root", type=Path, default=Path("outputs/v2/holdout"))
    return parser.parse_args()


def git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> int:
    args = parse_args()
    registry = load_v2_registry(args.registry)
    d2b_config = json.loads(args.d2b_config.read_text(encoding="utf-8"))
    d3_config = json.loads(args.d3_config.read_text(encoding="utf-8"))
    protocol_lock = json.loads(args.protocol_lock.read_text(encoding="utf-8"))
    d2c_lock = json.loads(args.d2c_lock.read_text(encoding="utf-8"))
    d3_lock = json.loads(args.d3_lock.read_text(encoding="utf-8"))
    authorization = json.loads(args.authorization.read_text(encoding="utf-8"))
    pipeline = load_single_frozen_pipeline(
        args.pipeline_registry, expected_hash=d3_config["expected_pipeline_hash"]
    )

    if os.environ.get(d3_config["authorization"]["environment_variable"]) != d3_config["authorization"]["required_environment_value"]:
        raise RuntimeError("D3 single-access environment authorization is absent.")
    authorize_holdout_access(
        args.authorization,
        protocol_lock_id=protocol_lock["lock_id"],
        implementation_commit=str(authorization["implementation_commit"]),
    )
    validate_d3_authorization(
        authorization,
        protocol_lock_id=protocol_lock["lock_id"],
        d2c_lock_id=d2c_lock["lock_id"],
        d3_lock_id=d3_lock["lock_id"],
        implementation_commit=str(authorization["implementation_commit"]),
        pipeline=pipeline,
        registry=registry,
    )

    existing = []
    for directory in (args.processed_root, args.output_root):
        if directory.exists():
            existing.extend(path for path in directory.rglob("*") if path.is_file())
    if existing:
        raise RuntimeError(
            "D3 is single-access and refuses pre-existing locked-evaluation files: "
            + ", ".join(path.as_posix() for path in existing)
        )

    sol = read_ohlcv_csv(args.sol_csv)
    btc = read_ohlcv_csv(args.btc_csv)
    aligned = sol.add_prefix("sol_").join(btc.add_prefix("btc_"), how="inner")
    if aligned.index.max() < registry.holdout_end:
        raise RuntimeError("Raw data do not cover the complete methodology-locked period.")
    aligned = aligned.loc[registry.development_start : registry.holdout_end].copy()

    predictions, raw_metrics, state_parameters = locked_evaluation(
        aligned=aligned,
        pipeline=pipeline,
        registry=registry,
        d2b_config=d2b_config,
    )

    args.processed_root.mkdir(parents=True, exist_ok=False)
    args.output_root.mkdir(parents=True, exist_ok=False)

    market_path = args.processed_root / "d3_locked_market_data.csv"
    aligned.loc[registry.holdout_start : registry.holdout_end].to_csv(
        market_path, index_label="Timestamp"
    )
    predictions_path = args.processed_root / "d3_locked_predictions.csv"
    predictions.to_csv(predictions_path, index_label="Timestamp")
    state_path = args.processed_root / "d3_state_parameters.json"
    write_json(state_path, state_parameters)

    integrity = {
        "pipeline_hash": pipeline.pipeline_hash,
        "signal_family": pipeline.signal_family,
        "horizon_candles": pipeline.horizon_candles,
        "calibration_method": pipeline.calibration_method,
        "decision_probability_distance_threshold": pipeline.decision_probability_distance_threshold,
        "pipeline_registry_sha256": sha256_file(args.pipeline_registry),
        "authorization_sha256": sha256_file(args.authorization),
        "d2c_lock_id": d2c_lock["lock_id"],
        "d3_lock_id": d3_lock["lock_id"],
        "rsi_reentry_performed": False,
        "pipeline_retuning_performed": False,
        "alternative_pipeline_executed": False,
    }
    integrity_path = args.output_root / "d3_pipeline_integrity.json"
    write_json(integrity_path, integrity)

    metric_path = args.output_root / "d3_raw_metric_summary.json"
    write_json(metric_path, raw_metrics)

    authorization_commit = git_commit()
    consumption = {
        "status": "CONSUMED_ONCE",
        "authorization_commit": authorization_commit,
        "implementation_commit": authorization["implementation_commit"],
        "authorization_sha256": sha256_file(args.authorization),
        "pipeline_hash": pipeline.pipeline_hash,
        "signal_family": pipeline.signal_family,
        "consumed_at_utc": datetime.now(timezone.utc).isoformat(),
        "single_access": True,
        "holdout_start_utc": registry.holdout_start.isoformat(),
        "holdout_end_utc": registry.holdout_end.isoformat(),
        "holdout_performance_accessed": True,
    }
    consumption_path = args.output_root / "d3_authorization_consumption.json"
    write_json(consumption_path, consumption)

    generated = [
        market_path,
        predictions_path,
        state_path,
        integrity_path,
        metric_path,
        consumption_path,
    ]
    manifest = {
        "checkpoint": "V2_D3_METHODOLOGY_LOCKED_EVALUATION",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution_scope": d3_config["execution_scope"],
        "implementation_commit": authorization["implementation_commit"],
        "authorization_commit": authorization_commit,
        "protocol_lock_id": protocol_lock["lock_id"],
        "d2c_lock_id": d2c_lock["lock_id"],
        "d3_lock_id": d3_lock["lock_id"],
        "pipeline_hash": pipeline.pipeline_hash,
        "signal_family": pipeline.signal_family,
        "holdout_start_utc": registry.holdout_start.isoformat(),
        "holdout_end_utc": registry.holdout_end.isoformat(),
        "market_rows": int(len(aligned.loc[registry.holdout_start : registry.holdout_end])),
        "prediction_rows": int(len(predictions)),
        "subperiods": sorted(predictions["holdout_subperiod"].unique().tolist()),
        "methodology_locked_evaluation_executed": True,
        "holdout_performance_accessed": True,
        "pipeline_retuning_performed": False,
        "rsi_reentry_performed": False,
        "statistical_gate_evaluated": False,
        "economic_gate_evaluated": False,
        "robustness_gate_evaluated": False,
        "multiplicity_adjustment_applied": False,
        "files": [file_record(path, ROOT) for path in generated],
    }
    manifest_path = args.processed_root / "d3_evaluation_manifest.json"
    write_json(manifest_path, manifest)

    status = {
        "status": "PASS",
        "checkpoint": manifest["checkpoint"],
        "implementation_commit": manifest["implementation_commit"],
        "authorization_commit": authorization_commit,
        "d3_lock_id": d3_lock["lock_id"],
        "pipeline_hash": pipeline.pipeline_hash,
        "signal_family": pipeline.signal_family,
        "frozen_pipeline_count": 1,
        "market_rows": manifest["market_rows"],
        "prediction_rows": manifest["prediction_rows"],
        "methodology_locked_evaluation_executed": True,
        "holdout_authorization_consumed": True,
        "holdout_performance_accessed": True,
        "predictive_model_fitting_performed": True,
        "pipeline_retuning_performed": False,
        "rsi_reentry_performed": False,
        "statistical_gate_evaluated": False,
        "economic_gate_evaluated": False,
        "robustness_gate_evaluated": False,
        "multiplicity_adjustment_applied": False,
        "manifest_sha256": sha256_file(manifest_path),
        "predictions_sha256": sha256_file(predictions_path),
    }
    status_path = args.output_root / "d3_locked_evaluation_status.json"
    write_json(status_path, status)

    print("Version 2 D3 methodology-locked evaluation completed.")
    print(f"Authorized family: {pipeline.signal_family.upper()}")
    print(f"Frozen pipeline hash: {pipeline.pipeline_hash}")
    print(f"Locked market rows: {manifest['market_rows']:,}")
    print(f"Prediction rows: {manifest['prediction_rows']:,}")
    print("Pipeline retuning performed: False")
    print("RSI re-entry performed: False")
    print("Statistical gate evaluated: False")
    print("Economic gate evaluated: False")
    print("Holdout performance accessed: True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
