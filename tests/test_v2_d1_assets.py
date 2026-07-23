from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "outputs" / "v2" / "development" / "d1_engine_status.json"


def test_v2_d1_generated_assets_when_present() -> None:
    if not STATUS.exists():
        pytest.skip("D1 generated assets are created after the D1 code checkpoint.")
    payload = json.loads(STATUS.read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    assert payload["registered_signal_specifications_audited"] == 84
    assert payload["nested_state_fits"] == 80
    assert payload["predictive_model_fitting_performed"] is False
    assert payload["state_filter_fitting_performed"] is True
    assert payload["holdout_performance_accessed"] is False
    diagnostics = pd.read_csv(ROOT / "data/processed/v2/development/d1_fold_state_diagnostics.csv")
    assert len(diagnostics) == 80
