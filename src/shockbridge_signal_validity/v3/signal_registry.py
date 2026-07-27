from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, unquote

REGISTRY_SCHEMA_VERSION = "v3.signal-interpretation-registry.v1"
MAX_REGISTERED_SIGNALS = 128
_REQUIRED = (
    "signal_family", "lookback_or_window", "threshold_or_band_parameter",
    "orientation", "interpretation", "crossing_rule", "persistence_rule",
    "normalisation_rule", "regime_interaction_policy", "registry_version",
    "parameter_policy",
)
_RSI = {
    "RSI_LEVEL", "RSI_CENTERED_SCALED", "RSI_SLOPE", "RSI_ACCELERATION",
    "RSI_ROLLING_RANGE", "RSI_BULLISH_DIVERGENCE", "RSI_BEARISH_DIVERGENCE",
    "RSI_OVERSOLD_MEAN_REVERSION", "RSI_OVERBOUGHT_MEAN_REVERSION",
    "RSI_TWO_SIDED_MEAN_REVERSION", "RSI_OVERBOUGHT_CONTINUATION",
    "RSI_OVERSOLD_CONTINUATION", "RSI_THRESHOLD_BREAK_CONTINUATION",
    "RSI_CROSS_UPPER", "RSI_CROSS_LOWER", "RSI_TIME_ABOVE_UPPER",
    "RSI_TIME_BELOW_LOWER", "RSI_EXTREME_PERSISTENCE",
    "RSI_TIME_SINCE_CROSSING", "RSI_EXIT_EXTREME",
}
_BB = {
    "BB_PERCENT_B", "BB_MIDDLE_DISTANCE", "BB_NEAREST_OUTER_DISTANCE",
    "BB_DISTANCE_MAGNITUDE", "BB_UPPER_MEAN_REVERSION",
    "BB_LOWER_MEAN_REVERSION", "BB_REENTRY_AFTER_OUTSIDE",
    "BB_UPPER_BREAKOUT", "BB_LOWER_BREAKDOWN", "BB_OUTSIDE_CONTINUATION",
    "BB_BANDWIDTH", "BB_BANDWIDTH_CHANGE", "BB_BANDWIDTH_ACCELERATION",
    "BB_SQUEEZE", "BB_POST_SQUEEZE_EXPANSION", "BB_EXPANSION_PERSISTENCE",
    "BB_CROSS_UPPER", "BB_CROSS_LOWER", "BB_TIME_OUTSIDE",
    "BB_CONSECUTIVE_OUTSIDE", "BB_REENTRY_TIMING",
    "BB_TIME_SINCE_SQUEEZE_RELEASE",
}

class SignalRegistryError(ValueError):
    pass

@dataclass(frozen=True)
class SignalSpec:
    signal_id: str
    signal_family: str
    lookback_or_window: int
    threshold_or_band_parameter: Mapping[str, Any]
    orientation: str
    interpretation: str
    crossing_rule: str
    persistence_rule: str
    normalisation_rule: str
    regime_interaction_policy: str
    registry_version: str
    parameter_policy: str
    base_signal_id: str | None = None
    context_feature: str | None = None


def _canonical(raw: Mapping[str, Any]) -> dict[str, Any]:
    missing = [name for name in _REQUIRED if name not in raw]
    if missing:
        raise SignalRegistryError(f"Signal specification missing fields: {missing}")
    parameter = raw["threshold_or_band_parameter"]
    if not isinstance(parameter, Mapping):
        raise SignalRegistryError("threshold_or_band_parameter must be a mapping")
    return {
        "family": str(raw["signal_family"]).strip().upper(),
        "window": int(raw["lookback_or_window"]),
        "parameter": dict(sorted(parameter.items())),
        "orientation": str(raw["orientation"]).strip().upper(),
        "interpretation": str(raw["interpretation"]).strip().upper(),
        "crossing": str(raw["crossing_rule"]).strip().upper(),
        "persistence": str(raw["persistence_rule"]).strip().upper(),
        "normalisation": str(raw["normalisation_rule"]).strip().upper(),
        "regime": str(raw["regime_interaction_policy"]).strip().upper(),
        "version": str(raw["registry_version"]).strip(),
        "parameter_policy": str(raw["parameter_policy"]).strip().upper(),
        "base": raw.get("base_signal_id") or None,
        "context": raw.get("context_feature") or None,
    }


def build_signal_id(raw: Mapping[str, Any]) -> str:
    payload = json.dumps(_canonical(raw), sort_keys=True, separators=(",", ":"))
    return "v3sig:" + quote(payload, safe="")


