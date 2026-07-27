from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

from shockbridge_signal_validity.v3.signal_runner import run_signal_engine

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configs" / "v3_signal_interpretation_registry.json"
FROZEN_ADAPTER = ROOT / "configs" / "v3_adapter_frozen_sol.json"
PRODUCTION_CONFIG = ROOT / "configs" / "v3_signal_engine_example.json"


def fixture(rows: int = 80) -> pd.DataFrame:
    timestamp = pd.date_range("2024-01-01", periods=rows, freq="4h", tz="UTC")
    x = np.arange(rows, dtype=float)
    close = 100.0 + 0.10 * x + np.sin(x / 4.0)
    return pd.DataFrame(
        {
            "timestamp": timestamp,
            "asset": "SOL",
            "venue": "binance",
            "open": close - 0.1,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 1000.0 + x,
        }
    )


def test_runner_writes_complete_deterministic_evidence_package(tmp_path: Path) -> None:
    input_path = tmp_path / "canonical.csv"
    fixture().to_csv(input_path, index=False)
    output = tmp_path / "output"
    config = {
        "input_path": str(input_path),
        "registry_path": str(REGISTRY),
        "timezone": "UTC",
        "training_only_parameters": {},
    }
    result = run_signal_engine(config, output)
    expected = {
        "signal_features.csv",
        "signal_registry_manifest.json",
        "signal_feature_manifest.json",
        "signal_coverage_report.json",
        "signal_validation_report.json",
        "canonical_validation_report.json",
    }
    assert {path.name for path in output.iterdir()} == expected
    first = {path.name: path.read_bytes() for path in output.iterdir()}
    second_result = run_signal_engine(config, output)
    second = {path.name: path.read_bytes() for path in output.iterdir()}
    assert first == second
    assert result.feature_manifest == second_result.feature_manifest


def test_runner_manifest_and_validation_preserve_gate_boundaries(tmp_path: Path) -> None:
    input_path = tmp_path / "canonical.csv"
    source = fixture()
    source.to_csv(input_path, index=False)
    output = tmp_path / "output"
    run_signal_engine(
        {
            "input_path": str(input_path),
            "registry_path": str(REGISTRY),
            "timezone": "UTC",
        },
        output,
    )
    manifest = json.loads((output / "signal_feature_manifest.json").read_text())
    validation = json.loads((output / "signal_validation_report.json").read_text())
    assert manifest["signal_count"] == 48
    assert manifest["source_rows"] == len(source)
    assert manifest["expected_rows"] == len(source) * 48
    assert manifest["rows"] == manifest["expected_rows"]
    assert manifest["row_count_identity_verified"] is True
    assert manifest["automatic_selection_performed"] is False
    assert manifest["target_accessed"] is False
    assert manifest["chronology_accessed"] is False
    assert validation["row_count_identity_verified"] is True
    assert validation["context_columns_accessed"] == []
    assert validation["next_gate"] == "V3-5"
    assert validation["richard_question_advanced_by"] == (
        "DEFINES_SIGNAL_INFORMATION_TO_BE_TESTED"
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_v3_g4_signal_outputs.py"),
            "--output-directory",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "Gate V3-4 output evidence verified." in completed.stdout

    adapter = json.loads(FROZEN_ADAPTER.read_text(encoding="utf-8"))
    production = json.loads(PRODUCTION_CONFIG.read_text(encoding="utf-8"))
    assert adapter["adapter"]["path"] == "data/raw/sol_usdt_4h.csv"
    assert adapter["adapter"]["constants"] == {
        "asset": "SOL/USDT",
        "venue": "binance_spot",
    }
    assert adapter["adapter"]["column_map"]["timestamp"] == "Date"
    assert production["input_path"] == (
        "outputs/v3/data_adapter/canonical_market_data.csv"
    )
    assert (ROOT / "data" / "raw" / "sol_usdt_4h.csv").is_file()

    parent = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_v3_g1_data_adapter.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert parent.returncode == 0, parent.stderr
    assert "Gate V3-1 historical lock objects verified" in parent.stdout
    assert "Current shared Version 3 exports preserve Gate V3-1 compatibility" in (
        parent.stdout
    )


def test_runner_uses_lf_for_deterministic_csv_evidence(tmp_path: Path) -> None:
    input_path = tmp_path / "canonical.csv"
    fixture().to_csv(input_path, index=False)
    output = tmp_path / "output"
    run_signal_engine(
        {
            "input_path": str(input_path),
            "registry_path": str(REGISTRY),
            "timezone": "UTC",
        },
        output,
    )
    payload = (output / "signal_features.csv").read_bytes()
    assert b"\r\n" not in payload
    assert payload.endswith(b"\n")
