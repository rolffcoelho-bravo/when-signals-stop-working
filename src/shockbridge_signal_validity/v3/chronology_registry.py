from __future__ import annotations

from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

REQUIRED_EVENT_FIELDS = (
    "event_id", "event_type", "start_timestamp", "end_timestamp", "source_id",
    "source_type", "source_locator", "source_publication_timestamp",
    "documentation_status", "severity_class", "timestamp_precision",
    "boundary_uncertainty", "notes",
)
MERGE_FIELDS = (
    "candidate_event_id", "canonical_event_id", "source_id", "action",
    "rationale", "model_outputs_consulted",
)
ALLOWED_EVENT_TYPES = {
    "LIQUIDITY_DISLOCATION", "FUNDING_STRESS", "LIQUIDATION_CASCADE",
    "VOLATILITY_SHOCK", "DOWNSIDE_DISLOCATION", "MARKET_STRUCTURE_BREAK",
    "EXCHANGE_OR_VENUE_DISRUPTION", "CROSS_MARKET_CONTAGION",
}
ALLOWED_SOURCE_TYPES = {
    "regulator_or_central_bank", "exchange_or_venue_notice",
    "clearing_or_settlement_notice", "official_market_operator",
    "peer_reviewed_or_institutional_research",
    "reputable_time_stamped_news_archive",
}
ALLOWED_DOCUMENTATION = {"CONFIRMED", "BOUNDARY_UNCERTAIN", "SOURCE_CONFLICT"}
ALLOWED_SEVERITY = {"DOCUMENTED", "MAJOR", "SYSTEMIC"}
ALLOWED_PRECISION = {"SECOND", "MINUTE", "HOUR", "DAY"}
EXPECTED_PARENT_LOCK = "V3_G4A_CHRONOLOGY_SIGNAL_USE_CONTRACT_LOCK.json"
EXPECTED_PARENT_BLOB = "d3c4ce27808e60b001e7d58e0c5e36be8d8cac6a"


class ChronologyRegistryError(ValueError):
    """Raised when the independent chronology contract is violated."""


def _timestamp(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ChronologyRegistryError(f"{field} must be an ISO-8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ChronologyRegistryError(f"{field} is not a valid timestamp: {value}") from exc
    if parsed.tzinfo != timezone.utc:
        raise ChronologyRegistryError(f"{field} must resolve to UTC")
    return parsed


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=list(fields), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row[field] for field in fields})
    return handle.getvalue().encode("utf-8")


def load_registry(path: Path) -> dict[str, Any]:
    control = json.loads(path.read_text(encoding="utf-8"))
    component_files = control.pop("component_files", None)
    if component_files is None:
        return control
    if not isinstance(component_files, Mapping):
        raise ChronologyRegistryError("component_files must be a mapping")
    root = path.resolve().parents[1]
    for key in ("events", "sources", "event_source_map", "merge_log"):
        relative = component_files.get(key)
        if not isinstance(relative, str) or not relative:
            raise ChronologyRegistryError(f"Registry component missing: {key}")
        control[key] = json.loads((root / relative).read_text(encoding="utf-8"))
    return control


