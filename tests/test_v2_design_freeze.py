from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_v2_registry_is_frozen_and_bounded() -> None:
    registry = json.loads(
        (ROOT / "configs" / "v2_experiment_registry.json").read_text(encoding="utf-8")
    )

    assert registry["freeze_status"] == "FROZEN_BEFORE_IMPLEMENTATION"
    assert registry["parent_release"]["tag"] == "v1.2.0"
    assert registry["parent_release"]["commit"].startswith("748d172")
    assert registry["horizons_candles"] == [1, 2, 3, 6]
    assert registry["horizons_hours"] == [4, 8, 12, 24]
    assert [item["id"] for item in registry["confirmatory_hypotheses"]] == [
        "H1_RSI_DIRECTION",
        "H2_BOLLINGER_DIRECTION",
    ]
    assert registry["multiple_testing"]["confirmatory_method"] == "Holm"
    assert registry["multiple_testing"]["confirmatory_familywise_alpha"] == 0.05
    assert registry["signal_grids"]["combined"]["full_cartesian_grid_prohibited"] is True
    assert registry["validation"]["shuffle"] is False
    assert registry["validation"]["minimum_positive_outer_folds"] == 3


def test_v2_holdout_follows_development_period() -> None:
    registry = json.loads(
        (ROOT / "configs" / "v2_experiment_registry.json").read_text(encoding="utf-8")
    )
    development_end = registry["data"]["development"]["end_utc"]
    holdout_start = registry["data"]["locked_evaluation"]["start_utc"]
    assert development_end < holdout_start
    assert (
        registry["data"]["locked_evaluation"]["classification"]
        == "methodology_locked_not_historically_unseen"
    )


def test_v2_protocol_lock_hashes() -> None:
    lock = json.loads((ROOT / "V2_PROTOCOL_LOCK.json").read_text(encoding="utf-8"))
    assert lock["parent_release"] == "v1.2.0"
    assert lock["status"] == "FROZEN_BEFORE_IMPLEMENTATION"

    for relative, expected in lock["files"].items():
        path = ROOT / relative
        assert path.exists(), relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, relative


def test_v2_design_documents_exist() -> None:
    required = [
        "V2_DESIGN_FREEZE.md",
        "docs/V2_RESEARCH_PROTOCOL.md",
        "docs/V2_MODEL_CONTRACT.md",
        "docs/V2_VALIDATION_GATES.md",
        "docs/V2_MULTIPLE_TESTING_CONTROL.md",
        "docs/V2_DATA_AND_REPLICATION_PLAN.md",
        "docs/V2_HOLDOUT_GOVERNANCE.md",
        "configs/v2_experiment_registry.json",
        "scripts/verify_v2_protocol_lock.py",
    ]
    missing = [relative for relative in required if not (ROOT / relative).exists()]
    assert not missing, missing
