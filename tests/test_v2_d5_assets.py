from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_d5_assets_verify_when_present() -> None:
    status = ROOT / "outputs/v2/publication/d5_publication_status.json"
    if not status.exists():
        pytest.skip("D5 assets are generated after the implementation commit.")
    subprocess.run(
        [sys.executable, "scripts/verify_v2_d5_assets.py"],
        cwd=ROOT,
        check=True,
    )