def validate_registry(registry: Mapping[str, Any]) -> dict[str, Any]:
    if registry.get("gate") != "V3-4B":
        raise ChronologyRegistryError("Unexpected gate identifier")
    if registry.get("parent_lock") != EXPECTED_PARENT_LOCK:
        raise ChronologyRegistryError("V3-4A parent lock path changed")
    if registry.get("parent_lock_blob_sha") != EXPECTED_PARENT_BLOB:
        raise ChronologyRegistryError("V3-4A parent lock blob changed")
    if registry.get("model_outputs_accessed") is not False:
        raise ChronologyRegistryError("Model outputs were accessed during chronology compilation")
    if registry.get("chronology_completeness_claimed") is not False:
        raise ChronologyRegistryError("Chronology cannot be represented as a complete event census")
    if registry.get("timezone") != "UTC":
        raise ChronologyRegistryError("Chronology timezone must be UTC")

    sample_start = _timestamp(str(registry.get("sample_start")), "sample_start")
    sample_end = _timestamp(str(registry.get("sample_end")), "sample_end")
    if sample_start >= sample_end:
        raise ChronologyRegistryError("Sample start must precede sample end")

    raw_sources = registry.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ChronologyRegistryError("Source registry is empty")
    sources: dict[str, Mapping[str, Any]] = {}
    for source in raw_sources:
        if not isinstance(source, Mapping):
            raise ChronologyRegistryError("Each source must be a mapping")
        source_id = str(source.get("source_id", ""))
        if not source_id or source_id in sources:
            raise ChronologyRegistryError(f"Duplicate or missing source_id: {source_id}")
        if source.get("source_type") not in ALLOWED_SOURCE_TYPES:
            raise ChronologyRegistryError(f"Disallowed source type: {source_id}")
        locator = str(source.get("source_locator", ""))
        if not locator.startswith("https://"):
            raise ChronologyRegistryError(f"Source locator must be HTTPS: {source_id}")
        _timestamp(str(source.get("source_publication_timestamp")), f"{source_id}.source_publication_timestamp")
        _timestamp(str(source.get("retrieved_timestamp")), f"{source_id}.retrieved_timestamp")
        if source.get("publication_time_precision") not in ALLOWED_PRECISION:
            raise ChronologyRegistryError(f"Invalid publication precision: {source_id}")
        sources[source_id] = source

    raw_events = registry.get("events")
    if not isinstance(raw_events, list) or not raw_events:
        raise ChronologyRegistryError("Chronology contains no events")
    events: dict[str, Mapping[str, Any]] = {}
    for event in raw_events:
        if not isinstance(event, Mapping):
            raise ChronologyRegistryError("Each event must be a mapping")
        missing = [field for field in REQUIRED_EVENT_FIELDS if field not in event]
        if missing:
            raise ChronologyRegistryError(f"Event fields missing: {missing}")
        event_id = str(event["event_id"])
        if not event_id or event_id in events:
            raise ChronologyRegistryError(f"Duplicate or missing event_id: {event_id}")
        if event["event_type"] not in ALLOWED_EVENT_TYPES:
            raise ChronologyRegistryError(f"Invalid event type: {event_id}")
        if event["documentation_status"] not in ALLOWED_DOCUMENTATION:
            raise ChronologyRegistryError(f"Invalid documentation status: {event_id}")
        if event["severity_class"] not in ALLOWED_SEVERITY:
            raise ChronologyRegistryError(f"Invalid severity class: {event_id}")
        if event["timestamp_precision"] not in ALLOWED_PRECISION:
            raise ChronologyRegistryError(f"Invalid timestamp precision: {event_id}")
        start = _timestamp(str(event["start_timestamp"]), f"{event_id}.start_timestamp")
        end = _timestamp(str(event["end_timestamp"]), f"{event_id}.end_timestamp")
        if start >= end:
            raise ChronologyRegistryError(f"Event start must precede end: {event_id}")
        if start < sample_start or end > sample_end:
            raise ChronologyRegistryError(f"Event lies outside frozen sample: {event_id}")
        source_id = str(event["source_id"])
        source = sources.get(source_id)
        if source is None:
            raise ChronologyRegistryError(f"Unknown primary source: {event_id}")
        for field in ("source_type", "source_locator", "source_publication_timestamp"):
            if event[field] != source[field]:
                raise ChronologyRegistryError(f"Primary-source mismatch for {event_id}: {field}")
        events[event_id] = event

    event_source_map = registry.get("event_source_map")
    if not isinstance(event_source_map, Mapping) or set(event_source_map) != set(events):
        raise ChronologyRegistryError("Event-source map must cover every canonical event exactly")
    referenced_sources: set[str] = set()
    for event_id, source_ids in event_source_map.items():
        if not isinstance(source_ids, list) or not source_ids:
            raise ChronologyRegistryError(f"Event has no source provenance: {event_id}")
        if events[event_id]["source_id"] != source_ids[0]:
            raise ChronologyRegistryError(f"Primary source must be first in provenance: {event_id}")
        if len(source_ids) != len(set(source_ids)):
            raise ChronologyRegistryError(f"Duplicate source mapping: {event_id}")
        for source_id in source_ids:
            if source_id not in sources:
                raise ChronologyRegistryError(f"Unknown supporting source: {event_id}/{source_id}")
            referenced_sources.add(source_id)
    if referenced_sources != set(sources):
        raise ChronologyRegistryError("Every registered source must support at least one event")

    merge_log = registry.get("merge_log")
    if not isinstance(merge_log, list) or not merge_log:
        raise ChronologyRegistryError("Merge log is empty")
    seen_candidates: set[str] = set()
    retained_events: set[str] = set()
    merge_sources: dict[str, set[str]] = {event_id: set() for event_id in events}
    for row in merge_log:
        if not isinstance(row, Mapping) or any(field not in row for field in MERGE_FIELDS):
            raise ChronologyRegistryError("Malformed merge-log row")
        candidate = str(row["candidate_event_id"])
        event_id = str(row["canonical_event_id"])
        source_id = str(row["source_id"])
        if candidate in seen_candidates:
            raise ChronologyRegistryError(f"Duplicate merge candidate: {candidate}")
        seen_candidates.add(candidate)
        if event_id not in events or source_id not in sources:
            raise ChronologyRegistryError(f"Unknown merge reference: {candidate}")
        if str(row["model_outputs_consulted"]).lower() != "false":
            raise ChronologyRegistryError(f"Model output consulted in merge decision: {candidate}")
        if row["action"] == "RETAINED_AS_CANONICAL":
            retained_events.add(event_id)
        elif row["action"] != "MERGED_SUPPORTING_SOURCE":
            raise ChronologyRegistryError(f"Invalid merge action: {candidate}")
        merge_sources[event_id].add(source_id)
    if retained_events != set(events):
        raise ChronologyRegistryError("Every canonical event requires one retained candidate")
    for event_id, expected_sources in event_source_map.items():
        if merge_sources[event_id] != set(expected_sources):
            raise ChronologyRegistryError(f"Merge log does not reproduce source map: {event_id}")

    confirmed = sum(event["documentation_status"] == "CONFIRMED" for event in events.values())
    boundary_uncertain = sum(event["documentation_status"] == "BOUNDARY_UNCERTAIN" for event in events.values())
    source_conflict = sum(event["documentation_status"] == "SOURCE_CONFLICT" for event in events.values())
    return {
        "event_count": len(events),
        "source_count": len(sources),
        "confirmed_event_count": confirmed,
        "boundary_uncertain_event_count": boundary_uncertain,
        "source_conflict_event_count": source_conflict,
    }


