from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any

import pandas as pd

from shockbridge_signal_validity.v2.causal_features import build_registered_signal_features
from shockbridge_signal_validity.v2.contracts import ProtocolViolation
from shockbridge_signal_validity.v2.filtered_states import CausalFilteredStateEngine
from shockbridge_signal_validity.v2.manifests import file_record, sha256_file, write_json
from shockbridge_signal_validity.v2.partitions import assert_development_only
from shockbridge_signal_validity.v2.predictive_screening import (
    STATE_PROBABILITY_COLUMNS,
    fit_common_benchmark_screening_fold,
    scalar_state_score_screening_fold,
    preliminary_gate_summary,
    select_screening_specification,
    unique_signal_specifications,
)
from shockbridge_signal_validity.v2.registry import load_v2_registry
from shockbridge_signal_validity.v2.signals import add_soft_state_interactions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run development-only Version 2 D2A nested signal screening.")
    parser.add_argument("--aligned", type=Path, default=Path("data/processed/v2/development/aligned_development_market_data.csv"))
    parser.add_argument("--targets", type=Path, default=Path("data/processed/v2/development/development_targets.csv"))
    parser.add_argument("--fold-plan", type=Path, default=Path("data/processed/v2/development/nested_fold_plan.csv"))
    parser.add_argument("--inventory", type=Path, default=Path("data/processed/v2/development/candidate_inventory.csv"))
    parser.add_argument("--causal", type=Path, default=Path("data/processed/v2/development/d1_causal_base_features.csv"))
    parser.add_argument("--registry", type=Path, default=Path("configs/v2_experiment_registry.json"))
    parser.add_argument("--protocol-lock", type=Path, default=Path("V2_PROTOCOL_LOCK.json"))
    parser.add_argument("--d0-lock", type=Path, default=Path("V2_D0_IMPLEMENTATION_LOCK.json"))
    parser.add_argument("--d1-lock", type=Path, default=Path("V2_D1_ENGINE_LOCK.json"))
    parser.add_argument("--d2a-lock", type=Path, default=Path("V2_D2A_SELECTION_LOCK.json"))
    parser.add_argument("--config", type=Path, default=Path("configs/v2_d2a_screening.json"))
    parser.add_argument("--processed-root", type=Path, default=Path("data/processed/v2/development"))
    parser.add_argument("--output-root", type=Path, default=Path("outputs/v2/development"))
    return parser.parse_args()


def git_commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()


def read_indexed_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    timestamp = "Timestamp" if "Timestamp" in frame.columns else frame.columns[0]
    frame[timestamp] = pd.to_datetime(frame[timestamp], utc=True, errors="raise")
    frame = frame.set_index(timestamp)
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise RuntimeError(f"Invalid chronological file: {path}")
    return frame


def fold_row(plan: pd.DataFrame, level: str, horizon: int, outer: int, inner: int | None = None) -> pd.Series:
    mask = (
        (plan["level"] == level)
        & (plan["horizon_candles"].astype(int) == int(horizon))
        & (plan["outer_fold"].astype(int) == int(outer))
    )
    if inner is not None:
        mask &= plan["inner_fold"].fillna(-1).astype(int) == int(inner)
    rows = plan.loc[mask]
    if len(rows) != 1:
        raise RuntimeError(f"Expected one {level} fold record for h={horizon}, outer={outer}, inner={inner}.")
    return rows.iloc[0]


def date(value: Any) -> pd.Timestamp:
    return pd.Timestamp(value)


