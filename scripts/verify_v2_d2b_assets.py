from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "v2" / "development"
OUTPUT = ROOT / "outputs" / "v2" / "development"


def main() -> int:
    required = [
        PROCESSED / "d2b_structural_pipeline_inventory.csv",
        PROCESSED / "d2b_inner_structural_results.csv",
        PROCESSED / "d2b_selected_structural_pipelines.csv",
        PROCESSED / "d2b_inner_calibration_results.csv",
        PROCESSED / "d2b_selected_calibrations.csv",
        PROCESSED / "d2b_inner_policy_results.csv",
        PROCESSED / "d2b_selected_decision_policies.csv",
        PROCESSED / "d2b_outer_fold_results.csv",
        PROCESSED / "d2b_outer_predictions.csv",
        PROCESSED / "d2b_family_horizon_summary.csv",
        PROCESSED / "d2b_selection_manifest.json",
        OUTPUT / "d2b_selection_status.json",
    ]
    missing = [path.as_posix() for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Missing D2B assets: " + ", ".join(missing))

    status = json.loads((OUTPUT / "d2b_selection_status.json").read_text(encoding="utf-8"))
    if status["status"] != "PASS":
        raise RuntimeError("D2B status is not PASS.")
    if status["production_structural_inventory_rows"] != 90:
        raise RuntimeError("D2B production structural inventory is not 90.")
    if status["executed_structural_inventory_rows"] != 90 or status["validation_mode"] is not False:
        raise RuntimeError("D2B production evidence was generated with a partial validation inventory.")
    expected = {
        "inner_structural_result_rows": 10800,
        "selected_structural_pipeline_rows": 40,
        "inner_calibration_result_rows": 360,
        "selected_calibration_rows": 40,
        "inner_policy_result_rows": 480,
        "selected_policy_rows": 40,
        "outer_fold_result_rows": 40,
    }
    for key, value in expected.items():
        if int(status[key]) != value:
            raise RuntimeError(f"D2B status field {key} must equal {value}.")
    if status["predictive_model_fitting_performed"] is not True:
        raise RuntimeError("D2B did not report predictive-model fitting.")
    if status["nested_pipeline_selection_performed"] is not True:
        raise RuntimeError("D2B did not report nested pipeline selection.")
    if status["isotonic_diagnostic_only"] is not True:
        raise RuntimeError("D2B isotonic governance flag is invalid.")
    if status["economic_gate_evaluated"] is not False:
        raise RuntimeError("D2B incorrectly reports final economic-gate evaluation.")
    if status["holdout_pipeline_freeze_performed"] is not False:
        raise RuntimeError("D2B incorrectly reports holdout-pipeline freeze.")
    if status["holdout_performance_accessed"] is not False:
        raise RuntimeError("D2B incorrectly reports holdout access.")

    inventory = pd.read_csv(PROCESSED / "d2b_structural_pipeline_inventory.csv")
    if len(inventory) != 90 or inventory["pipeline_id"].duplicated().any():
        raise RuntimeError("D2B structural inventory is incomplete or duplicated.")
    expected_family_counts = {
        "regularized_linear": 18,
        "spline_regularized": 24,
        "shallow_hist_gradient_boosting": 48,
    }
    if inventory.groupby("model_family").size().to_dict() != expected_family_counts:
        raise RuntimeError("D2B model-family inventory counts are invalid.")

    structural = pd.read_csv(PROCESSED / "d2b_inner_structural_results.csv")
    if len(structural) != 10800:
        raise RuntimeError("D2B structural result count is invalid.")
    keys = ["signal_family", "horizon_candles", "outer_fold", "inner_fold", "pipeline_id"]
    if structural.duplicated(keys).any():
        raise RuntimeError("D2B structural results contain duplicate keys.")
    evaluated = structural.loc[structural["status"] == "EVALUATED"]
    if evaluated.empty:
        raise RuntimeError("D2B contains no evaluated structural pipelines.")
    metric_columns = [
        "benchmark_log_loss",
        "candidate_log_loss",
        "incremental_log_loss",
        "benchmark_brier",
        "candidate_brier",
        "benchmark_ece",
        "candidate_ece",
    ]
    if not np.isfinite(evaluated[metric_columns].to_numpy(dtype=float)).all():
        raise RuntimeError("D2B evaluated structural metrics contain non-finite values.")

    selected_structural = pd.read_csv(PROCESSED / "d2b_selected_structural_pipelines.csv")
    context_keys = ["signal_family", "horizon_candles", "outer_fold"]
    if len(selected_structural) != 40 or selected_structural.duplicated(context_keys).any():
        raise RuntimeError("D2B selected structural-pipeline keys are invalid.")
    if not set(selected_structural["selected_pipeline_id"]).issubset(set(inventory["pipeline_id"])):
        raise RuntimeError("D2B selected an unregistered structural pipeline.")

    calibration = pd.read_csv(PROCESSED / "d2b_inner_calibration_results.csv")
    if len(calibration) != 360:
        raise RuntimeError("D2B calibration result count is invalid.")
    if set(calibration["calibration_method"]) != {"none", "sigmoid", "isotonic"}:
        raise RuntimeError("D2B calibration methods are incomplete.")
    isotonic = calibration.loc[calibration["calibration_method"] == "isotonic"]
    if isotonic["eligible_for_selection"].astype(bool).any():
        raise RuntimeError("D2B incorrectly made isotonic calibration selection-eligible.")

    selected_calibration = pd.read_csv(PROCESSED / "d2b_selected_calibrations.csv")
    if len(selected_calibration) != 40 or selected_calibration.duplicated(context_keys).any():
        raise RuntimeError("D2B selected-calibration keys are invalid.")
    if not set(selected_calibration["selected_calibration_method"]).issubset({"none", "sigmoid"}):
        raise RuntimeError("D2B selected diagnostic-only isotonic calibration.")

    policies = pd.read_csv(PROCESSED / "d2b_inner_policy_results.csv")
    if len(policies) != 480 or set(np.round(policies["threshold"], 8)) != {0.0, 0.02, 0.05, 0.1}:
        raise RuntimeError("D2B decision-policy grid is incomplete.")
    if ((policies["coverage"] < 0.0) | (policies["coverage"] > 1.0)).any():
        raise RuntimeError("D2B policy coverage is outside [0,1].")

    selected_policy = pd.read_csv(PROCESSED / "d2b_selected_decision_policies.csv")
    if len(selected_policy) != 40 or selected_policy.duplicated(context_keys).any():
        raise RuntimeError("D2B selected-policy keys are invalid.")
    if set(selected_policy["governance_interpretation"]) != {"DEVELOPMENT_POLICY_SELECTION_NOT_ECONOMIC_GATE"}:
        raise RuntimeError("D2B policy governance interpretation is invalid.")

    outer = pd.read_csv(PROCESSED / "d2b_outer_fold_results.csv")
    if len(outer) != 40 or outer.duplicated(context_keys).any():
        raise RuntimeError("D2B outer-fold result keys are invalid.")
    if not np.isfinite(outer[metric_columns].to_numpy(dtype=float)).all():
        raise RuntimeError("D2B outer metrics contain non-finite values.")
    if outer["economic_gate_evaluated"].astype(bool).any():
        raise RuntimeError("D2B outer evidence incorrectly reports final economic-gate evaluation.")

    predictions = pd.read_csv(PROCESSED / "d2b_outer_predictions.csv")
    prediction_keys = ["signal_family", "horizon_candles", "outer_fold", "Timestamp"]
    if predictions.empty or predictions.duplicated(prediction_keys).any():
        raise RuntimeError("D2B outer predictions are empty or duplicated.")
    for column in ["benchmark_probability", "candidate_probability"]:
        if ((predictions[column] <= 0.0) | (predictions[column] >= 1.0)).any():
            raise RuntimeError(f"D2B probability column is outside (0,1): {column}")

    summary = pd.read_csv(PROCESSED / "d2b_family_horizon_summary.csv")
    if len(summary) != 8:
        raise RuntimeError("D2B family-horizon summary must contain eight rows.")
    if set(summary["governance_interpretation"]) != {"DEVELOPMENT_GATE_ONLY_NO_HOLDOUT_EVIDENCE"}:
        raise RuntimeError("D2B summary has an invalid governance interpretation.")

    holdout_root = ROOT / "outputs" / "v2" / "holdout"
    holdout_files = [path for path in holdout_root.rglob("*") if path.is_file()] if holdout_root.exists() else []
    if holdout_files:
        raise RuntimeError("Unauthorized holdout files exist.")

    print("V2 D2B asset verification passed.")
    print(f"Structural inventory rows: {len(inventory):,}")
    print(f"Inner structural rows: {len(structural):,}")
    print(f"Selected pipelines: {len(selected_structural):,}")
    print(f"Outer prediction rows: {len(predictions):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
