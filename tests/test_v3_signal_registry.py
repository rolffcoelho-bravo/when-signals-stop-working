from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from shockbridge_signal_validity.v3.signal_registry import (
    SignalRegistryError,
    build_registry_manifest,
    load_registry,
    parse_signal_id,
    validate_registry,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configs" / "v3_signal_interpretation_registry.json"


def registry_value() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_registry_is_bounded_target_blind_and_nonselective() -> None:
    value = registry_value()
    specs = validate_registry(value)
    assert len(specs) == 48
    assert len(specs) <= value["bounded_candidate_limit"] == 128
    assert value["automatic_selection_performed"] is False
    assert value["target_access_permitted"] is False
    assert value["chronology_access_permitted"] is False
    assert value["predictive_claims_permitted"] is False
    assert value["economic_claims_permitted"] is False
    assert value["failure_claims_permitted"] is False


def test_every_signal_identifier_round_trips_complete_specification() -> None:
    for spec in validate_registry(registry_value()):
        parsed = parse_signal_id(spec.signal_id)
        assert parsed["family"] == spec.signal_family
        assert parsed["window"] == spec.lookback_or_window
        assert parsed["parameter"] == dict(spec.threshold_or_band_parameter)
        assert parsed["interpretation"] == spec.interpretation
        assert parsed["regime"] == spec.regime_interaction_policy
        assert parsed["parameter_policy"] == spec.parameter_policy


def test_registry_contains_required_families_interpretations_and_templates() -> None:
    specs = validate_registry(registry_value())
    interpretations = {(spec.signal_family, spec.interpretation) for spec in specs}
    required = {
        ("RSI", "RSI_OVERSOLD_MEAN_REVERSION"),
        ("RSI", "RSI_OVERBOUGHT_CONTINUATION"),
        ("RSI", "RSI_THRESHOLD_BREAK_CONTINUATION"),
        ("RSI", "RSI_BULLISH_DIVERGENCE"),
        ("BOLLINGER", "BB_LOWER_MEAN_REVERSION"),
        ("BOLLINGER", "BB_UPPER_BREAKOUT"),
        ("BOLLINGER", "BB_PERCENT_B"),
        ("BOLLINGER", "BB_SQUEEZE"),
        ("BOLLINGER", "BB_POST_SQUEEZE_EXPANSION"),
    }
    assert required.issubset(interpretations)
    assert sum(spec.parameter_policy == "TRAINING_ONLY_REQUIRED" for spec in specs) == 2
    assert sum(spec.regime_interaction_policy != "NONE" for spec in specs) == 4


def test_registry_manifest_records_no_selection_or_target_access() -> None:
    manifest = build_registry_manifest(registry_value())
    assert manifest["signal_count"] == 48
    assert manifest["base_signal_count"] == 44
    assert manifest["interaction_signal_count"] == 4
    assert manifest["adaptive_template_count"] == 2
    assert manifest["automatic_selection_performed"] is False
    assert manifest["target_accessed"] is False
    assert manifest["chronology_accessed"] is False


def test_registry_rejects_unsupported_interpretation() -> None:
    value = copy.deepcopy(registry_value())
    value["signals"][0]["interpretation"] = "TAMPERED"
    with pytest.raises(SignalRegistryError, match="Unsupported family or interpretation"):
        validate_registry(value)


def test_registry_rejects_automatic_selection_or_chronology_access() -> None:
    value = copy.deepcopy(registry_value())
    value["automatic_selection_performed"] = True
    with pytest.raises(SignalRegistryError, match="automatic_selection_performed"):
        validate_registry(value)
    value = copy.deepcopy(registry_value())
    value["chronology_access_permitted"] = True
    with pytest.raises(SignalRegistryError, match="chronology_access_permitted"):
        validate_registry(value)


def test_load_registry_validates_committed_object() -> None:
    loaded = load_registry(REGISTRY)
    assert loaded == registry_value()
