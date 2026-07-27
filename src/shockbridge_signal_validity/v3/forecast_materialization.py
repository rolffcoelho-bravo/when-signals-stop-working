from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .forecast_benchmark import benchmark_manifest, build_continuity_benchmark
from .forecast_contract import ForecastContract, ForecastProtocolViolation
from .forecast_inventory import (
    build_candidate_inventory,
    candidate_inventory_manifest,
    load_signal_registry_manifest,
)
from .forecast_matching import build_matched_pair, matched_pair_manifest
from .forecast_splits import build_nested_fold_plan
from .forecast_targets import build_development_targets, target_manifest


@dataclass(frozen=True)
class MaterializedFoundation:
    targets: pd.DataFrame
    folds: pd.DataFrame
    benchmark: pd.DataFrame
    candidates: pd.DataFrame
    matched_coverage: pd.DataFrame
    manifests: dict[str, dict[str, Any]]


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(frame: pd.DataFrame, *, index: bool = False) -> bytes:
    return frame.to_csv(index=index, lineterminator="\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def read_raw_ohlcv(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    if not source.is_file():
        raise ForecastProtocolViolation(f"Raw OHLCV source is missing: {source}")
    frame = pd.read_csv(source)
    required = {"Date", "Open", "High", "Low", "Close", "Volume"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ForecastProtocolViolation(
            "Raw OHLCV source is missing columns: " + ", ".join(missing)
        )
    frame = frame[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
    frame["timestamp"] = pd.to_datetime(frame.pop("Date"), utc=True, errors="raise")
    frame = frame.set_index("timestamp")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ForecastProtocolViolation("Raw OHLCV timestamps must be unique and chronological.")
    frame.columns = [str(column).lower() for column in frame.columns]
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ForecastProtocolViolation("Raw OHLCV values must be finite and complete.")
    if (numeric[["open", "high", "low", "close"]] <= 0.0).any().any():
        raise ForecastProtocolViolation("Raw OHLCV prices must be strictly positive.")
    if (numeric["volume"] < 0.0).any():
        raise ForecastProtocolViolation("Raw OHLCV volume cannot be negative.")
    if (numeric["low"] > numeric[["open", "close", "high"]].min(axis=1)).any():
        raise ForecastProtocolViolation("Raw OHLCV low exceeds an observed price.")
    if (numeric["high"] < numeric[["open", "close", "low"]].max(axis=1)).any():
        raise ForecastProtocolViolation("Raw OHLCV high is below an observed price.")
    return numeric


def load_signal_feature_matrix(
    path: str | Path,
    contract: ForecastContract,
    *,
    asset: str = "SOL/USDT",
    venue: str = "binance_spot",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    source = Path(path)
    if not source.is_file():
        raise ForecastProtocolViolation(
            "Gate V3-4 signal feature evidence is missing: " + str(source)
        )
    required = [
        "timestamp",
        "asset",
        "venue",
        "signal_id",
        "feature_value",
        "eligibility_status",
    ]
    long = pd.read_csv(source, usecols=required)
    long["timestamp"] = pd.to_datetime(long["timestamp"], utc=True, errors="raise")
    long = long.loc[
        (long["asset"].astype(str) == asset)
        & (long["venue"].astype(str) == venue)
        & (long["timestamp"] >= contract.development_start)
        & (long["timestamp"] <= contract.development_end)
    ].copy()
    if long.empty:
        raise ForecastProtocolViolation("No development signal rows matched asset and venue.")
    if long.duplicated(["timestamp", "signal_id"]).any():
        raise ForecastProtocolViolation("Signal evidence has duplicate timestamp-signal rows.")
    contract.assert_development_only(pd.DatetimeIndex(sorted(long["timestamp"].unique())))
    long["feature_value"] = pd.to_numeric(long["feature_value"], errors="coerce")
    matrix = long.pivot(index="timestamp", columns="signal_id", values="feature_value")
    matrix = matrix.sort_index(kind="mergesort").sort_index(axis=1)
    eligibility = (
        long.groupby(["signal_id", "eligibility_status"], sort=True)
        .size()
        .rename("rows")
        .reset_index()
    )
    return matrix, eligibility


def _target_series(targets: pd.DataFrame, horizon: int) -> pd.Series:
    subset = targets.loc[targets["horizon_candles"] == int(horizon), ["timestamp", "direction"]].copy()
    subset["timestamp"] = pd.to_datetime(subset["timestamp"], utc=True, errors="raise")
    return subset.set_index("timestamp")["direction"].astype(float).sort_index()


def build_matched_coverage(
    *,
    benchmark: pd.DataFrame,
    signal_matrix: pd.DataFrame,
    targets: pd.DataFrame,
    candidates: pd.DataFrame,
    contract: ForecastContract,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for horizon in contract.horizons:
        target = _target_series(targets, horizon)
        possible_rows = int(len(target))
        for candidate in candidates.itertuples(index=False):
            member_ids = [str(value) for value in json.loads(candidate.member_signal_ids)]
            missing_members = sorted(set(member_ids).difference(signal_matrix.columns))
            base_record: dict[str, object] = {
                "candidate_id": str(candidate.candidate_id),
                "candidate_kind": str(candidate.candidate_kind),
                "signal_family": str(candidate.signal_family),
                "candidate_block": str(candidate.candidate_block),
                "member_count": int(candidate.member_count),
                "horizon_candles": int(horizon),
                "horizon_hours": int(horizon * 4),
                "possible_target_rows": possible_rows,
                "model_fitting_performed": False,
                "signal_establishment_segment_accessed": False,
                "final_framework_reserve_accessed": False,
            }
            if missing_members:
                records.append(
                    {
                        **base_record,
                        "matched_rows": 0,
                        "coverage_ratio": 0.0,
                        "row_contract_id": None,
                        "start_utc": None,
                        "end_utc": None,
                        "coverage_status": "INELIGIBLE_SIGNAL_COLUMNS_MISSING",
                        "coverage_reason": "|".join(missing_members),
                    }
                )
                continue
            candidate_features = signal_matrix[member_ids]
            try:
                pair = build_matched_pair(
                    benchmark_features=benchmark,
                    candidate_features=candidate_features,
                    target=target,
                    candidate_id=str(candidate.candidate_id),
                    horizon_candles=int(horizon),
                    contract=contract,
                )
            except ForecastProtocolViolation as error:
                if "contains no complete rows" not in str(error):
                    raise
                records.append(
                    {
                        **base_record,
                        "matched_rows": 0,
                        "coverage_ratio": 0.0,
                        "row_contract_id": None,
                        "start_utc": None,
                        "end_utc": None,
                        "coverage_status": "INELIGIBLE_NO_COMPLETE_MATCHED_ROWS",
                        "coverage_reason": str(error),
                    }
                )
                continue
            manifest = matched_pair_manifest(pair)
            records.append(
                {
                    **base_record,
                    "matched_rows": int(manifest["matched_rows"]),
                    "coverage_ratio": float(manifest["matched_rows"]) / float(possible_rows),
                    "row_contract_id": str(manifest["row_contract_id"]),
                    "start_utc": str(manifest["start_utc"]),
                    "end_utc": str(manifest["end_utc"]),
                    "coverage_status": "MATCHED_ROWS_AVAILABLE",
                    "coverage_reason": None,
                }
            )
    coverage = pd.DataFrame.from_records(records)
    expected = len(candidates) * len(contract.horizons)
    if len(coverage) != expected:
        raise ForecastProtocolViolation(
            f"Matched coverage identity failed: expected {expected}, observed {len(coverage)}."
        )
    if coverage.duplicated(["candidate_id", "horizon_candles"]).any():
        raise ForecastProtocolViolation("Matched coverage contains duplicate candidate-horizon rows.")
    if coverage["model_fitting_performed"].any():
        raise ForecastProtocolViolation("Materialization performed model fitting.")
    return coverage.sort_values(
        ["horizon_candles", "candidate_kind", "signal_family", "candidate_id"],
        kind="mergesort",
    ).reset_index(drop=True)


def materialize_real_development_foundation(
    *,
    contract_path: str | Path,
    sol_path: str | Path,
    btc_path: str | Path,
    signal_features_path: str | Path,
    signal_registry_manifest_path: str | Path,
) -> MaterializedFoundation:
    contract = ForecastContract.from_path(contract_path)
    sol = read_raw_ohlcv(sol_path)
    btc = read_raw_ohlcv(btc_path)
    aligned = sol.index.intersection(btc.index).sort_values()
    if not aligned.equals(sol.index) or not aligned.equals(btc.index):
        raise ForecastProtocolViolation("SOL and BTC raw histories must align exactly.")

    targets = build_development_targets(sol["close"], contract)
    folds = build_nested_fold_plan(targets, contract)
    benchmark = build_continuity_benchmark(sol, btc["close"], contract)
    registry = load_signal_registry_manifest(signal_registry_manifest_path)
    candidates = build_candidate_inventory(registry)
    signal_matrix, eligibility = load_signal_feature_matrix(signal_features_path, contract)
    if not signal_matrix.index.equals(benchmark.index):
        raise ForecastProtocolViolation("Signal and benchmark development timestamps differ.")
    coverage = build_matched_coverage(
        benchmark=benchmark,
        signal_matrix=signal_matrix,
        targets=targets,
        candidates=candidates,
        contract=contract,
    )

    target_info = target_manifest(targets, contract)
    fold_info = {
        "schema_version": "v3.g5-fold-manifest.v1",
        "rows": int(len(folds)),
        "outer_rows": int((folds["level"] == "outer").sum()),
        "inner_rows": int((folds["level"] == "inner").sum()),
        "horizons_candles": list(contract.horizons),
        "shuffle": False,
        "purge_gap": "equal_to_horizon_candles",
        "signal_establishment_segment_accessed": False,
        "final_framework_reserve_accessed": False,
    }
    benchmark_info = benchmark_manifest(benchmark, contract)
    candidate_info = candidate_inventory_manifest(candidates)
    coverage_info = {
        "schema_version": "v3.g5-matched-coverage-manifest.v1",
        "rows": int(len(coverage)),
        "candidate_count": int(len(candidates)),
        "horizon_count": int(len(contract.horizons)),
        "candidate_horizon_identity_verified": int(len(coverage))
        == int(len(candidates) * len(contract.horizons)),
        "matched_rows_available": int(
            (coverage["coverage_status"] == "MATCHED_ROWS_AVAILABLE").sum()
        ),
        "ineligible_rows": int(
            (coverage["coverage_status"] != "MATCHED_ROWS_AVAILABLE").sum()
        ),
        "model_fitting_performed": False,
        "signal_establishment_segment_accessed": False,
        "final_framework_reserve_accessed": False,
    }
    source_info = {
        "schema_version": "v3.g5-materialization-source-manifest.v1",
        "sol_source": str(Path(sol_path).as_posix()),
        "btc_source": str(Path(btc_path).as_posix()),
        "raw_rows": int(len(sol)),
        "development_rows": int(len(benchmark)),
        "development_start_utc": benchmark.index.min().isoformat(),
        "development_end_utc": benchmark.index.max().isoformat(),
        "signal_matrix_rows": int(len(signal_matrix)),
        "signal_matrix_columns": int(len(signal_matrix.columns)),
        "eligibility_record_rows": int(len(eligibility)),
        "signal_establishment_segment_accessed": False,
        "final_framework_reserve_accessed": False,
    }
    return MaterializedFoundation(
        targets=targets,
        folds=folds,
        benchmark=benchmark,
        candidates=candidates,
        matched_coverage=coverage,
        manifests={
            "target_manifest": target_info,
            "fold_manifest": fold_info,
            "benchmark_manifest": benchmark_info,
            "candidate_inventory_manifest": candidate_info,
            "matched_coverage_manifest": coverage_info,
            "source_manifest": source_info,
        },
    )


def write_materialized_foundation(
    foundation: MaterializedFoundation,
    output_dir: str | Path,
) -> dict[str, Any]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    payloads: dict[str, bytes] = {
        "development_targets.csv": _csv_bytes(foundation.targets),
        "nested_fold_plan.csv": _csv_bytes(foundation.folds),
        "continuity_benchmark.csv": _csv_bytes(
            foundation.benchmark.reset_index(names="timestamp")
        ),
        "candidate_inventory.csv": _csv_bytes(foundation.candidates),
        "matched_row_coverage.csv": _csv_bytes(foundation.matched_coverage),
    }
    for key, manifest in foundation.manifests.items():
        payloads[f"{key}.json"] = _json_bytes(manifest)
    hashes: dict[str, str] = {}
    for relative, value in payloads.items():
        path = destination / relative
        path.write_bytes(value)
        hashes[relative] = _sha256_bytes(value)
    materialization_manifest: dict[str, Any] = {
        "schema_version": "v3.g5-foundation-materialization.v1",
        "status": "REAL_DEVELOPMENT_FOUNDATION_MATERIALIZED",
        "output_sha256": hashes,
        "development_rows": int(len(foundation.benchmark)),
        "target_rows": int(len(foundation.targets)),
        "fold_rows": int(len(foundation.folds)),
        "candidate_count": int(len(foundation.candidates)),
        "matched_coverage_rows": int(len(foundation.matched_coverage)),
        "large_move_labels_materialized": False,
        "large_move_threshold_policy": "TRAINING_FOLD_ONLY",
        "model_fitting_performed": False,
        "development_pipeline_selection_performed": False,
        "signal_establishment_segment_accessed": False,
        "final_framework_reserve_accessed": False,
        "predictive_claims_produced": False,
        "economic_claims_produced": False,
    }
    (destination / "materialization_manifest.json").write_bytes(
        _json_bytes(materialization_manifest)
    )
    return materialization_manifest
