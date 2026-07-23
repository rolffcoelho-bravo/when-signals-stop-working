from __future__ import annotations

import json
from pathlib import Path


def test_d2b_configuration_preserves_holdout_boundary() -> None:
    config = json.loads(Path("configs/v2_d2b_selection.json").read_text(encoding="utf-8"))
    assert config["execution_scope"] == "DEVELOPMENT_ONLY_FULL_NESTED_PIPELINE_SELECTION"
    assert config["governance"]["holdout_performance_access_enabled"] is False
    assert config["governance"]["holdout_pipeline_freeze_performed"] is False
    assert config["governance"]["isotonic_eligible_for_confirmatory_selection"] is False
    assert config["structural_selection"]["inventory_rows"] == 90


def test_d2b_asset_verifier_is_present() -> None:
    assert Path("scripts/verify_v2_d2b_assets.py").exists()
