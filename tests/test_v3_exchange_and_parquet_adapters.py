from __future__ import annotations

import pandas as pd

from shockbridge_signal_validity.v3 import CcxtOHLCVAdapter, FileMarketDataAdapter


def canonical_fixture() -> pd.DataFrame:
    return pd.DataFrame(
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


def test_parquet_reference_path_uses_same_canonical_contract(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "market.parquet"
    path.write_bytes(b"fixture")
    monkeypatch.setattr(
        pd,
        "read_parquet",
        lambda *_args, **_kwargs: canonical_fixture(),
    )
    result = FileMarketDataAdapter().load(
        {"path": str(path), "format": "parquet"}
    )
    assert result.validation.valid
    assert result.manifest.source_format == "parquet"


def test_ccxt_adapter_maps_exchange_frame(monkeypatch) -> None:
    source = canonical_fixture().drop(columns=["asset", "venue"]).copy()
    source = source.rename(
        columns={
            "timestamp": "Timestamp",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    ).set_index("Timestamp")
    source.index = pd.to_datetime(source.index, utc=True)

    import shockbridge_signal_validity.data as legacy_data

    monkeypatch.setattr(
        legacy_data,
        "fetch_ccxt_ohlcv",
        lambda **_kwargs: source,
    )
    result = CcxtOHLCVAdapter().load(
        {
            "symbol": "SOL/USDT",
            "asset": "SOL/USDT",
            "exchange": "binance",
            "timeframe": "4h",
            "start": "2026-01-01",
        }
    )
    assert result.validation.valid
    assert set(result.frame["asset"]) == {"SOL/USDT"}
    assert set(result.frame["venue"]) == {"binance"}
    assert result.manifest.source_format == "ccxt_ohlcv"
