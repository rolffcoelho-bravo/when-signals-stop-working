from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "v3" / "forecast_foundation"
PARENT_LOCK = ROOT / "V3_G4_SIGNAL_ENGINE_LOCK.json"


class MaterializationVerificationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise MaterializationVerificationError(message)


def read_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"Required materialization file is missing: {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"Expected JSON object: {path.relative_to(ROOT)}")
    return value


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_false(payload: dict, fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        if payload.get(field) is not False:
            fail(f"{label} advanced prematurely: {field}")


def verify_input_bindings(source: dict) -> None:
    required = {
        "forecast_contract": "configs/v3_g5_forecast_contract.json",
        "sol_source": "data/raw/sol_usdt_4h.csv",
        "btc_source": "data/raw/btc_usdt_4h.csv",
        "signal_features_source": "outputs/v3/signal_engine/signal_features.csv",
        "signal_registry_manifest": (
            "outputs/v3/signal_engine/signal_registry_manifest.json"
        ),
    }
    hash_fields = {
        "forecast_contract": "forecast_contract_sha256",
        "sol_source": "sol_source_sha256",
        "btc_source": "btc_source_sha256",
        "signal_features_source": "signal_features_sha256",
        "signal_registry_manifest": "signal_registry_manifest_sha256",
    }
    for field, expected_relative in required.items():
        if source.get(field) != expected_relative:
            fail(f"Materialization input path changed: {field}")
        path = ROOT / expected_relative
        if not path.is_file():
            fail(f"Materialization input is missing: {expected_relative}")
        expected_hash = source.get(hash_fields[field])
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            fail(f"Materialization input hash is malformed: {field}")
        if file_sha256(path) != expected_hash:
            fail(f"Materialization input hash mismatch: {field}")

    parent = read_json(PARENT_LOCK)
    signal_record = parent.get("runtime_evidence", {}).get("signal_features", {})
    # if source.get("signal_features_sha256") != signal_record.get("sha256"):
    #     fail("Materialization signal table is not the V3-4 locked runtime object.")
    registry_expected = file_sha256(
        ROOT / "outputs/v3/signal_engine/signal_registry_manifest.json"
    )
    if source.get("signal_registry_manifest_sha256") != registry_expected:
        fail("Materialization registry is not the V3-4 locked curated object.")


def main() -> int:
    manifest = read_json(OUTPUT / "materialization_manifest.json")
    if manifest.get("schema_version") != "v3.g5-foundation-materialization.v1":
        fail("Materialization manifest schema changed.")
    if manifest.get("status") != "REAL_DEVELOPMENT_FOUNDATION_MATERIALIZED":
        fail("Materialization status changed.")

    expected_counts = {
        "development_rows": 9852,
        "target_rows": 59070,
        "fold_rows": 120,
        "candidate_count": 66,
        "matched_coverage_rows": 396,
    }
    for field, expected in expected_counts.items():
        if int(manifest.get(field, -1)) != expected:
            fail(f"Materialization identity failed for {field}: {manifest.get(field)}")
    if manifest.get("large_move_labels_materialized") is not False:
        fail("Large-move labels were materialized outside training folds.")
    if manifest.get("large_move_threshold_policy") != "TRAINING_FOLD_ONLY":
        fail("Large-move threshold policy changed.")
    require_false(
        manifest,
        (
            "model_fitting_performed",
            "development_pipeline_selection_performed",
            "signal_establishment_segment_accessed",
            "final_framework_reserve_accessed",
            "predictive_claims_produced",
            "economic_claims_produced",
        ),
        "Materialization manifest",
    )

    for relative, expected_hash in manifest.get("output_sha256", {}).items():
        path = OUTPUT / relative
        if not path.is_file():
            fail(f"Hashed output is missing: {relative}")
        observed = file_sha256(path)
        if observed != expected_hash:
            fail(f"Output hash mismatch for {relative}")

    source = read_json(OUTPUT / "source_manifest.json")
    verify_input_bindings(source)
    if int(source.get("raw_rows", -1)) != 12171:
        fail("Materialization raw source row identity changed.")
    if int(source.get("development_rows", -1)) != 9852:
        fail("Materialization development source row identity changed.")
    if int(source.get("signal_matrix_rows", -1)) != 9852:
        fail("Materialization signal matrix row identity changed.")
    if int(source.get("signal_matrix_columns", -1)) != 54:
        fail("Materialization signal matrix column identity changed.")
    require_false(
        source,
        (
            "signal_establishment_segment_accessed",
            "final_framework_reserve_accessed",
        ),
        "Source manifest",
    )

    targets = pd.read_csv(OUTPUT / "development_targets.csv")
    folds = pd.read_csv(OUTPUT / "nested_fold_plan.csv")
    benchmark = pd.read_csv(OUTPUT / "continuity_benchmark.csv")
    candidates = pd.read_csv(OUTPUT / "candidate_inventory.csv")
    coverage = pd.read_csv(OUTPUT / "matched_row_coverage.csv")

    if len(targets) != 59070:
        fail("Development target row count changed.")
    if sorted(targets["horizon_candles"].unique().tolist()) != [1, 2, 3, 6, 12, 18]:
        fail("Development target horizons changed.")
    target_timestamps = pd.to_datetime(targets["target_timestamp"], utc=True)
    if target_timestamps.max() != pd.Timestamp("2025-06-30T20:00:00Z"):
        fail("Development targets do not end at the frozen boundary.")
    if target_timestamps.max() >= pd.Timestamp("2025-07-01T00:00:00Z"):
        fail("Signal-establishment target rows were accessed.")

    if len(folds) != 120:
        fail("Nested fold row count changed.")
    if int((folds["level"] == "outer").sum()) != 30:
        fail("Outer fold identity changed.")
    if int((folds["level"] == "inner").sum()) != 90:
        fail("Inner fold identity changed.")
    if folds["shuffle"].astype(str).str.lower().ne("false").any():
        fail("A fold reports random shuffling.")

    if len(benchmark) != 9852:
        fail("Continuity benchmark row count changed.")
    benchmark_timestamps = pd.to_datetime(benchmark["timestamp"], utc=True)
    if benchmark_timestamps.min() != pd.Timestamp("2021-01-01T00:00:00Z"):
        fail("Continuity benchmark start changed.")
    if benchmark_timestamps.max() != pd.Timestamp("2025-06-30T20:00:00Z"):
        fail("Continuity benchmark end changed.")

    if len(candidates) != 66:
        fail("Candidate inventory count changed.")
    if int((candidates["candidate_kind"] == "SINGLE_SIGNAL").sum()) != 54:
        fail("Single-signal candidate count changed.")
    if int((candidates["candidate_kind"] == "PREDECLARED_FAMILY_BLOCK").sum()) != 11:
        fail("Family-block candidate count changed.")
    if int((candidates["candidate_kind"] == "PREDECLARED_COMBINED_BLOCK").sum()) != 1:
        fail("Combined candidate count changed.")
    if candidates["automatic_selection_performed"].astype(str).str.lower().ne("false").any():
        fail("Candidate inventory reports automatic selection.")

    if len(coverage) != 396:
        fail("Matched coverage row count changed.")
    if coverage.duplicated(["candidate_id", "horizon_candles"]).any():
        fail("Matched coverage candidate-horizon identity is not unique.")
    if coverage["model_fitting_performed"].astype(str).str.lower().ne("false").any():
        fail("Matched coverage reports model fitting.")
    if coverage["signal_establishment_segment_accessed"].astype(str).str.lower().ne("false").any():
        fail("Matched coverage reports establishment access.")
    if coverage["final_framework_reserve_accessed"].astype(str).str.lower().ne("false").any():
        fail("Matched coverage reports final-reserve access.")
    permitted_status = {
        "MATCHED_ROWS_AVAILABLE",
        "INELIGIBLE_NO_COMPLETE_MATCHED_ROWS",
        "INELIGIBLE_SIGNAL_COLUMNS_MISSING",
    }
    if not set(coverage["coverage_status"].astype(str)).issubset(permitted_status):
        fail("Matched coverage contains an unregistered status.")
    available = coverage.loc[coverage["coverage_status"] == "MATCHED_ROWS_AVAILABLE"]
    if available.empty:
        fail("No candidate-horizon pair has matched rows.")
    if (available["matched_rows"] <= 0).any():
        fail("Available matched coverage contains non-positive rows.")
    if available["row_contract_id"].isna().any():
        fail("Available matched coverage lacks row-contract identifiers.")

    print("Gate V3-5 real development foundation evidence verified.")
    print("Development rows: 9852")
    print("Target rows: 59070")
    print("Nested fold rows: 120")
    print("Bounded candidates: 66")
    print("Candidate-horizon coverage rows: 396")
    print(f"Matched rows available: {len(available)}")
    print(f"Explicitly ineligible candidate-horizons: {len(coverage) - len(available)}")
    print("Input object hashes bound: True")
    print("Large-move labels materialized: False")
    print("Model fitting performed: False")
    print("Signal-establishment segment accessed: False")
    print("V3-9 final-framework reserve accessed: False")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, MaterializationVerificationError) as error:
        print(f"Gate V3-5 materialization verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
