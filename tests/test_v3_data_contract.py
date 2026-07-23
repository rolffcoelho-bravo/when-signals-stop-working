from __future__ import annotations

import pandas as pd
import pytest

from shockbridge_signal_validity.v3 import (
    CanonicalDataError,
    SourceManifest,
    canonicalize_market_frame,
    stable_frame_hash,
)


def valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": ["2026-01-01 04:00", "2026-01-01 00:00"],
            "asset": ["SOL/USDT", "SOL/USDT"],
            "venue": ["binance", "binance"],
            "open": [101.0, 100.0],
            "high": [103.0, 102.0],
            "low": [100.0, 99.0],
            "close": [102.0, 101.0],
            "volume": [12.0, 10.0],
        }
    )


def test_canonical_frame_is_utc_sorted_and_valid() -> None:
    frame, report = canonicalize_market_frame(valid_frame(), timezone="UTC")
    assert report.valid
    assert frame["timestamp"].dt.tz is not None
    assert frame["timestamp"].is_monotonic_increasing
    assert any(issue.code == "SOURCE_ORDER_NORMALIZED" for issue in report.issues)


def test_invalid_ohlc_and_duplicate_keys_fail_closed() -> None:
    raw = valid_frame()
    raw.loc[0, "low"] = 104.0
    raw.loc[1, ["timestamp", "asset", "venue"]] = raw.loc[
        0, ["timestamp", "asset", "venue"]
    ].to_numpy()
    _, report = canonicalize_market_frame(raw, timezone="UTC")
    assert not report.valid
    codes = {issue.code for issue in report.issues}
    assert "INVALID_OHLC_BOUNDS" in codes
    assert "DUPLICATE_CANONICAL_KEY" in codes


def test_missing_required_columns_are_reported() -> None:
    _, report = canonicalize_market_frame(valid_frame().drop(columns="volume"))
    assert not report.valid
    assert report.critical_count == 1
    assert report.issues[0].code == "MISSING_REQUIRED_COLUMNS"


def test_stable_frame_hash_is_deterministic_after_canonicalization() -> None:
    first, _ = canonicalize_market_frame(valid_frame())
    second, _ = canonicalize_market_frame(
        valid_frame().iloc[::-1].reset_index(drop=True)
    )
    assert stable_frame_hash(first) == stable_frame_hash(second)


def test_require_valid_raises_for_critical_report(tmp_path) -> None:
    from shockbridge_signal_validity.v3 import CanonicalMarketFrame

    frame, report = canonicalize_market_frame(valid_frame().drop(columns="volume"))
    manifest = SourceManifest(
        adapter_id="fixture",
        source_uri=tmp_path.as_uri(),
        source_format="fixture",
        source_sha256="0" * 64,
        config_sha256="1" * 64,
        schema_version="v3.canonical-market.v1",
        loaded_rows=len(frame),
        data_sha256="2" * 64,
    )
    with pytest.raises(CanonicalDataError):
        CanonicalMarketFrame(frame, report, manifest).require_valid()
