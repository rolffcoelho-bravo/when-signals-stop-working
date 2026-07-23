
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from shockbridge_signal_validity.v2.confirmatory_inference import (
    brier_score,
    expected_calibration_error,
    holm_adjusted_pvalues,
    matched_policy_returns,
    monthly_positive_concentration,
    moving_block_bootstrap_mean_interval,
    one_sided_predictive_comparison,
    select_development_block_length,
)
from shockbridge_signal_validity.v2.manifests import file_record, sha256_file, write_json


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Version 2 D4 confirmatory inference assets.")
    parser.add_argument("--config", type=Path, default=Path("configs/v2_d4_confirmatory_inference.json"))
    parser.add_argument("--predictions", type=Path, default=Path("data/processed/v2/holdout/d3_locked_predictions.csv"))
    parser.add_argument("--d3-manifest", type=Path, default=Path("data/processed/v2/holdout/d3_evaluation_manifest.json"))
    parser.add_argument("--d3-status", type=Path, default=Path("outputs/v2/holdout/d3_locked_evaluation_status.json"))
    parser.add_argument("--d3-integrity", type=Path, default=Path("outputs/v2/holdout/d3_pipeline_integrity.json"))
    parser.add_argument("--pipeline-registry", type=Path, default=Path("data/processed/v2/development/d2c_frozen_pipeline_registry.json"))
    parser.add_argument("--sol-csv", type=Path, default=Path("data/raw/sol_usdt_4h.csv"))
    parser.add_argument("--d4-lock", type=Path, default=Path("V2_D4_INFERENCE_LOCK.json"))
    parser.add_argument("--processed-root", type=Path, default=Path("data/processed/v2/holdout"))
    parser.add_argument("--output-root", type=Path, default=Path("outputs/v2/holdout"))
    return parser.parse_args()


def git_commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()


