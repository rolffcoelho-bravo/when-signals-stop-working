from __future__ import annotations

import json
from pathlib import Path


def test_d2b_lock_declares_development_only_full_selection() -> None:
    payload = json.loads(Path("V2_D2B_SELECTION_LOCK.json").read_text(encoding="utf-8"))
    assert payload["execution_scope"] == "DEVELOPMENT_ONLY_FULL_NESTED_PIPELINE_SELECTION"
    assert payload["parent_d2a_tag"] == "v2-d2a-screening-20260722"
    assert payload["expected_parent_commit"] == "cb45ff4"
    assert payload["lock_id"].startswith("v2-d2b-")
