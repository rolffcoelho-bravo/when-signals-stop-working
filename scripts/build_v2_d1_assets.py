from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
import pandas as pd

from shockbridge_signal_validity.v2.causal_features import (
    BASELINE_FEATURES,
    STATE_INPUT_FEATURES,
    build_causal_base_features,
    build_registered_signal_features,
    feature_dictionary,
    prefix_invariance_error,
)
from shockbridge_signal_validity.v2.filtered_states import CausalFilteredStateEngine
from shockbridge_signal_validity.v2.manifests import dataframe_sha256, file_record, sha256_file, write_json
from shockbridge_signal_validity.v2.partitions import assert_development_only
from shockbridge_signal_validity.v2.registry import load_v2_registry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build development-only Version 2 D1 causal feature and filtered-state assets.")
    parser.add_argument("--aligned", type=Path, default=Path("data/processed/v2/development/aligned_development_market_data.csv"))
    parser.add_argument("--candidate-inventory", type=Path, default=Path("data/processed/v2/development/candidate_inventory.csv"))
    parser.add_argument("--fold-plan", type=Path, default=Path("data/processed/v2/development/nested_fold_plan.csv"))
    parser.add_argument("--registry", type=Path, default=Path("configs/v2_experiment_registry.json"))
    parser.add_argument("--protocol-lock", type=Path, default=Path("V2_PROTOCOL_LOCK.json"))
    parser.add_argument("--d0-lock", type=Path, default=Path("V2_D0_IMPLEMENTATION_LOCK.json"))
    parser.add_argument("--d1-lock", type=Path, default=Path("V2_D1_ENGINE_LOCK.json"))
    parser.add_argument("--processed-root", type=Path, default=Path("data/processed/v2/development"))
    parser.add_argument("--output-root", type=Path, default=Path("outputs/v2/development"))
    return parser.parse_args()


def git_commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()


def read_indexed_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    timestamp_column = "Timestamp" if "Timestamp" in frame.columns else frame.columns[0]
    frame[timestamp_column] = pd.to_datetime(frame[timestamp_column], utc=True, errors="raise")
    frame = frame.set_index(timestamp_column)
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise RuntimeError(f"Invalid chronological file: {path}")
    return frame


def json_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def signal_specifications(inventory: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "signal_family", "interpretation", "period", "lower_threshold",
        "upper_threshold", "standard_deviations",
    ]
    return inventory[columns].drop_duplicates().sort_values(columns, na_position="last").reset_index(drop=True)


def signal_spec_id(row: pd.Series) -> str:
    if row["signal_family"] == "rsi":
        return (
            f"rsi-p{int(row['period'])}-l{int(row['lower_threshold'])}"
            f"-u{int(row['upper_threshold'])}-{row['interpretation']}"
        )
    return (
        f"bollinger-p{int(row['period'])}-k{float(row['standard_deviations']):g}"
        f"-{row['interpretation']}"
    )