def calibration_row(label: str, frame: pd.DataFrame) -> dict[str, object]:
    realised = frame["realised_direction"].astype(int).to_numpy()
    benchmark = frame["benchmark_probability"].to_numpy(float)
    candidate = frame["candidate_probability"].to_numpy(float)
    return {
        "segment": label,
        "rows": int(len(frame)),
        "benchmark_brier": brier_score(realised, benchmark),
        "candidate_brier": brier_score(realised, candidate),
        "candidate_minus_benchmark_brier": brier_score(realised, candidate) - brier_score(realised, benchmark),
        "benchmark_ece": expected_calibration_error(realised, benchmark),
        "candidate_ece": expected_calibration_error(realised, candidate),
        "candidate_minus_benchmark_ece": expected_calibration_error(realised, candidate) - expected_calibration_error(realised, benchmark),
    }


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    d3_manifest = json.loads(args.d3_manifest.read_text(encoding="utf-8"))
    d3_status = json.loads(args.d3_status.read_text(encoding="utf-8"))
    d3_integrity = json.loads(args.d3_integrity.read_text(encoding="utf-8"))
    pipeline_registry = json.loads(args.pipeline_registry.read_text(encoding="utf-8"))
    d4_lock = json.loads(args.d4_lock.read_text(encoding="utf-8"))

    expected_hash = config["expected_pipeline_hash"]
    if d3_status.get("status") != "PASS" or d3_status.get("holdout_performance_accessed") is not True:
        raise RuntimeError("D4 requires the completed D3 locked-evaluation checkpoint.")
    if d3_status.get("statistical_gate_evaluated") is not False or d3_status.get("economic_gate_evaluated") is not False:
        raise RuntimeError("D3 already reports inference or economic-gate evaluation.")
    if d3_manifest.get("pipeline_hash") != expected_hash or d3_integrity.get("pipeline_hash") != expected_hash:
        raise RuntimeError("D4 received a pipeline hash different from the D2C/D3 frozen hash.")
    pipelines = pipeline_registry.get("frozen_pipelines", [])
    if len(pipelines) != 1 or pipelines[0].get("signal_family") != "bollinger":
        raise RuntimeError("D4 requires exactly one frozen Bollinger pipeline.")
    if pipelines[0].get("pipeline_hash") != expected_hash:
        raise RuntimeError("D4 pipeline registry hash mismatch.")
    if d3_integrity.get("pipeline_retuning_performed") is not False or d3_integrity.get("rsi_reentry_performed") is not False:
        raise RuntimeError("D3 integrity flags prohibit D4 execution.")

    predictions = pd.read_csv(args.predictions)
    predictions["Timestamp"] = pd.to_datetime(predictions["Timestamp"], utc=True, errors="raise")
    predictions["target_timestamp"] = pd.to_datetime(predictions["target_timestamp"], utc=True, errors="raise")
    if len(predictions) != int(d3_status["prediction_rows"]):
        raise RuntimeError("D3 prediction count changed before D4.")
    if set(predictions["signal_family"].astype(str)) != {"bollinger"}:
        raise RuntimeError("D4 input contains an unauthorized signal family.")
    if set(predictions["pipeline_hash"].astype(str)) != {expected_hash}:
        raise RuntimeError("D4 input contains a non-frozen pipeline hash.")

    sol = pd.read_csv(args.sol_csv, parse_dates=["Date"]).set_index("Date").sort_index()
    development_end = pd.Timestamp(config["bootstrap"]["development_only_materialization"]["development_end_utc"])
    development_close = sol.loc[:development_end, "Close"]
    selected_block, acf = select_development_block_length(development_close)
    expected_block = int(config["bootstrap"]["primary_block_length"])
    if selected_block != expected_block:
        raise RuntimeError(f"Development-only block-length diagnostic resolved {selected_block}, expected {expected_block}.")

    loss_differential = predictions["incremental_observation_log_loss"].to_numpy(float)
    horizon = int(pipelines[0]["horizon_candles"])
    predictive = one_sided_predictive_comparison(loss_differential, horizon_candles=horizon)
    raw_pvalues = {"H1_RSI_DIRECTION": 1.0, "H2_BOLLINGER_DIRECTION": predictive.one_sided_p_value}
    adjusted = holm_adjusted_pvalues(raw_pvalues)

    block_lengths = [expected_block] + [int(value) for value in config["bootstrap"]["sensitivity_block_lengths"]]
    block_rows: list[dict[str, object]] = []
    predictive_intervals = {}
    for block in block_lengths:
        interval = moving_block_bootstrap_mean_interval(
            loss_differential,
            samples=int(config["bootstrap"]["samples"]),
            block_length=block,
            confidence_level=float(config["economic_gate"]["confidence_level"]),
            random_seed=int(config["bootstrap"]["random_seed"]),
        )
        predictive_intervals[block] = interval
        block_rows.append({
            "evidence_type": "predictive_loss_differential",
            "block_length": block,
            "mean": interval.mean,
            "ci_95_lower": interval.lower,
            "ci_95_upper": interval.upper,
            "bootstrap_probability_nonpositive": interval.probability_nonpositive,
            "conclusion_positive_lower_bound": interval.lower > 0.0,
        })

    calibration_rows = [calibration_row("OVERALL", predictions)]
    calibration_rows.extend(
        calibration_row(str(label), group)
        for label, group in predictions.groupby("holdout_subperiod", sort=True)
    )
    calibration = pd.DataFrame(calibration_rows)
    overall_calibration = calibration.loc[calibration["segment"].eq("OVERALL")].iloc[0]
    calibration_pass = bool(
        overall_calibration["candidate_minus_benchmark_brier"]
        <= float(config["calibration_gate"]["maximum_candidate_minus_benchmark_brier"])
        and overall_calibration["candidate_minus_benchmark_ece"]
        <= float(config["calibration_gate"]["maximum_candidate_minus_benchmark_ece"])
    )

    subperiod_rows: list[dict[str, object]] = []
    for label, group in predictions.groupby("holdout_subperiod", sort=True):
        subperiod_rows.append({
            "holdout_subperiod": str(label),
            "rows": int(len(group)),
            "mean_incremental_log_loss": float(group["incremental_observation_log_loss"].mean()),
            "predictive_contribution_positive": bool(group["incremental_observation_log_loss"].mean() > 0.0),
        })
    subperiods = pd.DataFrame(subperiod_rows)
    positive_subperiods = int(subperiods["predictive_contribution_positive"].sum())

    predictive_primary = predictive_intervals[expected_block]
    alpha = float(config["predictive_gate"]["familywise_alpha"])
    predictive_checks = {
        "positive_mean_incremental_log_loss": predictive.mean_loss_differential > 0.0,
        "holm_adjusted_p_below_alpha": adjusted["H2_BOLLINGER_DIRECTION"] < alpha,
        "positive_primary_bootstrap_lower_bound": predictive_primary.lower > 0.0,
        "minimum_positive_subperiods": positive_subperiods >= int(config["predictive_gate"]["minimum_positive_subperiods"]),
        "no_material_calibration_failure": calibration_pass,
    }
    predictive_gate_pass = all(predictive_checks.values())

    cost_rows: list[dict[str, object]] = []
    primary_policy = None
    primary_economic_interval = None
    cost_values = [int(config["economic_gate"]["primary_one_way_cost_bps"])] + [
        int(value) for value in config["economic_gate"]["sensitivity_one_way_cost_bps"]
    ]
    threshold = float(pipelines[0]["decision_probability_distance_threshold"])
    for cost_bps in cost_values:
        policy = matched_policy_returns(predictions, threshold, cost_bps)
        interval = moving_block_bootstrap_mean_interval(
            policy["incremental_net_return"],
            samples=int(config["bootstrap"]["samples"]),
            block_length=expected_block,
            confidence_level=float(config["economic_gate"]["confidence_level"]),
            random_seed=int(config["bootstrap"]["random_seed"]),
        )
        cost_rows.append({
            "one_way_cost_bps": cost_bps,
            "rows": int(len(policy)),
            "candidate_coverage": float(policy["candidate_decision_active"].mean()),
            "benchmark_coverage": float(policy["benchmark_decision_active"].mean()),
            "candidate_nonzero_decisions": int(policy["candidate_decision_active"].sum()),
            "benchmark_nonzero_decisions": int(policy["benchmark_decision_active"].sum()),
            "candidate_turnover_units": float(policy["candidate_turnover_units"].sum()),
            "benchmark_turnover_units": float(policy["benchmark_turnover_units"].sum()),
            "candidate_cumulative_gross_return": float(policy["candidate_gross_return"].sum()),
            "candidate_cumulative_net_return": float(policy["candidate_net_return"].sum()),
            "benchmark_cumulative_gross_return": float(policy["benchmark_gross_return"].sum()),
            "benchmark_cumulative_net_return": float(policy["benchmark_net_return"].sum()),
            "cumulative_incremental_gross_return": float(policy["incremental_gross_return"].sum()),
            "cumulative_incremental_net_return": float(policy["incremental_net_return"].sum()),
            "mean_incremental_net_return": interval.mean,
            "ci_95_lower": interval.lower,
            "ci_95_upper": interval.upper,
            "bootstrap_probability_nonpositive": interval.probability_nonpositive,
        })
        if cost_bps == int(config["economic_gate"]["primary_one_way_cost_bps"]):
            primary_policy = policy
            primary_economic_interval = interval

    if primary_policy is None or primary_economic_interval is None:
        raise RuntimeError("Primary economic policy was not evaluated.")

    for block in block_lengths:
        interval = moving_block_bootstrap_mean_interval(
            primary_policy["incremental_net_return"],
            samples=int(config["bootstrap"]["samples"]),
            block_length=block,
            confidence_level=float(config["economic_gate"]["confidence_level"]),
            random_seed=int(config["bootstrap"]["random_seed"]),
        )
        block_rows.append({
            "evidence_type": "economic_incremental_net_return_10bps",
            "block_length": block,
            "mean": interval.mean,
            "ci_95_lower": interval.lower,
            "ci_95_upper": interval.upper,
            "bootstrap_probability_nonpositive": interval.probability_nonpositive,
            "conclusion_positive_lower_bound": interval.lower > 0.0,
        })

    monthly, maximum_month_share, maximum_month = monthly_positive_concentration(primary_policy)
    economic_checks = {
        "positive_mean_incremental_net_return": primary_economic_interval.mean > 0.0,
        "positive_primary_bootstrap_lower_bound": primary_economic_interval.lower > 0.0,
        "minimum_candidate_coverage": float(primary_policy["candidate_decision_active"].mean()) >= float(config["economic_gate"]["minimum_candidate_coverage"]),
        "minimum_candidate_decisions": int(primary_policy["candidate_decision_active"].sum()) >= int(config["economic_gate"]["minimum_candidate_decisions"]),
    }
    economic_gate_pass = all(economic_checks.values())
    concentration_diagnostic_pass = maximum_month_share <= float(config["economic_gate"]["maximum_single_positive_month_share"])

    primary_subperiod_economic = primary_policy.groupby("holdout_subperiod", sort=True)["incremental_net_return"].agg(["mean", "sum"])
    subperiods = subperiods.merge(
        primary_subperiod_economic.rename(columns={"mean": "mean_incremental_net_return_10bps", "sum": "cumulative_incremental_net_return_10bps"}).reset_index(),
        on="holdout_subperiod",
        how="left",
    )

    predictive_table = pd.DataFrame([
        {
            "hypothesis_id": "H1_RSI_DIRECTION",
            "signal_family": "rsi",
            "holdout_status": "NO_PIPELINE_ADMITTED",
            "mean_incremental_log_loss": np.nan,
            "dm_style_statistic": np.nan,
            "raw_one_sided_p_value": 1.0,
            "holm_adjusted_p_value": adjusted["H1_RSI_DIRECTION"],
            "confirmatory_rejection": False,
        },
        {
            "hypothesis_id": "H2_BOLLINGER_DIRECTION",
            "signal_family": "bollinger",
            "holdout_status": "EVALUATED",
            "mean_incremental_log_loss": predictive.mean_loss_differential,
            "dm_style_standard_error": predictive.standard_error,
            "dm_style_statistic": predictive.statistic,
            "hac_lag": predictive.hac_lag,
            "raw_one_sided_p_value": predictive.one_sided_p_value,
            "holm_adjusted_p_value": adjusted["H2_BOLLINGER_DIRECTION"],
            "confirmatory_rejection": adjusted["H2_BOLLINGER_DIRECTION"] < alpha,
        },
    ])

    args.processed_root.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)
    generated_paths = []
    tables = {
        "d4_predictive_inference.csv": predictive_table,
        "d4_subperiod_results.csv": subperiods,
        "d4_economic_cost_sensitivity.csv": pd.DataFrame(cost_rows),
        "d4_block_length_sensitivity.csv": pd.DataFrame(block_rows),
        "d4_monthly_contribution.csv": monthly,
        "d4_calibration_summary.csv": calibration,
    }
    for name, table in tables.items():
        path = args.processed_root / name
        table.to_csv(path, index=False)
        generated_paths.append(path)

    gate_results = {
        "checkpoint": "V2_D4_CONFIRMATORY_INFERENCE_AND_ECONOMIC_GATES",
        "signal_family": "bollinger",
        "pipeline_hash": expected_hash,
        "confirmatory_family_size": 2,
        "predictive_gate": {
            "passed": predictive_gate_pass,
            "checks": predictive_checks,
            "mean_incremental_log_loss": predictive.mean_loss_differential,
            "dm_style_standard_error": predictive.standard_error,
            "dm_style_statistic": predictive.statistic,
            "raw_one_sided_p_value": predictive.one_sided_p_value,
            "holm_adjusted_p_value": adjusted["H2_BOLLINGER_DIRECTION"],
            "primary_bootstrap_ci_95_lower": predictive_primary.lower,
            "primary_bootstrap_ci_95_upper": predictive_primary.upper,
            "positive_subperiods": positive_subperiods,
            "required_positive_subperiods": int(config["predictive_gate"]["minimum_positive_subperiods"]),
            "calibration_pass": calibration_pass,
        },
        "economic_gate": {
            "passed": economic_gate_pass,
            "checks": economic_checks,
            "primary_one_way_cost_bps": int(config["economic_gate"]["primary_one_way_cost_bps"]),
            "mean_incremental_net_return": primary_economic_interval.mean,
            "ci_95_lower": primary_economic_interval.lower,
            "ci_95_upper": primary_economic_interval.upper,
            "candidate_coverage": float(primary_policy["candidate_decision_active"].mean()),
            "candidate_nonzero_decisions": int(primary_policy["candidate_decision_active"].sum()),
        },
        "concentration_diagnostic": {
            "passed": concentration_diagnostic_pass,
            "maximum_single_positive_month_share": maximum_month_share,
            "maximum_contributing_month": maximum_month,
            "threshold": float(config["economic_gate"]["maximum_single_positive_month_share"]),
        },
        "robustness_gate_fully_evaluated": False,
        "pipeline_retuning_performed": False,
        "rsi_reentry_performed": False,
        "panic_state_extension_used": False,
    }
    gate_path = args.output_root / "d4_gate_results.json"
    write_json(gate_path, gate_results)
    generated_paths.append(gate_path)

    if not predictive_gate_pass:
        evidence_grade = "NO_INCREMENTAL_EVIDENCE"
        determination = "LOCKED_EVALUATION_PREDICTIVE_GATE_FAILED"
    elif not economic_gate_pass:
        evidence_grade = "PREDICTIVE_EVIDENCE_ONLY"
        determination = "PREDICTIVE_GATE_PASSED_ECONOMIC_GATE_FAILED"
    else:
        evidence_grade = "PREDICTIVE_EVIDENCE_ONLY"
        determination = "PREDICTIVE_AND_ECONOMIC_GATES_PASSED_ROBUSTNESS_PENDING"

    verdict = {
        "signal_family": "bollinger",
        "pipeline_hash": expected_hash,
        "evidence_grade": evidence_grade,
        "determination": determination,
        "rsi_status": "NO_PIPELINE_ADMITTED",
        "primary_case_established": False,
        "external_replication_evaluated": False,
        "monitoring_ready": False,
        "robustness_gate_pending": True,
        "interpretation": (
            f"The frozen Bollinger pipeline produced a "
            f"{'positive' if predictive.mean_loss_differential > 0.0 else 'non-positive'} "
            f"mean benchmark-relative loss differential. The confirmatory predictive gate "
            f"{'passed' if predictive_gate_pass else 'did not pass'} after multiplicity, "
            f"dependence-aware bootstrap, chronological subperiod, and calibration controls. "
            f"At the primary 10-bps cost, the matched mean incremental net return was "
            f"{'positive' if primary_economic_interval.mean > 0.0 else 'non-positive'}, "
            f"and the economic gate {'passed' if economic_gate_pass else 'did not pass'} "
            f"under the confidence, coverage, and decision-count requirements."
        ),
    }
    verdict_path = args.output_root / "d4_final_evidence_grade.json"
    write_json(verdict_path, verdict)
    generated_paths.append(verdict_path)

    implementation_commit = git_commit()
    manifest = {
        "checkpoint": "V2_D4_CONFIRMATORY_INFERENCE_AND_ECONOMIC_GATES",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "implementation_commit": implementation_commit,
        "d3_evidence_commit": config["expected_parent_commit"],
        "d3_manifest_sha256": sha256_file(args.d3_manifest),
        "d3_predictions_sha256": sha256_file(args.predictions),
        "d4_lock_id": d4_lock["lock_id"],
        "pipeline_hash": expected_hash,
        "signal_family": "bollinger",
        "prediction_rows": int(len(predictions)),
        "confirmatory_family_size": 2,
        "holm_adjustment_applied": True,
        "statistical_gate_evaluated": True,
        "economic_gate_evaluated": True,
        "robustness_gate_fully_evaluated": False,
        "pipeline_retuning_performed": False,
        "rsi_reentry_performed": False,
        "panic_state_extension_used": False,
        "block_length_materialization_status": config["bootstrap"]["development_only_materialization"]["status"],
        "development_selected_primary_block_length": selected_block,
        "development_squared_return_acf_lags_1_to_48": acf,
        "evidence_grade": evidence_grade,
        "files": [file_record(path, ROOT) for path in generated_paths],
    }
    manifest_path = args.processed_root / "d4_confirmatory_manifest.json"
    write_json(manifest_path, manifest)

    status = {
        "status": "PASS",
        "checkpoint": manifest["checkpoint"],
        "implementation_commit": implementation_commit,
        "d4_lock_id": d4_lock["lock_id"],
        "pipeline_hash": expected_hash,
        "signal_family": "bollinger",
        "prediction_rows": int(len(predictions)),
        "statistical_gate_evaluated": True,
        "economic_gate_evaluated": True,
        "multiplicity_adjustment_applied": True,
        "predictive_gate_passed": predictive_gate_pass,
        "economic_gate_passed": economic_gate_pass,
        "robustness_gate_fully_evaluated": False,
        "evidence_grade": evidence_grade,
        "pipeline_retuning_performed": False,
        "rsi_reentry_performed": False,
        "panic_state_extension_used": False,
        "manifest_sha256": sha256_file(manifest_path),
        "gate_results_sha256": sha256_file(gate_path),
        "verdict_sha256": sha256_file(verdict_path),
    }
    status_path = args.output_root / "d4_inference_status.json"
    write_json(status_path, status)

    print("Version 2 D4 confirmatory inference and economic gates completed.")
    print(f"Authorized family: BOLLINGER")
    print(f"Mean incremental log loss: {predictive.mean_loss_differential:.9f}")
    print(f"Raw one-sided p-value: {predictive.one_sided_p_value:.6f}")
    print(f"Holm-adjusted p-value: {adjusted['H2_BOLLINGER_DIRECTION']:.6f}")
    print(f"Positive locked subperiods: {positive_subperiods}/3")
    print(f"Predictive gate passed: {predictive_gate_pass}")
    print(f"Mean incremental net return at 10 bps: {primary_economic_interval.mean:.9f}")
    print(f"Economic gate passed: {economic_gate_pass}")
    print(f"Evidence grade: {evidence_grade}")
    print("Pipeline retuning performed: False")
    print("RSI re-entry performed: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
