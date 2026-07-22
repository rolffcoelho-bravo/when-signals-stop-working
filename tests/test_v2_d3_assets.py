from pathlib import Path
import subprocess

import pytest


def test_d3_assets_verify_when_present() -> None:
    status = Path("outputs/v2/holdout/d3_locked_evaluation_status.json")
    if not status.exists():
        pytest.skip("D3 assets are generated only after single-access authorization.")
    result = subprocess.run(
        ["python", "scripts/verify_v2_d3_assets.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
