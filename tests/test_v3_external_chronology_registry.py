from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from shockbridge_signal_validity.v3.chronology_registry import (
    ChronologyRegistryError,
    load_registry,
    render_outputs,
    validate_registry,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configs" / "v3_external_chronology_registry.json"
OUTPUT = ROOT / "outputs" / "v3" / "g4b_chronology"


def registry_value() -> dict:
    return load_registry(REGISTRY)


def test_registry_validates_complete_independent_package() -> None:
    result = validate_registry(registry_value())
    assert result == {
        "event_count": 17,
        "source_count": 27,
        "confirmed_event_count": 12,
        "boundary_uncertain_event_count": 5,
        "source_conflict_event_count": 0,
    }


def test_registry_parent_is_authoritative_v3_g4a_lock() -> None:
    registry = registry_value()
    assert registry["parent_lock_blob_sha"] == "d3c4ce27808e60b001e7d58e0c5e36be8d8cac6a"
    assert registry["model_outputs_accessed"] is False


def test_rendered_outputs_equal_tracked_evidence() -> None:
    rendered = render_outputs(registry_value())
    assert set(rendered) == {
        "external_chronology.csv",
        "chronology_merge_log.csv",
        "chronology_provenance.json",
        "chronology_manifest.json",
    }
    for name, payload in rendered.items():
        assert payload == (OUTPUT / name).read_bytes()


def test_manifest_hashes_match_rendered_evidence() -> None:
    rendered = render_outputs(registry_value())
    manifest = json.loads(rendered["chronology_manifest.json"])
    for name, expected in manifest["files"].items():
        assert hashlib.sha256(rendered[name]).hexdigest() == expected


def test_every_event_is_within_frozen_sample() -> None:
    registry = registry_value()
    validate_registry(registry)
    assert registry["sample_start"] == "2021-01-01T00:00:00Z"
    assert registry["sample_end"] == "2026-07-22T08:00:00Z"


def test_uncertain_boundaries_are_excluded_from_primary_timing() -> None:
    manifest = json.loads((OUTPUT / "chronology_manifest.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader(io.StringIO((OUTPUT / "external_chronology.csv").read_text(encoding="utf-8"))))
    uncertain = {row["event_id"] for row in rows if row["documentation_status"] != "CONFIRMED"}
    assert uncertain == set(manifest["primary_timing_excluded_event_ids"])
    assert uncertain.isdisjoint(manifest["primary_timing_eligible_event_ids"])


def test_merge_log_never_consults_model_outputs() -> None:
    rows = list(csv.DictReader((OUTPUT / "chronology_merge_log.csv").open(encoding="utf-8")))
    assert rows
    assert {row["model_outputs_consulted"] for row in rows} == {"false"}


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"model_outputs_accessed": True}, "Model outputs were accessed"),
        ({"chronology_completeness_claimed": True}, "complete event census"),
        ({"parent_lock_blob_sha": "bad"}, "parent lock blob changed"),
    ],
)
def test_registry_fails_closed_on_governance_mutations(mutation: dict, message: str) -> None:
    registry = registry_value()
    registry.update(mutation)
    with pytest.raises(ChronologyRegistryError, match=message):
        validate_registry(registry)


def test_registry_rejects_event_outside_sample() -> None:
    registry = registry_value()
    registry["events"][0]["start_timestamp"] = "2020-12-31T20:00:00Z"
    with pytest.raises(ChronologyRegistryError, match="outside frozen sample"):
        validate_registry(registry)


def test_registry_rejects_primary_source_mismatch() -> None:
    registry = registry_value()
    registry["events"][0]["source_locator"] = "https://example.com/changed"
    with pytest.raises(ChronologyRegistryError, match="Primary-source mismatch"):
        validate_registry(registry)


def test_registry_rejects_unmapped_source() -> None:
    registry = registry_value()
    registry["event_source_map"][registry["events"][0]["event_id"]] = []
    with pytest.raises(ChronologyRegistryError, match="no source provenance"):
        validate_registry(registry)


def test_registry_rejects_merge_decision_using_model_output() -> None:
    registry = registry_value()
    registry["merge_log"][0]["model_outputs_consulted"] = "true"
    with pytest.raises(ChronologyRegistryError, match="Model output consulted"):
        validate_registry(registry)


def test_ordering_is_deterministic_under_input_shuffle() -> None:
    registry = registry_value()
    rendered = render_outputs(registry)
    shuffled = copy.deepcopy(registry)
    shuffled["events"] = list(reversed(shuffled["events"]))
    shuffled["sources"] = list(reversed(shuffled["sources"]))
    shuffled["merge_log"] = list(reversed(shuffled["merge_log"]))
    shuffled["event_source_map"] = dict(reversed(list(shuffled["event_source_map"].items())))
    assert render_outputs(shuffled) == rendered


def test_portable_launchers_preserve_user_site_and_run_exact_gate() -> None:
    powershell = (ROOT / "RUN_V3_G4B_CHRONOLOGY.ps1").read_bytes().decode("ascii")
    posix = (ROOT / "RUN_V3_G4B_CHRONOLOGY.sh").read_text(encoding="utf-8")
    assert 'SetEnvironmentVariable("PYTHONNOUSERSITE", $null, "Process")' in powershell
    assert '$PreviousPythonNoUserSite' in powershell
    assert 'finally {' in powershell
    assert "PYTHONNOUSERSITE=1" not in powershell
    assert "unset PYTHONNOUSERSITE" in posix
    assert "PYTHONNOUSERSITE=1" not in posix
    for text in (powershell, posix):
        assert "tests/test_v3_external_chronology_registry.py" in text
        assert "tests/test_v3_cross_gate_lineage.py" in text
        assert "scripts/verify_v3_cross_gate_lineage.py" in text
        assert "scripts/run_v3_g4b_chronology.py" in text
        assert "scripts/verify_v3_g4b_chronology_lock.py" in text
