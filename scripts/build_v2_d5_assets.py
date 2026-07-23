from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shockbridge_signal_validity.v2.robustness_publication import (
    active_confidence_stratification,
    development_component_stability,
    joint_influence_trim_summary,
    leave_one_group_out_summary,
    matched_policy_contributions,
    robustness_classification,
    state_stratification,
)


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Version 2 D5 robustness and publication evidence."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/v2_d5_robustness_publication.json"),
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        default=Path("data/processed/v2/holdout/d3_locked_predictions.csv"),
    )
    parser.add_argument(
        "--pipeline-registry",
        type=Path,
        default=Path(
            "data/processed/v2/development/d2c_frozen_pipeline_registry.json"
        ),
    )
    parser.add_argument(
        "--d2b-outer-results",
        type=Path,
        default=Path("data/processed/v2/development/d2b_outer_fold_results.csv"),
    )
    parser.add_argument(
        "--d2c-component-audit",
        type=Path,
        default=Path(
            "data/processed/v2/development/d2c_component_selection_audit.csv"
        ),
    )
    parser.add_argument(
        "--d4-status",
        type=Path,
        default=Path("outputs/v2/holdout/d4_inference_status.json"),
    )
    parser.add_argument(
        "--d4-gates",
        type=Path,
        default=Path("outputs/v2/holdout/d4_gate_results.json"),
    )
    parser.add_argument(
        "--d4-verdict",
        type=Path,
        default=Path("outputs/v2/holdout/d4_final_evidence_grade.json"),
    )
    parser.add_argument(
        "--d4-predictive",
        type=Path,
        default=Path("data/processed/v2/holdout/d4_predictive_inference.csv"),
    )
    parser.add_argument(
        "--d4-subperiods",
        type=Path,
        default=Path("data/processed/v2/holdout/d4_subperiod_results.csv"),
    )
    parser.add_argument(
        "--d4-costs",
        type=Path,
        default=Path("data/processed/v2/holdout/d4_economic_cost_sensitivity.csv"),
    )
    parser.add_argument(
        "--d4-blocks",
        type=Path,
        default=Path("data/processed/v2/holdout/d4_block_length_sensitivity.csv"),
    )
    parser.add_argument(
        "--d4-months",
        type=Path,
        default=Path("data/processed/v2/holdout/d4_monthly_contribution.csv"),
    )
    parser.add_argument(
        "--d4-calibration",
        type=Path,
        default=Path("data/processed/v2/holdout/d4_calibration_summary.csv"),
    )
    parser.add_argument(
        "--processed-root",
        type=Path,
        default=Path("data/processed/v2/publication"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("outputs/v2/publication"),
    )
    parser.add_argument(
        "--implementation-commit",
        type=str,
        default=None,
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_record(path: Path) -> dict[str, object]:
    return {
        "path": path.resolve().relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def implementation_commit(explicit: str | None) -> str:
    if explicit:
        return explicit
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def save_figure(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, format="svg", bbox_inches="tight")
    plt.close()


def build_figures(
    d4_gates: dict[str, object],
    costs: pd.DataFrame,
    subperiods: pd.DataFrame,
    months: pd.DataFrame,
    component_stability: pd.DataFrame,
    figure_root: Path,
) -> list[Path]:
    generated: list[Path] = []

    predictive = d4_gates["predictive_gate"]
    mean_value = float(predictive["mean_incremental_log_loss"])
    lower = float(predictive["primary_bootstrap_ci_95_lower"])
    upper = float(predictive["primary_bootstrap_ci_95_upper"])
    plt.figure(figsize=(8.5, 3.8))
    plt.errorbar(
        [mean_value],
        [0],
        xerr=[[mean_value - lower], [upper - mean_value]],
        fmt="o",
        capsize=6,
    )
    plt.axvline(0.0, linewidth=1.0)
    plt.yticks([0], ["Frozen Bollinger pipeline"])
    plt.xlabel("Benchmark minus candidate observation log loss")
    plt.title("Version 2 locked predictive evidence")
    path = figure_root / "d5_predictive_interval.svg"
    save_figure(path)
    generated.append(path)

    cost_sorted = costs.sort_values("one_way_cost_bps")
    plt.figure(figsize=(8.5, 4.8))
    plt.errorbar(
        cost_sorted["one_way_cost_bps"],
        cost_sorted["mean_incremental_net_return"],
        yerr=np.vstack(
            [
                cost_sorted["mean_incremental_net_return"]
                - cost_sorted["ci_95_lower"],
                cost_sorted["ci_95_upper"]
                - cost_sorted["mean_incremental_net_return"],
            ]
        ),
        fmt="o-",
        capsize=5,
    )
    plt.axhline(0.0, linewidth=1.0)
    plt.xlabel("One-way transaction cost (basis points)")
    plt.ylabel("Mean candidate minus benchmark net return")
    plt.title("Economic sensitivity with dependence-aware intervals")
    path = figure_root / "d5_cost_sensitivity.svg"
    save_figure(path)
    generated.append(path)

    subperiod_sorted = subperiods.sort_values("holdout_subperiod")
    plt.figure(figsize=(8.5, 4.8))
    plt.bar(
        subperiod_sorted["holdout_subperiod"],
        subperiod_sorted["mean_incremental_log_loss"],
    )
    plt.axhline(0.0, linewidth=1.0)
    plt.xlabel("Locked chronological subperiod")
    plt.ylabel("Mean incremental log-loss contribution")
    plt.title("Chronological consistency of the frozen pipeline")
    path = figure_root / "d5_subperiod_predictive_contribution.svg"
    save_figure(path)
    generated.append(path)

    month_sorted = months.sort_values("calendar_month")
    plt.figure(figsize=(10.5, 5.0))
    plt.bar(
        month_sorted["calendar_month"],
        month_sorted["cumulative_incremental_net_return"],
    )
    plt.axhline(0.0, linewidth=1.0)
    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Calendar month")
    plt.ylabel("Cumulative candidate minus benchmark net return")
    plt.title("Monthly contribution concentration at 10 basis points")
    path = figure_root / "d5_monthly_economic_contribution.svg"
    save_figure(path)
    generated.append(path)

    component_sorted = component_stability.sort_values(
        ["modal_share", "component"],
        ascending=[True, True],
    )
    plt.figure(figsize=(9.5, 6.0))
    plt.barh(component_sorted["component"], component_sorted["modal_share"])
    plt.axvline(0.8, linewidth=1.0)
    plt.xlim(0.0, 1.05)
    plt.xlabel("Modal share across five outer development folds")
    plt.title("Development component stability")
    path = figure_root / "d5_development_component_stability.svg"
    save_figure(path)
    generated.append(path)

    return generated


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    d4_status = json.loads(args.d4_status.read_text(encoding="utf-8"))
    d4_gates = json.loads(args.d4_gates.read_text(encoding="utf-8"))
    d4_verdict = json.loads(args.d4_verdict.read_text(encoding="utf-8"))
    pipeline_registry = json.loads(
        args.pipeline_registry.read_text(encoding="utf-8")
    )

    expected_hash = str(config["expected_pipeline_hash"])
    expected_grade = str(config["expected_d4_evidence_grade"])

    require(d4_status.get("status") == "PASS", "D5 requires a completed D4 checkpoint.")
    require(
        d4_status.get("evidence_grade") == expected_grade,
        "D4 evidence grade changed before D5.",
    )
    require(
        d4_status.get("predictive_gate_passed") is False,
        "D5 expected the frozen predictive gate failure.",
    )
    require(
        d4_status.get("economic_gate_passed") is False,
        "D5 expected the frozen economic gate failure.",
    )
    require(
        d4_status.get("robustness_gate_fully_evaluated") is False,
        "D4 already reports robustness completion.",
    )
    require(
        d4_status.get("pipeline_hash") == expected_hash,
        "D4 status pipeline hash changed.",
    )
    require(
        d4_gates.get("pipeline_hash") == expected_hash,
        "D4 gate pipeline hash changed.",
    )
    require(
        d4_verdict.get("pipeline_hash") == expected_hash,
        "D4 verdict pipeline hash changed.",
    )
    require(
        d4_verdict.get("evidence_grade") == expected_grade,
        "D4 verdict grade changed.",
    )
    require(
        d4_status.get("pipeline_retuning_performed") is False
        and d4_status.get("rsi_reentry_performed") is False
        and d4_status.get("panic_state_extension_used") is False,
        "D4 governance flags prohibit D5 execution.",
    )

    pipelines = pipeline_registry.get("frozen_pipelines", [])
    require(
        len(pipelines) == 1
        and pipelines[0].get("signal_family") == "bollinger"
        and pipelines[0].get("pipeline_hash") == expected_hash,
        "D5 requires the single frozen Bollinger pipeline.",
    )
    pipeline = pipelines[0]

    predictions = pd.read_csv(args.predictions)
    predictions["Timestamp"] = pd.to_datetime(
        predictions["Timestamp"], utc=True, errors="raise"
    )
    predictions["target_timestamp"] = pd.to_datetime(
        predictions["target_timestamp"], utc=True, errors="raise"
    )
    require(
        len(predictions) == int(d4_status["prediction_rows"]),
        "D3 prediction count changed before D5.",
    )
    require(
        set(predictions["signal_family"].astype(str)) == {"bollinger"},
        "D5 input contains an unauthorized signal family.",
    )
    require(
        set(predictions["pipeline_hash"].astype(str)) == {expected_hash},
        "D5 input contains an unauthorized pipeline hash.",
    )

    threshold = float(pipeline["decision_probability_distance_threshold"])
    primary_cost = float(config["primary_one_way_cost_bps"])
    policy = matched_policy_contributions(
        predictions,
        probability_distance_threshold=threshold,
        one_way_cost_bps=primary_cost,
    )
    policy["calendar_month"] = policy["Timestamp"].dt.strftime("%Y-%m")

    d4_predictive = pd.read_csv(args.d4_predictive)
    d4_subperiods = pd.read_csv(args.d4_subperiods)
    d4_costs = pd.read_csv(args.d4_costs)
    d4_blocks = pd.read_csv(args.d4_blocks)
    d4_months = pd.read_csv(args.d4_months)
    d4_calibration = pd.read_csv(args.d4_calibration)
    d2b_outer = pd.read_csv(args.d2b_outer_results)
    d2c_component_audit = pd.read_csv(args.d2c_component_audit)

    leave_month = leave_one_group_out_summary(
        policy,
        group_column="calendar_month",
        predictive_column="incremental_observation_log_loss",
        economic_column="incremental_net_return",
    )
    influence = joint_influence_trim_summary(
        policy,
        predictive_column="incremental_observation_log_loss",
        economic_column="incremental_net_return",
        trim_fractions=config["influence_trim_fractions"],
    )
    states = state_stratification(
        policy,
        minimum_interpretable_rows=int(config["minimum_state_rows"]),
    )
    confidence = active_confidence_stratification(
        policy,
        quantiles=int(config["active_confidence_quantiles"]),
    )
    components = development_component_stability(
        d2b_outer,
        signal_family="bollinger",
        horizon_candles=int(pipeline["horizon_candles"]),
    )

    predictive_blocks = d4_blocks.loc[
        d4_blocks["evidence_type"].eq("predictive_loss_differential")
    ]
    economic_blocks = d4_blocks.loc[
        d4_blocks["evidence_type"].eq("economic_incremental_net_return_10bps")
    ]
    overall_calibration = d4_calibration.loc[
        d4_calibration["segment"].eq("OVERALL")
    ].iloc[0]
    subperiod_calibration = d4_calibration.loc[
        ~d4_calibration["segment"].eq("OVERALL")
    ]

    exact_spec_row = components.loc[
        components["component"].eq("signal_specification")
    ].iloc[0]
    model_family_row = components.loc[
        components["component"].eq("model_family")
    ].iloc[0]
    state_stress_rows = int(
        states.loc[states["state_label"].astype(str).eq("stress"), "rows"].sum()
    )

    robustness_rows = [
        {
            "diagnostic": "confirmatory_multiplicity",
            "diagnostic_status": "FAIL",
            "observed_value": float(
                d4_gates["predictive_gate"]["holm_adjusted_p_value"]
            ),
            "reference_value": float(config["familywise_alpha"]),
            "interpretation": "Holm-adjusted p-value remained above alpha.",
        },
        {
            "diagnostic": "predictive_bootstrap_lower_bounds",
            "diagnostic_status": (
                "PASS"
                if bool(predictive_blocks["conclusion_positive_lower_bound"].all())
                else "FAIL"
            ),
            "observed_value": float(predictive_blocks["ci_95_lower"].min()),
            "reference_value": 0.0,
            "interpretation": "All registered predictive block-length intervals must exclude zero.",
        },
        {
            "diagnostic": "economic_bootstrap_lower_bounds",
            "diagnostic_status": (
                "PASS"
                if bool(economic_blocks["conclusion_positive_lower_bound"].all())
                else "FAIL"
            ),
            "observed_value": float(economic_blocks["ci_95_lower"].min()),
            "reference_value": 0.0,
            "interpretation": "All registered economic block-length intervals must exclude zero.",
        },
        {
            "diagnostic": "cost_sensitivity_mean_sign",
            "diagnostic_status": (
                "PASS"
                if bool((d4_costs["mean_incremental_net_return"] > 0.0).all())
                else "CAUTION"
            ),
            "observed_value": float(
                (d4_costs["mean_incremental_net_return"] > 0.0).mean()
            ),
            "reference_value": 1.0,
            "interpretation": "Mean incremental net return sign across 5, 10 and 20 bps.",
        },
        {
            "diagnostic": "chronological_subperiod_sign",
            "diagnostic_status": (
                "PASS"
                if int(
                    d4_subperiods["predictive_contribution_positive"]
                    .astype(str)
                    .str.lower()
                    .eq("true")
                    .sum()
                )
                >= 2
                else "FAIL"
            ),
            "observed_value": float(
                d4_subperiods["predictive_contribution_positive"]
                .astype(str)
                .str.lower()
                .eq("true")
                .sum()
            ),
            "reference_value": 2.0,
            "interpretation": "At least two of three locked subperiods were positive.",
        },
        {
            "diagnostic": "all_subperiods_positive",
            "diagnostic_status": (
                "PASS"
                if bool(
                    d4_subperiods["predictive_contribution_positive"]
                    .astype(str)
                    .str.lower()
                    .eq("true")
                    .all()
                )
                else "CAUTION"
            ),
            "observed_value": float(
                d4_subperiods["predictive_contribution_positive"]
                .astype(str)
                .str.lower()
                .eq("true")
                .mean()
            ),
            "reference_value": 1.0,
            "interpretation": "One locked subperiod had non-positive predictive contribution.",
        },
        {
            "diagnostic": "overall_calibration_non_dominance",
            "diagnostic_status": (
                "PASS"
                if float(overall_calibration["candidate_minus_benchmark_brier"])
                <= 0.001
                and float(overall_calibration["candidate_minus_benchmark_ece"])
                <= 0.01
                else "FAIL"
            ),
            "observed_value": float(
                overall_calibration["candidate_minus_benchmark_brier"]
            ),
            "reference_value": 0.001,
            "interpretation": "Overall Brier and calibration-error controls remained within bounds.",
        },
        {
            "diagnostic": "subperiod_calibration_consistency",
            "diagnostic_status": (
                "PASS"
                if bool(
                    (
                        subperiod_calibration[
                            "candidate_minus_benchmark_brier"
                        ]
                        <= 0.0
                    ).all()
                )
                else "CAUTION"
            ),
            "observed_value": float(
                subperiod_calibration[
                    "candidate_minus_benchmark_brier"
                ].max()
            ),
            "reference_value": 0.0,
            "interpretation": "Candidate Brier performance was not uniformly better by subperiod.",
        },
        {
            "diagnostic": "monthly_positive_concentration",
            "diagnostic_status": (
                "PASS"
                if bool(d4_gates["concentration_diagnostic"]["passed"])
                else "FAIL"
            ),
            "observed_value": float(
                d4_gates["concentration_diagnostic"][
                    "maximum_single_positive_month_share"
                ]
            ),
            "reference_value": float(
                d4_gates["concentration_diagnostic"]["threshold"]
            ),
            "interpretation": "No single positive month exceeded the frozen concentration threshold.",
        },
        {
            "diagnostic": "leave_one_month_out_mean_sign",
            "diagnostic_status": (
                "PASS"
                if bool(
                    leave_month["predictive_mean_positive"].all()
                    and leave_month["economic_mean_positive"].all()
                )
                else "CAUTION"
            ),
            "observed_value": float(
                min(
                    leave_month["mean_incremental_log_loss"].min(),
                    leave_month["mean_incremental_net_return_10bps"].min(),
                )
            ),
            "reference_value": 0.0,
            "interpretation": "Favourable means persisted after excluding each calendar month.",
        },
        {
            "diagnostic": "joint_tail_trim_mean_sign",
            "diagnostic_status": (
                "PASS"
                if bool(
                    influence["predictive_mean_positive"].all()
                    and influence["economic_mean_positive"].all()
                )
                else "CAUTION"
            ),
            "observed_value": float(
                influence.loc[
                    influence["joint_tail_trim_fraction"].eq(
                        max(config["influence_trim_fractions"])
                    ),
                    "mean_incremental_log_loss",
                ].iloc[0]
            ),
            "reference_value": 0.0,
            "interpretation": "Favourable means persisted after registered joint tail trimming.",
        },
        {
            "diagnostic": "development_model_family_stability",
            "diagnostic_status": (
                "PASS"
                if float(model_family_row["modal_share"]) >= 0.80
                else "CAUTION"
            ),
            "observed_value": float(model_family_row["modal_share"]),
            "reference_value": 0.80,
            "interpretation": "Model-family selection stability across outer development folds.",
        },
        {
            "diagnostic": "development_exact_signal_specification_stability",
            "diagnostic_status": (
                "PASS"
                if float(exact_spec_row["modal_share"]) >= 0.80
                else "CAUTION"
            ),
            "observed_value": float(exact_spec_row["modal_share"]),
            "reference_value": 0.80,
            "interpretation": "Exact signal specification was diffuse across development folds.",
        },
        {
            "diagnostic": "stress_state_sample_sufficiency",
            "diagnostic_status": (
                "PASS"
                if state_stress_rows >= int(config["minimum_state_rows"])
                else "CAUTION"
            ),
            "observed_value": float(state_stress_rows),
            "reference_value": float(config["minimum_state_rows"]),
            "interpretation": "Stress-state evidence is descriptive and too small for a panic claim.",
        },
        {
            "diagnostic": "active_confidence_economic_consistency",
            "diagnostic_status": (
                "PASS"
                if bool(
                    (
                        confidence["mean_incremental_net_return_10bps"] > 0.0
                    ).all()
                )
                else "CAUTION"
            ),
            "observed_value": float(
                confidence["mean_incremental_net_return_10bps"].min()
            ),
            "reference_value": 0.0,
            "interpretation": "Economic contribution was not positive across active-confidence strata.",
        },
    ]
    robustness_matrix = pd.DataFrame(robustness_rows)
    robustness_matrix["confirmatory_effect"] = (
        "NO_UPGRADE_OR_REVERSAL_PERMITTED"
    )
    classification = robustness_classification(robustness_matrix)

    args.processed_root.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)
    figure_root = args.output_root / "figures"

    tables = {
        "d5_leave_one_month_out.csv": leave_month,
        "d5_influence_trim_sensitivity.csv": influence,
        "d5_state_stratification.csv": states,
        "d5_active_confidence_stratification.csv": confidence,
        "d5_development_component_stability.csv": components,
        "d5_robustness_matrix.csv": robustness_matrix,
    }
    generated_paths: list[Path] = []
    for name, table in tables.items():
        path = args.processed_root / name
        table.to_csv(path, index=False)
        generated_paths.append(path)

    figure_paths = build_figures(
        d4_gates=d4_gates,
        costs=d4_costs,
        subperiods=d4_subperiods,
        months=d4_months,
        component_stability=components,
        figure_root=figure_root,
    )
    generated_paths.extend(figure_paths)

    robustness_results = {
        "checkpoint": "V2_D5_ROBUSTNESS_AND_PUBLICATION",
        "signal_family": "bollinger",
        "pipeline_hash": expected_hash,
        "d4_evidence_grade_preserved": expected_grade,
        "robustness_determination": classification.determination,
        "fragility_class": classification.fragility_class,
        "diagnostic_counts": {
            "pass": classification.favourable_diagnostics,
            "caution": classification.caution_diagnostics,
            "fail": classification.failed_diagnostics,
        },
        "positive_mean_not_sufficient_for_establishment": True,
        "robustness_supports_primary_case_upgrade": False,
        "external_replication_triggered": False,
        "external_replication_status": "NOT_TRIGGERED_PRIMARY_CONFIRMATORY_GATE_FAILED",
        "state_diagnostic_status": "DESCRIPTIVE_ONLY",
        "panic_state_claim_permitted": False,
        "pipeline_retuning_performed": False,
        "rsi_reentry_performed": False,
        "panic_state_extension_used": False,
    }
    robustness_path = args.output_root / "d5_robustness_results.json"
    write_json(robustness_path, robustness_results)
    generated_paths.append(robustness_path)

    final_verdict = {
        "checkpoint": "V2_D5_FINAL_PRIMARY_CASE_DETERMINATION",
        "version": "2.0",
        "primary_case": "BINANCE_SOL_USDT_4H",
        "rsi": {
            "status": "NO_PIPELINE_ADMITTED",
            "holdout_evaluated": False,
            "interpretation": (
                "No RSI pipeline satisfied the frozen development-admission controls; "
                "RSI did not enter the methodology-locked evaluation."
            ),
        },
        "bollinger": {
            "status": "NO_INCREMENTAL_EVIDENCE",
            "pipeline_hash": expected_hash,
            "holdout_evaluated": True,
            "mean_incremental_log_loss": float(
                d4_gates["predictive_gate"]["mean_incremental_log_loss"]
            ),
            "raw_one_sided_p_value": float(
                d4_gates["predictive_gate"]["raw_one_sided_p_value"]
            ),
            "holm_adjusted_p_value": float(
                d4_gates["predictive_gate"]["holm_adjusted_p_value"]
            ),
            "positive_locked_subperiods": int(
                d4_gates["predictive_gate"]["positive_subperiods"]
            ),
            "mean_incremental_net_return_10bps": float(
                d4_gates["economic_gate"]["mean_incremental_net_return"]
            ),
            "economic_ci_95_lower": float(
                d4_gates["economic_gate"]["ci_95_lower"]
            ),
            "predictive_gate_passed": False,
            "economic_gate_passed": False,
            "robustness_diagnostics_completed": True,
        },
        "primary_case_established": False,
        "evidence_grade": "NO_INCREMENTAL_EVIDENCE",
        "determination": (
            "Stable incremental value was not established for RSI or Bollinger "
            "under the frozen Version 2 primary-case protocol."
        ),
        "favourable_evidence_boundary": (
            "The frozen Bollinger pipeline produced favourable average predictive "
            "and economic contributions in parts of the locked sample, but the "
            "evidence did not survive the complete multiplicity-adjusted and "
            "dependence-aware confidence requirements."
        ),
        "external_replication_status": (
            "NOT_TRIGGERED_PRIMARY_CONFIRMATORY_GATE_FAILED"
        ),
        "monitoring_ready": False,
        "operational_deployment_supported": False,
        "pipeline_retuning_performed": False,
        "rsi_reentry_performed": False,
        "panic_state_extension_used": False,
        "v2_1_scope": (
            "SEPARATE_PRE_SPECIFIED_SIGNAL_GOVERNANCE_STUDY_NO_EFFECT_ON_V2"
        ),
    }
    verdict_path = args.output_root / "v2_final_evidence_grade.json"
    write_json(verdict_path, final_verdict)
    generated_paths.append(verdict_path)

    model_card = f"""# Frozen Bollinger Pipeline Model Card

## Model identity

- Signal family: Bollinger Bands
- Frozen pipeline hash: `{expected_hash}`
- Signal specification: `{pipeline["signal_specification"]["signal_spec_id"]}`
- Interpretation: `{pipeline["signal_specification"]["interpretation"]}`
- Model family: `{pipeline["structural_pipeline"]["model_family"]}`
- Estimation window: `{pipeline["structural_pipeline"]["window_scheme"]}`
- Soft state conditioning: `{pipeline["structural_pipeline"]["regime_conditioned"]}`
- Calibration: `{pipeline["calibration_method"]}`
- Abstention distance: `{threshold:.2f}`
- Horizon: `{pipeline["horizon_hours"]}` hours

## Development admission

The family passed the D2C development-admission controls and was frozen before
the methodology-locked period was accessed. Development admission was not a
claim of final predictive or economic validity.

## Locked-evaluation determination

- Mean incremental log loss: `{d4_gates["predictive_gate"]["mean_incremental_log_loss"]:.9f}`
- Raw one-sided p-value: `{d4_gates["predictive_gate"]["raw_one_sided_p_value"]:.6f}`
- Holm-adjusted p-value: `{d4_gates["predictive_gate"]["holm_adjusted_p_value"]:.6f}`
- Positive locked subperiods: `{d4_gates["predictive_gate"]["positive_subperiods"]} of 3`
- Mean incremental net return at 10 bps: `{d4_gates["economic_gate"]["mean_incremental_net_return"]:.9f}`
- Economic 95% lower bound: `{d4_gates["economic_gate"]["ci_95_lower"]:.9f}`
- Final evidence grade: `NO_INCREMENTAL_EVIDENCE`

## Model boundaries

The pipeline is not approved for operational deployment. The locked evidence
does not support a claim of stable incremental value. Positive average
contributions do not override multiplicity-adjusted inference, bootstrap
uncertainty, chronological instability, or economic confidence requirements.

The existing filtered stress state is descriptive. It does not establish
investor panic, liquidity causality, or liquidation causality. Those mechanisms
belong to the separately frozen V2.1 research programme.

## Governance

- Pipeline retuning after D3: prohibited and not performed.
- RSI re-entry: prohibited and not performed.
- Panic-state conditioning in V2: prohibited and not performed.
- Monitoring admission: not granted.
"""
    model_card_path = args.output_root / "V2_FROZEN_BOLLINGER_MODEL_CARD.md"
    model_card_path.write_text(model_card, encoding="utf-8")
    generated_paths.append(model_card_path)

    report = f"""# Version 2 Final Evidence Report

## Executive determination

Version 2 did not establish stable incremental value for either confirmatory
technical-signal family.

RSI did not pass development admission and therefore did not enter the locked
evaluation. The sole admitted Bollinger pipeline produced a positive average
benchmark-relative loss differential and favourable mean economic contribution,
but the full confirmatory predictive and economic gates failed.

The immutable Version 2 evidence grade is:

> `NO_INCREMENTAL_EVIDENCE`

## Confirmatory evidence

| Measure | Result |
|---|---:|
| Bollinger mean incremental log loss | {d4_gates["predictive_gate"]["mean_incremental_log_loss"]:.9f} |
| Raw one-sided p-value | {d4_gates["predictive_gate"]["raw_one_sided_p_value"]:.6f} |
| Holm-adjusted p-value | {d4_gates["predictive_gate"]["holm_adjusted_p_value"]:.6f} |
| Primary predictive bootstrap lower bound | {d4_gates["predictive_gate"]["primary_bootstrap_ci_95_lower"]:.9f} |
| Positive locked subperiods | {d4_gates["predictive_gate"]["positive_subperiods"]} of 3 |
| Mean incremental net return at 10 bps | {d4_gates["economic_gate"]["mean_incremental_net_return"]:.9f} |
| Economic 95% lower bound | {d4_gates["economic_gate"]["ci_95_lower"]:.9f} |
| Candidate coverage | {d4_gates["economic_gate"]["candidate_coverage"]:.2%} |
| Candidate decisions | {d4_gates["economic_gate"]["candidate_nonzero_decisions"]} |

## Robustness and concentration

The D5 diagnostics found that favourable means were not driven by a single
calendar month and remained positive under leave-one-month-out and registered
joint-tail-trimming checks. Mean economic contribution also remained positive
at 5, 10 and 20 basis points.

These favourable diagnostics do not establish validity. Predictive and
economic bootstrap lower bounds crossed zero across every registered block
length, the Holm-adjusted p-value exceeded 0.05, one locked subperiod had a
negative predictive contribution, exact signal-parameter selection was diffuse
across development folds, and active-confidence strata did not show uniform
economic contribution.

Robustness determination:

> `{classification.determination}`

Fragility classification:

> `{classification.fragility_class}`

## State evidence boundary

The locked sample contains only {state_stress_rows} observations labelled as
stress by the existing filtered-state engine. This is insufficient for a
confirmatory panic interpretation. State-stratified outputs are descriptive
only and cannot change the Version 2 verdict.

## Institutional interpretation

The evidence supports a governance conclusion rather than a trading claim:

> Technical-signal use should not be authorized merely because average
> contributions are favourable. Establishment requires multiplicity-adjusted,
> dependence-aware, chronologically stable and economically bounded evidence.

Version 2 therefore closes with no RSI admission, no established Bollinger
incremental value, no operational deployment authorization, and no monitoring
status.

## V2.1 separation

V2.1 will test whether independently defined panic-consistent, liquidity-stress
or liquidation regimes can govern signal interpretation, degradation,
suspension or revalidation. It cannot alter any Version 2 decision.
"""
    report_path = args.output_root / "V2_FINAL_EVIDENCE_REPORT.md"
    report_path.write_text(report, encoding="utf-8")
    generated_paths.append(report_path)

    impl_commit = implementation_commit(args.implementation_commit)
    manifest = {
        "checkpoint": "V2_D5_ROBUSTNESS_AND_PUBLICATION",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "implementation_commit": impl_commit,
        "source_d4_evidence_commit": config["expected_parent_commit"],
        "source_d4_tag": config["expected_parent_tag"],
        "pipeline_hash": expected_hash,
        "prediction_rows": int(len(predictions)),
        "d3_predictions_sha256": sha256_file(args.predictions),
        "d4_status_sha256": sha256_file(args.d4_status),
        "d4_gate_results_sha256": sha256_file(args.d4_gates),
        "d4_verdict_sha256": sha256_file(args.d4_verdict),
        "robustness_diagnostics_completed": True,
        "publication_evidence_completed": True,
        "final_evidence_grade": "NO_INCREMENTAL_EVIDENCE",
        "primary_case_established": False,
        "external_replication_triggered": False,
        "pipeline_retuning_performed": False,
        "rsi_reentry_performed": False,
        "panic_state_extension_used": False,
        "files": [file_record(path) for path in generated_paths],
    }
    manifest_path = args.processed_root / "d5_publication_manifest.json"
    write_json(manifest_path, manifest)

    status = {
        "status": "PASS",
        "checkpoint": manifest["checkpoint"],
        "implementation_commit": impl_commit,
        "pipeline_hash": expected_hash,
        "prediction_rows": int(len(predictions)),
        "robustness_diagnostics_completed": True,
        "publication_evidence_completed": True,
        "robustness_determination": classification.determination,
        "fragility_class": classification.fragility_class,
        "final_evidence_grade": "NO_INCREMENTAL_EVIDENCE",
        "primary_case_established": False,
        "external_replication_triggered": False,
        "pipeline_retuning_performed": False,
        "rsi_reentry_performed": False,
        "panic_state_extension_used": False,
        "manifest_sha256": sha256_file(manifest_path),
        "robustness_results_sha256": sha256_file(robustness_path),
        "final_verdict_sha256": sha256_file(verdict_path),
    }
    status_path = args.output_root / "d5_publication_status.json"
    write_json(status_path, status)

    print("Version 2 D5 robustness and publication evidence completed.")
    print(f"Prediction rows: {len(predictions):,}")
    print(
        "Robustness determination: "
        f"{classification.determination}"
    )
    print(f"Fragility class: {classification.fragility_class}")
    print("Final evidence grade: NO_INCREMENTAL_EVIDENCE")
    print("Primary case established: False")
    print("External replication triggered: False")
    print("Pipeline retuning performed: False")
    print("RSI re-entry performed: False")
    print("V2.1 panic-state extension used: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
