
from pathlib import Path
import subprocess

import pytest


def test_d4_assets_verify_when_present() -> None:
    status = Path("outputs/v2/holdout/d4_inference_status.json")
    if not status.exists():
        pytest.skip("D4 assets are generated only after D3 evidence is committed.")
    result = subprocess.run(["python", "scripts/verify_v2_d4_assets.py"], check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
