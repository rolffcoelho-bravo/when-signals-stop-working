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
    feature_key: str
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
    except ValueError as error:
        raise SignalRegistryError("Signal identifier is not decodable") from error
    expected = {
        "family", "window", "parameter", "orientation", "interpretation",
        "crossing", "persistence", "normalisation", "regime", "version",
        "parameter_policy", "base", "context",
    }
    if set(value) != expected:
        raise SignalRegistryError("Signal identifier fields are incomplete")
    return value


def _expand(registry: Mapping[str, Any]) -> list[dict[str, Any]]:
    defaults = registry.get("defaults")
    entries = registry.get("signals")
    if not isinstance(defaults, Mapping) or not isinstance(entries, list) or not entries:
        raise SignalRegistryError("Compact registry requires defaults and signals")
    expanded: list[dict[str, Any]] = []
    by_key: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise SignalRegistryError("Signal entry must be a mapping")
        key = str(entry.get("feature_key", "")).strip()
        template = str(entry.get("template", "")).strip()
        if not key or key in by_key:
            raise SignalRegistryError("Feature keys must be non-empty and unique")
        base = defaults.get(template)
        if not isinstance(base, Mapping):
            raise SignalRegistryError(f"Unknown signal template: {template}")
        raw = {
            **dict(base),
            **{k: v for k, v in entry.items() if k not in {"feature_key", "template"}},
        }
        raw.setdefault("regime_interaction_policy", "NONE")
        raw.setdefault("base_signal_id", None)
        raw.setdefault("context_feature", None)
        raw["feature_key"] = key
        raw["signal_id"] = build_signal_id(raw)
        expanded.append(raw)
        by_key[key] = raw

    interactions = registry.get("interactions", [])
    if not isinstance(interactions, list):
        raise SignalRegistryError("interactions must be a list")
    for entry in interactions:
        key = str(entry.get("feature_key", "")).strip()
        base_key = str(entry.get("base_feature_key", "")).strip()
        context = str(entry.get("context_feature", "")).strip()
        if not key or key in by_key or base_key not in by_key or not context:
            raise SignalRegistryError("Interaction feature/base/context is invalid")
        base = by_key[base_key]
        raw = {
            "feature_key": key,
            "signal_family": base["signal_family"],
            "lookback_or_window": base["lookback_or_window"],
            "threshold_or_band_parameter": {
                "base_feature_key": base_key,
                "context_feature": context,
            },
            "orientation": base["orientation"],
            "interpretation": base["interpretation"],
            "crossing_rule": base["crossing_rule"],
            "persistence_rule": base["persistence_rule"],
            "normalisation_rule": "BASE_TIMES_CONTEXT",
            "regime_interaction_policy": "MULTIPLY_CONTEXT_PRESERVE_COMPONENTS",
            "registry_version": registry.get("registry_version", "v1"),
            "parameter_policy": "FIXED",
            "base_signal_id": base["signal_id"],
            "context_feature": context,
        }
        raw["signal_id"] = build_signal_id(raw)
        expanded.append(raw)
        by_key[key] = raw
    return expanded


def _validate_parameters(value: Mapping[str, Any]) -> None:
    family = value["family"]
    policy = value["parameter_policy"]
    parameter = value["parameter"]
    if value["regime"] != "NONE":
        return
    if family == "RSI":
        if policy == "FIXED":
            lower = float(parameter.get("lower", float("nan")))
            upper = float(parameter.get("upper", float("nan")))
            if not 0.0 <= lower < upper <= 100.0:
                raise SignalRegistryError("Fixed RSI thresholds are invalid")
        else:
            lower_q = float(parameter.get("lower_quantile", float("nan")))
            upper_q = float(parameter.get("upper_quantile", float("nan")))
            if not 0.0 < lower_q < upper_q < 1.0:
                raise SignalRegistryError("Adaptive RSI quantiles are invalid")
        if int(parameter.get("range_window", 0)) < 2:
            raise SignalRegistryError("RSI range window is invalid")
        if int(parameter.get("divergence_window", 0)) < 1:
            raise SignalRegistryError("RSI divergence window is invalid")
    else:
        deviations = float(parameter.get("standard_deviations", float("nan")))
        if not deviations > 0.0:
            raise SignalRegistryError("Bollinger standard-deviation parameter is invalid")
        if policy == "FIXED":
            threshold = float(parameter.get("squeeze_threshold", float("nan")))
            if not threshold > 0.0:
                raise SignalRegistryError("Fixed Bollinger squeeze threshold is invalid")
        else:
            quantile = float(parameter.get("squeeze_quantile", float("nan")))
            if not 0.0 < quantile < 1.0:
                raise SignalRegistryError("Adaptive Bollinger squeeze quantile is invalid")


