from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v2_d0_implementation_lock_matches_files() -> None:
    payload = json.loads(
        (ROOT / "V2_D0_IMPLEMENTATION_LOCK.json").read_text(encoding="utf-8")
    )
    assert payload["protocol_lock_id"] == "v2-protocol-068f03ca1452c5ef"
    assert payload["execution_scope"] == "DEVELOPMENT_ONLY_NO_MODEL_FITTING"
    assert payload["lock_id"].startswith("v2-d0-")
    for relative, expected_hash in payload["protected_files"].items():
        path = ROOT / relative
        assert path.exists(), relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash
