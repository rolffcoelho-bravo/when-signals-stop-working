from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

import pandas as pd

from shockbridge_signal_validity.data import read_ohlcv_csv
from shockbridge_signal_validity.v2.inventory import (
    build_candidate_inventory,
    build_decision_policy_inventory,
)
from shockbridge_signal_validity.v2.manifests import (
    dataframe_sha256,
    file_record,
    sha256_file,
    write_json,
)
from shockbridge_signal_validity.v2.partitions import (
    assert_development_only,
    build_development_partition,
)
from shockbridge_signal_validity.v2.registry import load_v2_registry
from shockbridge_signal_validity.v2.splits import build_nested_fold_plan
from shockbridge_signal_validity.v2.targets import build_development_targets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build Version 2 development-only partition, target, fold, and "
            "candidate-inventory assets without fitting models or accessing "
            "locked-evaluation performance."
        )
    )
    parser.add_argument(
        "--sol-csv", type=Path, default=Path("data/raw/sol_usdt_4h.csv")
    )
    parser.add_argument(
        "--btc-csv", type=Path, default=Path("data/raw/btc_usdt_4h.csv")
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("configs/v2_experiment_registry.json"),
    )
    parser.add_argument(
        "--protocol-lock", type=Path, default=Path("V2_PROTOCOL_LOCK.json")
    )
    parser.add_argument(
        "--processed-root", type=Path, default=Path("data/processed/v2/development")
    )
    parser.add_argument(
        "--output-root", type=Path, default=Path("outputs/v2/development")
    )
    return parser.parse_args()


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> int:
    args = parse_args()
    root = Path.cwd().resolve()
    registry = load_v2_registry(args.registry)
    protocol_lock = json.loads(args.protocol_lock.read_text(encoding="utf-8"))

    sol = read_ohlcv_csv(args.sol_csv)
    btc = read_ohlcv_csv(args.btc_csv)
    aligned = sol.add_prefix("sol_").join(
        btc.add_prefix("btc_"), how="inner"
    )
    partition = build_development_partition(aligned, registry)
    assert_development_only(partition.frame, registry)

    args.processed_root.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)
    holdout_root = Path("outputs/v2/holdout")
    existing_holdout_files = list(holdout_root.rglob("*")) if holdout_root.exists() else []
    existing_holdout_files = [path for path in existing_holdout_files if path.is_file()]
    if existing_holdout_files:
        raise RuntimeError(
            "Holdout output files exist before authorization: "
            + ", ".join(path.as_posix() for path in existing_holdout_files)
        )

    aligned_path = args.processed_root / "aligned_development_market_data.csv"
    partition.frame.to_csv(aligned_path, index_label="Timestamp")

    targets = build_development_targets(
        partition.frame["sol_Close"],
        registry.horizons,
        registry.development_end,
    )
    targets_path = args.processed_root / "development_targets.csv"
    targets.to_csv(targets_path, index_label="Timestamp")

    fold_plan = build_nested_fold_plan(
        targets.index,
        registry.horizons,
        registry.outer_folds,
        registry.inner_folds,
    )
    folds_path = args.processed_root / "nested_fold_plan.csv"
    fold_plan.to_csv(folds_path, index=False)

    inventory = build_candidate_inventory(registry)
    inventory_path = args.processed_root / "candidate_inventory.csv"
    inventory.to_csv(inventory_path, index=False)

    policies = build_decision_policy_inventory(registry)
    policies_path = args.processed_root / "decision_policy_inventory.csv"
    policies.to_csv(policies_path, index=False)

    implementation_commit = git_commit()
    manifest = {
        "asset_scope": {
            "primary": registry.payload["data"]["primary_asset"],
            "context": registry.payload["data"]["market_context"],
            "venue": registry.payload["data"]["primary_venue"],
            "frequency": registry.payload["data"]["frequency"],
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution_scope": "DEVELOPMENT_ONLY_NO_MODEL_FITTING",
        "implementation_commit": implementation_commit,
        "protocol_lock_id": protocol_lock["lock_id"],
        "registry": {
            "path": args.registry.as_posix(),
            "sha256": registry.sha256,
            "version": registry.protocol_version,
        },
        "partition": {
            "start_utc": partition.start.isoformat(),
            "end_utc": partition.end.isoformat(),
            "locked_evaluation_start_utc": registry.holdout_start.isoformat(),
            "source_rows": partition.source_rows,
            "development_rows": partition.rows,
            "aligned_frame_sha256": dataframe_sha256(partition.frame),
            "target_frame_sha256": dataframe_sha256(targets),
        },
        "folds": {
            "outer": registry.outer_folds,
            "inner": registry.inner_folds,
            "horizons_candles": list(registry.horizons),
            "plan_rows": int(len(fold_plan)),
        },
        "candidate_inventory": {
            "rows": int(len(inventory)),
            "rsi_rows": int((inventory["signal_family"] == "rsi").sum()),
            "bollinger_rows": int((inventory["signal_family"] == "bollinger").sum()),
            "model_fitting_performed": False,
        },
        "holdout": {
            "performance_accessed": False,
            "output_files_created": 0,
        },
        "files": [
            file_record(path, root)
            for path in [
                aligned_path,
                targets_path,
                folds_path,
                inventory_path,
                policies_path,
            ]
        ],
    }
    manifest_path = args.processed_root / "development_partition_manifest.json"
    write_json(manifest_path, manifest)

    status = {
        "status": "PASS",
        "checkpoint": "V2_IMPLEMENTATION_SCAFFOLD",
        "protocol_lock_id": protocol_lock["lock_id"],
        "implementation_commit": implementation_commit,
        "development_rows": partition.rows,
        "candidate_inventory_rows": int(len(inventory)),
        "nested_fold_plan_rows": int(len(fold_plan)),
        "model_fitting_performed": False,
        "holdout_performance_accessed": False,
        "manifest_sha256": sha256_file(manifest_path),
    }
    write_json(args.output_root / "scaffold_status.json", status)

    print("Version 2 development scaffold generated.")
    print(f"Development rows: {partition.rows:,}")
    print(f"Registered candidate specifications: {len(inventory):,}")
    print(f"Nested fold-plan rows: {len(fold_plan):,}")
    print("Model fitting performed: False")
    print("Holdout performance accessed: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
