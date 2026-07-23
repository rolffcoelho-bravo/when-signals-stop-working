from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "v2" / "holdout"
OUTPUT = ROOT / "outputs" / "v2" / "holdout"
DEVELOPMENT = ROOT / "data" / "processed" / "v2" / "development"
AUTHORIZATION = ROOT / "outputs" / "v2" / "development" / "d3_holdout_authorization.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    required = [
        PROCESSED / "d3_locked_market_data.csv",
        PROCESSED / "d3_locked_predictions.csv",
        PROCESSED / "d3_state_parameters.json",
        PROCESSED / "d3_evaluation_manifest.json",
        OUTPUT / "d3_pipeline_integrity.json",
        OUTPUT / "d3_raw_metric_summary.json",
        OUTPUT / "d3_authorization_consumption.json",
        OUTPUT / "d3_locked_evaluation_status.json",
        AUTHORIZATION,
    ]
    missing = [path.as_posix() for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Missing D3 assets: " + ", ".join(missing))

    status = json.loads((OUTPUT / "d3_locked_evaluation_status.json").read_text(encoding="utf-8"))
    if status["status"] != "PASS":
        raise RuntimeError("D3 status is not PASS.")
    if status["signal_family"] != "bollinger" or int(status["frozen_pipeline_count"]) != 1:
        raise RuntimeError("D3 executed an unauthorized family or pipeline count.")
    if status["pipeline_hash"] != "2f85b54f8f178ec59c2bfb8a06cd8dedb3e053e2bec4da40cb446d380def2851":
        raise RuntimeError("D3 pipeline hash is not the D2C-frozen hash.")
    required_true = [
        "methodology_locked_evaluation_executed",
        "holdout_authorization_consumed",
        "holdout_performance_accessed",
        "predictive_model_fitting_performed",
    ]
    if not all(status[key] is True for key in required_true):
        raise RuntimeError("D3 execution flags are incomplete.")
    required_false = [
        "pipeline_retuning_performed",
        "rsi_reentry_performed",
        "statistical_gate_evaluated",
        "economic_gate_evaluated",
        "robustness_gate_evaluated",
        "multiplicity_adjustment_applied",
    ]
    if not all(status[key] is False for key in required_false):
        raise RuntimeError("D3 governance flags are invalid.")

    predictions = pd.read_csv(PROCESSED / "d3_locked_predictions.csv")
    predictions["Timestamp"] = pd.to_datetime(predictions["Timestamp"], utc=True, errors="raise")
    predictions["target_timestamp"] = pd.to_datetime(predictions["target_timestamp"], utc=True, errors="raise")
    if len(predictions) != int(status["prediction_rows"]) or len(predictions) < 100:
        raise RuntimeError("D3 prediction-row count is invalid.")
    if predictions["Timestamp"].duplicated().any() or not predictions["Timestamp"].is_monotonic_increasing:
        raise RuntimeError("D3 predictions are not uniquely chronological.")
    if predictions["Timestamp"].min() != pd.Timestamp("2025-07-01T00:00:00Z"):
        raise RuntimeError("D3 predictions do not begin at the locked-evaluation boundary.")
    if predictions["target_timestamp"].max() > pd.Timestamp("2026-07-22T08:00:00Z"):
        raise RuntimeError("D3 targets extend beyond the locked-evaluation boundary.")
    if set(predictions["signal_family"]) != {"bollinger"}:
        raise RuntimeError("D3 predictions contain an unauthorized signal family.")
    if set(predictions["pipeline_hash"]) != {status["pipeline_hash"]}:
        raise RuntimeError("D3 prediction pipeline hashes are inconsistent.")
    if set(predictions["holdout_subperiod"]) != {"P1", "P2", "P3"}:
        raise RuntimeError("D3 does not contain the three frozen chronological subperiods.")
    probability_columns = ["benchmark_probability", "candidate_probability"]
    if ((predictions[probability_columns] <= 0.0) | (predictions[probability_columns] >= 1.0)).any().any():
        raise RuntimeError("D3 probabilities fall outside (0, 1).")

    metrics = json.loads((OUTPUT / "d3_raw_metric_summary.json").read_text(encoding="utf-8"))
    if metrics["interpretation"] != "RAW_METHODOLOGY_LOCKED_EVALUATION_EVIDENCE_NO_VERDICT":
        raise RuntimeError("D3 raw metrics contain an invalid interpretation.")
    if set(metrics["subperiods"]) != {"P1", "P2", "P3"}:
        raise RuntimeError("D3 raw metrics do not cover all subperiods.")
    for flag in [
        "statistical_gate_evaluated",
        "economic_gate_evaluated",
        "multiplicity_adjustment_applied",
        "robustness_gate_evaluated",
    ]:
        if metrics[flag] is not False:
            raise RuntimeError(f"D3 incorrectly reports {flag}.")

    integrity = json.loads((OUTPUT / "d3_pipeline_integrity.json").read_text(encoding="utf-8"))
    registry = json.loads((DEVELOPMENT / "d2c_frozen_pipeline_registry.json").read_text(encoding="utf-8"))
    if integrity["pipeline_hash"] != registry["frozen_pipelines"][0]["pipeline_hash"]:
        raise RuntimeError("D3 pipeline integrity does not match D2C.")
    if integrity["rsi_reentry_performed"] is not False or integrity["pipeline_retuning_performed"] is not False:
        raise RuntimeError("D3 integrity flags are invalid.")

    consumption = json.loads((OUTPUT / "d3_authorization_consumption.json").read_text(encoding="utf-8"))
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    if consumption["status"] != "CONSUMED_ONCE" or consumption["single_access"] is not True:
        raise RuntimeError("D3 authorization was not consumed exactly once.")
    if consumption["authorization_sha256"] != sha256(AUTHORIZATION):
        raise RuntimeError("D3 consumed authorization checksum is invalid.")
    if authorization["approval_record_created_before_results"] is not True:
        raise RuntimeError("D3 authorization was not recorded before results.")

    manifest_path = PROCESSED / "d3_evaluation_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256(manifest_path) != status["manifest_sha256"]:
        raise RuntimeError("D3 manifest checksum is invalid.")
    if sha256(PROCESSED / "d3_locked_predictions.csv") != status["predictions_sha256"]:
        raise RuntimeError("D3 prediction checksum is invalid.")
    for record in manifest["files"]:
        path = ROOT / record["path"]
        if not path.exists() or sha256(path) != record["sha256"]:
            raise RuntimeError(f"D3 generated-file checksum mismatch: {record['path']}")

    print("V2 D3 asset verification passed.")
    print(f"Authorized family: {status['signal_family'].upper()}")
    print(f"Prediction rows: {len(predictions):,}")
    print("Statistical gate evaluated: False")
    print("Economic gate evaluated: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
