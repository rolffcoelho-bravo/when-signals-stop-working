from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from shockbridge_signal_validity.v3.market_structure_runner import run_market_structure


def synthetic_panel(periods: int = 60) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01", periods=periods, freq="4h", tz="UTC")
    rows: list[dict[str, object]] = []
    common = np.sin(np.linspace(0.0, 7.0, periods)) * 0.003
    for index, asset in enumerate(("SOL", "BTC", "ETH", "BNB")):
        returns = common + np.cos(
            np.linspace(0.0, 4.0 + index, periods)
        ) * (0.0005 + index * 0.0001)
        closes = (100.0 + index * 10.0) * np.exp(np.cumsum(returns))
        for timestamp, close in zip(timestamps, closes):
            rows.append(
                {
                    "timestamp": timestamp,
                    "asset": asset,
                    "venue": "fixture",
                    "open": close * 0.999,
                    "high": close * 1.002,
                    "low": close * 0.998,
                    "close": close,
                    "volume": 1000.0 + index,
                }
            )
    return pd.DataFrame(rows)


def test_runner_emits_complete_evidence_package(tmp_path: Path) -> None:
    source = tmp_path / "canonical.csv"
    synthetic_panel().to_csv(source, index=False)
    config = {
        "input_path": str(source),
        "panel": {
            "members": [
                "SOL@fixture",
                "BTC@fixture",
                "ETH@fixture",
                "BNB@fixture",
            ],
            "dependence_windows": [20],
            "minimum_complete_observations": 15,
            "minimum_window_coverage": 0.80,
            "estimator": "sample",
            "network_threshold": 0.50,
        },
        "causal_features": {
            "volatility_windows": [6, 18],
            "stress_window": 18,
            "volume_window": 18,
        },
        "network": {
            "threshold": 0.50,
            "community_resolution": 1.0,
            "dynamic_window": 3,
        },
    }
    output = tmp_path / "outputs"
    result = run_market_structure(config, output)
    expected = {
        "market_structure_features.csv",
        "causal_series_features.csv",
        "market_structure_manifest.json",
        "market_structure_diagnostics.json",
        "canonical_validation_report.json",
    }
    assert expected == {path.name for path in output.iterdir()}
    manifest = json.loads(
        (output / "market_structure_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["schema_version"] == "v3.market-structure-extension.v1"
    assert manifest["manifest_sha256"] == result.manifest.manifest_sha256
    data = pd.read_csv(output / "market_structure_features.csv")
    assert "network_modularity" in data
    assert "mst_total_distance" in data