def parse_signal_id(signal_id: str) -> dict[str, Any]:
    if not str(signal_id).startswith("v3sig:"):
        raise SignalRegistryError("Signal identifier has an unexpected prefix")
    try:
        value = json.loads(unquote(str(signal_id)[6:]))
    except (ValueError, json.JSONDecodeError) as error:
        raise SignalRegistryError("Signal identifier is not decodable") from error
    if set(value) != {
        "family", "window", "parameter", "orientation", "interpretation",
        "crossing", "persistence", "normalisation", "regime", "version",
        "parameter_policy", "base", "context",
    }:
        raise SignalRegistryError("Signal identifier fields are incomplete")
    return value


def _spec(raw: Mapping[str, Any]) -> SignalSpec:
    value = _canonical(raw)
    family, interpretation = value["family"], value["interpretation"]
    if family not in {"RSI", "BOLLINGER"}:
        raise SignalRegistryError(f"Unsupported signal family: {family}")
    if value["window"] < 2:
        raise SignalRegistryError("lookback_or_window must be at least 2")
    if value["parameter_policy"] not in {"FIXED", "TRAINING_ONLY_REQUIRED"}:
        raise SignalRegistryError("Unsupported parameter policy")
    if value["regime"] not in {"NONE", "MULTIPLY_CONTEXT_PRESERVE_COMPONENTS"}:
        raise SignalRegistryError("Unsupported interaction policy")
    if interpretation not in (_RSI if family == "RSI" else _BB):
        raise SignalRegistryError(f"Unsupported interpretation: {interpretation}")
    if raw.get("signal_id") != build_signal_id(raw):
        raise SignalRegistryError("Signal identifier does not reproduce its specification")
    if parse_signal_id(str(raw["signal_id"])) != value:
        raise SignalRegistryError("Signal identifier round-trip changed specification")
    if value["regime"] == "NONE" and (value["base"] or value["context"]):
        raise SignalRegistryError("Base/context fields require an interaction")
    if value["regime"] != "NONE" and not (value["base"] and value["context"]):
        raise SignalRegistryError("Interactions require base and context fields")
    return SignalSpec(str(raw["signal_id"]), family, value["window"], value["parameter"],
                      value["orientation"], interpretation, value["crossing"],
                      value["persistence"], value["normalisation"], value["regime"],
                      value["version"], value["parameter_policy"], value["base"], value["context"])


def validate_registry(registry: Mapping[str, Any]) -> tuple[SignalSpec, ...]:
    expected = {
        "schema_version": REGISTRY_SCHEMA_VERSION, "gate": "V3-4",
        "automatic_selection_performed": False, "target_access_permitted": False,
        "chronology_access_permitted": False, "predictive_claims_permitted": False,
        "failure_claims_permitted": False,
    }
    for key, value in expected.items():
        if registry.get(key) != value:
            raise SignalRegistryError(f"Registry boundary changed: {key}")
    raw = registry.get("signals")
    if not isinstance(raw, list) or not raw or len(raw) > MAX_REGISTERED_SIGNALS:
        raise SignalRegistryError("Signal registry is empty or unbounded")
    specs = tuple(_spec(item) for item in raw)
    ids = [item.signal_id for item in specs]
    if len(ids) != len(set(ids)):
        raise SignalRegistryError("Signal identifiers must be unique")
    by_id = {item.signal_id: item for item in specs}
    for item in specs:
        if item.regime_interaction_policy != "NONE":
            base = by_id.get(item.base_signal_id or "")
            if base is None or base.signal_family != item.signal_family:
                raise SignalRegistryError("Interaction base is missing or mismatched")
            if base.regime_interaction_policy != "NONE":
                raise SignalRegistryError("Nested interactions are prohibited")
    return specs


def load_registry(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_registry(value)
    return value


def registry_sha256(registry: Mapping[str, Any]) -> str:
    payload = json.dumps(registry, sort_keys=True, separators=(",", ":")).encode()
    return sha256(payload).hexdigest()


def build_registry_manifest(registry: Mapping[str, Any]) -> dict[str, Any]:
    specs = validate_registry(registry)
    return {
        "schema_version": "v3.signal-registry-manifest.v1",
        "registry_sha256": registry_sha256(registry),
        "signal_count": len(specs),
        "base_signal_count": sum(x.regime_interaction_policy == "NONE" for x in specs),
        "interaction_signal_count": sum(x.regime_interaction_policy != "NONE" for x in specs),
        "adaptive_template_count": sum(x.parameter_policy == "TRAINING_ONLY_REQUIRED" for x in specs),
        "automatic_selection_performed": False,
        "target_accessed": False,
        "chronology_accessed": False,
    }