def fit_states(causal: pd.DataFrame, fold: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = causal.loc[date(fold["train_start_utc"]):date(fold["train_end_utc"])].dropna()
    test = causal.loc[date(fold["test_start_utc"]):date(fold["test_end_utc"])].dropna()
    engine = CausalFilteredStateEngine().fit(train)
    return engine.training_probabilities_.copy(), engine.filter_forward(test)


def raw_signal_features(close: pd.Series, specification: Any) -> pd.DataFrame:
    frame = build_registered_signal_features(
        close,
        signal_family=specification.signal_family,
        interpretation=specification.interpretation,
        period=specification.period,
        lower_threshold=specification.lower_threshold,
        upper_threshold=specification.upper_threshold,
        standard_deviations=specification.standard_deviations,
    )
    return frame.add_prefix(f"{specification.signal_family}_")


def fold_signal_features(raw: pd.DataFrame, specification: Any, states: pd.DataFrame) -> pd.DataFrame:
    score = (
        raw[f"{specification.signal_family}_rsi_signal_score"]
        if specification.signal_family == "rsi"
        else raw[f"{specification.signal_family}_bb_signal_score"]
    )
    interactions = add_soft_state_interactions(score.reindex(states.index), states)
    return raw.reindex(states.index).join(interactions)


def result_record(result: Any) -> dict[str, object]:
    return {
        "train_rows": result.train_rows,
        "test_rows": result.test_rows,
        "benchmark_log_loss": result.benchmark_log_loss,
        "candidate_log_loss": result.candidate_log_loss,
        "incremental_log_loss": result.incremental_log_loss,
        "benchmark_brier": result.benchmark_brier,
        "candidate_brier": result.candidate_brier,
    }


def main() -> int:
    args = parse_args()
    root = Path.cwd().resolve()
    registry = load_v2_registry(args.registry)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    locks = {
        "protocol": json.loads(args.protocol_lock.read_text(encoding="utf-8"))["lock_id"],
        "d0": json.loads(args.d0_lock.read_text(encoding="utf-8"))["lock_id"],
        "d1": json.loads(args.d1_lock.read_text(encoding="utf-8"))["lock_id"],
        "d2a": json.loads(args.d2a_lock.read_text(encoding="utf-8"))["lock_id"],
    }
    if config["execution_scope"] != "DEVELOPMENT_ONLY_PREDICTIVE_SCREENING":
        raise RuntimeError("D2A configuration has an invalid execution scope.")

    holdout_root = Path("outputs/v2/holdout")
    holdout_files = [path for path in holdout_root.rglob("*") if path.is_file()] if holdout_root.exists() else []
    if holdout_files:
        raise RuntimeError("Unauthorized holdout outputs exist before D2A execution.")

    aligned = read_indexed_csv(args.aligned)
    targets = read_indexed_csv(args.targets)
    causal = read_indexed_csv(args.causal)
    assert_development_only(aligned, registry)
    assert_development_only(targets, registry)
    assert_development_only(causal, registry)

    inventory = pd.read_csv(args.inventory)
    specifications = unique_signal_specifications(inventory)
    if len(specifications) != 84:
        raise RuntimeError(f"D2A expected 84 registered standalone signal specifications, found {len(specifications)}.")
    raw_features = {spec.signal_spec_id: raw_signal_features(aligned["sol_Close"], spec) for spec in specifications}
    signal_scores = pd.DataFrame(index=aligned.index)
    for spec in specifications:
        score_column = (
            f"{spec.signal_family}_rsi_signal_score"
            if spec.signal_family == "rsi"
            else f"{spec.signal_family}_bb_signal_score"
        )
        signal_scores[spec.signal_spec_id] = raw_features[spec.signal_spec_id][score_column]
    spec_by_id = {spec.signal_spec_id: spec for spec in specifications}

    plan = pd.read_csv(args.fold_plan)
    args.processed_root.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)

    inner_records: list[dict[str, object]] = []
    selected_records: list[dict[str, object]] = []
    outer_records: list[dict[str, object]] = []
    prediction_records: list[pd.DataFrame] = []

    for horizon in registry.horizons:
        target = pd.to_numeric(targets[f"direction_h{horizon}"], errors="coerce")
        for outer_fold in range(1, registry.outer_folds + 1):
            outer = fold_row(plan, "outer", horizon, outer_fold)
            inner_contexts: dict[int, tuple[pd.Series, pd.DataFrame, pd.DataFrame, Any]] = {}
            for inner_fold in range(1, registry.inner_folds + 1):
                inner = fold_row(plan, "inner", horizon, outer_fold, inner_fold)
                train_states, test_states = fit_states(causal, inner)
                benchmark = fit_common_benchmark_screening_fold(
                    baseline_features=causal,
                    train_states=train_states,
                    test_states=test_states,
                    target=target,
                    signal_scores=signal_scores,
                    train_start=date(inner["train_start_utc"]),
                    train_end=date(inner["train_end_utc"]),
                    test_start=date(inner["test_start_utc"]),
                    test_end=date(inner["test_end_utc"]),
                    random_state=int(config["screening_model"]["random_state"]),
                )
                inner_contexts[inner_fold] = (inner, train_states, test_states, benchmark)

            outer_train_states, outer_test_states = fit_states(causal, outer)
            outer_benchmark = fit_common_benchmark_screening_fold(
                baseline_features=causal,
                train_states=outer_train_states,
                test_states=outer_test_states,
                target=target,
                signal_scores=signal_scores,
                train_start=date(outer["train_start_utc"]),
                train_end=date(outer["train_end_utc"]),
                test_start=date(outer["test_start_utc"]),
                test_end=date(outer["test_end_utc"]),
                random_state=int(config["screening_model"]["random_state"]),
            )

            for family in ("rsi", "bollinger"):
                family_specs = [spec for spec in specifications if spec.signal_family == family]
                family_inner_records: list[dict[str, object]] = []
                for spec in family_specs:
                    raw = raw_features[spec.signal_spec_id]
                    for inner_fold, (inner, train_states, test_states, benchmark) in inner_contexts.items():
                        fold_states = pd.concat([train_states, test_states]).sort_index()
                        try:
                            result = scalar_state_score_screening_fold(
                                benchmark=benchmark,
                                signal_score=signal_scores[spec.signal_spec_id],
                                states=fold_states,
                                ridge=1.0,
                            )
                            record = {
                                "status": "EVALUATED",
                                "horizon_candles": int(horizon),
                                "horizon_hours": int(horizon) * 4,
                                "outer_fold": outer_fold,
                                "inner_fold": inner_fold,
                                "signal_family": family,
                                "signal_spec_id": spec.signal_spec_id,
                                **result_record(result),
                            }
                        except ProtocolViolation as exc:
                            record = {
                                "status": "STRUCTURALLY_UNAVAILABLE",
                                "reason": str(exc),
                                "horizon_candles": int(horizon),
                                "horizon_hours": int(horizon) * 4,
                                "outer_fold": outer_fold,
                                "inner_fold": inner_fold,
                                "signal_family": family,
                                "signal_spec_id": spec.signal_spec_id,
                                "train_rows": 0,
                                "test_rows": 0,
                                "benchmark_log_loss": None,
                                "candidate_log_loss": None,
                                "incremental_log_loss": None,
                                "benchmark_brier": None,
                                "candidate_brier": None,
                            }
                        family_inner_records.append(record)
                        inner_records.append(record)

                family_inner = pd.DataFrame.from_records(family_inner_records)
                eligible = family_inner.loc[family_inner["status"] == "EVALUATED"].copy()
                counts = eligible.groupby("signal_spec_id")["inner_fold"].nunique()
                complete_ids = counts.loc[counts == registry.inner_folds].index
                eligible = eligible.loc[eligible["signal_spec_id"].isin(complete_ids)]
                if eligible.empty:
                    raise RuntimeError(f"No complete inner screening candidate for {family}, h={horizon}, outer={outer_fold}.")
                selected = select_screening_specification(eligible)
                selected_id = str(selected["signal_spec_id"])
                spec = spec_by_id[selected_id]
                selected_records.append(
                    {
                        "signal_family": family,
                        "horizon_candles": int(horizon),
                        "horizon_hours": int(horizon) * 4,
                        "outer_fold": outer_fold,
                        "selected_signal_spec_id": selected_id,
                        "interpretation": spec.interpretation,
                        "period": spec.period,
                        "lower_threshold": spec.lower_threshold,
                        "upper_threshold": spec.upper_threshold,
                        "standard_deviations": spec.standard_deviations,
                        "mean_inner_incremental_log_loss": float(selected["mean_incremental_log_loss"]),
                        "inner_standard_error": float(selected["standard_error_incremental_log_loss"]),
                        "positive_inner_folds": int(selected["positive_inner_folds"]),
                        "calibration_not_dominated": bool(selected["calibration_not_dominated"]),
                    }
                )

                fold_states = pd.concat([outer_train_states, outer_test_states]).sort_index()
                result = scalar_state_score_screening_fold(
                    benchmark=outer_benchmark,
                    signal_score=signal_scores[selected_id],
                    states=fold_states,
                    ridge=1.0,
                )
                outer_record = {
                    "signal_family": family,
                    "horizon_candles": int(horizon),
                    "horizon_hours": int(horizon) * 4,
                    "outer_fold": outer_fold,
                    "selected_signal_spec_id": selected_id,
                    **result_record(result),
                }
                outer_records.append(outer_record)
                prediction = pd.DataFrame(
                    {
                        "Timestamp": result.timestamps,
                        "signal_family": family,
                        "horizon_candles": int(horizon),
                        "horizon_hours": int(horizon) * 4,
                        "outer_fold": outer_fold,
                        "selected_signal_spec_id": selected_id,
                        "benchmark_probability": result.benchmark_probability,
                        "candidate_probability": result.candidate_probability,
                        "realised_direction": result.realised,
                    }
                )
                prediction["benchmark_log_loss_observation"] = -(
                    prediction["realised_direction"] * prediction["benchmark_probability"].clip(1e-9, 1 - 1e-9).map(__import__("math").log)
                    + (1 - prediction["realised_direction"]) * (1 - prediction["benchmark_probability"].clip(1e-9, 1 - 1e-9)).map(__import__("math").log)
                )
                prediction["candidate_log_loss_observation"] = -(
                    prediction["realised_direction"] * prediction["candidate_probability"].clip(1e-9, 1 - 1e-9).map(__import__("math").log)
                    + (1 - prediction["realised_direction"]) * (1 - prediction["candidate_probability"].clip(1e-9, 1 - 1e-9)).map(__import__("math").log)
                )
                prediction["incremental_log_loss_observation"] = prediction["benchmark_log_loss_observation"] - prediction["candidate_log_loss_observation"]
                prediction_records.append(prediction)

    inner_frame = pd.DataFrame.from_records(inner_records)
    selected_frame = pd.DataFrame.from_records(selected_records)
    outer_frame = pd.DataFrame.from_records(outer_records)
    predictions = pd.concat(prediction_records, ignore_index=True)
    summary = preliminary_gate_summary(outer_frame)

    inner_path = args.processed_root / "d2a_inner_screen_results.csv"
    selected_path = args.processed_root / "d2a_selected_signal_specifications.csv"
    outer_path = args.processed_root / "d2a_outer_fold_results.csv"
    predictions_path = args.processed_root / "d2a_outer_predictions.csv"
    summary_path = args.processed_root / "d2a_family_horizon_summary.csv"
    inner_frame.to_csv(inner_path, index=False)
    selected_frame.to_csv(selected_path, index=False)
    outer_frame.to_csv(outer_path, index=False)
    predictions.to_csv(predictions_path, index=False)
    summary.to_csv(summary_path, index=False)

    implementation_commit = git_commit()
    manifest = {
        "checkpoint": "V2_D2A_NESTED_LINEAR_SIGNAL_SCREENING",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution_scope": config["execution_scope"],
        "implementation_commit": implementation_commit,
        "locks": locks,
        "registry_sha256": registry.sha256,
        "registered_signal_specifications": len(specifications),
        "inner_result_rows": int(len(inner_frame)),
        "selected_specification_rows": int(len(selected_frame)),
        "outer_fold_result_rows": int(len(outer_frame)),
        "outer_prediction_rows": int(len(predictions)),
        "preliminary_screening_passes": int(summary["screening_gate_pass"].sum()),
        "final_pipeline_selection_performed": False,
        "nonlinear_model_selection_performed": False,
        "economic_gate_evaluated": False,
        "holdout_performance_accessed": False,
        "files": [file_record(path, root) for path in [inner_path, selected_path, outer_path, predictions_path, summary_path]],
    }
    manifest_path = args.processed_root / "d2a_selection_manifest.json"
    write_json(manifest_path, manifest)
    status = {
        "status": "PASS",
        "checkpoint": manifest["checkpoint"],
        "implementation_commit": implementation_commit,
        "d2a_lock_id": locks["d2a"],
        "registered_signal_specifications": len(specifications),
        "inner_result_rows": int(len(inner_frame)),
        "selected_specification_rows": int(len(selected_frame)),
        "outer_fold_result_rows": int(len(outer_frame)),
        "outer_prediction_rows": int(len(predictions)),
        "predictive_model_fitting_performed": True,
        "screening_model_family": "regularized_linear",
        "final_pipeline_selection_performed": False,
        "holdout_performance_accessed": False,
        "manifest_sha256": sha256_file(manifest_path),
    }
    write_json(args.output_root / "d2a_selection_status.json", status)

    print("Version 2 D2A nested linear signal screening completed.")
    print(f"Registered signal specifications: {len(specifications):,}")
    print(f"Inner screening result rows: {len(inner_frame):,}")
    print(f"Outer selected specifications: {len(selected_frame):,}")
    print(f"Outer fold results: {len(outer_frame):,}")
    print(f"Outer prediction rows: {len(predictions):,}")
    print("Predictive model fitting performed: True")
    print("Final pipeline selection performed: False")
    print("Holdout performance accessed: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
