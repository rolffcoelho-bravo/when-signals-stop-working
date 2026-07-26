from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pandas as pd

from .panic_regime_governance_base import (
    CHALLENGER_MODEL_ID,
    DIAGNOSTICS_SCHEMA_VERSION,
    FAMILY_BLOCK,
    FAMILY_ORDER,
    PANIC_MODEL_IDS,
    PanicRegimeDiagnosticsConfig,
    PanicRegimeDiagnosticsError,
    _logistic,
    _logit,
)


def _ridge_coefficients(x: np.ndarray, y: np.ndarray, penalty: float) -> tuple[np.ndarray, float]:
    design = np.column_stack([np.ones(len(x)), x])
    regularizer = np.eye(design.shape[1]) * penalty
    regularizer[0, 0] = 0.0
    coefficients = np.linalg.solve(design.T @ design + regularizer, design.T @ y)
    prediction = design @ coefficients
    denominator = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - float(np.sum((y - prediction) ** 2)) / denominator if denominator > 0.0 else 0.0
    return coefficients, r2


def build_mechanism_contributions(
    probabilities: pd.DataFrame,
    mechanism: pd.DataFrame,
    config: PanicRegimeDiagnosticsConfig,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    family_columns = [f"{family}_score" for family in FAMILY_ORDER]
    base = mechanism[["timestamp", *family_columns, "evidence_sufficiency"]].copy()
    output: list[dict[str, Any]] = []

    monotone = probabilities.loc[
        probabilities["model_id"].eq("MONOTONE_MECHANISM_SCORE_V1")
    ][["timestamp", "raw_probability", "filtered_probability"]]
    monotone = base.merge(monotone, on="timestamp", how="left", sort=True)
    for row in monotone.itertuples(index=False):
        scores = {family: getattr(row, f"{family}_score") for family in FAMILY_ORDER}
        available = [family for family, value in scores.items() if np.isfinite(value)]
        if row.evidence_sufficiency != "SUFFICIENT" or not available or not np.isfinite(row.raw_probability):
            continue
        count = len(available)
        for family in available:
            contribution_logit = config.monotone_logistic_slope * (scores[family] - 0.5) / count
            counterfactual_scores = [0.5 if name == family else scores[name] for name in available]
            counterfactual_composite = float(np.mean(counterfactual_scores))
            counterfactual_probability = float(
                _logistic(
                    config.monotone_logistic_slope * (counterfactual_composite - 0.5)
                )
            )
            output.append(
                {
                    "timestamp": row.timestamp,
                    "model_id": "MONOTONE_MECHANISM_SCORE_V1",
                    "family": family,
                    "contribution_method": "EXACT_EQUAL_WEIGHT_LOGIT_AND_NEUTRAL_PERTURBATION",
                    "family_score": float(scores[family]),
                    "logit_contribution": float(contribution_logit),
                    "full_probability": float(row.raw_probability),
                    "counterfactual_probability": counterfactual_probability,
                    "probability_contribution": float(row.raw_probability - counterfactual_probability),
                    "surrogate_r2": np.nan,
                    "status": "VALID_EXACT_MONOTONE_DECOMPOSITION",
                }
            )

    hmm = probabilities.loc[
        probabilities["model_id"].eq("CAUSAL_GAUSSIAN_HMM_V1")
    ][["timestamp", "filtered_probability"]]
    hmm = base.merge(hmm, on="timestamp", how="left", sort=True).reset_index(drop=True)
    coefficients: np.ndarray | None = None
    surrogate_r2: float | None = None
    refits: list[dict[str, Any]] = []
    for index, row in hmm.iterrows():
        probability = float(row["filtered_probability"]) if pd.notna(row["filtered_probability"]) else np.nan
        if index >= config.contribution_minimum_history and (
            coefficients is None
            or (index - config.contribution_minimum_history) % config.contribution_refit_interval == 0
        ):
            history = hmm.iloc[:index].copy()
            valid = history["filtered_probability"].notna()
            if int(valid.sum()) >= config.contribution_minimum_history:
                x = history.loc[valid, family_columns].fillna(0.5).to_numpy(dtype=float)
                y = _logit(history.loc[valid, "filtered_probability"].to_numpy(dtype=float))
                coefficients, surrogate_r2 = _ridge_coefficients(
                    x, y, config.contribution_ridge_penalty
                )
                refits.append(
                    {
                        "forecast_origin_index": int(index),
                        "forecast_origin_timestamp": row["timestamp"].isoformat(),
                        "training_rows": int(len(y)),
                        "r2": float(surrogate_r2),
                    }
                )
        if coefficients is None or not np.isfinite(probability):
            continue
        scores = np.asarray(
            [0.5 if pd.isna(row[column]) else float(row[column]) for column in family_columns],
            dtype=float,
        )
        current_logit = float(_logit(np.array([probability]))[0])
        for family_position, family in enumerate(FAMILY_ORDER):
            observed_score = row[f"{family}_score"]
            if not np.isfinite(observed_score):
                continue
            effect = float(coefficients[family_position + 1] * (float(observed_score) - 0.5))
            counterfactual_probability = float(_logistic(current_logit - effect))
            output.append(
                {
                    "timestamp": row["timestamp"],
                    "model_id": "CAUSAL_GAUSSIAN_HMM_V1",
                    "family": family,
                    "contribution_method": "CAUSAL_RIDGE_SURROGATE_NEUTRAL_PERTURBATION",
                    "family_score": float(observed_score),
                    "logit_contribution": effect,
                    "full_probability": probability,
                    "counterfactual_probability": counterfactual_probability,
                    "probability_contribution": probability - counterfactual_probability,
                    "surrogate_r2": float(surrogate_r2) if surrogate_r2 is not None else np.nan,
                    "status": "VALID_DIAGNOSTIC_SURROGATE_NOT_EXACT_HMM_DECOMPOSITION",
                }
            )
    frame = pd.DataFrame(output)
    if not frame.empty:
        frame = frame.sort_values(["timestamp", "model_id", "family"], kind="mergesort").reset_index(drop=True)
    diagnostics = {
        "monotone_method": "EXACT_EQUAL_WEIGHT_LOGIT_AND_NEUTRAL_PERTURBATION",
        "hmm_method": "CAUSAL_RIDGE_SURROGATE_NEUTRAL_PERTURBATION",
        "hmm_surrogate_refits": refits,
        "hmm_semantic_boundary": (
            "The HMM contribution diagnostic is a causal surrogate perturbation around the "
            "observed posterior. It is not an exact decomposition of the HMM likelihood."
        ),
    }
    return frame, diagnostics


def build_cross_model_disagreement(
    probabilities: pd.DataFrame,
    config: PanicRegimeDiagnosticsConfig,
) -> pd.DataFrame:
    columns = ["timestamp", "filtered_probability", "lower_95", "upper_95", "probability_publishable"]
    monotone = probabilities.loc[
        probabilities["model_id"].eq("MONOTONE_MECHANISM_SCORE_V1"), columns
    ].rename(columns={
        "filtered_probability": "monotone_probability",
        "lower_95": "monotone_lower_95",
        "upper_95": "monotone_upper_95",
        "probability_publishable": "monotone_publishable",
    })
    hmm = probabilities.loc[
        probabilities["model_id"].eq("CAUSAL_GAUSSIAN_HMM_V1"), columns
    ].rename(columns={
        "filtered_probability": "hmm_probability",
        "lower_95": "hmm_lower_95",
        "upper_95": "hmm_upper_95",
        "probability_publishable": "hmm_publishable",
    })
    output = monotone.merge(hmm, on="timestamp", how="outer", sort=True)
    valid = output[["monotone_probability", "hmm_probability"]].notna().all(axis=1)
    output["signed_probability_difference"] = (
        output["monotone_probability"] - output["hmm_probability"]
    ).where(valid)
    output["disagreement_index"] = output["signed_probability_difference"].abs()
    output["disagreement_class"] = "INSUFFICIENT_MODEL_EVIDENCE"
    output.loc[
        valid & (output["disagreement_index"] < config.disagreement_moderate_threshold),
        "disagreement_class",
    ] = "LOW"
    output.loc[
        valid
        & (output["disagreement_index"] >= config.disagreement_moderate_threshold)
        & (output["disagreement_index"] < config.disagreement_high_threshold),
        "disagreement_class",
    ] = "MODERATE"
    output.loc[
        valid & (output["disagreement_index"] >= config.disagreement_high_threshold),
        "disagreement_class",
    ] = "HIGH_MODEL_RISK_ESCALATION"
    intervals = output[[
        "monotone_lower_95",
        "monotone_upper_95",
        "hmm_lower_95",
        "hmm_upper_95",
    ]].notna().all(axis=1)
    output["intervals_overlap"] = pd.Series(pd.NA, index=output.index, dtype="boolean")
    output.loc[intervals, "intervals_overlap"] = (
        np.maximum(output.loc[intervals, "monotone_lower_95"], output.loc[intervals, "hmm_lower_95"])
        <= np.minimum(output.loc[intervals, "monotone_upper_95"], output.loc[intervals, "hmm_upper_95"])
    )
    output["diagnostic_only"] = True
    output["model_selection_performed"] = False
    output["ensemble_probability_produced"] = False
    return output.sort_values("timestamp", kind="mergesort").reset_index(drop=True)


def build_mechanism_coverage(
    market_structure: pd.DataFrame,
    causal_series: pd.DataFrame,
    engine_diagnostics: Mapping[str, Any],
    dependence_window: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    feature_registry = engine_diagnostics.get("feature_registry")
    if not isinstance(feature_registry, Mapping) or not feature_registry:
        raise PanicRegimeDiagnosticsError("Engine diagnostics feature_registry is missing.")
    market = market_structure.copy()
    market["timestamp"] = pd.to_datetime(market["timestamp"], utc=True, errors="coerce")
    market = market.loc[pd.to_numeric(market["window"], errors="coerce").eq(dependence_window)].copy()
    series = causal_series.copy()
    series["timestamp"] = pd.to_datetime(series["timestamp"], utc=True, errors="coerce")
    series["series_id"] = series["series_id"].astype("string").str.strip()
    rows: list[dict[str, Any]] = []

    for feature_name, metadata in sorted(feature_registry.items()):
        if not isinstance(metadata, Mapping):
            continue
        family = str(metadata["family"])
        source = str(metadata["source"])
        source_column = str(metadata["source_column"])
        if source == "market":
            if source_column not in market:
                continue
            for row in market[["timestamp", "eligibility_status", source_column]].itertuples(index=False):
                rows.append({
                    "timestamp": row.timestamp,
                    "series_id": "__MARKET_PANEL__",
                    "source_level": "MARKET",
                    "feature": feature_name,
                    "source_column": source_column,
                    "family": family,
                    "evidence_block": FAMILY_BLOCK[family],
                    "available": bool(row.eligibility_status == "ELIGIBLE" and np.isfinite(getattr(row, source_column))),
                    "governed_exclusion": False,
                    "exclusion_reason": "",
                })
        else:
            if source_column not in series:
                continue
            for row in series[["timestamp", "series_id", source_column]].itertuples(index=False):
                rows.append({
                    "timestamp": row.timestamp,
                    "series_id": str(row.series_id),
                    "source_level": "ASSET_VENUE",
                    "feature": feature_name,
                    "source_column": source_column,
                    "family": family,
                    "evidence_block": FAMILY_BLOCK[family],
                    "available": bool(np.isfinite(getattr(row, source_column))),
                    "governed_exclusion": False,
                    "exclusion_reason": "",
                })

    if "contagion_radius" in market:
        for row in market[["timestamp", "contagion_radius"]].itertuples(index=False):
            rows.append({
                "timestamp": row.timestamp,
                "series_id": "__MARKET_PANEL__",
                "source_level": "MARKET",
                "feature": "network__contagion_radius",
                "source_column": "contagion_radius",
                "family": "network",
                "evidence_block": "STRUCTURAL",
                "available": bool(np.isfinite(row.contagion_radius)),
                "governed_exclusion": True,
                "exclusion_reason": "AMBIGUOUS_MONOTONE_PANIC_DIRECTION",
            })
    coverage = pd.DataFrame(rows)
    if coverage.empty:
        raise PanicRegimeDiagnosticsError("No mechanism coverage rows could be constructed.")
    coverage = coverage.sort_values(
        ["timestamp", "family", "feature", "series_id"], kind="mergesort"
    ).reset_index(drop=True)

    admitted = coverage.loc[~coverage["governed_exclusion"]].copy()
    by_family = {}
    for family, group in admitted.groupby("family", sort=True):
        share = float(group["available"].mean()) if len(group) else 0.0
        by_family[family] = {
            "rows": int(len(group)),
            "available_rows": int(group["available"].sum()),
            "coverage_share": share,
            "missing_share": 1.0 - share,
            "data_investment_priority": (
                "HIGH"
                if FAMILY_BLOCK[family] == "MARKET_PLUMBING" and share < 0.50
                else "MEDIUM" if share < 0.80 else "LOW"
            ),
        }
    by_feature = {
        feature: {
            "family": str(group["family"].iloc[0]),
            "rows": int(len(group)),
            "coverage_share": float(group["available"].mean()),
        }
        for feature, group in admitted.groupby("feature", sort=True)
    }
    by_series = {
        series_id: {
            "rows": int(len(group)),
            "coverage_share": float(group["available"].mean()),
        }
        for series_id, group in admitted.groupby("series_id", sort=True)
    }
    summary = {
        "schema_version": DIAGNOSTICS_SCHEMA_VERSION,
        "by_family": by_family,
        "by_feature": by_feature,
        "by_series_id": by_series,
        "governed_exclusions": sorted(
            coverage.loc[coverage["governed_exclusion"], "feature"].unique().tolist()
        ),
        "coverage_used_for_model_selection": False,
    }
    return coverage, summary
