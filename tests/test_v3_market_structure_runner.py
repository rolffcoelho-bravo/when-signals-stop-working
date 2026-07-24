from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from shockbridge_signal_validity.v3.market_structure_runner import run_market_structure
from tests.test_v3_market_structure import synthetic_panel


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
