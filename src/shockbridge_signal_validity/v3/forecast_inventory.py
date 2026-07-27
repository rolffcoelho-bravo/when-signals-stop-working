from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .forecast_contract import ForecastProtocolViolation


_BLOCKS = (
    "RSI_LEVEL_DYNAMICS",
    "RSI_MEAN_REVERSION",
    "RSI_CONTINUATION",
    "RSI_DIVERGENCE",
    "BOLLINGER_POSITION",
    "BOLLINGER_MEAN_REVERSION",
    "BOLLINGER_BREAKOUT",
    "BOLLINGER_VOLATILITY_STRUCTURE",
)


def _block(definition: dict[str, Any]) -> str:
    family = str(definition.get("signal_family", "")).upper()
    interpretation = str(definition.get("interpretation", "")).upper()
    feature_key = str(definition.get("feature_key", "")).lower()

    if family == "RSI":
        if "divergence" in feature_key or "DIVERGENCE" in interpretation:
            return "RSI_DIVERGENCE"
        if "MEAN_REVERSION" in interpretation:
            return "RSI_MEAN_REVERSION"
        if "CONTINUATION" in interpretation:
            return "RSI_CONTINUATION"
        return "RSI_LEVEL_DYNAMICS"

    if family == "BOLLINGER":
        if any(token in interpretation for token in ("MEAN_REVERSION", "REENTRY")):
            return "BOLLINGER_MEAN_REVERSION"
        if any(
            token in interpretation
            for token in ("BREAKOUT", "BREAKDOWN", "CONTINUATION")
        ):
            return "BOLLINGER_BREAKOUT"
        if any(
            token in interpretation
            for token in ("BANDWIDTH", "SQUEEZE", "EXPANSION")
        ) or any(token in feature_key for token in ("bandwidth", "squeeze", "expansion")):
            return "BOLLINGER_VOLATILITY_STRUCTURE"
        return "BOLLINGER_POSITION"

    raise ForecastProtocolViolation(f"Unsupported signal family in manifest: {family!r}")


def _candidate_id(kind: str, identity: str) -> str:
    digest = sha256(f"{kind}|{identity}".encode("utf-8")).hexdigest()
    return f"v3g5:{kind.lower()}:{digest}"


def load_signal_registry_manifest(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ForecastProtocolViolation("Signal registry manifest must be an object.")
    if payload.get("schema_version") != "v3.signal-registry-manifest.v1":
        raise ForecastProtocolViolation("Unexpected signal registry manifest schema.")
    if payload.get("signal_count") != 48:
        raise ForecastProtocolViolation("Gate V3-5 requires exactly 48 locked signals.")
    if payload.get("automatic_selection_performed") is not False:
        raise ForecastProtocolViolation("Parent registry performed automatic selection.")
    definitions = payload.get("signal_definitions")
    if not isinstance(definitions, list) or len(definitions) != 48:
        raise ForecastProtocolViolation("Signal definition count is not 48.")
    signal_ids = [str(item.get("signal_id", "")) for item in definitions]
    if any(not value.startswith("v3sig:") for value in signal_ids):
        raise ForecastProtocolViolation("Malformed locked signal identifier.")
    if len(set(signal_ids)) != 48:
        raise ForecastProtocolViolation("Locked signal identifiers are not unique.")
    return payload


def build_candidate_inventory(manifest: dict[str, Any]) -> pd.DataFrame:
    definitions = manifest["signal_definitions"]
    records: list[dict[str, object]] = []
    block_members: dict[str, list[str]] = {block: [] for block in _BLOCKS}

    for definition in definitions:
        signal_id = str(definition["signal_id"])
        block = _block(definition)
        block_members[block].append(signal_id)
        records.append(
            {
                "candidate_id": _candidate_id("single", signal_id),
                "candidate_kind": "SINGLE_SIGNAL",
                "signal_family": str(definition["signal_family"]),
                "candidate_block": block,
                "member_signal_ids": json.dumps([signal_id], separators=(",", ":")),
                "member_count": 1,
                "confirmatory_role": "ELIGIBLE_BY_FAMILY",
                "parameter_policy": str(definition["parameter_policy"]),
                "regime_interaction_policy": str(
                    definition["regime_interaction_policy"]
                ),
                "automatic_selection_performed": False,
            }
        )

    for block in _BLOCKS:
        members = sorted(block_members[block])
        if not members:
            raise ForecastProtocolViolation(f"Predeclared candidate block is empty: {block}")
        family = "RSI" if block.startswith("RSI_") else "BOLLINGER"
        identity = block + "|" + "|".join(members)
        records.append(
            {
                "candidate_id": _candidate_id("block", identity),
                "candidate_kind": "PREDECLARED_FAMILY_BLOCK",
                "signal_family": family,
                "candidate_block": block,
                "member_signal_ids": json.dumps(members, separators=(",", ":")),
                "member_count": len(members),
                "confirmatory_role": "ELIGIBLE_BY_FAMILY",
                "parameter_policy": "MIXED_PRESERVED",
                "regime_interaction_policy": "MIXED_PRESERVED",
                "automatic_selection_performed": False,
            }
        )

    all_members = sorted(str(item["signal_id"]) for item in definitions)
    records.append(
        {
            "candidate_id": _candidate_id("combined", "|".join(all_members)),
            "candidate_kind": "PREDECLARED_COMBINED_BLOCK",
            "signal_family": "COMBINED",
            "candidate_block": "RSI_BOLLINGER_COMBINED_SECONDARY",
            "member_signal_ids": json.dumps(all_members, separators=(",", ":")),
            "member_count": len(all_members),
            "confirmatory_role": "SECONDARY_ONLY",
            "parameter_policy": "MIXED_PRESERVED",
            "regime_interaction_policy": "MIXED_PRESERVED",
            "automatic_selection_performed": False,
        }
    )

    frame = pd.DataFrame.from_records(records)
    if len(frame) != 57:
        raise ForecastProtocolViolation(
            f"Candidate inventory identity failed: expected 57, observed {len(frame)}."
        )
    if frame["candidate_id"].duplicated().any():
        raise ForecastProtocolViolation("Candidate identifiers are not unique.")
    if frame["automatic_selection_performed"].any():
        raise ForecastProtocolViolation("Candidate inventory selected candidates automatically.")
    return frame.sort_values(
        ["candidate_kind", "signal_family", "candidate_block", "candidate_id"],
        kind="mergesort",
    ).reset_index(drop=True)


def candidate_inventory_manifest(frame: pd.DataFrame) -> dict[str, object]:
    required = {
        "candidate_id",
        "candidate_kind",
        "signal_family",
        "candidate_block",
        "member_signal_ids",
        "member_count",
        "confirmatory_role",
        "automatic_selection_performed",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ForecastProtocolViolation(
            "Candidate inventory is missing: " + ", ".join(missing)
        )
    return {
        "schema_version": "v3.g5-candidate-inventory.v1",
        "candidate_count": int(len(frame)),
        "single_signal_candidates": int(
            (frame["candidate_kind"] == "SINGLE_SIGNAL").sum()
        ),
        "family_block_candidates": int(
            (frame["candidate_kind"] == "PREDECLARED_FAMILY_BLOCK").sum()
        ),
        "combined_secondary_candidates": int(
            (frame["candidate_kind"] == "PREDECLARED_COMBINED_BLOCK").sum()
        ),
        "automatic_selection_performed": False,
        "full_cartesian_combination_performed": False,
        "negative_or_ineligible_candidates_deleted": False,
    }
