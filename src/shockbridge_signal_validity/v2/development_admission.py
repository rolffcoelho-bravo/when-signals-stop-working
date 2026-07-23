from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import pandas as pd

from .contracts import ProtocolViolation
from .predictive_screening import ScreeningSpecification

CONFIRMATORY_FAMILIES = ("rsi", "bollinger")


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ProtocolViolation(f"{label} is missing columns: " + ", ".join(missing))


def _standard_error(values: pd.Series) -> float:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if len(numeric) <= 1:
        return 0.0
    return float(numeric.std(ddof=1) / np.sqrt(len(numeric)))


def _positive_concentration(values: pd.Series) -> float:
    gains = pd.to_numeric(values, errors="coerce").astype(float)
    positive = gains.clip(lower=0.0)
    total = float(positive.sum())
    return float(positive.max() / total) if total > 0.0 else 1.0


def build_family_horizon_admission(
    outer_results: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    required = {
        "signal_family",
        "horizon_candles",
        "outer_fold",
        "incremental_log_loss",
        "benchmark_brier",
        "candidate_brier",
        "benchmark_ece",
        "candidate_ece",
        "policy_coverage",
        "policy_nonzero_decisions",
        "policy_mean_net_edge",
    }
    _require_columns(outer_results, required, "D2C outer results")
    gates = config["admission_gates"]
    records: list[dict[str, Any]] = []

    for (family, horizon), group in outer_results.groupby(
        ["signal_family", "horizon_candles"], sort=True
    ):
        gains = pd.to_numeric(group["incremental_log_loss"], errors="coerce")
        if gains.isna().any():
            raise ProtocolViolation(f"D2C contains non-numeric loss evidence for {family}, h={horizon}.")
        outer_folds = int(group["outer_fold"].nunique())
        mean_gain = float(gains.mean())
        positive_folds = int((gains > 0.0).sum())
        concentration = _positive_concentration(gains)
        mean_candidate_brier = float(group["candidate_brier"].mean())
        mean_benchmark_brier = float(group["benchmark_brier"].mean())
        mean_candidate_ece = float(group["candidate_ece"].mean())
        mean_benchmark_ece = float(group["benchmark_ece"].mean())
        mean_coverage = float(group["policy_coverage"].mean())
        total_decisions = int(group["policy_nonzero_decisions"].sum())
        mean_net_edge = float(group["policy_mean_net_edge"].mean())

        checks = {
            "COMPLETE_OUTER_FOLDS": outer_folds == int(gates["required_outer_folds"]),
            "POSITIVE_MEAN_INCREMENTAL_LOG_LOSS": mean_gain > 0.0,
            "MINIMUM_POSITIVE_OUTER_FOLDS": positive_folds
            >= int(gates["minimum_positive_outer_folds"]),
            "FOLD_CONCENTRATION_CONTROL": concentration
            <= float(gates["maximum_single_fold_share_of_positive_gain"]),
            "BRIER_NON_DOMINANCE": mean_candidate_brier
            <= mean_benchmark_brier + float(gates["brier_tolerance"]),
            "ECE_NON_DOMINANCE": mean_candidate_ece
            <= mean_benchmark_ece + float(gates["ece_tolerance"]),
            "MINIMUM_POLICY_COVERAGE": mean_coverage
            >= float(gates["minimum_mean_policy_coverage"]),
            "MINIMUM_POLICY_DECISIONS": total_decisions
            >= int(gates["minimum_total_policy_decisions"]),
        }
        failures = [name for name, passed in checks.items() if not passed]
        records.append(
            {
                "signal_family": str(family),
                "horizon_candles": int(horizon),
                "horizon_hours": int(horizon) * 4,
                "outer_folds": outer_folds,
                "mean_incremental_log_loss": mean_gain,
                "standard_error_incremental_log_loss": _standard_error(gains),
                "positive_outer_folds": positive_folds,
                "maximum_single_fold_share_of_positive_gain": concentration,
                "mean_candidate_brier": mean_candidate_brier,
                "mean_benchmark_brier": mean_benchmark_brier,
                "mean_candidate_ece": mean_candidate_ece,
                "mean_benchmark_ece": mean_benchmark_ece,
                "mean_policy_coverage": mean_coverage,
                "total_policy_nonzero_decisions": total_decisions,
                "mean_policy_net_edge_diagnostic": mean_net_edge,
                **{f"gate_{name.lower()}": bool(value) for name, value in checks.items()},
                "development_admission_pass": not failures,
                "failure_reasons": "|".join(failures),
                "economic_gate_evaluated": False,
                "holdout_evidence_used": False,
                "governance_interpretation": "DEVELOPMENT_ADMISSION_ONLY_NO_HOLDOUT_EVIDENCE",
            }
        )

    frame = pd.DataFrame.from_records(records).sort_values(
        ["signal_family", "horizon_candles"]
    ).reset_index(drop=True)
    expected = {(family, horizon) for family in CONFIRMATORY_FAMILIES for horizon in (1, 2, 3, 6)}
    observed = set(zip(frame["signal_family"], frame["horizon_candles"].astype(int)))
    if observed != expected:
        raise ProtocolViolation("D2C requires all eight confirmatory family-horizon contexts.")
    return frame


def select_family_decisions(admission: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        admission,
        {
            "signal_family",
            "horizon_candles",
            "development_admission_pass",
            "mean_incremental_log_loss",
            "positive_outer_folds",
            "maximum_single_fold_share_of_positive_gain",
            "mean_candidate_brier",
            "failure_reasons",
        },
        "D2C family-horizon admission",
    )
    records: list[dict[str, Any]] = []
    for family in CONFIRMATORY_FAMILIES:
        group = admission.loc[admission["signal_family"] == family].copy()
        eligible = group.loc[group["development_admission_pass"].astype(bool)].copy()
        if eligible.empty:
            failure_map = ";".join(
                f"h{int(row.horizon_candles)}:{row.failure_reasons or 'UNSPECIFIED'}"
                for row in group.itertuples()
            )
            records.append(
                {
                    "signal_family": family,
                    "family_decision": "NO_PIPELINE_ADMITTED",
                    "pipeline_admitted": False,
                    "selected_horizon_candles": None,
                    "selected_horizon_hours": None,
                    "selected_mean_incremental_log_loss": None,
                    "selected_positive_outer_folds": None,
                    "rejection_reasons": failure_map,
                    "holdout_eligible": False,
                }
            )
            continue
        eligible = eligible.sort_values(
            [
                "mean_incremental_log_loss",
                "positive_outer_folds",
                "maximum_single_fold_share_of_positive_gain",
                "mean_candidate_brier",
                "horizon_candles",
            ],
            ascending=[False, False, True, True, True],
        )
        selected = eligible.iloc[0]
        records.append(
            {
                "signal_family": family,
                "family_decision": "PIPELINE_ADMITTED_FOR_METHODOLOGY_LOCKED_EVALUATION",
                "pipeline_admitted": True,
                "selected_horizon_candles": int(selected["horizon_candles"]),
                "selected_horizon_hours": int(selected["horizon_candles"]) * 4,
                "selected_mean_incremental_log_loss": float(selected["mean_incremental_log_loss"]),
                "selected_positive_outer_folds": int(selected["positive_outer_folds"]),
                "rejection_reasons": "",
                "holdout_eligible": True,
            }
        )
    return pd.DataFrame.from_records(records)


def select_final_signal_specification(
    inner_screen: pd.DataFrame,
    family: str,
    horizon: int,
    required_rows: int,
    brier_tolerance: float,
) -> pd.Series:
    required = {
        "status",
        "signal_family",
        "horizon_candles",
        "outer_fold",
        "inner_fold",
        "signal_spec_id",
        "incremental_log_loss",
        "candidate_brier",
        "benchmark_brier",
    }
    _require_columns(inner_screen, required, "D2A inner screening evidence")
    subset = inner_screen.loc[
        (inner_screen["status"] == "EVALUATED")
        & (inner_screen["signal_family"] == family)
        & (inner_screen["horizon_candles"].astype(int) == int(horizon))
    ].copy()
    grouped = (
        subset.groupby("signal_spec_id", as_index=False)
        .agg(
            evaluation_rows=("inner_fold", "size"),
            outer_folds=("outer_fold", "nunique"),
            inner_folds=("inner_fold", "nunique"),
            mean_incremental_log_loss=("incremental_log_loss", "mean"),
            standard_error_incremental_log_loss=("incremental_log_loss", _standard_error),
            positive_evaluations=("incremental_log_loss", lambda x: int((pd.Series(x) > 0.0).sum())),
            mean_candidate_brier=("candidate_brier", "mean"),
            mean_benchmark_brier=("benchmark_brier", "mean"),
        )
    )
    eligible = grouped.loc[
        (grouped["evaluation_rows"] == int(required_rows))
        & (grouped["mean_candidate_brier"] <= grouped["mean_benchmark_brier"] + float(brier_tolerance))
    ].copy()
    if eligible.empty:
        raise ProtocolViolation(f"No complete final signal specification for {family}, h={horizon}.")
    eligible = eligible.sort_values(
        [
            "mean_incremental_log_loss",
            "positive_evaluations",
            "standard_error_incremental_log_loss",
            "signal_spec_id",
        ],
        ascending=[False, False, True, True],
    )
    return eligible.iloc[0]


def select_final_structural_pipeline(
    inner_structural: pd.DataFrame,
    family: str,
    horizon: int,
    required_rows: int,
    brier_tolerance: float,
    ece_tolerance: float,
) -> pd.Series:
    required = {
        "status",
        "signal_family",
        "horizon_candles",
        "outer_fold",
        "inner_fold",
        "pipeline_id",
        "model_family",
        "window_scheme",
        "regime_conditioned",
        "parameters_json",
        "complexity_rank",
        "incremental_log_loss",
        "candidate_brier",
        "benchmark_brier",
        "candidate_ece",
        "benchmark_ece",
    }
    _require_columns(inner_structural, required, "D2B inner structural evidence")
    subset = inner_structural.loc[
        (inner_structural["status"] == "EVALUATED")
        & (inner_structural["signal_family"] == family)
        & (inner_structural["horizon_candles"].astype(int) == int(horizon))
    ].copy()
    identity = [
        "pipeline_id",
        "model_family",
        "window_scheme",
        "regime_conditioned",
        "parameters_json",
        "complexity_rank",
    ]
    grouped = (
        subset.groupby(identity, as_index=False)
        .agg(
            evaluation_rows=("inner_fold", "size"),
            outer_folds=("outer_fold", "nunique"),
            inner_folds=("inner_fold", "nunique"),
            mean_incremental_log_loss=("incremental_log_loss", "mean"),
            standard_error_incremental_log_loss=("incremental_log_loss", _standard_error),
            positive_evaluations=("incremental_log_loss", lambda x: int((pd.Series(x) > 0.0).sum())),
            mean_candidate_brier=("candidate_brier", "mean"),
            mean_benchmark_brier=("benchmark_brier", "mean"),
            mean_candidate_ece=("candidate_ece", "mean"),
            mean_benchmark_ece=("benchmark_ece", "mean"),
        )
    )
    eligible = grouped.loc[
        (grouped["evaluation_rows"] == int(required_rows))
        & (grouped["mean_candidate_brier"] <= grouped["mean_benchmark_brier"] + float(brier_tolerance))
        & (grouped["mean_candidate_ece"] <= grouped["mean_benchmark_ece"] + float(ece_tolerance))
    ].copy()
    if eligible.empty:
        raise ProtocolViolation(f"No complete final structural pipeline for {family}, h={horizon}.")
    eligible = eligible.sort_values(
        [
            "mean_incremental_log_loss",
            "positive_evaluations",
            "standard_error_incremental_log_loss",
            "complexity_rank",
            "pipeline_id",
        ],
        ascending=[False, False, True, True, True],
    )
    return eligible.iloc[0]


def select_final_calibration(
    inner_calibration: pd.DataFrame,
    family: str,
    horizon: int,
    required_rows: int,
) -> pd.Series:
    required = {
        "signal_family",
        "horizon_candles",
        "outer_fold",
        "inner_fold",
        "calibration_method",
        "eligible_for_selection",
        "incremental_log_loss",
        "candidate_brier",
        "candidate_ece",
    }
    _require_columns(inner_calibration, required, "D2B calibration evidence")
    subset = inner_calibration.loc[
        (inner_calibration["signal_family"] == family)
        & (inner_calibration["horizon_candles"].astype(int) == int(horizon))
        & inner_calibration["eligible_for_selection"].astype(bool)
    ].copy()
    grouped = (
        subset.groupby("calibration_method", as_index=False)
        .agg(
            evaluation_rows=("inner_fold", "size"),
            mean_incremental_log_loss=("incremental_log_loss", "mean"),
            positive_evaluations=("incremental_log_loss", lambda x: int((pd.Series(x) > 0.0).sum())),
            mean_candidate_brier=("candidate_brier", "mean"),
            mean_candidate_ece=("candidate_ece", "mean"),
        )
    )
    eligible = grouped.loc[grouped["evaluation_rows"] == int(required_rows)].copy()
    if eligible.empty:
        raise ProtocolViolation(f"No complete final calibration method for {family}, h={horizon}.")
    eligible["calibration_complexity"] = eligible["calibration_method"].map({"none": 0, "sigmoid": 1}).fillna(9)
    eligible = eligible.sort_values(
        [
            "mean_incremental_log_loss",
            "positive_evaluations",
            "mean_candidate_brier",
            "mean_candidate_ece",
            "calibration_complexity",
        ],
        ascending=[False, False, True, True, True],
    )
    return eligible.iloc[0]


def select_final_policy(
    inner_policy: pd.DataFrame,
    family: str,
    horizon: int,
    required_rows: int,
    minimum_coverage: float,
    minimum_decisions: int,
) -> pd.Series:
    required = {
        "signal_family",
        "horizon_candles",
        "outer_fold",
        "inner_fold",
        "threshold",
        "coverage",
        "nonzero_decisions",
        "mean_net_edge",
    }
    _require_columns(inner_policy, required, "D2B policy evidence")
    subset = inner_policy.loc[
        (inner_policy["signal_family"] == family)
        & (inner_policy["horizon_candles"].astype(int) == int(horizon))
    ].copy()
    grouped = (
        subset.groupby("threshold", as_index=False)
        .agg(
            evaluation_rows=("inner_fold", "size"),
            mean_coverage=("coverage", "mean"),
            total_nonzero_decisions=("nonzero_decisions", "sum"),
            mean_net_edge=("mean_net_edge", "mean"),
            positive_evaluations=("mean_net_edge", lambda x: int((pd.Series(x) > 0.0).sum())),
        )
    )
    eligible = grouped.loc[
        (grouped["evaluation_rows"] == int(required_rows))
        & (grouped["mean_coverage"] >= float(minimum_coverage))
        & (grouped["total_nonzero_decisions"] >= int(minimum_decisions))
    ].copy()
    if eligible.empty:
        raise ProtocolViolation(f"No complete final decision policy for {family}, h={horizon}.")
    eligible = eligible.sort_values(
        ["mean_net_edge", "positive_evaluations", "mean_coverage", "threshold"],
        ascending=[False, False, False, True],
    )
    return eligible.iloc[0]


def specification_payload(specification: ScreeningSpecification) -> dict[str, Any]:
    return {
        "signal_spec_id": specification.signal_spec_id,
        "signal_family": specification.signal_family,
        "interpretation": specification.interpretation,
        "period": specification.period,
        "lower_threshold": specification.lower_threshold,
        "upper_threshold": specification.upper_threshold,
        "standard_deviations": specification.standard_deviations,
    }


def pipeline_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
