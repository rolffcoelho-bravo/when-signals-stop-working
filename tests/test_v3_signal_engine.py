from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v3.signal_engine import (
    SignalEngineError,
    compute_signal_feature_frame,
)
from shockbridge_signal_validity.v3.signal_math import wilder_rsi
from shockbridge_signal_validity.v3.signal_registry import validate_registry

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configs" / "v3_signal_interpretation_registry.json"


def registry_value() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def fixture(rows: int = 120) -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-01", periods=rows, freq="4h", tz="UTC")
    pieces: list[pd.DataFrame] = []
    for offset, asset in enumerate(("SOL", "BTC")):
        x = np.arange(rows, dtype=float)
        close = 100.0 + 20.0 * offset + 0.05 * x + 2.0 * np.sin(x / 5.0 + offset)
        pieces.append(
            pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "asset": asset,
                    "venue": "binance",
                    "open": close - 0.1,
                    "high": close + 0.5,
                    "low": close - 0.5,
                    "close": close,
                    "volume": 1000.0 + 10.0 * np.cos(x / 7.0),
                }
            )
        )
    return pd.concat(pieces, ignore_index=True)


def ordered(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.sort_values(
        ["timestamp", "asset", "venue", "signal_id"], kind="mergesort"
    ).reset_index(drop=True)


def test_engine_emits_every_registered_signal_for_every_source_row() -> None:
    source = fixture()
    specs = validate_registry(registry_value())
    result = compute_signal_feature_frame(source, registry_value())
    assert len(result.frame) == len(source) * len(specs)
    assert result.frame["signal_id"].nunique() == len(specs) == 48
    assert result.frame["feature_key"].nunique() == 48
    assert result.feature_manifest["source_rows"] == len(source)
    assert result.feature_manifest["automatic_selection_performed"] is False
    assert result.validation_report["target_accessed"] is False
    assert result.validation_report["chronology_accessed"] is False
    assert result.validation_report["next_gate"] == "V3-5"

    reference = pd.Series(
        [
            44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10,
            45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28,
            46.28, 46.00, 46.03, 46.41, 46.22, 45.64, 46.21,
        ]
    )
    calculated = wilder_rsi(reference, 14)
    initial_up = reference.diff().clip(lower=0.0).iloc[1:15].mean()
    initial_down = (-reference.diff().clip(upper=0.0)).iloc[1:15].mean()
    expected_initial = 100.0 - 100.0 / (1.0 + initial_up / initial_down)
    assert calculated.iloc[:14].isna().all()
    assert calculated.iloc[14] == pytest.approx(expected_initial)
    recursive_up = (
        13.0 * initial_up + max(reference.iloc[15] - reference.iloc[14], 0.0)
    ) / 14.0
    recursive_down = (
        13.0 * initial_down + max(reference.iloc[14] - reference.iloc[15], 0.0)
    ) / 14.0
    expected_next = 100.0 - 100.0 / (1.0 + recursive_up / recursive_down)
    assert calculated.iloc[15] == pytest.approx(expected_next)


def test_engine_preserves_early_history_and_ineligible_templates() -> None:
    result = compute_signal_feature_frame(fixture(), registry_value())
    counts = result.frame["eligibility_status"].value_counts()
    assert counts["ELIGIBLE"] > 0
    assert counts["INSUFFICIENT_HISTORY_OR_UNDEFINED"] > 0
    assert counts["INELIGIBLE_TRAINING_PARAMETER_REQUIRED"] > 0
    assert counts["INELIGIBLE_CONTEXT_UNAVAILABLE"] > 0
    assert result.coverage_report["automatic_candidate_deletion_performed"] is False


def test_future_append_cannot_change_earlier_features() -> None:
    source = fixture(120)
    extended_source = fixture(132)
    original = compute_signal_feature_frame(source, registry_value()).frame
    extended = compute_signal_feature_frame(extended_source, registry_value()).frame
    earlier = extended.loc[extended["timestamp"] <= source["timestamp"].max()]
    pd.testing.assert_frame_equal(ordered(original), ordered(earlier), check_dtype=False)


def test_input_row_order_cannot_change_ordered_output_identity() -> None:
    source = fixture()
    shuffled = source.sample(frac=1.0, random_state=17).reset_index(drop=True)
    first = compute_signal_feature_frame(source, registry_value())
    second = compute_signal_feature_frame(shuffled, registry_value())
    pd.testing.assert_frame_equal(first.frame, second.frame, check_dtype=False)
    assert first.feature_manifest["output_sha256"] == second.feature_manifest["output_sha256"]
    assert first.feature_manifest["manifest_sha256"] == second.feature_manifest["manifest_sha256"]


def test_training_only_templates_require_external_training_parameters() -> None:
    specs = validate_registry(registry_value())
    adaptive = [spec for spec in specs if spec.parameter_policy == "TRAINING_ONLY_REQUIRED"]
    parameters = {
        spec.feature_key: (
            {"lower": 25.0, "upper": 75.0}
            if spec.signal_family == "RSI"
            else {"squeeze_threshold": 0.06}
        )
        for spec in adaptive
    }
    result = compute_signal_feature_frame(
        fixture(),
        registry_value(),
        training_only_parameters=parameters,
    )
    for spec in adaptive:
        statuses = result.frame.loc[
            result.frame["signal_id"] == spec.signal_id,
            "eligibility_status",
        ]
        assert (statuses == "ELIGIBLE").any()
    assert result.feature_manifest["training_only_parameter_sets_supplied"] == 2
    assert result.validation_report["adaptive_parameters_estimated_by_engine"] is False


def test_invalid_training_only_parameters_fail_closed() -> None:
    specs = validate_registry(registry_value())
    rsi_adaptive = next(
        spec
        for spec in specs
        if spec.signal_family == "RSI"
        and spec.parameter_policy == "TRAINING_ONLY_REQUIRED"
    )
    with pytest.raises(SignalEngineError, match="thresholds are invalid"):
        compute_signal_feature_frame(
            fixture(),
            registry_value(),
            training_only_parameters={
                rsi_adaptive.feature_key: {"lower": 80.0, "upper": 20.0}
            },
        )
    with pytest.raises(
        SignalEngineError,
        match="unregistered or non-adaptive feature keys",
    ):
        compute_signal_feature_frame(
            fixture(),
            registry_value(),
            training_only_parameters={"unknown": {"lower": 25.0, "upper": 75.0}},
        )


def test_registered_interactions_preserve_base_and_context_components() -> None:
    source = fixture()
    context = source[["timestamp", "asset", "venue"]].copy()
    context["p_range"] = 0.50
    context["p_trend"] = 0.30
    context["p_panic_consistent"] = 0.10
    context["dominant_eigenvalue_share"] = 0.70
    result = compute_signal_feature_frame(
        source,
        registry_value(),
        context_frame=context,
    )
    interactions = result.frame.loc[
        result.frame["regime_interaction_policy"]
        == "MULTIPLY_CONTEXT_PRESERVE_COMPONENTS"
    ]
    eligible = interactions.loc[interactions["eligibility_status"] == "ELIGIBLE"]
    assert not eligible.empty
    np.testing.assert_allclose(
        eligible["feature_value"].to_numpy(),
        (eligible["base_signal_value"] * eligible["context_value"]).to_numpy(),
    )
    assert result.validation_report["interaction_components_preserved"] is True

    invalid_context = context.copy()
    invalid_context.loc[0, "p_range"] = 1.2
    with pytest.raises(SignalEngineError, match=r"must be in \[0, 1\]"):
        compute_signal_feature_frame(
            source,
            registry_value(),
            context_frame=invalid_context,
        )


def test_missing_required_ohlcv_or_duplicate_keys_fail_closed() -> None:
    source = fixture()
    with pytest.raises(SignalEngineError, match="Missing canonical columns"):
        compute_signal_feature_frame(source.drop(columns=["close"]), registry_value())
    duplicated = pd.concat([source, source.iloc[[0]]], ignore_index=True)
    with pytest.raises(SignalEngineError, match="Duplicate canonical keys"):
        compute_signal_feature_frame(duplicated, registry_value())
    invalid_bounds = source.copy()
    invalid_bounds.loc[0, "high"] = invalid_bounds.loc[0, "close"] - 1.0
    with pytest.raises(SignalEngineError, match="violate low/high bounds"):
        compute_signal_feature_frame(invalid_bounds, registry_value())


def test_gate_produces_no_predictive_economic_deterioration_or_failure_claim() -> None:
    result = compute_signal_feature_frame(fixture(), registry_value())
    for field in (
        "predictive_claims_produced",
        "economic_claims_produced",
        "deterioration_claims_produced",
        "failure_claims_produced",
    ):
        assert result.validation_report[field] is False
        assert result.feature_manifest[field] is False
    assert result.feature_manifest["frozen_v1_v2_determinations_modified"] is False
