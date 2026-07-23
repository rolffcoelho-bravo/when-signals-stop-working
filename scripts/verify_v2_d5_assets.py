from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    config_path = ROOT / "configs/v2_d5_robustness_publication.json"
    processed_root = ROOT / "data/processed/v2/publication"
    output_root = ROOT / "outputs/v2/publication"

    config = json.loads(config_path.read_text(encoding="utf-8"))
    d4_status_path = ROOT / "outputs/v2/holdout/d4_inference_status.json"
    d4_gates_path = ROOT / "outputs/v2/holdout/d4_gate_results.json"
    d4_verdict_path = ROOT / "outputs/v2/holdout/d4_final_evidence_grade.json"
    predictions_path = ROOT / "data/processed/v2/holdout/d3_locked_predictions.csv"

    d4_status = json.loads(d4_status_path.read_text(encoding="utf-8"))
    d4_gates = json.loads(d4_gates_path.read_text(encoding="utf-8"))
    d4_verdict = json.loads(d4_verdict_path.read_text(encoding="utf-8"))
    manifest_path = processed_root / "d5_publication_manifest.json"
    status_path = output_root / "d5_publication_status.json"
    robustness_path = output_root / "d5_robustness_results.json"
    verdict_path = output_root / "v2_final_evidence_grade.json"

    for path in (
        manifest_path,
        status_path,
        robustness_path,
        verdict_path,
    ):
        require(path.exists(), f"Missing D5 asset: {path.relative_to(ROOT)}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    status = json.loads(status_path.read_text(encoding="utf-8"))
    robustness = json.loads(robustness_path.read_text(encoding="utf-8"))
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))

    expected_hash = str(config["expected_pipeline_hash"])
    expected_grade = str(config["expected_d4_evidence_grade"])

    require(status.get("status") == "PASS", "D5 status is not PASS.")
    require(
        status.get("checkpoint") == "V2_D5_ROBUSTNESS_AND_PUBLICATION",
        "Unexpected D5 checkpoint.",
    )
    require(
        status.get("pipeline_hash") == expected_hash,
        "D5 status pipeline hash changed.",
    )
    require(
        int(status.get("prediction_rows", -1)) == int(d4_status["prediction_rows"]),
        "D5 prediction count does not match D4.",
    )
    require(
        int(status["prediction_rows"]) == len(pd.read_csv(predictions_path)),
        "D5 prediction count does not match D3 predictions.",
    )
    require(
        status.get("final_evidence_grade") == expected_grade,
        "D5 changed the frozen D4 evidence grade.",
    )
    require(
        status.get("primary_case_established") is False,
        "D5 incorrectly established the primary case.",
    )
    require(
        status.get("robustness_diagnostics_completed") is True
        and status.get("publication_evidence_completed") is True,
        "D5 completion flags are invalid.",
    )
    require(
        status.get("external_replication_triggered") is False,
        "D5 incorrectly triggered external replication.",
    )
    require(
        status.get("pipeline_retuning_performed") is False
        and status.get("rsi_reentry_performed") is False
        and status.get("panic_state_extension_used") is False,
        "D5 governance flags are invalid.",
    )

    require(
        d4_status.get("evidence_grade") == expected_grade
        and d4_status.get("predictive_gate_passed") is False
        and d4_status.get("economic_gate_passed") is False,
        "The frozen D4 evidence changed before D5 verification.",
    )
    require(
        d4_status.get("pipeline_hash") == expected_hash
        and d4_gates.get("pipeline_hash") == expected_hash
        and d4_verdict.get("pipeline_hash") == expected_hash,
        "A frozen pipeline hash changed.",
    )
    require(
        d4_status.get("robustness_gate_fully_evaluated") is False,
        "D4 was retroactively modified to report D5 robustness.",
    )

    require(
        manifest.get("source_d4_evidence_commit")
        == config["expected_parent_commit"],
        "D5 manifest has the wrong D4 parent.",
    )
    require(
        manifest.get("source_d4_tag") == config["expected_parent_tag"],
        "D5 manifest has the wrong D4 tag.",
    )
    require(
        manifest.get("d3_predictions_sha256") == sha256_file(predictions_path),
        "D3 predictions changed.",
    )
    require(
        manifest.get("d4_status_sha256") == sha256_file(d4_status_path),
        "D4 status changed.",
    )
    require(
        manifest.get("d4_gate_results_sha256") == sha256_file(d4_gates_path),
        "D4 gate results changed.",
    )
    require(
        manifest.get("d4_verdict_sha256") == sha256_file(d4_verdict_path),
        "D4 verdict changed.",
    )

    for record in manifest.get("files", []):
        path = ROOT / str(record["path"])
        require(path.exists(), f"Manifest file missing: {record['path']}")
        require(
            path.stat().st_size == int(record["bytes"]),
            f"Manifest byte count mismatch: {record['path']}",
        )
        require(
            sha256_file(path) == record["sha256"],
            f"Manifest checksum mismatch: {record['path']}",
        )

    require(
        status.get("manifest_sha256") == sha256_file(manifest_path),
        "D5 manifest hash mismatch.",
    )
    require(
        status.get("robustness_results_sha256") == sha256_file(robustness_path),
        "D5 robustness hash mismatch.",
    )
    require(
        status.get("final_verdict_sha256") == sha256_file(verdict_path),
        "D5 verdict hash mismatch.",
    )

    leave_month = pd.read_csv(processed_root / "d5_leave_one_month_out.csv")
    influence = pd.read_csv(processed_root / "d5_influence_trim_sensitivity.csv")
    states = pd.read_csv(processed_root / "d5_state_stratification.csv")
    confidence = pd.read_csv(
        processed_root / "d5_active_confidence_stratification.csv"
    )
    components = pd.read_csv(
        processed_root / "d5_development_component_stability.csv"
    )
    matrix = pd.read_csv(processed_root / "d5_robustness_matrix.csv")

    predictions = pd.read_csv(predictions_path)
    expected_months = pd.to_datetime(
        predictions["Timestamp"], utc=True, errors="raise"
    ).dt.strftime("%Y-%m").nunique()
    require(
        len(leave_month) == int(expected_months),
        "Leave-one-month-out table has the wrong row count.",
    )
    require(
        leave_month["excluded_group"].nunique() == int(expected_months),
        "Leave-one-month-out months are not unique.",
    )
    require(
        bool(leave_month["predictive_mean_positive"].all())
        and bool(leave_month["economic_mean_positive"].all()),
        "D5 leave-one-month-out signs do not match the locked evidence.",
    )

    require(
        len(influence) == len(config["influence_trim_fractions"]),
        "Influence table has the wrong row count.",
    )
    require(
        sorted(influence["joint_tail_trim_fraction"].round(6).tolist())
        == sorted(round(float(x), 6) for x in config["influence_trim_fractions"]),
        "Influence trim fractions changed.",
    )
    require(
        bool(influence["predictive_mean_positive"].all())
        and bool(influence["economic_mean_positive"].all()),
        "D5 influence signs do not match the locked evidence.",
    )

    require(
        int(states["rows"].sum()) == int(status["prediction_rows"]),
        "State-stratification rows do not reconcile.",
    )
    require(
        set(states["confirmatory_effect"].astype(str))
        == {"NONE_DIAGNOSTIC_ONLY"},
        "State diagnostics received confirmatory effect.",
    )
    require(
        int(confidence["rows"].sum())
        == int(d4_gates["economic_gate"]["candidate_nonzero_decisions"]),
        "Active-confidence rows do not reconcile to candidate decisions.",
    )
    require(
        set(confidence["confirmatory_effect"].astype(str))
        == {"NONE_DIAGNOSTIC_ONLY"},
        "Confidence diagnostics received confirmatory effect.",
    )

    require(
        set(components["component"].astype(str))
        == {
            "model_family",
            "window_scheme",
            "regime_conditioning",
            "calibration_method",
            "decision_threshold",
            "signal_specification",
            "signal_period",
            "signal_width",
            "signal_interpretation",
        },
        "Development-component inventory is incomplete.",
    )
    require(
        not bool(components["holdout_reexecution_performed"].any()),
        "D5 reexecuted alternative pipelines on holdout.",
    )

    required_diagnostics = {
        "confirmatory_multiplicity",
        "predictive_bootstrap_lower_bounds",
        "economic_bootstrap_lower_bounds",
        "cost_sensitivity_mean_sign",
        "chronological_subperiod_sign",
        "all_subperiods_positive",
        "overall_calibration_non_dominance",
        "subperiod_calibration_consistency",
        "monthly_positive_concentration",
        "leave_one_month_out_mean_sign",
        "joint_tail_trim_mean_sign",
        "development_model_family_stability",
        "development_exact_signal_specification_stability",
        "stress_state_sample_sufficiency",
        "active_confidence_economic_consistency",
    }
    require(
        set(matrix["diagnostic"].astype(str)) == required_diagnostics,
        "Robustness matrix is incomplete.",
    )
    require(
        set(matrix["confirmatory_effect"].astype(str))
        == {"NO_UPGRADE_OR_REVERSAL_PERMITTED"},
        "D5 diagnostics were allowed to alter the confirmatory verdict.",
    )
    require(
        matrix.loc[
            matrix["diagnostic"].eq("confirmatory_multiplicity"),
            "diagnostic_status",
        ].iloc[0]
        == "FAIL",
        "D5 did not preserve the multiplicity failure.",
    )
    require(
        matrix.loc[
            matrix["diagnostic"].eq("predictive_bootstrap_lower_bounds"),
            "diagnostic_status",
        ].iloc[0]
        == "FAIL",
        "D5 did not preserve predictive bootstrap uncertainty.",
    )
    require(
        matrix.loc[
            matrix["diagnostic"].eq("economic_bootstrap_lower_bounds"),
            "diagnostic_status",
        ].iloc[0]
        == "FAIL",
        "D5 did not preserve economic bootstrap uncertainty.",
    )

    require(
        robustness.get("d4_evidence_grade_preserved") == expected_grade,
        "D5 robustness results changed the D4 grade.",
    )
    require(
        robustness.get("robustness_supports_primary_case_upgrade") is False,
        "D5 incorrectly supports a primary-case upgrade.",
    )
    require(
        robustness.get("panic_state_claim_permitted") is False
        and robustness.get("state_diagnostic_status") == "DESCRIPTIVE_ONLY",
        "D5 made an unauthorized panic-state claim.",
    )

    require(
        verdict.get("evidence_grade") == expected_grade,
        "Final V2 verdict changed the evidence grade.",
    )
    require(
        verdict.get("primary_case_established") is False,
        "Final V2 verdict incorrectly establishes the primary case.",
    )
    require(
        verdict["rsi"]["status"] == "NO_PIPELINE_ADMITTED",
        "Final V2 verdict changed the RSI decision.",
    )
    require(
        verdict["bollinger"]["status"] == "NO_INCREMENTAL_EVIDENCE",
        "Final V2 verdict changed the Bollinger decision.",
    )
    require(
        verdict.get("pipeline_retuning_performed") is False
        and verdict.get("rsi_reentry_performed") is False
        and verdict.get("panic_state_extension_used") is False,
        "Final V2 verdict has invalid governance flags.",
    )

    figure_root = output_root / "figures"
    expected_figures = {
        "d5_predictive_interval.svg",
        "d5_cost_sensitivity.svg",
        "d5_subperiod_predictive_contribution.svg",
        "d5_monthly_economic_contribution.svg",
        "d5_development_component_stability.svg",
    }
    require(
        {path.name for path in figure_root.glob("*.svg")} == expected_figures,
        "D5 publication figure set is incomplete.",
    )
    for figure in figure_root.glob("*.svg"):
        text = figure.read_text(encoding="utf-8")
        require("<svg" in text and figure.stat().st_size > 1000, f"Invalid SVG: {figure}")

    report = (output_root / "V2_FINAL_EVIDENCE_REPORT.md").read_text(
        encoding="utf-8"
    )
    card = (output_root / "V2_FROZEN_BOLLINGER_MODEL_CARD.md").read_text(
        encoding="utf-8"
    )
    require(
        "`NO_INCREMENTAL_EVIDENCE`" in report
        and "V2.1 separation" in report,
        "Final evidence report is incomplete.",
    )
    require(
        expected_hash in card
        and "not approved for operational deployment" in card,
        "Frozen model card is incomplete.",
    )

    print("V2 D5 asset verification passed.")
    print(f"Prediction rows: {status['prediction_rows']:,}")
    print(f"Robustness diagnostics: {len(matrix)}")
    print(f"Publication figures: {len(expected_figures)}")
    print(f"Final evidence grade: {status['final_evidence_grade']}")
    print("Primary case established: False")
    print("Pipeline retuning performed: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
