from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_v3_g3_final_acceptance.py"


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "run_v3_g3_final_acceptance_under_test",
        RUNNER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the V3-3D acceptance runner.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _valid_evidence() -> dict[str, Any]:
    return {
        "external_chronology_validation_complete": False,
        "external_chronology_deferred_to_later_robustness": True,
    }


def test_chronology_governance_accepts_frozen_deferred_contract() -> None:
    runner = _load_runner()
    result = runner._verify_chronology_governance(_valid_evidence())
    assert result == {
        "external_chronology_validation_complete": False,
        "external_chronology_deferred_to_later_robustness": True,
        "external_chronology_used": False,
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            {"external_chronology_validation_complete": True},
            "must remain incomplete",
        ),
        (
            {"remove": "external_chronology_validation_complete"},
            "must remain incomplete",
        ),
        (
            {"external_chronology_deferred_to_later_robustness": False},
            "explicitly deferred",
        ),
        (
            {"external_chronology_used": True},
            "was used before",
        ),
    ],
)
def test_chronology_governance_fails_closed(
    mutation: dict[str, Any],
    message: str,
) -> None:
    runner = _load_runner()
    evidence = _valid_evidence()
    removed = mutation.get("remove")
    if removed is not None:
        evidence.pop(str(removed))
    else:
        evidence.update(mutation)

    with pytest.raises(RuntimeError, match=message):
        runner._verify_chronology_governance(evidence)
