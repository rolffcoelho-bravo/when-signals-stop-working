from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_v2_final_release_audit_verifier() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/verify_v2_final_audit.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "READY_FOR_PULL_REQUEST" in completed.stdout
    assert "D5 protected files changed: False" in completed.stdout
