import json
from pathlib import Path


def test_d2c_lock_has_expected_scope() -> None:
    payload = json.loads(Path("V2_D2C_ADMISSION_LOCK.json").read_text(encoding="utf-8"))
    assert payload["checkpoint"] == "V2_D2C_DEVELOPMENT_ADMISSION_AND_PIPELINE_FREEZE"
    assert payload["expected_parent_commit"] == "93ecb7e"
    assert payload["holdout_authorization_enabled"] is False
    assert "src/shockbridge_signal_validity/v2/development_admission.py" in payload["protected_files"]
