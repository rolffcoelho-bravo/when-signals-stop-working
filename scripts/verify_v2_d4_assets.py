from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "v2" / "holdout"
OUTPUT = ROOT / "outputs" / "v2" / "holdout"
CONFIG = ROOT / "configs" / "v2_d4_confirmatory_inference.json"
EXPECTED_HASH = "2f85b54f8f178ec59c2bfb8a06cd8dedb3e053e2bec4da40cb446d380def2851"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not pd.isna(value):
        return bool(value)
    text = str(value).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    raise RuntimeError(f"Invalid boolean value in D4 evidence: {value!r}")


def close(left: object, right: object, tolerance: float = 1e-12) -> bool:
    return math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance)


def expected_grade(predictive_pass: bool, economic_pass: bool) -> tuple[str, str]:
    if not predictive_pass:
        return "NO_INCREMENTAL_EVIDENCE", "LOCKED_EVALUATION_PREDICTIVE_GATE_FAILED"
    if not economic_pass:
        return "PREDICTIVE_EVIDENCE_ONLY", "PREDICTIVE_GATE_PASSED_ECONOMIC_GATE_FAILED"
    return "PREDICTIVE_EVIDENCE_ONLY", "PREDICTIVE_AND_ECONOMIC_GATES_PASSED_ROBUSTNESS_PENDING"


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

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    status = json.loads((OUTPUT / "d4_inference_status.json").read_text(encoding="utf-8"))
    gates = json.loads((OUTPUT / "d4_gate_results.json").read_text(encoding="utf-8"))
    verdict = json.loads((OUTPUT / "d4_final_evidence_grade.json").read_text(encoding="utf-8"))

    if status["status"] != "PASS" or status["pipeline_hash"] != EXPECTED_HASH:
        raise RuntimeError("D4 status or frozen pipeline hash is invalid.")
    if gates["pipeline_hash"] != EXPECTED_HASH or verdict["pipeline_hash"] != EXPECTED_HASH:
        raise RuntimeError("D4 gate or verdict pipeline hash is invalid.")

    required_true = [
        "statistical_gate_evaluated",
        "economic_gate_evaluated",
        "multiplicity_adjustment_applied",
    ]
    if not all(status[key] is True for key in required_true):
        raise RuntimeError("D4 did not complete required inference gates.")
    required_false = [
        "robustness_gate_fully_evaluated",
        "pipeline_retuning_performed",
        "rsi_reentry_performed",
        "panic_state_extension_used",
    ]
    if not all(status[key] is False for key in required_false):
        raise RuntimeError("D4 governance flags are invalid.")
    if gates["robustness_gate_fully_evaluated"] is not False:
        raise RuntimeError("D4 robustness status is invalid.")
    if any(gates[key] is not False for key in ["pipeline_retuning_performed", "rsi_reentry_performed", "panic_state_extension_used"]):
        raise RuntimeError("D4 gate-governance flags are invalid.")

    predictive = pd.read_csv(PROCESSED / "d4_predictive_inference.csv")
    if set(predictive["hypothesis_id"]) != {"H1_RSI_DIRECTION", "H2_BOLLINGER_DIRECTION"}:
        raise RuntimeError("D4 confirmatory family is incomplete.")
    if len(predictive) != 2:
        raise RuntimeError("D4 confirmatory table must contain exactly two hypotheses.")

    rsi = predictive.loc[predictive["hypothesis_id"].eq("H1_RSI_DIRECTION")].iloc[0]
    bollinger = predictive.loc[predictive["hypothesis_id"].eq("H2_BOLLINGER_DIRECTION")].iloc[0]
    if rsi["holdout_status"] != "NO_PIPELINE_ADMITTED" or not close(rsi["raw_one_sided_p_value"], 1.0):
        raise RuntimeError("D4 RSI multiplicity treatment is invalid.")
    if as_bool(rsi["confirmatory_rejection"]):
        raise RuntimeError("D4 RSI cannot be rejected without an admitted pipeline.")

    raw_p = float(bollinger["raw_one_sided_p_value"])
    adjusted_p = float(bollinger["holm_adjusted_p_value"])
    alpha = float(config["predictive_gate"]["familywise_alpha"])
    if not (0.0 <= raw_p <= adjusted_p <= 1.0):
        raise RuntimeError("D4 Bollinger p-values are invalid.")
    if as_bool(bollinger["confirmatory_rejection"]) != (adjusted_p < alpha):
        raise RuntimeError("D4 confirmatory rejection flag is inconsistent.")

    predictive_gate = gates["predictive_gate"]
    if not close(bollinger["mean_incremental_log_loss"], predictive_gate["mean_incremental_log_loss"]):
        raise RuntimeError("D4 predictive mean is inconsistent across assets.")
    if not close(raw_p, predictive_gate["raw_one_sided_p_value"]) or not close(adjusted_p, predictive_gate["holm_adjusted_p_value"]):
        raise RuntimeError("D4 predictive p-values are inconsistent across assets.")

    subperiods = pd.read_csv(PROCESSED / "d4_subperiod_results.csv")
    expected_subperiods = int(config["predictive_gate"]["subperiod_count"])
    if len(subperiods) != expected_subperiods or subperiods["holdout_subperiod"].nunique() != expected_subperiods:
        raise RuntimeError("D4 subperiod count is invalid.")
    if int(subperiods["rows"].sum()) != int(status["prediction_rows"]):
        raise RuntimeError("D4 subperiod rows do not reconcile to the locked predictions.")
    recomputed_flags = subperiods["mean_incremental_log_loss"].astype(float) > 0.0
    recorded_flags = subperiods["predictive_contribution_positive"].map(as_bool)
    if not recomputed_flags.equals(recorded_flags):
        raise RuntimeError("D4 subperiod sign flags are inconsistent with their means.")
    positive_subperiods = int(recorded_flags.sum())
    if positive_subperiods != int(predictive_gate["positive_subperiods"]):
        raise RuntimeError("D4 positive-subperiod count is inconsistent.")

    calibration = pd.read_csv(PROCESSED / "d4_calibration_summary.csv")
    overall = calibration.loc[calibration["segment"].eq("OVERALL")]
    if len(overall) != 1:
        raise RuntimeError("D4 overall calibration row is missing or duplicated.")
    overall_row = overall.iloc[0]
    calibration_pass = bool(
        float(overall_row["candidate_minus_benchmark_brier"])
        <= float(config["calibration_gate"]["maximum_candidate_minus_benchmark_brier"])
        and float(overall_row["candidate_minus_benchmark_ece"])
        <= float(config["calibration_gate"]["maximum_candidate_minus_benchmark_ece"])
    )

    predictive_checks = {
        "positive_mean_incremental_log_loss": float(predictive_gate["mean_incremental_log_loss"]) > 0.0,
        "holm_adjusted_p_below_alpha": float(predictive_gate["holm_adjusted_p_value"]) < alpha,
        "positive_primary_bootstrap_lower_bound": float(predictive_gate["primary_bootstrap_ci_95_lower"]) > 0.0,
        "minimum_positive_subperiods": positive_subperiods >= int(predictive_gate["required_positive_subperiods"]),
        "no_material_calibration_failure": calibration_pass,
    }
    if predictive_checks != predictive_gate["checks"]:
        raise RuntimeError("D4 predictive checks are inconsistent with the recorded evidence.")
    predictive_pass = all(predictive_checks.values())
    if predictive_pass is not bool(predictive_gate["passed"]) or predictive_pass is not bool(status["predictive_gate_passed"]):
        raise RuntimeError("D4 predictive-gate verdict is inconsistent.")

    costs = pd.read_csv(PROCESSED / "d4_economic_cost_sensitivity.csv")
    expected_costs = {
        int(config["economic_gate"]["primary_one_way_cost_bps"]),
        *[int(value) for value in config["economic_gate"]["sensitivity_one_way_cost_bps"]],
    }
    if set(costs["one_way_cost_bps"].astype(int)) != expected_costs:
        raise RuntimeError("D4 cost sensitivity is incomplete.")
    primary_cost = int(config["economic_gate"]["primary_one_way_cost_bps"])
    primary_rows = costs.loc[costs["one_way_cost_bps"].astype(int).eq(primary_cost)]
    if len(primary_rows) != 1:
        raise RuntimeError("D4 primary economic row is missing or duplicated.")
    primary = primary_rows.iloc[0]
    economic_gate = gates["economic_gate"]
    for column, key in [
        ("mean_incremental_net_return", "mean_incremental_net_return"),
        ("ci_95_lower", "ci_95_lower"),
        ("ci_95_upper", "ci_95_upper"),
        ("candidate_coverage", "candidate_coverage"),
    ]:
        if not close(primary[column], economic_gate[key]):
            raise RuntimeError(f"D4 primary economic value is inconsistent: {column}")
    if int(primary["candidate_nonzero_decisions"]) != int(economic_gate["candidate_nonzero_decisions"]):
        raise RuntimeError("D4 decision count is inconsistent.")

    economic_checks = {
        "positive_mean_incremental_net_return": float(economic_gate["mean_incremental_net_return"]) > 0.0,
        "positive_primary_bootstrap_lower_bound": float(economic_gate["ci_95_lower"]) > 0.0,
        "minimum_candidate_coverage": float(economic_gate["candidate_coverage"]) >= float(config["economic_gate"]["minimum_candidate_coverage"]),
        "minimum_candidate_decisions": int(economic_gate["candidate_nonzero_decisions"]) >= int(config["economic_gate"]["minimum_candidate_decisions"]),
    }
    if economic_checks != economic_gate["checks"]:
        raise RuntimeError("D4 economic checks are inconsistent with the recorded evidence.")
    economic_pass = all(economic_checks.values())
    if economic_pass is not bool(economic_gate["passed"]) or economic_pass is not bool(status["economic_gate_passed"]):
        raise RuntimeError("D4 economic-gate verdict is inconsistent.")

    blocks = pd.read_csv(PROCESSED / "d4_block_length_sensitivity.csv")
    expected_blocks = {
        int(config["bootstrap"]["primary_block_length"]),
        *[int(value) for value in config["bootstrap"]["sensitivity_block_lengths"]],
    }
    if set(blocks["block_length"].astype(int)) != expected_blocks:
        raise RuntimeError("D4 block-length sensitivity is incomplete.")
    recorded_block_flags = blocks["conclusion_positive_lower_bound"].map(as_bool)
    recomputed_block_flags = blocks["ci_95_lower"].astype(float) > 0.0
    if not recorded_block_flags.equals(recomputed_block_flags):
        raise RuntimeError("D4 block-length conclusions are inconsistent with their intervals.")

    concentration = gates["concentration_diagnostic"]
    concentration_pass = float(concentration["maximum_single_positive_month_share"]) <= float(concentration["threshold"])
    if concentration_pass is not bool(concentration["passed"]):
        raise RuntimeError("D4 concentration diagnostic is inconsistent.")

    grade, determination = expected_grade(predictive_pass, economic_pass)
    if status["evidence_grade"] != grade or verdict["evidence_grade"] != grade:
        raise RuntimeError("D4 evidence grade is inconsistent with the gates.")
    if verdict["determination"] != determination or verdict["primary_case_established"] is not False:
        raise RuntimeError("D4 final determination is invalid.")
    if verdict["rsi_status"] != "NO_PIPELINE_ADMITTED":
        raise RuntimeError("D4 changed the RSI determination.")

    manifest_path = PROCESSED / "d4_confirmatory_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256(manifest_path) != status["manifest_sha256"]:
        raise RuntimeError("D4 manifest checksum is invalid.")
    if manifest["d3_predictions_sha256"] != sha256(PROCESSED / "d3_locked_predictions.csv"):
        raise RuntimeError("D4 does not bind to the committed D3 predictions.")
    if manifest["evidence_grade"] != grade or manifest["prediction_rows"] != status["prediction_rows"]:
        raise RuntimeError("D4 manifest summary is inconsistent.")
    for record in manifest["files"]:
        path = ROOT / record["path"]
        if not path.exists() or sha256(path) != record["sha256"]:
            raise RuntimeError(f"D4 generated-file checksum mismatch: {record['path']}")

    print("V2 D4 asset verification passed.")
    print(f"Evidence grade: {grade}")
    print(f"Positive locked subperiods: {positive_subperiods}/{expected_subperiods}")
    print(f"Predictive gate passed: {predictive_pass}")
    print(f"Economic gate passed: {economic_pass}")
    print("Pipeline retuning performed: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())