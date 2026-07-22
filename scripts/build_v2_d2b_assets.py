from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
import pandas as pd

from shockbridge_signal_validity.v2.causal_features import build_registered_signal_features
from shockbridge_signal_validity.v2.contracts import ProtocolViolation
from shockbridge_signal_validity.v2.filtered_states import CausalFilteredStateEngine
from shockbridge_signal_validity.v2.manifests import file_record, sha256_file, write_json
from shockbridge_signal_validity.v2.partitions import assert_development_only
from shockbridge_signal_validity.v2.pipeline_selection import (
    ABSTENTION_THRESHOLDS,
    CALIBRATION_METHODS,
    ELIGIBLE_CALIBRATION_METHODS,
    build_structural_pipeline_inventory,
    development_stability_summary,
    directional_policy_metrics,
    matched_pipeline_fold,
    select_abstention_policy,
    select_calibration_method,
    select_structural_pipeline,
    structural_specification_from_row,
)
from shockbridge_signal_validity.v2.predictive_screening import unique_signal_specifications
from shockbridge_signal_validity.v2.registry import load_v2_registry
from shockbridge_signal_validity.v2.signals import add_soft_state_interactions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Version 2 D2B nested model, window, calibration, and abstention selection on development data only."
    )
    parser.add_argument("--aligned", type=Path, default=Path("data/processed/v2/development/aligned_development_market_data.csv"))
    parser.add_argument("--targets", type=Path, default=Path("data/processed/v2/development/development_targets.csv"))
    parser.add_argument("--fold-plan", type=Path, default=Path("data/processed/v2/development/nested_fold_plan.csv"))
    parser.add_argument("--candidate-inventory", type=Path, default=Path("data/processed/v2/development/candidate_inventory.csv"))
    parser.add_argument("--causal", type=Path, default=Path("data/processed/v2/development/d1_causal_base_features.csv"))
    parser.add_argument("--d2a-selected", type=Path, default=Path("data/processed/v2/development/d2a_selected_signal_specifications.csv"))
    parser.add_argument("--registry", type=Path, default=Path("configs/v2_experiment_registry.json"))
    parser.add_argument("--config", type=Path, default=Path("configs/v2_d2b_selection.json"))
    parser.add_argument("--protocol-lock", type=Path, default=Path("V2_PROTOCOL_LOCK.json"))
    parser.add_argument("--d0-lock", type=Path, default=Path("V2_D0_IMPLEMENTATION_LOCK.json"))
    parser.add_argument("--d1-lock", type=Path, default=Path("V2_D1_ENGINE_LOCK.json"))
    parser.add_argument("--d2a-lock", type=Path, default=Path("V2_D2A_SELECTION_LOCK.json"))
    parser.add_argument("--d2b-lock", type=Path, default=Path("V2_D2B_SELECTION_LOCK.json"))
    parser.add_argument("--processed-root", type=Path, default=Path("data/processed/v2/development"))
    parser.add_argument("--output-root", type=Path, default=Path("outputs/v2/development"))
    parser.add_argument("--validation-max-structural-configurations", type=int, default=None)
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
        raise RuntimeError(f"Expected one {level} fold for h={horizon}, outer={outer}, inner={inner}.")
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
    score_column = (
        f"{specification.signal_family}_rsi_signal_score"
        if specification.signal_family == "rsi"
        else f"{specification.signal_family}_bb_signal_score"
    )
    score = raw[score_column].reindex(states.index)
    return raw.reindex(states.index).join(add_soft_state_interactions(score, states))


def result_record(result: Any) -> dict[str, Any]:
    return {
        "train_rows": result.train_rows,
        "fit_rows": result.fit_rows,
        "calibration_rows": result.calibration_rows,
        "test_rows": result.test_rows,
        "benchmark_log_loss": result.benchmark_log_loss,
        "candidate_log_loss": result.candidate_log_loss,
        "incremental_log_loss": result.incremental_log_loss,
        "benchmark_brier": result.benchmark_brier,
        "candidate_brier": result.candidate_brier,
        "benchmark_ece": result.benchmark_ece,
        "candidate_ece": result.candidate_ece,
    }


