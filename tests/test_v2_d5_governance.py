from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_d5_governance_prohibits_verdict_rescue() -> None:
    config = json.loads(
        (ROOT / "configs/v2_d5_robustness_publication.json").read_text(
            encoding="utf-8"
        )
    )
    governance = config["governance"]
    assert governance["pipeline_retuning_permitted"] is False
    assert governance["alternative_holdout_pipeline_execution_permitted"] is False
    assert governance["rsi_reentry_permitted"] is False
    assert governance["d4_verdict_mutable"] is False
    assert governance["panic_state_extension_in_v2_verdict"] is False
    assert governance["robustness_diagnostics_can_upgrade_verdict"] is False


def test_d5_expected_parent_and_grade_are_frozen() -> None:
    config = json.loads(
        (ROOT / "configs/v2_d5_robustness_publication.json").read_text(
            encoding="utf-8"
        )
    )
    assert config["expected_parent_commit"] == "69f1c40"
    assert (
        config["expected_parent_tag"]
        == "v2-d4-confirmatory-inference-20260723"
    )
    assert config["expected_d4_evidence_grade"] == "NO_INCREMENTAL_EVIDENCE"
    assert config["expected_signal_family"] == "bollinger"


def test_v2_1_is_separate_from_d5() -> None:
    text = (
        ROOT / "docs/V2_D5_ROBUSTNESS_AND_PUBLICATION.md"
    ).read_text(encoding="utf-8")
    assert "cannot" in text
    assert "V2.1" in text
    assert "panic-state" in text
