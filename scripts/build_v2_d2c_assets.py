from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any

import pandas as pd

from shockbridge_signal_validity.v2.development_admission import (
    build_family_horizon_admission,
    pipeline_hash,
    select_family_decisions,
    select_final_calibration,
    select_final_policy,
    select_final_signal_specification,
    select_final_structural_pipeline,
    specification_payload,
)
from shockbridge_signal_validity.v2.manifests import file_record, sha256_file, write_json
from shockbridge_signal_validity.v2.predictive_screening import unique_signal_specifications

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "v2" / "development"
OUTPUT = ROOT / "outputs" / "v2" / "development"


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def git_tag_commit(tag: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"{tag}^{{commit}}"], cwd=ROOT, text=True).strip()


def read_lock(path: Path) -> str:
    return str(json.loads(path.read_text(encoding="utf-8"))["lock_id"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Version 2 D2C development-admission assets.")
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "v2_d2c_admission.json")
    parser.add_argument("--candidate-inventory", type=Path, default=PROCESSED / "candidate_inventory.csv")
    parser.add_argument("--d2a-inner", type=Path, default=PROCESSED / "d2a_inner_screen_results.csv")
    parser.add_argument("--d2b-structural", type=Path, default=PROCESSED / "d2b_inner_structural_results.csv")
    parser.add_argument("--d2b-calibration", type=Path, default=PROCESSED / "d2b_inner_calibration_results.csv")
    parser.add_argument("--d2b-policy", type=Path, default=PROCESSED / "d2b_inner_policy_results.csv")
    parser.add_argument("--d2b-outer", type=Path, default=PROCESSED / "d2b_outer_fold_results.csv")
    parser.add_argument("--processed-root", type=Path, default=PROCESSED)
    parser.add_argument("--output-root", type=Path, default=OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    locks = {
        "protocol": read_lock(ROOT / "V2_PROTOCOL_LOCK.json"),
        "d0": read_lock(ROOT / "V2_D0_IMPLEMENTATION_LOCK.json"),
        "d1": read_lock(ROOT / "V2_D1_ENGINE_LOCK.json"),
        "d2a": read_lock(ROOT / "V2_D2A_SELECTION_LOCK.json"),
        "d2b": read_lock(ROOT / "V2_D2B_SELECTION_LOCK.json"),
        "d2c": read_lock(ROOT / "V2_D2C_ADMISSION_LOCK.json"),
    }

    candidate_inventory = pd.read_csv(args.candidate_inventory)
    specification_map = {
        specification.signal_spec_id: specification
        for specification in unique_signal_specifications(candidate_inventory)
    }
    d2a_inner = pd.read_csv(args.d2a_inner)
    d2b_structural = pd.read_csv(args.d2b_structural)
    d2b_calibration = pd.read_csv(args.d2b_calibration)
    d2b_policy = pd.read_csv(args.d2b_policy)
    d2b_outer = pd.read_csv(args.d2b_outer)

    admission = build_family_horizon_admission(d2b_outer, config)
    decisions = select_family_decisions(admission)
    requirements = config["final_component_selection"]
    gates = config["admission_gates"]
    required_rows = int(requirements["required_pooled_inner_rows"])

    pipeline_records: list[dict[str, Any]] = []
    component_records: list[dict[str, Any]] = []

    for decision in decisions.itertuples(index=False):
        if not bool(decision.pipeline_admitted):
            continue
        family = str(decision.signal_family)
        horizon = int(decision.selected_horizon_candles)
        signal = select_final_signal_specification(
            d2a_inner,
            family,
            horizon,
            required_rows,
            float(gates["brier_tolerance"]),
        )
        structural = select_final_structural_pipeline(
            d2b_structural,
            family,
            horizon,
            required_rows,
            float(gates["brier_tolerance"]),
            float(gates["ece_tolerance"]),
        )
        calibration = select_final_calibration(d2b_calibration, family, horizon, required_rows)
        policy = select_final_policy(
            d2b_policy,
            family,
            horizon,
            required_rows,
            float(gates["minimum_mean_policy_coverage"]),
            int(gates["minimum_total_policy_decisions"]),
        )
        signal_id = str(signal["signal_spec_id"])
        if signal_id not in specification_map:
            raise RuntimeError(f"D2C selected unknown signal specification: {signal_id}")
        specification = specification_payload(specification_map[signal_id])
        pipeline = {
            "signal_family": family,
            "horizon_candles": horizon,
            "horizon_hours": horizon * 4,
            "target": "future_return_direction",
            "signal_specification": specification,
            "structural_pipeline": {
                "pipeline_id": str(structural["pipeline_id"]),
                "model_family": str(structural["model_family"]),
                "window_scheme": str(structural["window_scheme"]),
                "regime_conditioned": bool(structural["regime_conditioned"]),
                "parameters": json.loads(str(structural["parameters_json"])),
            },
            "calibration_method": str(calibration["calibration_method"]),
            "decision_probability_distance_threshold": float(policy["threshold"]),
            "development_selection_evidence": {
                "family_horizon_mean_incremental_log_loss": float(decision.selected_mean_incremental_log_loss),
                "family_horizon_positive_outer_folds": int(decision.selected_positive_outer_folds),
                "signal_mean_inner_incremental_log_loss": float(signal["mean_incremental_log_loss"]),
                "structural_mean_inner_incremental_log_loss": float(structural["mean_incremental_log_loss"]),
                "calibration_mean_inner_incremental_log_loss": float(calibration["mean_incremental_log_loss"]),
                "policy_mean_inner_net_edge_diagnostic": float(policy["mean_net_edge"]),
                "policy_mean_inner_coverage": float(policy["mean_coverage"]),
                "policy_total_inner_decisions": int(policy["total_nonzero_decisions"]),
            },
            "economic_gate_evaluated": False,
            "holdout_performance_accessed": False,
        }
        pipeline["pipeline_hash"] = pipeline_hash(pipeline)
        pipeline_records.append(pipeline)
        component_records.extend(
            [
                {
                    "signal_family": family,
                    "horizon_candles": horizon,
                    "component": "SIGNAL_SPECIFICATION",
                    "selected_id": signal_id,
                    "mean_selection_metric": float(signal["mean_incremental_log_loss"]),
                    "positive_evaluations": int(signal["positive_evaluations"]),
                    "evaluation_rows": int(signal["evaluation_rows"]),
                },
                {
                    "signal_family": family,
                    "horizon_candles": horizon,
                    "component": "STRUCTURAL_PIPELINE",
                    "selected_id": str(structural["pipeline_id"]),
                    "mean_selection_metric": float(structural["mean_incremental_log_loss"]),
                    "positive_evaluations": int(structural["positive_evaluations"]),
                    "evaluation_rows": int(structural["evaluation_rows"]),
                },
                {
                    "signal_family": family,
                    "horizon_candles": horizon,
                    "component": "CALIBRATION",
                    "selected_id": str(calibration["calibration_method"]),
                    "mean_selection_metric": float(calibration["mean_incremental_log_loss"]),
                    "positive_evaluations": int(calibration["positive_evaluations"]),
                    "evaluation_rows": int(calibration["evaluation_rows"]),
                },
                {
                    "signal_family": family,
                    "horizon_candles": horizon,
                    "component": "DECISION_POLICY",
                    "selected_id": f"threshold_{float(policy['threshold']):g}",
                    "mean_selection_metric": float(policy["mean_net_edge"]),
                    "positive_evaluations": int(policy["positive_evaluations"]),
                    "evaluation_rows": int(policy["evaluation_rows"]),
                },
            ]
        )

    args.processed_root.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)
    admission_path = args.processed_root / "d2c_family_horizon_admission.csv"
    decisions_path = args.processed_root / "d2c_family_decisions.csv"
    components_path = args.processed_root / "d2c_component_selection_audit.csv"
    registry_path = args.processed_root / "d2c_frozen_pipeline_registry.json"
    admission.to_csv(admission_path, index=False)
    decisions.to_csv(decisions_path, index=False)
    pd.DataFrame.from_records(
        component_records,
        columns=[
            "signal_family",
            "horizon_candles",
            "component",
            "selected_id",
            "mean_selection_metric",
            "positive_evaluations",
            "evaluation_rows",
        ],
    ).to_csv(components_path, index=False)

    source_tag = "v2-d2b-selection-20260722"
    registry = {
        "checkpoint": "V2_D2C_DEVELOPMENT_ADMISSION_AND_PIPELINE_FREEZE",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "implementation_commit": git_commit(),
        "source_d2b_tag": source_tag,
        "source_d2b_commit": git_tag_commit(source_tag),
        "locks": locks,
        "family_decisions": json.loads(decisions.to_json(orient="records")),
        "frozen_pipelines": pipeline_records,
        "frozen_pipeline_count": len(pipeline_records),
        "family_level_pipeline_freeze_completed": True,
        "economic_gate_evaluated": False,
        "holdout_authorization_enabled": False,
        "holdout_performance_accessed": False,
    }
    write_json(registry_path, registry)

    authorization_path = args.output_root / "d2c_holdout_authorization.json"
    authorization = {
        "authorized": False,
        "checkpoint": "D2C",
        "reason": "D2C freezes family-level decisions but does not authorize methodology-locked evaluation access.",
        "required_next_checkpoint": "D3_METHODOLOGY_LOCKED_EVALUATION_AUTHORIZATION",
        "frozen_pipeline_count": len(pipeline_records),
        "holdout_performance_accessed": False,
    }
    write_json(authorization_path, authorization)

    generated = [admission_path, decisions_path, components_path, registry_path, authorization_path]
    manifest = {
        "checkpoint": registry["checkpoint"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution_scope": config["execution_scope"],
        "implementation_commit": registry["implementation_commit"],
        "source_d2b_tag": source_tag,
        "source_d2b_commit": registry["source_d2b_commit"],
        "locks": locks,
        "family_horizon_rows": int(len(admission)),
        "family_decision_rows": int(len(decisions)),
        "admitted_families": int(decisions["pipeline_admitted"].astype(bool).sum()),
        "rejected_families": int((~decisions["pipeline_admitted"].astype(bool)).sum()),
        "component_selection_rows": int(len(component_records)),
        "frozen_pipeline_count": int(len(pipeline_records)),
        "development_admission_evaluated": True,
        "family_level_pipeline_freeze_completed": True,
        "economic_gate_evaluated": False,
        "holdout_authorization_enabled": False,
        "holdout_performance_accessed": False,
        "files": [file_record(path, ROOT) for path in generated],
    }
    manifest_path = args.processed_root / "d2c_admission_manifest.json"
    write_json(manifest_path, manifest)

    status = {
        "status": "PASS",
        "checkpoint": registry["checkpoint"],
        "implementation_commit": registry["implementation_commit"],
        "d2c_lock_id": locks["d2c"],
        "family_horizon_rows": int(len(admission)),
        "family_decision_rows": int(len(decisions)),
        "admitted_families": manifest["admitted_families"],
        "rejected_families": manifest["rejected_families"],
        "component_selection_rows": int(len(component_records)),
        "frozen_pipeline_count": int(len(pipeline_records)),
        "development_admission_evaluated": True,
        "family_level_pipeline_freeze_completed": True,
        "predictive_model_fitting_performed": False,
        "economic_gate_evaluated": False,
        "holdout_authorization_enabled": False,
        "holdout_performance_accessed": False,
        "manifest_sha256": sha256_file(manifest_path),
        "pipeline_registry_sha256": sha256_file(registry_path),
    }
    write_json(args.output_root / "d2c_admission_status.json", status)

    print("Version 2 D2C development admission and pipeline freeze completed.")
    print(f"Family-horizon admission rows: {len(admission):,}")
    print(f"Admitted families: {manifest['admitted_families']:,}")
    print(f"Rejected families: {manifest['rejected_families']:,}")
    print(f"Frozen pipelines: {len(pipeline_records):,}")
    for row in decisions.itertuples(index=False):
        print(f"{row.signal_family.upper()}: {row.family_decision}")
    print("Economic gate evaluated: False")
    print("Holdout authorization enabled: False")
    print("Holdout performance accessed: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
