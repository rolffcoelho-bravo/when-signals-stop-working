from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from test_indicators import make_prices


def save_csv(frame, path: Path) -> None:
    output = frame.copy()
    output.index.name = "Date"
    output.reset_index().to_csv(path, index=False)


def test_market_data_validation_script(tmp_path: Path) -> None:
    sol_path = tmp_path / "sol.csv"
    btc_path = tmp_path / "btc.csv"
    output_path = tmp_path / "validation.json"

    save_csv(make_prices(30, 700), sol_path)
    save_csv(make_prices(31, 700), btc_path)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_market_data.py",
            "--sol-csv",
            str(sol_path),
            "--btc-csv",
            str(btc_path),
            "--output",
            str(output_path),
        ],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    validation = json.loads(output_path.read_text(encoding="utf-8"))
    assert validation["status"] == "PASS"
    assert validation["overlapping_timestamps"] == 700