def observation_losses(realised: np.ndarray, probability: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(probability, dtype=float), 1e-9, 1.0 - 1e-9)
    y = np.asarray(realised, dtype=float)
    return -(y * np.log(values) + (1.0 - y) * np.log(1.0 - values))


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
        "d2b": json.loads(args.d2b_lock.read_text(encoding="utf-8"))["lock_id"],
    }
    if config["execution_scope"] != "DEVELOPMENT_ONLY_FULL_NESTED_PIPELINE_SELECTION":
        raise RuntimeError("D2B configuration has an invalid execution scope.")

    holdout_root = Path("outputs/v2/holdout")
    holdout_files = [path for path in holdout_root.rglob("*") if path.is_file()] if holdout_root.exists() else []
    if holdout_files:
        raise RuntimeError("Unauthorized holdout outputs exist before D2B execution.")

    validation_limit = args.validation_max_structural_configurations
    if validation_limit is not None:
        required_value = config["validation_override"]["required_environment_value"]
        variable = config["validation_override"]["environment_variable"]
        if os.getenv(variable) != required_value:
            raise RuntimeError(f"Validation inventory limits require {variable}={required_value}.")
        if validation_limit < 1:
            raise RuntimeError("Validation structural-configuration limit must be positive.")

    aligned = read_indexed_csv(args.aligned)
    targets = read_indexed_csv(args.targets)
    causal = read_indexed_csv(args.causal)
    assert_development_only(aligned, registry)
    assert_development_only(targets, registry)
    assert_development_only(causal, registry)

    plan = pd.read_csv(args.fold_plan)
    candidate_inventory = pd.read_csv(args.candidate_inventory)
    specifications = unique_signal_specifications(candidate_inventory)
    spec_by_id = {spec.signal_spec_id: spec for spec in specifications}
    d2a_selected = pd.read_csv(args.d2a_selected)
    if len(d2a_selected) != 40 or d2a_selected.duplicated(["signal_family", "horizon_candles", "outer_fold"]).any():
        raise RuntimeError("D2B requires exactly 40 unique D2A selected signal specifications.")
    unknown = sorted(set(d2a_selected["selected_signal_spec_id"]) - set(spec_by_id))
    if unknown:
        raise RuntimeError("D2A selected unknown signal specifications: " + ", ".join(unknown))

    structural_inventory = build_structural_pipeline_inventory(registry.payload)
    production_inventory_rows = len(structural_inventory)
    if validation_limit is not None:
        structural_inventory = structural_inventory.iloc[:validation_limit].copy()
    structural_specs = {
        row.pipeline_id: structural_specification_from_row(row)
        for _, row in structural_inventory.iterrows()
    }

    raw_cache: dict[str, pd.DataFrame] = {}
    for selected_id in sorted(set(d2a_selected["selected_signal_spec_id"])):
        raw_cache[selected_id] = raw_signal_features(aligned["sol_Close"], spec_by_id[selected_id])

    args.processed_root.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)

    structural_records: list[dict[str, Any]] = []
    selected_structural_records: list[dict[str, Any]] = []
    calibration_records: list[dict[str, Any]] = []
    selected_calibration_records: list[dict[str, Any]] = []
    policy_records: list[dict[str, Any]] = []
    selected_policy_records: list[dict[str, Any]] = []
    outer_records: list[dict[str, Any]] = []
    prediction_records: list[pd.DataFrame] = []

    calibration_config = config["calibration"]
    random_state = int(config["random_state"])

    for horizon in registry.horizons:
        target = pd.to_numeric(targets[f"direction_h{horizon}"], errors="coerce")
        future_return = pd.to_numeric(targets[f"future_log_return_h{horizon}"], errors="coerce")
        for outer_fold in range(1, registry.outer_folds + 1):
            outer = fold_row(plan, "outer", horizon, outer_fold)
            outer_train_states, outer_test_states = fit_states(causal, outer)
            outer_states = pd.concat([outer_train_states, outer_test_states]).sort_index()

            inner_contexts: dict[int, tuple[pd.Series, pd.DataFrame]] = {}
            for inner_fold in range(1, registry.inner_folds + 1):
                inner = fold_row(plan, "inner", horizon, outer_fold, inner_fold)
                train_states, test_states = fit_states(causal, inner)
                inner_contexts[inner_fold] = (inner, pd.concat([train_states, test_states]).sort_index())

            for family in ("rsi", "bollinger"):
                selected_row = d2a_selected.loc[
                    (d2a_selected["signal_family"] == family)
                    & (d2a_selected["horizon_candles"].astype(int) == int(horizon))
                    & (d2a_selected["outer_fold"].astype(int) == int(outer_fold))
                ]
                if len(selected_row) != 1:
                    raise RuntimeError(f"Missing D2A selection for {family}, h={horizon}, outer={outer_fold}.")
                selected_signal_id = str(selected_row.iloc[0]["selected_signal_spec_id"])
                signal_spec = spec_by_id[selected_signal_id]
                raw = raw_cache[selected_signal_id]

                family_structural_records: list[dict[str, Any]] = []
                for inner_fold, (inner, states) in inner_contexts.items():
                    signal_frame = fold_signal_features(raw, signal_spec, states)
                    for _, pipeline_row in structural_inventory.iterrows():
                        pipeline = structural_specs[str(pipeline_row["pipeline_id"])]
                        base_record = {
                            "horizon_candles": int(horizon),
                            "horizon_hours": int(horizon) * 4,
                            "outer_fold": int(outer_fold),
                            "inner_fold": int(inner_fold),
                            "signal_family": family,
                            "selected_signal_spec_id": selected_signal_id,
                            "pipeline_id": pipeline.pipeline_id,
                            "model_family": pipeline.model_family,
                            "window_scheme": pipeline.window_scheme,
                            "regime_conditioned": pipeline.regime_conditioned,
                            "parameters_json": json.dumps(pipeline.parameters, sort_keys=True),
                            "complexity_rank": pipeline.complexity_rank,
                        }
                        try:
                            result = matched_pipeline_fold(
                                baseline_features=causal,
                                states=states,
                                signal_features=signal_frame,
                                target=target,
                                future_return=future_return,
                                train_start=date(inner["train_start_utc"]),
                                train_end=date(inner["train_end_utc"]),
                                test_start=date(inner["test_start_utc"]),
                                test_end=date(inner["test_end_utc"]),
                                specification=pipeline,
                                registry_payload=registry.payload,
                                calibration_method="none",
                                horizon_candles=int(horizon),
                                random_state=random_state,
                            )
                            record = {"status": "EVALUATED", **base_record, **result_record(result)}
                        except (ProtocolViolation, ValueError, np.linalg.LinAlgError) as exc:
                            record = {
                                "status": "STRUCTURALLY_UNAVAILABLE",
                                "reason": str(exc),
                                **base_record,
                                "train_rows": 0,
                                "fit_rows": 0,
                                "calibration_rows": 0,
                                "test_rows": 0,
                                "benchmark_log_loss": None,
                                "candidate_log_loss": None,
                                "incremental_log_loss": None,
                                "benchmark_brier": None,
                                "candidate_brier": None,
                                "benchmark_ece": None,
                                "candidate_ece": None,
                            }
                        structural_records.append(record)
                        family_structural_records.append(record)

                family_structural = pd.DataFrame.from_records(family_structural_records)
                eligible = family_structural.loc[family_structural["status"] == "EVALUATED"].copy()
                complete = eligible.groupby("pipeline_id")["inner_fold"].nunique()
                complete_ids = complete.loc[complete == registry.inner_folds].index
                eligible = eligible.loc[eligible["pipeline_id"].isin(complete_ids)]
                if eligible.empty:
                    raise RuntimeError(f"No complete D2B structural pipeline for {family}, h={horizon}, outer={outer_fold}.")
                selected_structural = select_structural_pipeline(eligible)
                pipeline_id = str(selected_structural["pipeline_id"])
                pipeline = structural_specs[pipeline_id]
                selected_structural_records.append(
                    {
                        "signal_family": family,
                        "horizon_candles": int(horizon),
                        "horizon_hours": int(horizon) * 4,
                        "outer_fold": int(outer_fold),
                        "selected_signal_spec_id": selected_signal_id,
                        "selected_pipeline_id": pipeline_id,
                        "model_family": pipeline.model_family,
                        "window_scheme": pipeline.window_scheme,
                        "regime_conditioned": pipeline.regime_conditioned,
                        "parameters_json": json.dumps(pipeline.parameters, sort_keys=True),
                        "mean_inner_incremental_log_loss": float(selected_structural["mean_incremental_log_loss"]),
                        "positive_inner_folds": int(selected_structural["positive_inner_folds"]),
                        "inner_standard_error": float(selected_structural["standard_error_incremental_log_loss"]),
                        "calibration_not_dominated": bool(selected_structural["calibration_not_dominated"]),
                    }
                )

                calibration_result_objects: dict[tuple[str, int], Any] = {}
                family_calibration_records: list[dict[str, Any]] = []
                for calibration_method in CALIBRATION_METHODS:
                    for inner_fold, (inner, states) in inner_contexts.items():
                        signal_frame = fold_signal_features(raw, signal_spec, states)
                        result = matched_pipeline_fold(
                            baseline_features=causal,
                            states=states,
                            signal_features=signal_frame,
                            target=target,
                            future_return=future_return,
                            train_start=date(inner["train_start_utc"]),
                            train_end=date(inner["train_end_utc"]),
                            test_start=date(inner["test_start_utc"]),
                            test_end=date(inner["test_end_utc"]),
                            specification=pipeline,
                            registry_payload=registry.payload,
                            calibration_method=calibration_method,
                            horizon_candles=int(horizon),
                            calibration_fraction=float(calibration_config["chronological_fraction"]),
                            minimum_fit_rows=int(calibration_config["minimum_fit_rows"]),
                            minimum_calibration_rows=int(calibration_config["minimum_calibration_rows"]),
                            random_state=random_state,
                        )
                        calibration_result_objects[(calibration_method, inner_fold)] = result
                        record = {
                            "signal_family": family,
                            "horizon_candles": int(horizon),
                            "horizon_hours": int(horizon) * 4,
                            "outer_fold": int(outer_fold),
                            "inner_fold": int(inner_fold),
                            "selected_signal_spec_id": selected_signal_id,
                            "selected_pipeline_id": pipeline_id,
                            "calibration_method": calibration_method,
                            "eligible_for_selection": calibration_method in ELIGIBLE_CALIBRATION_METHODS,
                            "governance_role": "CONFIRMATORY_CANDIDATE" if calibration_method in ELIGIBLE_CALIBRATION_METHODS else "DIAGNOSTIC_ONLY",
                            **result_record(result),
                        }
                        calibration_records.append(record)
                        family_calibration_records.append(record)

                selected_calibration = select_calibration_method(pd.DataFrame.from_records(family_calibration_records))
                calibration_method = str(selected_calibration["calibration_method"])
                selected_calibration_records.append(
                    {
                        "signal_family": family,
                        "horizon_candles": int(horizon),
                        "horizon_hours": int(horizon) * 4,
                        "outer_fold": int(outer_fold),
                        "selected_signal_spec_id": selected_signal_id,
                        "selected_pipeline_id": pipeline_id,
                        "selected_calibration_method": calibration_method,
                        "mean_inner_incremental_log_loss": float(selected_calibration["mean_incremental_log_loss"]),
                        "mean_candidate_brier": float(selected_calibration["mean_candidate_brier"]),
                        "mean_candidate_ece": float(selected_calibration["mean_candidate_ece"]),
                        "positive_inner_folds": int(selected_calibration["positive_inner_folds"]),
                    }
                )

                family_policy_records: list[dict[str, Any]] = []
                for inner_fold in range(1, registry.inner_folds + 1):
                    result = calibration_result_objects[(calibration_method, inner_fold)]
                    for threshold in ABSTENTION_THRESHOLDS:
                        metrics = directional_policy_metrics(
                            result.candidate_probability,
                            result.future_return,
                            threshold=float(threshold),
                            one_way_cost_bps=float(config["decision_policy"]["primary_one_way_cost_bps"]),
                        )
                        record = {
                            "signal_family": family,
                            "horizon_candles": int(horizon),
                            "horizon_hours": int(horizon) * 4,
                            "outer_fold": int(outer_fold),
                            "inner_fold": int(inner_fold),
                            "selected_signal_spec_id": selected_signal_id,
                            "selected_pipeline_id": pipeline_id,
                            "selected_calibration_method": calibration_method,
                            **metrics,
                        }
                        policy_records.append(record)
                        family_policy_records.append(record)

                selected_policy = select_abstention_policy(pd.DataFrame.from_records(family_policy_records))
                threshold = float(selected_policy["threshold"])
                selected_policy_records.append(
                    {
                        "signal_family": family,
                        "horizon_candles": int(horizon),
                        "horizon_hours": int(horizon) * 4,
                        "outer_fold": int(outer_fold),
                        "selected_signal_spec_id": selected_signal_id,
                        "selected_pipeline_id": pipeline_id,
                        "selected_calibration_method": calibration_method,
                        "selected_threshold": threshold,
                        "mean_inner_coverage": float(selected_policy["mean_coverage"]),
                        "inner_nonzero_decisions": int(selected_policy["total_nonzero_decisions"]),
                        "mean_inner_net_edge": float(selected_policy["mean_net_edge"]),
                        "positive_inner_folds": int(selected_policy["positive_inner_folds"]),
                        "governance_interpretation": selected_policy["governance_interpretation"],
                    }
                )

                outer_signal_frame = fold_signal_features(raw, signal_spec, outer_states)
                outer_result = matched_pipeline_fold(
                    baseline_features=causal,
                    states=outer_states,
                    signal_features=outer_signal_frame,
                    target=target,
                    future_return=future_return,
                    train_start=date(outer["train_start_utc"]),
                    train_end=date(outer["train_end_utc"]),
                    test_start=date(outer["test_start_utc"]),
                    test_end=date(outer["test_end_utc"]),
                    specification=pipeline,
                    registry_payload=registry.payload,
                    calibration_method=calibration_method,
                    horizon_candles=int(horizon),
                    calibration_fraction=float(calibration_config["chronological_fraction"]),
                    minimum_fit_rows=int(calibration_config["minimum_fit_rows"]),
                    minimum_calibration_rows=int(calibration_config["minimum_calibration_rows"]),
                    random_state=random_state,
                )
                outer_policy = directional_policy_metrics(
                    outer_result.candidate_probability,
                    outer_result.future_return,
                    threshold=threshold,
                    one_way_cost_bps=float(config["decision_policy"]["primary_one_way_cost_bps"]),
                )
                outer_records.append(
                    {
                        "signal_family": family,
                        "horizon_candles": int(horizon),
                        "horizon_hours": int(horizon) * 4,
                        "outer_fold": int(outer_fold),
                        "selected_signal_spec_id": selected_signal_id,
                        "selected_pipeline_id": pipeline_id,
                        "model_family": pipeline.model_family,
                        "window_scheme": pipeline.window_scheme,
                        "regime_conditioned": pipeline.regime_conditioned,
                        "parameters_json": json.dumps(pipeline.parameters, sort_keys=True),
                        "selected_calibration_method": calibration_method,
                        "selected_threshold": threshold,
                        **result_record(outer_result),
                        "policy_coverage": outer_policy["coverage"],
                        "policy_nonzero_decisions": outer_policy["nonzero_decisions"],
                        "policy_mean_net_edge": outer_policy["mean_net_edge"],
                        "policy_cumulative_net_return": outer_policy["cumulative_net_return"],
                        "policy_turnover_units": outer_policy["turnover_units"],
                        "economic_gate_evaluated": False,
                    }
                )

                prediction = pd.DataFrame(
                    {
                        "Timestamp": outer_result.timestamps,
                        "signal_family": family,
                        "horizon_candles": int(horizon),
                        "horizon_hours": int(horizon) * 4,
                        "outer_fold": int(outer_fold),
                        "selected_signal_spec_id": selected_signal_id,
                        "selected_pipeline_id": pipeline_id,
                        "selected_calibration_method": calibration_method,
                        "selected_threshold": threshold,
                        "benchmark_probability": outer_result.benchmark_probability,
                        "candidate_probability": outer_result.candidate_probability,
                        "realised_direction": outer_result.realised,
                        "future_log_return": outer_result.future_return,
                    }
                )
                benchmark_loss = observation_losses(outer_result.realised, outer_result.benchmark_probability)
                candidate_loss = observation_losses(outer_result.realised, outer_result.candidate_probability)
                prediction["benchmark_log_loss_observation"] = benchmark_loss
                prediction["candidate_log_loss_observation"] = candidate_loss
                prediction["incremental_log_loss_observation"] = benchmark_loss - candidate_loss
                prediction["decision_active"] = (prediction["candidate_probability"] - 0.5).abs() > threshold
                prediction["directional_position"] = np.where(
                    prediction["decision_active"],
                    np.where(prediction["candidate_probability"] > 0.5, 1, -1),
                    0,
                )
                prediction_records.append(prediction)

    structural_frame = pd.DataFrame.from_records(structural_records)
    selected_structural_frame = pd.DataFrame.from_records(selected_structural_records)
    calibration_frame = pd.DataFrame.from_records(calibration_records)
    selected_calibration_frame = pd.DataFrame.from_records(selected_calibration_records)
    policy_frame = pd.DataFrame.from_records(policy_records)
    selected_policy_frame = pd.DataFrame.from_records(selected_policy_records)
    outer_frame = pd.DataFrame.from_records(outer_records)
    predictions = pd.concat(prediction_records, ignore_index=True)
    summary = development_stability_summary(outer_frame)

    paths = {
        "inventory": args.processed_root / "d2b_structural_pipeline_inventory.csv",
        "structural": args.processed_root / "d2b_inner_structural_results.csv",
        "selected_structural": args.processed_root / "d2b_selected_structural_pipelines.csv",
        "calibration": args.processed_root / "d2b_inner_calibration_results.csv",
        "selected_calibration": args.processed_root / "d2b_selected_calibrations.csv",
        "policy": args.processed_root / "d2b_inner_policy_results.csv",
        "selected_policy": args.processed_root / "d2b_selected_decision_policies.csv",
        "outer": args.processed_root / "d2b_outer_fold_results.csv",
        "predictions": args.processed_root / "d2b_outer_predictions.csv",
        "summary": args.processed_root / "d2b_family_horizon_summary.csv",
    }
    structural_inventory.to_csv(paths["inventory"], index=False)
    structural_frame.to_csv(paths["structural"], index=False)
    selected_structural_frame.to_csv(paths["selected_structural"], index=False)
    calibration_frame.to_csv(paths["calibration"], index=False)
    selected_calibration_frame.to_csv(paths["selected_calibration"], index=False)
    policy_frame.to_csv(paths["policy"], index=False)
    selected_policy_frame.to_csv(paths["selected_policy"], index=False)
    outer_frame.to_csv(paths["outer"], index=False)
    predictions.to_csv(paths["predictions"], index=False)
    summary.to_csv(paths["summary"], index=False)

    implementation_commit = git_commit()
    validation_mode = validation_limit is not None
    manifest = {
        "checkpoint": "V2_D2B_FULL_NESTED_PIPELINE_SELECTION",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution_scope": config["execution_scope"],
        "implementation_commit": implementation_commit,
        "locks": locks,
        "registry_sha256": registry.sha256,
        "d2a_selected_specification_rows": int(len(d2a_selected)),
        "production_structural_inventory_rows": int(production_inventory_rows),
        "executed_structural_inventory_rows": int(len(structural_inventory)),
        "validation_mode": validation_mode,
        "inner_structural_result_rows": int(len(structural_frame)),
        "selected_structural_pipeline_rows": int(len(selected_structural_frame)),
        "inner_calibration_result_rows": int(len(calibration_frame)),
        "selected_calibration_rows": int(len(selected_calibration_frame)),
        "inner_policy_result_rows": int(len(policy_frame)),
        "selected_policy_rows": int(len(selected_policy_frame)),
        "outer_fold_result_rows": int(len(outer_frame)),
        "outer_prediction_rows": int(len(predictions)),
        "development_stability_passes": int(summary["development_stability_pass"].sum()),
        "nested_pipeline_selection_performed": True,
        "isotonic_used_for_selection": False,
        "economic_gate_evaluated": False,
        "holdout_pipeline_freeze_performed": False,
        "holdout_performance_accessed": False,
        "files": [file_record(path, root) for path in paths.values()],
    }
    manifest_path = args.processed_root / "d2b_selection_manifest.json"
    write_json(manifest_path, manifest)

    status = {
        "status": "PASS",
        "checkpoint": manifest["checkpoint"],
        "implementation_commit": implementation_commit,
        "d2b_lock_id": locks["d2b"],
        "production_structural_inventory_rows": int(production_inventory_rows),
        "executed_structural_inventory_rows": int(len(structural_inventory)),
        "validation_mode": validation_mode,
        "inner_structural_result_rows": int(len(structural_frame)),
        "selected_structural_pipeline_rows": int(len(selected_structural_frame)),
        "inner_calibration_result_rows": int(len(calibration_frame)),
        "selected_calibration_rows": int(len(selected_calibration_frame)),
        "inner_policy_result_rows": int(len(policy_frame)),
        "selected_policy_rows": int(len(selected_policy_frame)),
        "outer_fold_result_rows": int(len(outer_frame)),
        "outer_prediction_rows": int(len(predictions)),
        "predictive_model_fitting_performed": True,
        "nested_pipeline_selection_performed": True,
        "isotonic_diagnostic_only": True,
        "economic_gate_evaluated": False,
        "holdout_pipeline_freeze_performed": False,
        "holdout_performance_accessed": False,
        "manifest_sha256": sha256_file(manifest_path),
    }
    write_json(args.output_root / "d2b_selection_status.json", status)

    print("Version 2 D2B full nested pipeline selection completed.")
    print(f"Production structural configurations: {production_inventory_rows:,}")
    print(f"Executed structural configurations: {len(structural_inventory):,}")
    print(f"Inner structural result rows: {len(structural_frame):,}")
    print(f"Selected structural pipelines: {len(selected_structural_frame):,}")
    print(f"Calibration result rows: {len(calibration_frame):,}")
    print(f"Decision-policy result rows: {len(policy_frame):,}")
    print(f"Outer fold results: {len(outer_frame):,}")
    print(f"Outer prediction rows: {len(predictions):,}")
    print("Nested pipeline selection performed: True")
    print("Economic gate evaluated: False")
    print("Holdout pipeline freeze performed: False")
    print("Holdout performance accessed: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
