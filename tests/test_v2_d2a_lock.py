from __future__ import annotations

import json
from pathlib import Path


def test_d2a_lock_declares_development_only_screening() -> None:
    payload = json.loads(Path("V2_D2A_SELECTION_LOCK.json").read_text(encoding="utf-8"))
    assert payload["execution_scope"] == "DEVELOPMENT_ONLY_PREDICTIVE_SCREENING"
    assert payload["parent_d1_tag"] == "v2-d1-causal-engine-20260722"
    assert payload["lock_id"].startswith("v2-d2a-")
