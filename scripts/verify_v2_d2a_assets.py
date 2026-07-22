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
        PROCESSED / "d2a_inner_screen_results.csv",
        PROCESSED / "d2a_selected_signal_specifications.csv",
        PROCESSED / "d2a_outer_fold_results.csv",
        PROCESSED / "d2a_outer_predictions.csv",
        PROCESSED / "d2a_family_horizon_summary.csv",
        PROCESSED / "d2a_selection_manifest.json",
        OUTPUT / "d2a_selection_status.json",
    ]
    missing = [path.as_posix() for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Missing D2A assets: " + ", ".join(missing))

    status = json.loads((OUTPUT / "d2a_selection_status.json").read_text(encoding="utf-8"))
    if status["status"] != "PASS":
        raise RuntimeError("D2A status is not PASS.")
    if status["registered_signal_specifications"] != 84:
        raise RuntimeError("D2A did not screen the 84 registered signal specifications.")
    if status["selected_specification_rows"] != 40 or status["outer_fold_result_rows"] != 40:
        raise RuntimeError("D2A must produce 40 selected specifications and 40 outer results.")
    if status["predictive_model_fitting_performed"] is not True:
        raise RuntimeError("D2A did not report predictive-model fitting.")
    if status["final_pipeline_selection_performed"] is not False:
        raise RuntimeError("D2A incorrectly reports final pipeline selection.")
    if status["holdout_performance_accessed"] is not False:
        raise RuntimeError("D2A incorrectly reports holdout access.")

    inner = pd.read_csv(PROCESSED / "d2a_inner_screen_results.csv")
    evaluated = inner.loc[inner["status"] == "EVALUATED"]
    expected_contexts = 4 * 5 * 3
    if evaluated.groupby(["horizon_candles", "outer_fold", "inner_fold"])["signal_spec_id"].nunique().min() < 84:
        raise RuntimeError("At least one D2A inner context lacks the full signal registry.")
    if evaluated[["benchmark_log_loss", "candidate_log_loss", "incremental_log_loss"]].isna().any().any():
        raise RuntimeError("Evaluated D2A inner results contain missing primary metrics.")

    selected = pd.read_csv(PROCESSED / "d2a_selected_signal_specifications.csv")
    if selected.duplicated(["signal_family", "horizon_candles", "outer_fold"]).any():
        raise RuntimeError("D2A selected specification keys are not unique.")

    outer = pd.read_csv(PROCESSED / "d2a_outer_fold_results.csv")
    if not np.isfinite(outer["incremental_log_loss"].to_numpy(dtype=float)).all():
        raise RuntimeError("D2A outer results contain non-finite incremental loss.")

    predictions = pd.read_csv(PROCESSED / "d2a_outer_predictions.csv")
    if predictions.duplicated(["signal_family", "horizon_candles", "outer_fold", "Timestamp"]).any():
        raise RuntimeError("D2A outer predictions contain duplicate keys.")
    for column in ["benchmark_probability", "candidate_probability"]:
        if ((predictions[column] <= 0.0) | (predictions[column] >= 1.0)).any():
            raise RuntimeError(f"D2A probability column is outside (0,1): {column}")

    summary = pd.read_csv(PROCESSED / "d2a_family_horizon_summary.csv")
    if len(summary) != 8:
        raise RuntimeError("D2A family-horizon summary must contain eight rows.")
    if set(summary["governance_interpretation"]) != {"PRELIMINARY_SCREENING_ONLY_NOT_FINAL_GATE_2"}:
        raise RuntimeError("D2A summary has an invalid governance interpretation.")

    holdout_root = ROOT / "outputs" / "v2" / "holdout"
    holdout_files = [path for path in holdout_root.rglob("*") if path.is_file()] if holdout_root.exists() else []
    if holdout_files:
        raise RuntimeError("Unauthorized holdout files exist.")

    print("V2 D2A asset verification passed.")
    print(f"Inner screening rows: {len(inner):,}")
    print(f"Selected specifications: {len(selected):,}")
    print(f"Outer prediction rows: {len(predictions):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
