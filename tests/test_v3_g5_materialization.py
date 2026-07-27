from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from shockbridge_signal_validity.v3.forecast_materialization import (
    materialize_real_development_foundation,
    read_raw_ohlcv,
    write_materialized_foundation,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"
REGISTRY = ROOT / "evidence" / "v3" / "g4_signal_lock" / "signal_registry_manifest.json"


def _write_market(path: Path, index: pd.DatetimeIndex, scale: float) -> None:
    trend = np.linspace(0.0, 1.0, len(index))
    close = scale * np.exp(0.001 * np.arange(len(index)) + 0.01 * np.sin(trend * 20.0))
    frame = pd.DataFrame(
        {
            "Date": index,
            "Open": close * 0.999,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": 1000.0 + np.arange(len(index), dtype=float),
        }
    )
    frame.to_csv(path, index=False, lineterminator="\n")


def _write_signal_features(path: Path, index: pd.DatetimeIndex) -> str:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    records: list[dict[str, object]] = []
    all_missing_signal = str(registry["signal_definitions"][0]["signal_id"])
    for signal_position, definition in enumerate(registry["signal_definitions"]):
        signal_id = str(definition["signal_id"])
        for row_position, timestamp in enumerate(index):
            value = np.nan if signal_id == all_missing_signal else (
                float(signal_position + 1) + float(row_position) / 1000.0
            )
            records.append(
                {
                    "timestamp": timestamp,
                    "asset": "SOL/USDT",
                    "venue": "binance_spot",
                    "signal_id": signal_id,
                    "feature_value": value,
                    "eligibility_status": (
                        "INELIGIBLE_TRAINING_PARAMETER_REQUIRED"
                        if signal_id == all_missing_signal
                        else "ELIGIBLE"
                    ),
                }
            )
    pd.DataFrame.from_records(records).to_csv(path, index=False, lineterminator="\n")
    return all_missing_signal


def _foundation(tmp_path: Path):
    index = pd.date_range("2021-01-01T00:00:00Z", periods=500, freq="4h")
    sol = tmp_path / "sol.csv"
    btc = tmp_path / "btc.csv"
    signals = tmp_path / "signals.csv"
    _write_market(sol, index, 10.0)
    _write_market(btc, index, 30000.0)
    missing_signal = _write_signal_features(signals, index)
    foundation = materialize_real_development_foundation(
        contract_path=CONTRACT,
        sol_path=sol,
        btc_path=btc,
        signal_features_path=signals,
        signal_registry_manifest_path=REGISTRY,
    )
    return foundation, missing_signal


def test_raw_ohlcv_reader_is_deterministic_and_strict(tmp_path: Path) -> None:
    index = pd.date_range("2021-01-01T00:00:00Z", periods=40, freq="4h")
    source = tmp_path / "market.csv"
    _write_market(source, index, 10.0)
    first = read_raw_ohlcv(source)
    second = read_raw_ohlcv(source)
    pd.testing.assert_frame_equal(first, second)
    assert first.index.equals(index)
    assert list(first.columns) == ["open", "high", "low", "close", "volume"]


def test_materialization_builds_all_registered_foundation_objects(tmp_path: Path) -> None:
    foundation, _ = _foundation(tmp_path)
    assert len(foundation.targets) == 500 * 6 - sum((1, 2, 3, 6, 12, 18))
    assert len(foundation.folds) == 120
    assert len(foundation.benchmark) == 500
    assert len(foundation.candidates) == 57
    assert len(foundation.matched_coverage) == 342
    assert set(foundation.targets["segment"]) == {"DEVELOPMENT"}
    assert foundation.matched_coverage["model_fitting_performed"].eq(False).all()


def test_unavailable_signal_remains_explicit_in_coverage(tmp_path: Path) -> None:
    foundation, missing_signal = _foundation(tmp_path)
    single = foundation.candidates.loc[
        foundation.candidates["member_signal_ids"]
        == json.dumps([missing_signal], separators=(",", ":"))
    ]
    assert len(single) == 1
    candidate_id = str(single.iloc[0]["candidate_id"])
    coverage = foundation.matched_coverage.loc[
        foundation.matched_coverage["candidate_id"] == candidate_id
    ]
    assert len(coverage) == 6
    assert set(coverage["coverage_status"]) == {
        "INELIGIBLE_NO_COMPLETE_MATCHED_ROWS"
    }
    assert coverage["matched_rows"].eq(0).all()


def test_available_pairs_have_identical_hashed_row_contracts(tmp_path: Path) -> None:
    foundation, _ = _foundation(tmp_path)
    available = foundation.matched_coverage.loc[
        foundation.matched_coverage["coverage_status"] == "MATCHED_ROWS_AVAILABLE"
    ]
    assert not available.empty
    assert available["matched_rows"].gt(0).all()
    assert available["row_contract_id"].notna().all()
    assert available["row_contract_id"].str.fullmatch(r"[0-9a-f]{64}").all()
    assert available["coverage_ratio"].between(0.0, 1.0, inclusive="both").all()


def test_written_evidence_is_deterministic_and_claim_free(tmp_path: Path) -> None:
    foundation, _ = _foundation(tmp_path)
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first = write_materialized_foundation(foundation, first_dir)
    second = write_materialized_foundation(foundation, second_dir)
    assert first == second
    assert first["model_fitting_performed"] is False
    assert first["development_pipeline_selection_performed"] is False
    assert first["signal_establishment_segment_accessed"] is False
    assert first["final_framework_reserve_accessed"] is False
    assert first["predictive_claims_produced"] is False
    assert first["economic_claims_produced"] is False
    for relative, digest in first["output_sha256"].items():
        assert (first_dir / relative).read_bytes() == (second_dir / relative).read_bytes()
        assert len(digest) == 64
