import json
from pathlib import Path


def test_d2c_config_keeps_holdout_closed() -> None:
    payload = json.loads(Path("configs/v2_d2c_admission.json").read_text(encoding="utf-8"))
    assert payload["governance"]["holdout_authorization_enabled"] is False
    assert payload["governance"]["holdout_performance_access_enabled"] is False
    assert payload["governance"]["economic_gate_evaluated"] is False


def test_d2c_runners_and_verifier_are_present() -> None:
    for path in [
        "RUN_V2_D2C_ADMISSION.ps1",
        "RUN_V2_D2C_ADMISSION.sh",
        "scripts/build_v2_d2c_assets.py",
        "scripts/verify_v2_d2c_assets.py",
    ]:
        assert Path(path).exists()
