from __future__ import annotations

import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from shockbridge_signal_validity.data import read_ohlcv_csv
from shockbridge_signal_validity.features import (
    BASELINE_FEATURES,
    BOLLINGER_FEATURES,
    COMBINED_FEATURES,
    RSI_FEATURES,
    FeatureConfig,
    build_feature_frame,
)


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
CONFIG_PATH = ROOT / "configs" / "sol_4h_primary.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def save_indexed(frame: pd.DataFrame, path: Path) -> None:
    output = frame.copy()
    output.index.name = "timestamp_utc"
    output.reset_index().to_csv(path, index=False)


def main() -> int:
    config_data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    feature = FeatureConfig(
        horizon=int(config_data["forecast_horizon_candles"]),
        cost_bps=float(config_data["estimated_one_way_cost_bps"]),
        rsi_period=int(config_data["rsi"]["period"]),
        rsi_lower=float(config_data["rsi"]["lower"]),
        rsi_upper=float(config_data["rsi"]["upper"]),
        bollinger_period=int(config_data["bollinger"]["period"]),
        bollinger_std=float(config_data["bollinger"]["standard_deviations"]),
    )

    sol_path = RAW / "sol_usdt_4h.csv"
    btc_path = RAW / "btc_usdt_4h.csv"
    sol = read_ohlcv_csv(sol_path)
    btc = read_ohlcv_csv(btc_path)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    existing_download_manifest: dict = {}
    download_manifest_path = RAW / "download_manifest.json"
    if download_manifest_path.exists():
        existing_download_manifest = json.loads(
            download_manifest_path.read_text(encoding="utf-8")
        )
    public_download_manifest = {
        "schema_version": 1,
        "data_snapshot_id": config_data["data_snapshot_id"],
        "original_downloaded_at_utc": existing_download_manifest.get(
            "downloaded_at_utc"
        ),
        "venue": "Binance spot",
        "access_library": "CCXT",
        "authentication": "none; public market data",
        "timeframe": config_data["timeframe"],
        "requested_start_utc": config_data["sample_start_utc"],
        "download_end_exclusive_utc": config_data[
            "download_end_exclusive_utc"
        ],
        "last_included_candle_utc": config_data["sample_last_candle_utc"],
        "assets": {
            "SOL/USDT": {
                "file": "data/raw/sol_usdt_4h.csv",
                "rows": len(sol),
                "first_timestamp_utc": sol.index.min().isoformat(),
                "last_timestamp_utc": sol.index.max().isoformat(),
                "sha256": sha256(sol_path),
            },
            "BTC/USDT": {
                "file": "data/raw/btc_usdt_4h.csv",
                "rows": len(btc),
                "first_timestamp_utc": btc.index.min().isoformat(),
                "last_timestamp_utc": btc.index.max().isoformat(),
                "sha256": sha256(btc_path),
            },
        },
        "documentation": [
            "https://developers.binance.com/en/docs/products/spot/rest-api",
            "https://github.com/binance/binance-public-data",
            "https://github.com/ccxt/ccxt/wiki/manual",
        ],
        "rights_notice": (
            "The repository MIT license covers ShockBridge-authored code and "
            "documentation, not third-party market data. Reuse remains subject "
            "to the source venue's applicable terms."
        ),
    }
    download_manifest_path.write_text(
        json.dumps(public_download_manifest, indent=2), encoding="utf-8"
    )

    aligned = sol.add_prefix("sol_").join(btc.add_prefix("btc_"), how="inner")
    save_indexed(aligned, PROCESSED / "aligned_market_data.csv")

    features = build_feature_frame(sol, btc, feature)
    save_indexed(features, PROCESSED / "model_features.csv")

    splitter = TimeSeriesSplit(
        n_splits=int(config_data["chronological_folds"]),
        gap=feature.horizon,
    )
    assignment_rows: list[dict] = []
    boundary_rows: list[dict] = []
    for fold, (train_idx, test_idx) in enumerate(splitter.split(features), start=1):
        train_dates = features.index[train_idx]
        test_dates = features.index[test_idx]
        boundary_rows.append({
            "fold": fold,
            "train_start_utc": train_dates.min().isoformat(),
            "train_end_utc": train_dates.max().isoformat(),
            "test_start_utc": test_dates.min().isoformat(),
            "test_end_utc": test_dates.max().isoformat(),
            "n_train": len(train_dates),
            "n_test": len(test_dates),
            "gap_observations": feature.horizon,
        })
        assignment_rows.extend(
            {"fold": fold, "timestamp_utc": timestamp.isoformat(), "partition": "train"}
            for timestamp in train_dates
        )
        assignment_rows.extend(
            {"fold": fold, "timestamp_utc": timestamp.isoformat(), "partition": "test"}
            for timestamp in test_dates
        )

    pd.DataFrame(boundary_rows).to_csv(PROCESSED / "fold_boundaries.csv", index=False)
    pd.DataFrame(assignment_rows).to_csv(PROCESSED / "fold_assignments.csv", index=False)

    feature_manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_snapshot_id": config_data["data_snapshot_id"],
        "target": {
            "future_return": "log SOL close return over the next four-hour candle",
            "target_up": "1 when future_return > 0, otherwise 0",
        },
        "feature_config": {
            "horizon": feature.horizon,
            "cost_bps": feature.cost_bps,
            "rsi_period": feature.rsi_period,
            "rsi_lower": feature.rsi_lower,
            "rsi_upper": feature.rsi_upper,
            "bollinger_period": feature.bollinger_period,
            "bollinger_std": feature.bollinger_std,
            "regime_lookback": feature.regime_lookback,
        },
        "feature_groups": {
            "baseline": BASELINE_FEATURES,
            "rsi": RSI_FEATURES,
            "bollinger": BOLLINGER_FEATURES,
            "combined": COMBINED_FEATURES,
        },
        "rows": len(features),
        "columns": list(features.columns),
        "sample_start_utc": features.index.min().isoformat(),
        "sample_end_utc": features.index.max().isoformat(),
    }
    (PROCESSED / "feature_manifest.json").write_text(
        json.dumps(feature_manifest, indent=2), encoding="utf-8"
    )

    runtime = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": ".".join(map(str, sys.version_info[:3])),
        "packages": {
            name: package_version(name)
            for name in [
                "when-signals-stop-working",
                "numpy",
                "pandas",
                "scipy",
                "scikit-learn",
                "matplotlib",
                "ccxt",
                "pytest",
            ]
        },
    }
    environment_dir = ROOT / "environment"
    environment_dir.mkdir(exist_ok=True)
    (environment_dir / "runtime_versions.json").write_text(
        json.dumps(runtime, indent=2), encoding="utf-8"
    )

    checksum_targets: list[Path] = []
    for directory in [RAW, PROCESSED, OUTPUTS, ROOT / "configs", environment_dir]:
        if directory.exists():
            checksum_targets.extend(
                path for path in directory.rglob("*")
                if path.is_file() and path.name != "REPLICATION_CHECKSUMS.sha256"
            )

    checksum_lines = [
        f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}"
        for path in sorted(checksum_targets)
    ]
    (ROOT / "REPLICATION_CHECKSUMS.sha256").write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8"
    )

    replication_manifest = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_snapshot_id": config_data["data_snapshot_id"],
        "source": {
            "venue": "Binance spot",
            "pairs": ["SOL/USDT", "BTC/USDT"],
            "timeframe": "4h",
            "access": "public OHLCV through CCXT; no API key",
            "source_terms_notice": (
                "The repository MIT license covers ShockBridge-authored code and "
                "documentation, not third-party market data. Reuse remains subject "
                "to the source venue's applicable terms."
            ),
        },
        "snapshot": {
            "requested_start_utc": config_data["sample_start_utc"],
            "last_included_candle_utc": config_data["sample_last_candle_utc"],
            "download_end_exclusive_utc": config_data["download_end_exclusive_utc"],
            "sol_rows": len(sol),
            "btc_rows": len(btc),
            "aligned_rows": len(aligned),
            "model_rows": len(features),
        },
        "public_evidence": {
            "raw_data": [
                "data/raw/sol_usdt_4h.csv",
                "data/raw/btc_usdt_4h.csv",
                "data/raw/download_manifest.json",
                "data/raw/data_validation.json",
            ],
            "processed_data": [
                "data/processed/aligned_market_data.csv",
                "data/processed/model_features.csv",
                "data/processed/fold_boundaries.csv",
                "data/processed/fold_assignments.csv",
                "data/processed/feature_manifest.json",
            ],
            "model_outputs": [
                "outputs/research_report.md",
                "outputs/run_manifest.json",
                "outputs/final_verdicts.json",
                "outputs/stage_1_event_study.csv",
                "outputs/stage_2_fold_results.csv",
                "outputs/stage_2_oos_predictions.csv",
                "outputs/stage_3_regime_summary.csv",
                "outputs/figures/*.svg",
            ],
        },
        "verification": {
            "checksums": "REPLICATION_CHECKSUMS.sha256",
            "public_release_audit": "scripts/audit_public_release.py",
        },
    }
    (ROOT / "REPLICATION_MANIFEST.json").write_text(
        json.dumps(replication_manifest, indent=2), encoding="utf-8"
    )

    print("Replication assets generated.")
    print(f"Processed features: {len(features):,} rows")
    print(f"Checksums: {len(checksum_lines):,} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
