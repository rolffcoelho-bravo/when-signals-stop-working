from __future__ import annotations

import json
from pathlib import Path
import re

import pandas as pd

from shockbridge_signal_validity.v2.registry import load_v2_registry


WINDOWS_PATH = re.compile(r"[A-Za-z]:\\")


def main() -> int:
    registry = load_v2_registry()
    required = [
        Path("data/processed/v2/development/aligned_development_market_data.csv"),
        Path("data/processed/v2/development/development_targets.csv"),
        Path("data/processed/v2/development/nested_fold_plan.csv"),
        Path("data/processed/v2/development/candidate_inventory.csv"),
        Path("data/processed/v2/development/decision_policy_inventory.csv"),
        Path("data/processed/v2/development/development_partition_manifest.json"),
        Path("outputs/v2/development/scaffold_status.json"),
    ]
    missing = [path.as_posix() for path in required if not path.exists()]
    if missing:
        raise SystemExit("Missing V2 development assets: " + ", ".join(missing))

    holdout_root = Path("outputs/v2/holdout")
    holdout_files = [path for path in holdout_root.rglob("*") if path.is_file()] if holdout_root.exists() else []
    if holdout_files:
        raise SystemExit("Unauthorized holdout outputs exist.")

    aligned = pd.read_csv(required[0], parse_dates=["Timestamp"])
    timestamps = pd.DatetimeIndex(aligned["Timestamp"])
    if timestamps.max() >= registry.holdout_start:
        raise SystemExit("Development asset includes locked-evaluation timestamps.")

    targets = pd.read_csv(required[1], parse_dates=["Timestamp"])
    for horizon in registry.horizons:
        target_column = f"target_timestamp_h{horizon}"
        parsed = pd.to_datetime(targets[target_column], utc=True, errors="coerce")
        if parsed.dropna().gt(registry.development_end).any():
            raise SystemExit(f"Target horizon {horizon} crosses the development boundary.")

    folds = pd.read_csv(required[2])
    expected_rows = len(registry.horizons) * registry.outer_folds * (1 + registry.inner_folds)
    if len(folds) != expected_rows:
        raise SystemExit("Unexpected nested fold-plan row count.")
    if (folds["purge_rows"] != folds["horizon_candles"]).any():
        raise SystemExit("A fold purge gap does not equal its forecast horizon.")

    inventory = pd.read_csv(required[3])
    if inventory["candidate_id"].duplicated().any():
        raise SystemExit("Candidate identifiers are not unique.")
    if set(inventory["signal_family"]) != {"rsi", "bollinger"}:
        raise SystemExit("Confirmatory inventory contains an unexpected signal family.")

    for path in [required[5], required[6]]:
        raw = path.read_text(encoding="utf-8")
        if WINDOWS_PATH.search(raw) or "/home/" in raw:
            raise SystemExit(f"Manifest contains a local absolute path: {path}")

    status = json.loads(required[6].read_text(encoding="utf-8"))
    if status.get("status") != "PASS":
        raise SystemExit("Development scaffold status is not PASS.")
    if status.get("model_fitting_performed") is not False:
        raise SystemExit("Scaffold incorrectly reports model fitting.")
    if status.get("holdout_performance_accessed") is not False:
        raise SystemExit("Scaffold incorrectly reports holdout access.")

    print("V2 development scaffold verification passed.")
    print(f"Protocol lock: {status['protocol_lock_id']}")
    print(f"Candidate specifications: {len(inventory):,}")
    print(f"Nested fold-plan rows: {len(folds):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