def render_outputs(registry: Mapping[str, Any]) -> dict[str, bytes]:
    counts = validate_registry(registry)
    events = sorted(registry["events"], key=lambda row: (row["start_timestamp"], row["event_id"]))
    sources = sorted(registry["sources"], key=lambda row: row["source_id"])
    event_source_map = {
        key: registry["event_source_map"][key]
        for key in sorted(registry["event_source_map"])
    }
    merge_log = sorted(
        registry["merge_log"],
        key=lambda row: (row["canonical_event_id"], row["candidate_event_id"]),
    )

    chronology_bytes = _csv_bytes(events, REQUIRED_EVENT_FIELDS)
    merge_bytes = _csv_bytes(merge_log, MERGE_FIELDS)
    provenance = {
        "schema_version": "v3.chronology-provenance.v1",
        "gate": "V3-4B",
        "status": "INDEPENDENT_SOURCE_PROVENANCE_COMPILED",
        "compiled_timestamp": registry["compiled_timestamp"],
        "compilation_method": registry["compilation_method"],
        "model_outputs_accessed": False,
        "chronology_completeness_claimed": False,
        "timezone": registry["timezone"],
        "sample_start": registry["sample_start"],
        "sample_end": registry["sample_end"],
        "sources": sources,
        "event_source_map": event_source_map,
        "source_policy": registry["source_policy"],
        "limitations": registry["limitations"],
    }
    provenance_bytes = _json_bytes(provenance)
    event_type_counts = dict(sorted(Counter(row["event_type"] for row in events).items()))
    eligible = [row["event_id"] for row in events if row["documentation_status"] == "CONFIRMED"]
    excluded = [row["event_id"] for row in events if row["documentation_status"] != "CONFIRMED"]
    manifest = {
        "schema_version": "v3.chronology-manifest.v1",
        "gate": "V3-4B",
        "status": "CHRONOLOGY_COMPILED_PROVENANCE_LOCK_READY",
        "parent_gate": "V3-4A",
        "parent_lock": EXPECTED_PARENT_LOCK,
        "parent_lock_blob_sha": EXPECTED_PARENT_BLOB,
        "sample_start": registry["sample_start"],
        "sample_end": registry["sample_end"],
        **counts,
        "event_type_counts": event_type_counts,
        "primary_timing_eligible_event_ids": eligible,
        "primary_timing_excluded_event_ids": excluded,
        "model_outputs_accessed": False,
        "chronology_completeness_claimed": False,
        "event_alignment_executed": False,
        "files": {
            "chronology_merge_log.csv": _sha256_bytes(merge_bytes),
            "chronology_provenance.json": _sha256_bytes(provenance_bytes),
            "external_chronology.csv": _sha256_bytes(chronology_bytes),
        },
        "v3_4c_may_access_model_outputs_only_after_v3_4b_lock": True,
        "next_subgate": "V3-4C",
    }
    return {
        "external_chronology.csv": chronology_bytes,
        "chronology_merge_log.csv": merge_bytes,
        "chronology_provenance.json": provenance_bytes,
        "chronology_manifest.json": _json_bytes(manifest),
    }


def write_outputs(registry_path: Path, output_directory: Path) -> dict[str, str]:
    registry = load_registry(registry_path)
    rendered = render_outputs(registry)
    output_directory.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    for name, payload in rendered.items():
        (output_directory / name).write_bytes(payload)
        hashes[name] = _sha256_bytes(payload)
    return hashes
