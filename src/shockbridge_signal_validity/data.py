from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


_REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def standardize_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a UTC-indexed OHLCV frame with canonical column names."""
    data = frame.copy()

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data.columns = [str(column).strip().title() for column in data.columns]

    date_candidates = [
        column for column in ("Date", "Datetime", "Timestamp") if column in data.columns
    ]
    if date_candidates:
        date_column = date_candidates[0]
        data[date_column] = pd.to_datetime(
            data[date_column], utc=True, errors="coerce"
        )
        data = data.set_index(date_column)
    elif not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("OHLCV data require a Date, Datetime, or Timestamp column.")

    data.index = pd.to_datetime(data.index, utc=True, errors="coerce")
    data = data.loc[~data.index.isna()].sort_index()
    data = data.loc[~data.index.duplicated(keep="last")]

    missing = [column for column in _REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(f"Missing OHLCV columns: {missing}")

    return (
        data[_REQUIRED_COLUMNS]
        .apply(pd.to_numeric, errors="coerce")
        .dropna()
        .sort_index()
    )


def read_ohlcv_csv(path: Path) -> pd.DataFrame:
    return standardize_ohlcv(pd.read_csv(path))


def fetch_ccxt_ohlcv(
    symbol: str,
    timeframe: str,
    start: str,
    end: str | None = None,
    exchange_id: str = "binance",
    limit: int = 1000,
) -> pd.DataFrame:
    """Download public OHLCV history with ccxt pagination."""
    try:
        import ccxt
    except ImportError as exc:
        raise RuntimeError(
            "Install ccxt or provide local CSV files with --sol-csv and --btc-csv."
        ) from exc

    exchange_class: Any = getattr(ccxt, exchange_id, None)
    if exchange_class is None:
        raise ValueError(f"Unknown ccxt exchange: {exchange_id}")

    exchange = exchange_class({"enableRateLimit": True})
    exchange.load_markets()

    if symbol not in exchange.markets:
        raise ValueError(f"{symbol} is not available on {exchange_id}.")

    since = int(pd.Timestamp(start, tz="UTC").timestamp() * 1000)
    end_ms = (
        int(pd.Timestamp(end, tz="UTC").timestamp() * 1000)
        if end is not None
        else None
    )

    rows: list[list[float]] = []
    while True:
        batch = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=since,
            limit=limit,
        )
        if not batch:
            break

        for row in batch:
            if end_ms is not None and int(row[0]) >= end_ms:
                break
            rows.append(row)

        last_timestamp = int(batch[-1][0])
        if end_ms is not None and last_timestamp >= end_ms:
            break
        if len(batch) < limit:
            break
        if last_timestamp < since:
            break

        since = last_timestamp + 1

    if not rows:
        raise RuntimeError(
            f"No OHLCV data returned for {symbol} on {exchange_id}."
        )

    frame = pd.DataFrame(
        rows,
        columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"],
    )
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], unit="ms", utc=True)
    return standardize_ohlcv(frame)
