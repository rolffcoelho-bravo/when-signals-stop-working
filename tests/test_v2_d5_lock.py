from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_d5_lock_is_valid() -> None:
    subprocess.run(
        [sys.executable, "scripts/verify_v2_d5_lock.py"],
        cwd=ROOT,
        check=True,
    )


def test_d5_lock_freezes_governance_boundaries() -> None:
    payload = json.loads(
        (ROOT / "V2_D5_ROBUSTNESS_LOCK.json").read_text(encoding="utf-8")
    )
    assert payload["expected_parent_commit"] == "69f1c40"
    assert payload["expected_d4_evidence_grade"] == "NO_INCREMENTAL_EVIDENCE"
    assert payload["pipeline_retuning_permitted"] is False
    assert payload["rsi_reentry_permitted"] is False
    assert payload["panic_state_extension_used"] is False