def main() -> int:
    args = parse_args()
    root = Path.cwd().resolve()
    registry = load_v2_registry(args.registry)
    protocol_lock = json.loads(args.protocol_lock.read_text(encoding="utf-8"))
    d0_lock = json.loads(args.d0_lock.read_text(encoding="utf-8"))
    d1_lock = json.loads(args.d1_lock.read_text(encoding="utf-8"))

    aligned = read_indexed_csv(args.aligned)
    assert_development_only(aligned, registry)
    if aligned.index.min() < registry.development_start or aligned.index.max() > registry.development_end:
        raise RuntimeError("D1 aligned data fall outside the frozen development partition.")

    holdout_root = Path("outputs/v2/holdout")
    holdout_files = [path for path in holdout_root.rglob("*") if path.is_file()] if holdout_root.exists() else []
    if holdout_files:
        raise RuntimeError("Unauthorized holdout outputs exist before D1 execution.")

    args.processed_root.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)

    causal = build_causal_base_features(aligned)
    causal_path = args.processed_root / "d1_causal_base_features.csv"
    causal.to_csv(causal_path, index_label="Timestamp")

    dictionary = feature_dictionary()
    dictionary_path = args.processed_root / "d1_feature_dictionary.csv"
    dictionary.to_csv(dictionary_path, index=False)

    inventory = pd.read_csv(args.candidate_inventory)
    specs = signal_specifications(inventory)
    cutoff = int(len(aligned) * 0.80)
    signal_audits: list[dict[str, Any]] = []
    close = pd.to_numeric(aligned["sol_Close"], errors="raise")
    for _, row in specs.iterrows():
        kwargs = {
            "signal_family": str(row["signal_family"]),
            "interpretation": str(row["interpretation"]),
            "period": int(row["period"]),
            "lower_threshold": None if pd.isna(row["lower_threshold"]) else float(row["lower_threshold"]),
            "upper_threshold": None if pd.isna(row["upper_threshold"]) else float(row["upper_threshold"]),
            "standard_deviations": None if pd.isna(row["standard_deviations"]) else float(row["standard_deviations"]),
        }
        builder = lambda series, values=kwargs: build_registered_signal_features(series, **values)
        features = builder(close)
        error = prefix_invariance_error(builder, close, cutoff)
        signal_audits.append(
            {
                "signal_spec_id": signal_spec_id(row),
                **kwargs,
                "feature_columns": int(features.shape[1]),
                "complete_rows": int(features.dropna().shape[0]),
                "prefix_invariance_max_abs_error": float(error),
                "prefix_invariant": bool(np.isfinite(error) and error <= 1e-12),
                "feature_frame_sha256": dataframe_sha256(features),
            }
        )
    audit_frame = pd.DataFrame.from_records(signal_audits)
    if not audit_frame["prefix_invariant"].all():
        raise RuntimeError("At least one registered signal specification failed prefix invariance.")
    audit_path = args.processed_root / "d1_registered_signal_feature_audit.csv"
    audit_frame.to_csv(audit_path, index=False)

    fold_plan = pd.read_csv(args.fold_plan)
    diagnostics: list[dict[str, Any]] = []
    parameter_records: list[dict[str, Any]] = []
    outer_probabilities: list[pd.DataFrame] = []
    for _, fold in fold_plan.iterrows():
        train_start = pd.Timestamp(fold["train_start_utc"])
        train_end = pd.Timestamp(fold["train_end_utc"])
        test_start = pd.Timestamp(fold["test_start_utc"])
        test_end = pd.Timestamp(fold["test_end_utc"])
        train = causal.loc[train_start:train_end, STATE_INPUT_FEATURES].dropna()
        test = causal.loc[test_start:test_end, STATE_INPUT_FEATURES].dropna()
        engine = CausalFilteredStateEngine().fit(train)
        probabilities = engine.filter_forward(test)
        prefix_length = max(1, len(test) // 2)
        prefix_probabilities = engine.filter_forward(test.iloc[:prefix_length])
        prefix_error = float(
            (
                probabilities.iloc[:prefix_length][["state_p_range", "state_p_trend", "state_p_stress"]]
                - prefix_probabilities[["state_p_range", "state_p_trend", "state_p_stress"]]
            ).abs().to_numpy().max()
        )
        sums = probabilities[["state_p_range", "state_p_trend", "state_p_stress"]].sum(axis=1)
        parameters = engine.parameter_record()
        fold_identity = {
            "level": str(fold["level"]),
            "horizon_candles": int(fold["horizon_candles"]),
            "outer_fold": int(fold["outer_fold"]),
            "inner_fold": None if pd.isna(fold["inner_fold"]) else int(fold["inner_fold"]),
        }
        parameter_record = {**fold_identity, "parameters": parameters}
        parameter_record["parameter_sha256"] = json_hash(parameter_record)
        parameter_records.append(parameter_record)
        diagnostics.append(
            {
                **fold_identity,
                "train_rows_complete": int(len(train)),
                "test_rows_complete": int(len(test)),
                "train_end_utc": train.index.max().isoformat(),
                "test_start_utc": test.index.min().isoformat(),
                "probability_sum_max_abs_error": float((sums - 1.0).abs().max()),
                "minimum_probability": float(probabilities[["state_p_range", "state_p_trend", "state_p_stress"]].min().min()),
                "prefix_invariance_max_abs_error": prefix_error,
                "range_share": float((probabilities["state_label"] == "range").mean()),
                "trend_share": float((probabilities["state_label"] == "trend").mean()),
                "stress_share": float((probabilities["state_label"] == "stress").mean()),
                "minimum_covariance_eigenvalue": float(min(min(values) for values in parameters["covariance_eigenvalues"])),
                "transition_row_sum_max_abs_error": float(np.abs(np.asarray(parameters["transition_matrix"]).sum(axis=1) - 1.0).max()),
                "parameter_sha256": parameter_record["parameter_sha256"],
            }
        )
        if fold_identity["level"] == "outer":
            output = probabilities.reset_index(names="Timestamp")
            output.insert(0, "outer_fold", fold_identity["outer_fold"])
            output.insert(0, "horizon_candles", fold_identity["horizon_candles"])
            outer_probabilities.append(output)

    diagnostics_frame = pd.DataFrame.from_records(diagnostics)
    if len(diagnostics_frame) != len(fold_plan):
        raise RuntimeError("D1 state diagnostics do not cover the complete nested fold plan.")
    if (diagnostics_frame["probability_sum_max_abs_error"] > 1e-10).any():
        raise RuntimeError("Filtered state probabilities failed normalization.")
    if (diagnostics_frame["prefix_invariance_max_abs_error"] > 1e-12).any():
        raise RuntimeError("Filtered state engine failed prefix invariance.")
    diagnostics_path = args.processed_root / "d1_fold_state_diagnostics.csv"
    diagnostics_frame.to_csv(diagnostics_path, index=False)

    parameters_path = args.processed_root / "d1_fold_state_parameters.json"
    write_json(parameters_path, {"records": parameter_records})

    outer_frame = pd.concat(outer_probabilities, ignore_index=True)
    outer_path = args.processed_root / "d1_outer_filtered_state_probabilities.csv"
    outer_frame.to_csv(outer_path, index=False)

    implementation_commit = git_commit()
    manifest = {
        "checkpoint": "V2_D1_CAUSAL_FEATURE_AND_FILTERED_STATE_ENGINE",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution_scope": "DEVELOPMENT_ONLY_NO_PREDICTIVE_MODEL_FITTING",
        "implementation_commit": implementation_commit,
        "protocol_lock_id": protocol_lock["lock_id"],
        "d0_lock_id": d0_lock["lock_id"],
        "d1_lock_id": d1_lock["lock_id"],
        "registry_sha256": registry.sha256,
        "development_rows": int(len(aligned)),
        "causal_feature_columns": list(BASELINE_FEATURES),
        "registered_signal_specifications_audited": int(len(audit_frame)),
        "nested_state_fits": int(len(diagnostics_frame)),
        "outer_probability_rows": int(len(outer_frame)),
        "predictive_model_fitting_performed": False,
        "state_filter_fitting_performed": True,
        "holdout_performance_accessed": False,
        "files": [
            file_record(path, root)
            for path in [
                causal_path,
                dictionary_path,
                audit_path,
                diagnostics_path,
                parameters_path,
                outer_path,
            ]
        ],
    }
    manifest_path = args.processed_root / "d1_engine_manifest.json"
    write_json(manifest_path, manifest)

    status = {
        "status": "PASS",
        "checkpoint": "V2_D1_CAUSAL_FEATURE_AND_FILTERED_STATE_ENGINE",
        "protocol_lock_id": protocol_lock["lock_id"],
        "d0_lock_id": d0_lock["lock_id"],
        "d1_lock_id": d1_lock["lock_id"],
        "implementation_commit": implementation_commit,
        "development_rows": int(len(aligned)),
        "registered_signal_specifications_audited": int(len(audit_frame)),
        "nested_state_fits": int(len(diagnostics_frame)),
        "outer_probability_rows": int(len(outer_frame)),
        "predictive_model_fitting_performed": False,
        "state_filter_fitting_performed": True,
        "holdout_performance_accessed": False,
        "manifest_sha256": sha256_file(manifest_path),
    }
    write_json(args.output_root / "d1_engine_status.json", status)

    print("Version 2 D1 causal feature and filtered-state assets generated.")
    print(f"Development rows: {len(aligned):,}")
    print(f"Registered signal specifications audited: {len(audit_frame):,}")
    print(f"Nested state fits: {len(diagnostics_frame):,}")
    print(f"Outer filtered-probability rows: {len(outer_frame):,}")
    print("Predictive model fitting performed: False")
    print("State-filter fitting performed: True")
    print("Holdout performance accessed: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
