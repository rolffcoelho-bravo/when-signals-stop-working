from __future__ import annotations

import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v3.forecast_benchmark import (
    BASE_BENCHMARK_FEATURES,
    build_continuity_benchmark,
)
from shockbridge_signal_validity.v3.forecast_contract import (
    ForecastContract,
    ForecastProtocolViolation,
)
from shockbridge_signal_validity.v3.forecast_inventory import (
    build_candidate_inventory,
    load_signal_registry_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"
REGISTRY = ROOT / "evidence" / "v3" / "g4_signal_lock" / "signal_registry_manifest.json"


def contract() -> ForecastContract:
    return ForecastContract.from_path(CONTRACT)


def market(rows: int = 500) -> tuple[pd.DataFrame, pd.Series]:
    index = pd.date_range("2021-01-01", periods=rows, freq="4h", tz="UTC")
    phase = np.arange(rows, dtype=float)
    sol = 30.0 * np.exp(0.0003 * phase + 0.01 * np.sin(phase / 10.0))
    btc = 29000.0 * np.exp(0.0002 * phase + 0.01 * np.cos(phase / 12.0))
    frame = pd.DataFrame(
        {
            "high": sol * 1.01,
            "low": sol * 0.99,
            "close": sol,
            "volume": 1000.0 + np.square(np.sin(phase / 8.0)) * 100.0,
        },
        index=index,
    )
    return frame, pd.Series(btc, index=index, name="btc_close")


def test_continuity_benchmark_preserves_version_2_base_features() -> None:
    frame, btc = market()
    benchmark = build_continuity_benchmark(frame, btc, contract())
    assert tuple(benchmark.columns) == BASE_BENCHMARK_FEATURES
    assert benchmark.index.equals(frame.index)
    assert benchmark.iloc[40:].notna().all().all()


def test_continuity_benchmark_is_prefix_invariant() -> None:
    frame, btc = market(600)
    full = build_continuity_benchmark(frame, btc, contract())
    prefix = build_continuity_benchmark(frame.iloc[:500], btc.iloc[:500], contract())
    pd.testing.assert_frame_equal(full.loc[prefix.index], prefix)


def test_continuity_benchmark_rejects_missing_btc_alignment() -> None:
    frame, btc = market()
    with pytest.raises(ForecastProtocolViolation, match="align exactly"):
        build_continuity_benchmark(frame, btc.drop(btc.index[100]), contract())


def test_candidate_inventory_preserves_all_locked_signals_and_bounded_blocks() -> None:
    manifest = load_signal_registry_manifest(REGISTRY)
    inventory = build_candidate_inventory(manifest)
    assert len(inventory) == 57
    assert int((inventory["candidate_kind"] == "SINGLE_SIGNAL").sum()) == 48
    assert int((inventory["candidate_kind"] == "PREDECLARED_FAMILY_BLOCK").sum()) == 8
    assert int((inventory["candidate_kind"] == "PREDECLARED_COMBINED_BLOCK").sum()) == 1
    assert not inventory["candidate_id"].duplicated().any()
    assert not inventory["automatic_selection_performed"].any()
    blocks = set(
        inventory.loc[
            inventory["candidate_kind"] == "PREDECLARED_FAMILY_BLOCK",
            "candidate_block",
        ]
    )
    assert blocks == {
        "RSI_LEVEL_DYNAMICS",
        "RSI_MEAN_REVERSION",
        "RSI_CONTINUATION",
        "RSI_DIVERGENCE",
        "BOLLINGER_POSITION",
        "BOLLINGER_MEAN_REVERSION",
        "BOLLINGER_BREAKOUT",
        "BOLLINGER_VOLATILITY_STRUCTURE",
    }


def test_registry_manifest_count_mutation_fails_closed(tmp_path: Path) -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    payload["signal_count"] = 47
    mutated = tmp_path / "mutated.json"
    mutated.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ForecastProtocolViolation, match="exactly 48"):
        load_signal_registry_manifest(mutated)


def test_standalone_foundation_verifier_passes() -> None:
    completed = subprocess.run(
        ["python", "scripts/verify_v3_g5_foundation.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "Gate V3-5 forecast foundation verified." in completed.stdout
    assert "Nested fold records: 120" in completed.stdout
    assert "Bounded candidate inventory: 57" in completed.stdout
    assert "Model fitting performed: False" in completed.stdout