def _spec(raw: Mapping[str, Any]) -> SignalSpec:
    value = _canonical(raw)
    family = value["family"]
    interpretation = value["interpretation"]
    permitted = _RSI if family == "RSI" else _BB
    if family not in {"RSI", "BOLLINGER"} or interpretation not in permitted:
        raise SignalRegistryError(
            f"Unsupported family or interpretation: {family}/{interpretation}"
        )
    if value["window"] < 2:
        raise SignalRegistryError("Signal window is invalid")
    if value["parameter_policy"] not in {"FIXED", "TRAINING_ONLY_REQUIRED"}:
        raise SignalRegistryError("Parameter policy is invalid")
    if value["regime"] not in {"NONE", "MULTIPLY_CONTEXT_PRESERVE_COMPONENTS"}:
        raise SignalRegistryError("Unsupported interaction policy")
    _validate_parameters(value)
    signal_id = build_signal_id(raw)
    if parse_signal_id(signal_id) != value:
        raise SignalRegistryError("Signal identifier round-trip changed specification")
    return SignalSpec(
        signal_id,
        str(raw["feature_key"]),
        family,
        value["window"],
        value["parameter"],
        value["orientation"],
        interpretation,
        value["crossing"],
        value["persistence"],
        value["normalisation"],
        value["regime"],
        value["version"],
        value["parameter_policy"],
        value["base"],
        value["context"],
    )


def validate_registry(registry: Mapping[str, Any]) -> tuple[SignalSpec, ...]:
    expected = {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "gate": "V3-4",
        "bounded_candidate_limit": MAX_REGISTERED_SIGNALS,
        "automatic_selection_performed": False,
        "target_access_permitted": False,
        "chronology_access_permitted": False,
        "predictive_claims_permitted": False,
        "economic_claims_permitted": False,
        "deterioration_claims_permitted": False,
        "failure_claims_permitted": False,
        "adaptive_parameters_require_training_only_supply": True,
        "fixed_candidates_remain_visible": True,
        "interaction_components_preserved": True,
        "frozen_v1_v2_determinations_modified": False,
    }
    for key, expected_value in expected.items():
        if registry.get(key) != expected_value:
            raise SignalRegistryError(f"Registry boundary changed: {key}")
    raw = _expand(registry)
    if len(raw) > MAX_REGISTERED_SIGNALS:
        raise SignalRegistryError("Signal registry exceeds bounded limit")
    specs = tuple(_spec(item) for item in raw)
    identifiers = [item.signal_id for item in specs]
    if len(identifiers) != len(set(identifiers)):
        raise SignalRegistryError("Signal identifiers must be unique")
    by_id = {item.signal_id: item for item in specs}
    for item in specs:
        if item.regime_interaction_policy != "NONE":
            base = by_id.get(item.base_signal_id or "")
            if (
                base is None
                or base.signal_family != item.signal_family
                or base.regime_interaction_policy != "NONE"
            ):
                raise SignalRegistryError(
                    "Interaction base is missing, mismatched, or nested"
                )
    return specs


def load_registry(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_registry(value)
    return value


def registry_sha256(registry: Mapping[str, Any]) -> str:
    payload = json.dumps(
        registry,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def build_registry_manifest(registry: Mapping[str, Any]) -> dict[str, Any]:
    specs = validate_registry(registry)
    return {
        "schema_version": "v3.signal-registry-manifest.v1",
        "registry_sha256": registry_sha256(registry),
        "signal_count": len(specs),
        "base_signal_count": sum(
            item.regime_interaction_policy == "NONE" for item in specs
        ),
        "interaction_signal_count": sum(
            item.regime_interaction_policy != "NONE" for item in specs
        ),
        "adaptive_template_count": sum(
            item.parameter_policy == "TRAINING_ONLY_REQUIRED" for item in specs
        ),
        "automatic_selection_performed": False,
        "target_accessed": False,
        "chronology_accessed": False,
    }
