from __future__ import annotations

import json

import pandas as pd

from shockbridge_signal_validity.v3.data_runner import run_data_adapter


def test_runner_writes_canonical_evidence(tmp_path) -> None:
    source = tmp_path / "market.csv"
    pd.DataFrame(
        {
            "time": ["2026-01-01T00:00:00Z", "2026-01-01T04:00:00Z"],
            "o": [100.0, 101.0],
            "h": [102.0, 103.0],
            "l": [99.0, 100.0],
            "c": [101.0, 102.0],
            "v": [10.0, 12.0],
        }
    ).to_csv(source, index=False)
    output = tmp_path / "outputs"
    result = run_data_adapter(
        {
            "adapter_type": "file",
            "adapter": {
                "path": str(source),
                "column_map": {
                    "timestamp": "time",
                    "open": "o",
                    "high": "h",
                    "low": "l",
                    "close": "c",
                    "volume": "v",
                },
                "constants": {"asset": "SOL/USDT", "venue": "fixture"},
            },
        },
        output,
    )
    assert result.validation.valid
    assert (output / "canonical_market_data.csv").is_file()
    manifest = json.loads((output / "source_manifest.json").read_text())
    report = json.loads((output / "validation_report.json").read_text())
    assert len(manifest["manifest_sha256"]) == 64
    assert report["valid"] is True
