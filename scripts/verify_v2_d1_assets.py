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
        PROCESSED / "d1_causal_base_features.csv",
        PROCESSED / "d1_feature_dictionary.csv",
        PROCESSED / "d1_registered_signal_feature_audit.csv",
        PROCESSED / "d1_fold_state_diagnostics.csv",
        PROCESSED / "d1_fold_state_parameters.json",
        PROCESSED / "d1_outer_filtered_state_probabilities.csv",
        PROCESSED / "d1_engine_manifest.json",
        OUTPUT / "d1_engine_status.json",
    ]
    missing = [path.relative_to(ROOT).as_posix() for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Missing D1 assets: " + ", ".join(missing))

    status = json.loads((OUTPUT / "d1_engine_status.json").read_text(encoding="utf-8"))
    if status["status"] != "PASS":
        raise RuntimeError("D1 status is not PASS.")
    if status["predictive_model_fitting_performed"] is not False:
        raise RuntimeError("D1 incorrectly reports predictive-model fitting.")
    if status["state_filter_fitting_performed"] is not True:
        raise RuntimeError("D1 did not report state-filter fitting.")
    if status["holdout_performance_accessed"] is not False:
        raise RuntimeError("D1 incorrectly reports holdout access.")

    audit = pd.read_csv(PROCESSED / "d1_registered_signal_feature_audit.csv")
    if len(audit) != 84 or not audit["prefix_invariant"].astype(bool).all():
        raise RuntimeError("Registered signal-feature audit is incomplete or non-causal.")

    diagnostics = pd.read_csv(PROCESSED / "d1_fold_state_diagnostics.csv")
    if len(diagnostics) != 80:
        raise RuntimeError("D1 state diagnostics must cover 80 nested fold records.")
    if (diagnostics["probability_sum_max_abs_error"] > 1e-10).any():
        raise RuntimeError("D1 state probabilities do not sum to one.")
    if (diagnostics["prefix_invariance_max_abs_error"] > 1e-12).any():
        raise RuntimeError("D1 filtered-state engine is not prefix invariant.")
    if (diagnostics["minimum_covariance_eigenvalue"] <= 0.0).any():
        raise RuntimeError("D1 state covariance is not positive definite.")

    probabilities = pd.read_csv(PROCESSED / "d1_outer_filtered_state_probabilities.csv")
    probability_columns = ["state_p_range", "state_p_trend", "state_p_stress"]
    sums = probabilities[probability_columns].sum(axis=1)
    if not np.allclose(sums.to_numpy(), 1.0, atol=1e-10):
        raise RuntimeError("Stored outer state probabilities do not sum to one.")
    if probabilities.duplicated(["horizon_candles", "outer_fold", "Timestamp"]).any():
        raise RuntimeError("Stored outer state probabilities contain duplicate keys.")

    holdout_root = ROOT / "outputs" / "v2" / "holdout"
    holdout_files = [path for path in holdout_root.rglob("*") if path.is_file()] if holdout_root.exists() else []
    if holdout_files:
        raise RuntimeError("Unauthorized holdout files exist.")

    print("V2 D1 asset verification passed.")
    print(f"Registered signal specifications: {len(audit):,}")
    print(f"Nested state fits: {len(diagnostics):,}")
    print(f"Outer probability rows: {len(probabilities):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
