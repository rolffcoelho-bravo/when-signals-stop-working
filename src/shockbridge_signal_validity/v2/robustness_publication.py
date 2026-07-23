from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RobustnessClassification:
    determination: str
    fragility_class: str
    favourable_diagnostics: int
    caution_diagnostics: int
    failed_diagnostics: int


def matched_policy_contributions(
    frame: pd.DataFrame,
    probability_distance_threshold: float,
    one_way_cost_bps: float,
) -> pd.DataFrame:
    required = {
        "candidate_probability",
        "benchmark_probability",
        "future_return",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError("Missing policy columns: " + ", ".join(missing))

    result = frame.copy()
    candidate_probability = result["candidate_probability"].to_numpy(float)
    benchmark_probability = result["benchmark_probability"].to_numpy(float)
    future_return = result["future_return"].to_numpy(float)
    threshold = float(probability_distance_threshold)

    candidate_active = np.abs(candidate_probability - 0.5) > threshold
    benchmark_active = np.abs(benchmark_probability - 0.5) > threshold

    candidate_position = np.where(
        candidate_active,
        np.where(candidate_probability > 0.5, 1.0, -1.0),
        0.0,
    )
    benchmark_position = np.where(
        benchmark_active,
        np.where(benchmark_probability > 0.5, 1.0, -1.0),
        0.0,
    )

    candidate_prior = np.concatenate([[0.0], candidate_position[:-1]])
    benchmark_prior = np.concatenate([[0.0], benchmark_position[:-1]])
    candidate_turnover = np.abs(candidate_position - candidate_prior)
    benchmark_turnover = np.abs(benchmark_position - benchmark_prior)
    cost = float(one_way_cost_bps) / 10000.0

    result["candidate_decision_active"] = candidate_active
    result["benchmark_decision_active"] = benchmark_active
    result["candidate_position"] = candidate_position
    result["benchmark_position"] = benchmark_position
    result["candidate_turnover_units"] = candidate_turnover
    result["benchmark_turnover_units"] = benchmark_turnover
    result["candidate_net_return"] = candidate_position * future_return - candidate_turnover * cost
    result["benchmark_net_return"] = benchmark_position * future_return - benchmark_turnover * cost
    result["incremental_net_return"] = (
        result["candidate_net_return"] - result["benchmark_net_return"]
    )
    result["candidate_confidence_distance"] = np.abs(candidate_probability - 0.5)
    return result


def leave_one_group_out_summary(
    frame: pd.DataFrame,
    group_column: str,
    predictive_column: str,
    economic_column: str,
) -> pd.DataFrame:
    required = {group_column, predictive_column, economic_column}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError("Missing leave-one-group-out columns: " + ", ".join(missing))

    rows: list[dict[str, object]] = []
    groups = sorted(frame[group_column].dropna().astype(str).unique())
    for group in groups:
        retained = frame.loc[frame[group_column].astype(str) != group]
        rows.append(
            {
                "excluded_group": group,
                "retained_rows": int(len(retained)),
                "mean_incremental_log_loss": float(retained[predictive_column].mean()),
                "predictive_mean_positive": bool(retained[predictive_column].mean() > 0.0),
                "mean_incremental_net_return_10bps": float(retained[economic_column].mean()),
                "economic_mean_positive": bool(retained[economic_column].mean() > 0.0),
            }
        )
    return pd.DataFrame(rows)


def joint_influence_trim_summary(
    frame: pd.DataFrame,
    predictive_column: str,
    economic_column: str,
    trim_fractions: Iterable[float],
) -> pd.DataFrame:
    required = {predictive_column, economic_column}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError("Missing influence columns: " + ", ".join(missing))

    rows: list[dict[str, object]] = []
    for raw_fraction in trim_fractions:
        fraction = float(raw_fraction)
        if not 0.0 <= fraction < 0.5:
            raise ValueError("Trim fractions must be in [0, 0.5).")

        if fraction == 0.0:
            retained = frame
        else:
            predictive_bounds = frame[predictive_column].quantile(
                [fraction, 1.0 - fraction]
            )
            economic_bounds = frame[economic_column].quantile(
                [fraction, 1.0 - fraction]
            )
            mask = frame[predictive_column].between(
                float(predictive_bounds.iloc[0]),
                float(predictive_bounds.iloc[1]),
            ) & frame[economic_column].between(
                float(economic_bounds.iloc[0]),
                float(economic_bounds.iloc[1]),
            )
            retained = frame.loc[mask]

        rows.append(
            {
                "joint_tail_trim_fraction": fraction,
                "retained_rows": int(len(retained)),
                "retained_share": float(len(retained) / len(frame)),
                "mean_incremental_log_loss": float(retained[predictive_column].mean()),
                "predictive_mean_positive": bool(retained[predictive_column].mean() > 0.0),
                "mean_incremental_net_return_10bps": float(retained[economic_column].mean()),
                "economic_mean_positive": bool(retained[economic_column].mean() > 0.0),
            }
        )
    return pd.DataFrame(rows)


def state_stratification(
    frame: pd.DataFrame,
    minimum_interpretable_rows: int,
) -> pd.DataFrame:
    required = {
        "state_label",
        "state_p_stress",
        "incremental_observation_log_loss",
        "incremental_net_return",
        "candidate_decision_active",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError("Missing state-stratification columns: " + ", ".join(missing))

    table = (
        frame.groupby("state_label", sort=True)
        .agg(
            rows=("state_label", "size"),
            mean_state_p_stress=("state_p_stress", "mean"),
            candidate_coverage=("candidate_decision_active", "mean"),
            mean_incremental_log_loss=("incremental_observation_log_loss", "mean"),
            mean_incremental_net_return_10bps=("incremental_net_return", "mean"),
        )
        .reset_index()
    )
    table["sample_share"] = table["rows"] / int(len(frame))
    table["minimum_interpretable_rows"] = int(minimum_interpretable_rows)
    table["descriptively_interpretable"] = (
        table["rows"] >= int(minimum_interpretable_rows)
    )
    table["confirmatory_effect"] = "NONE_DIAGNOSTIC_ONLY"
    return table


def active_confidence_stratification(
    frame: pd.DataFrame,
    quantiles: int,
) -> pd.DataFrame:
    required = {
        "candidate_decision_active",
        "candidate_confidence_distance",
        "incremental_observation_log_loss",
        "incremental_net_return",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError("Missing confidence-stratification columns: " + ", ".join(missing))

    active = frame.loc[frame["candidate_decision_active"]].copy()
    if len(active) < int(quantiles):
        raise ValueError("Insufficient active decisions for confidence stratification.")

    labels = [f"Q{index + 1}" for index in range(int(quantiles))]
    active["active_confidence_stratum"] = pd.qcut(
        active["candidate_confidence_distance"],
        q=int(quantiles),
        labels=labels,
        duplicates="drop",
    )

    table = (
        active.groupby("active_confidence_stratum", sort=True, observed=True)
        .agg(
            rows=("active_confidence_stratum", "size"),
            minimum_confidence_distance=("candidate_confidence_distance", "min"),
            maximum_confidence_distance=("candidate_confidence_distance", "max"),
            mean_confidence_distance=("candidate_confidence_distance", "mean"),
            mean_incremental_log_loss=("incremental_observation_log_loss", "mean"),
            mean_incremental_net_return_10bps=("incremental_net_return", "mean"),
        )
        .reset_index()
    )
    table["predictive_mean_positive"] = table["mean_incremental_log_loss"] > 0.0
    table["economic_mean_positive"] = (
        table["mean_incremental_net_return_10bps"] > 0.0
    )
    table["confirmatory_effect"] = "NONE_DIAGNOSTIC_ONLY"
    return table


def _signal_components(signal_specification: str) -> dict[str, str]:
    text = str(signal_specification)
    period = re.search(r"-p([0-9]+)", text)
    width = re.search(r"-k([0-9.]+)", text)
    interpretation = text.rsplit("-", maxsplit=1)[-1]
    return {
        "signal_period": period.group(1) if period else "UNKNOWN",
        "signal_width": width.group(1) if width else "UNKNOWN",
        "signal_interpretation": interpretation,
    }


def development_component_stability(
    outer_results: pd.DataFrame,
    signal_family: str,
    horizon_candles: int,
) -> pd.DataFrame:
    selected = outer_results.loc[
        outer_results["signal_family"].astype(str).eq(str(signal_family))
        & outer_results["horizon_candles"].astype(int).eq(int(horizon_candles))
    ].copy()
    if selected.empty:
        raise ValueError("No development rows match the frozen family and horizon.")

    selected["regime_conditioned"] = selected["regime_conditioned"].astype(str)
    signal_components = selected["selected_signal_spec_id"].map(_signal_components)
    for column in ("signal_period", "signal_width", "signal_interpretation"):
        selected[column] = [component[column] for component in signal_components]

    components = {
        "model_family": "model_family",
        "window_scheme": "window_scheme",
        "regime_conditioning": "regime_conditioned",
        "calibration_method": "selected_calibration_method",
        "decision_threshold": "selected_threshold",
        "signal_specification": "selected_signal_spec_id",
        "signal_period": "signal_period",
        "signal_width": "signal_width",
        "signal_interpretation": "signal_interpretation",
    }

    rows: list[dict[str, object]] = []
    for component, column in components.items():
        counts = selected[column].astype(str).value_counts(dropna=False)
        modal_value = str(counts.index[0])
        modal_count = int(counts.iloc[0])
        share = float(modal_count / len(selected))
        if share >= 0.80:
            classification = "STABLE"
        elif share >= 0.60:
            classification = "MODERATELY_STABLE"
        else:
            classification = "DIFFUSE"
        rows.append(
            {
                "component": component,
                "outer_development_rows": int(len(selected)),
                "unique_values": int(len(counts)),
                "modal_value": modal_value,
                "modal_count": modal_count,
                "modal_share": share,
                "stability_classification": classification,
                "holdout_reexecution_performed": False,
            }
        )
    return pd.DataFrame(rows)


def robustness_classification(matrix: pd.DataFrame) -> RobustnessClassification:
    if "diagnostic_status" not in matrix.columns:
        raise ValueError("Robustness matrix requires diagnostic_status.")

    counts = matrix["diagnostic_status"].astype(str).value_counts()
    passed = int(counts.get("PASS", 0))
    caution = int(counts.get("CAUTION", 0))
    failed = int(counts.get("FAIL", 0))

    if failed > 0:
        determination = "FAVOURABLE_MEANS_NOT_CONFIDENCE_ROBUST"
        fragility = "UNCERTAINTY_AND_PARAMETER_SPECIFICATION_SENSITIVE"
    elif caution > 0:
        determination = "MIXED_DIAGNOSTIC_STABILITY"
        fragility = "MODERATE_DIAGNOSTIC_FRAGILITY"
    else:
        determination = "BROAD_DIAGNOSTIC_STABILITY"
        fragility = "LOW_OBSERVED_DIAGNOSTIC_FRAGILITY"

    return RobustnessClassification(
        determination=determination,
        fragility_class=fragility,
        favourable_diagnostics=passed,
        caution_diagnostics=caution,
        failed_diagnostics=failed,
    )


def canonical_json_sha256(payload: object) -> str:
    import hashlib

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
