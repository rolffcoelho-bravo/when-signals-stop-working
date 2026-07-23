from __future__ import annotations

import json

import numpy as np
import pandas as pd

from shockbridge_signal_validity.v3.spectral_runner import run_spectral_features


def test_spectral_runner_emits_governed_outputs(tmp_path) -> None:
    timestamps = pd.date_range("2024-01-01", periods=50, freq="4h", tz="UTC")
    rows = []
    for index, asset in enumerate(("SOL", "BTC", "ETH")):
        returns = (
            np.sin(np.linspace(0.0, 5.0, len(timestamps))) * 0.003
            + (index + 1) * 0.0001
        )
        closes = (100.0 + 10.0 * index) * np.exp(np.cumsum(returns))
        for timestamp, close in zip(timestamps, closes):
            rows.append(
                {
                    "timestamp": timestamp,
                    "asset": asset,
                    "venue": "binance",
                    "open": close * 0.999,
                    "high": close * 1.002,
                    "low": close * 0.998,
                    "close": close,
                    "volume": 1000.0 + index,
                }
            )
    input_path = tmp_path / "canonical.csv"
    pd.DataFrame(rows).to_csv(input_path, index=False)
    output = tmp_path / "output"
    result = run_spectral_features(
        {
            "input_path": str(input_path),
            "panel": {
                "members": [
                    "SOL@binance",
                    "BTC@binance",
                    "ETH@binance",
                ],
                "dependence_windows": [20],
                "minimum_complete_observations": 15,
                "minimum_window_coverage": 0.8,
            },
            "causal_features": {
                "volatility_windows": [6],
                "stress_window": 12,
                "volume_window": 12,
            },
        },
        output,
    )

    assert result.manifest.timestamps == 50
    expected = {
        "canonical_validation_report.json",
        "causal_series_features.csv",
        "spectral_diagnostics.json",
        "spectral_manifest.json",
        "spectral_market_structure.csv",
    }
    assert {path.name for path in output.iterdir()} == expected
    manifest = json.loads((output / "spectral_manifest.json").read_text())
    assert manifest["output_sha256"] == result.manifest.output_sha256
    assert manifest["manifest_sha256"] == result.manifest.manifest_sha256
