from __future__ import annotations

import pandas as pd
import pytest

from shockbridge_signal_validity.v3 import (
    CanonicalDataError,
    FileMarketDataAdapter,
    OptionalFieldFileAdapter,
    merge_optional_fields,
)


def test_differently_formatted_csvs_map_to_same_canonical_frame(tmp_path) -> None:
    standard = pd.DataFrame(
        {
            "timestamp": ["2026-01-01T00:00:00Z", "2026-01-01T04:00:00Z"],
            "asset": ["SOL/USDT", "SOL/USDT"],
            "venue": ["binance", "binance"],
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [10.0, 12.0],
        }
    )
    alternate = pd.DataFrame(
        {
            "time_ms": [1767225600000, 1767240000000],
            "o": [100.0, 101.0],
            "h": [102.0, 103.0],
            "l": [99.0, 100.0],
            "c": [101.0, 102.0],
            "qty": [10.0, 12.0],
        }
    )
    standard_path = tmp_path / "standard.csv"
    alternate_path = tmp_path / "alternate.csv"
    standard.to_csv(standard_path, index=False)
    alternate.to_csv(alternate_path, index=False)

    first = FileMarketDataAdapter().load({"path": str(standard_path)})
    second = FileMarketDataAdapter().load(
        {
            "path": str(alternate_path),
            "timestamp_unit": "ms",
            "column_map": {
                "timestamp": "time_ms",
                "open": "o",
                "high": "h",
                "low": "l",
                "close": "c",
                "volume": "qty",
            },
            "constants": {"asset": "SOL/USDT", "venue": "binance"},
        }
    )
    assert first.validation.valid
    assert second.validation.valid
    pd.testing.assert_frame_equal(first.frame, second.frame)
    assert first.data_sha256 == second.data_sha256


def test_adapter_rejects_unregistered_mapping_target(tmp_path) -> None:
    path = tmp_path / "data.csv"
    pd.DataFrame({"x": [1]}).to_csv(path, index=False)
    with pytest.raises(CanonicalDataError, match="unregistered"):
        FileMarketDataAdapter().load(
            {"path": str(path), "column_map": {"secret_alpha": "x"}}
        )


def test_optional_fields_merge_without_forward_fill(tmp_path) -> None:
    base_path = tmp_path / "base.csv"
    pd.DataFrame(
        {
            "timestamp": ["2026-01-01T00:00:00Z", "2026-01-01T04:00:00Z"],
            "asset": ["SOL/USDT", "SOL/USDT"],
            "venue": ["binance", "binance"],
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [10.0, 12.0],
        }
    ).to_csv(base_path, index=False)
    optional_path = tmp_path / "funding.csv"
    pd.DataFrame(
        {
            "timestamp": ["2026-01-01T00:00:00Z"],
            "asset": ["SOL/USDT"],
            "venue": ["binance"],
            "funding_rate": [0.0001],
        }
    ).to_csv(optional_path, index=False)

    base = FileMarketDataAdapter().load({"path": str(base_path)})
    supplemental = OptionalFieldFileAdapter().load(
        {"path": str(optional_path), "fields": ["funding_rate"]}
    )
    merged = merge_optional_fields(base, supplemental)
    assert merged.validation.valid
    assert merged.frame["funding_rate"].notna().sum() == 1
    assert pd.isna(merged.frame.loc[1, "funding_rate"])


def test_duplicate_optional_keys_are_rejected(tmp_path) -> None:
    path = tmp_path / "duplicates.csv"
    row = {
        "timestamp": "2026-01-01T00:00:00Z",
        "asset": "SOL/USDT",
        "venue": "binance",
        "open_interest": 1000,
    }
    pd.DataFrame([row, row]).to_csv(path, index=False)
    with pytest.raises(CanonicalDataError, match="duplicate"):
        OptionalFieldFileAdapter().load(
            {"path": str(path), "fields": ["open_interest"]}
        )
