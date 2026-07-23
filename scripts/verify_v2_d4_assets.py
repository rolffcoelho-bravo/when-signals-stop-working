
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "v2" / "holdout"
OUTPUT = ROOT / "outputs" / "v2" / "holdout"
EXPECTED_HASH = "2f85b54f8f178ec59c2bfb8a06cd8dedb3e053e2bec4da40cb446d380def2851"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    required = [
        PROCESSED / "d4_predictive_inference.csv",
        PROCESSED / "d4_subperiod_results.csv",
        PROCESSED / "d4_economic_cost_sensitivity.csv",
        PROCESSED / "d4_block_length_sensitivity.csv",
        PROCESSED / "d4_monthly_contribution.csv",
        PROCESSED / "d4_calibration_summary.csv",
        PROCESSED / "d4_confirmatory_manifest.json",
        OUTPUT / "d4_gate_results.json",
        OUTPUT / "d4_final_evidence_grade.json",
        OUTPUT / "d4_inference_status.json",
    ]
    missing = [path.as_posix() for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Missing D4 assets: " + ", ".join(missing))

    status = json.loads((OUTPUT / "d4_inference_status.json").read_text(encoding="utf-8"))
    if status["status"] != "PASS" or status["pipeline_hash"] != EXPECTED_HASH:
        raise RuntimeError("D4 status or frozen pipeline hash is invalid.")
    required_true = ["statistical_gate_evaluated", "economic_gate_evaluated", "multiplicity_adjustment_applied"]
    if not all(status[key] is True for key in required_true):
        raise RuntimeError("D4 did not complete required inference gates.")
    required_false = ["predictive_gate_passed", "economic_gate_passed", "robustness_gate_fully_evaluated", "pipeline_retuning_performed", "rsi_reentry_performed", "panic_state_extension_used"]
    if not all(status[key] is False for key in required_false):
        raise RuntimeError("D4 governance or gate flags are invalid.")
    if status["evidence_grade"] != "NO_INCREMENTAL_EVIDENCE":
        raise RuntimeError("D4 evidence grade is inconsistent with the locked evidence.")

    predictive = pd.read_csv(PROCESSED / "d4_predictive_inference.csv")
    if set(predictive["hypothesis_id"]) != {"H1_RSI_DIRECTION", "H2_BOLLINGER_DIRECTION"}:
        raise RuntimeError("D4 confirmatory family is incomplete.")
    rsi = predictive.loc[predictive["hypothesis_id"].eq("H1_RSI_DIRECTION")].iloc[0]
    bollinger = predictive.loc[predictive["hypothesis_id"].eq("H2_BOLLINGER_DIRECTION")].iloc[0]
    if rsi["holdout_status"] != "NO_PIPELINE_ADMITTED" or float(rsi["raw_one_sided_p_value"]) != 1.0:
        raise RuntimeError("D4 RSI multiplicity treatment is invalid.")
    if not (float(bollinger["mean_incremental_log_loss"]) > 0.0):
        raise RuntimeError("D4 locked mean loss differential changed unexpectedly.")
    if not (float(bollinger["holm_adjusted_p_value"]) > 0.05):
        raise RuntimeError("D4 Holm result changed unexpectedly.")

    subperiods = pd.read_csv(PROCESSED / "d4_subperiod_results.csv")
    if len(subperiods) != 3 or int(subperiods["predictive_contribution_positive"].sum()) != 1:
        raise RuntimeError("D4 subperiod evidence is invalid.")

    costs = pd.read_csv(PROCESSED / "d4_economic_cost_sensitivity.csv")
    if set(costs["one_way_cost_bps"].astype(int)) != {5, 10, 20}:
        raise RuntimeError("D4 cost sensitivity is incomplete.")
    primary = costs.loc[costs["one_way_cost_bps"].eq(10)].iloc[0]
    if not (float(primary["mean_incremental_net_return"]) < 0.0):
        raise RuntimeError("D4 primary economic mean changed unexpectedly.")
    if float(primary["candidate_coverage"]) < 0.10 or int(primary["candidate_nonzero_decisions"]) < 100:
        raise RuntimeError("D4 coverage accounting is invalid.")

    blocks = pd.read_csv(PROCESSED / "d4_block_length_sensitivity.csv")
    if set(blocks["block_length"].astype(int)) != {14, 21, 28}:
        raise RuntimeError("D4 block-length sensitivity is incomplete.")
    if blocks["conclusion_positive_lower_bound"].astype(bool).any():
        raise RuntimeError("D4 block sensitivity should not report a positive lower bound.")

    gates = json.loads((OUTPUT / "d4_gate_results.json").read_text(encoding="utf-8"))
    if gates["predictive_gate"]["passed"] is not False or gates["economic_gate"]["passed"] is not False:
        raise RuntimeError("D4 gate verdicts are invalid.")
    if gates["concentration_diagnostic"]["passed"] is not False:
        raise RuntimeError("D4 concentration diagnostic is invalid.")

    verdict = json.loads((OUTPUT / "d4_final_evidence_grade.json").read_text(encoding="utf-8"))
    if verdict["evidence_grade"] != "NO_INCREMENTAL_EVIDENCE" or verdict["primary_case_established"] is not False:
        raise RuntimeError("D4 final evidence grade is invalid.")
    if verdict["rsi_status"] != "NO_PIPELINE_ADMITTED":
        raise RuntimeError("D4 changed the RSI determination.")

    manifest_path = PROCESSED / "d4_confirmatory_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256(manifest_path) != status["manifest_sha256"]:
        raise RuntimeError("D4 manifest checksum is invalid.")
    if manifest["d3_predictions_sha256"] != sha256(PROCESSED / "d3_locked_predictions.csv"):
        raise RuntimeError("D4 does not bind to the committed D3 predictions.")
    for record in manifest["files"]:
        path = ROOT / record["path"]
        if not path.exists() or sha256(path) != record["sha256"]:
            raise RuntimeError(f"D4 generated-file checksum mismatch: {record['path']}")

    print("V2 D4 asset verification passed.")
    print(f"Evidence grade: {status['evidence_grade']}")
    print("Predictive gate passed: False")
    print("Economic gate passed: False")
    print("Pipeline retuning performed: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
