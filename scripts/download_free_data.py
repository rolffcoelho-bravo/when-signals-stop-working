from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from shockbridge_signal_validity.data import fetch_ccxt_ohlcv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download free public four-hour SOL and BTC OHLCV candles."
    )
    parser.add_argument("--exchange", default="binance")
    parser.add_argument("--sol-symbol", default="SOL/USDT")
    parser.add_argument("--btc-symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="4h")
    parser.add_argument("--start", default="2021-01-01T00:00:00Z")
    parser.add_argument("--end", default="2026-07-22T12:00:00Z")
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("data/raw"),
    )
    return parser.parse_args()


def save_frame(frame, path: Path) -> None:
    output = frame.copy()
    output.index.name = "Date"
    output.reset_index().to_csv(path, index=False)


def main() -> int:
    args = parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)

    print("Downloading SOL candles...")
    sol = fetch_ccxt_ohlcv(
        symbol=args.sol_symbol,
        timeframe=args.timeframe,
        start=args.start,
        end=args.end,
        exchange_id=args.exchange,
    )

    print("Downloading BTC candles...")
    btc = fetch_ccxt_ohlcv(
        symbol=args.btc_symbol,
        timeframe=args.timeframe,
        start=args.start,
        end=args.end,
        exchange_id=args.exchange,
    )

    sol_path = args.output_directory / "sol_usdt_4h.csv"
    btc_path = args.output_directory / "btc_usdt_4h.csv"
    save_frame(sol, sol_path)
    save_frame(btc, btc_path)

    manifest = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "exchange": args.exchange,
        "sol_symbol": args.sol_symbol,
        "btc_symbol": args.btc_symbol,
        "timeframe": args.timeframe,
        "requested_start": args.start,
        "requested_end": args.end,
        "sol_rows": len(sol),
        "btc_rows": len(btc),
        "sol_first_timestamp": str(sol.index.min()),
        "sol_last_timestamp": str(sol.index.max()),
        "btc_first_timestamp": str(btc.index.min()),
        "btc_last_timestamp": str(btc.index.max()),
        "files": {
            "sol": str(sol_path),
            "btc": str(btc_path),
        },
        "source_endpoint_class": "Binance public spot market-data API accessed through CCXT",
        "source_documentation": [
            "https://developers.binance.com/en/docs/products/spot/rest-api",
            "https://github.com/ccxt/ccxt/wiki/manual",
        ],
        "snapshot_policy": (
            "The default end is frozen for exact V1 replication. Use explicit "
            "arguments to create a new data vintage."
        ),
        "note": (
            "Public exchange OHLCV data. No account credentials, private account "
            "data, or trading permissions were used."
        ),
    }

    manifest_path = args.output_directory / "download_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"SOL data: {sol_path} ({len(sol)} rows)")
    print(f"BTC data: {btc_path} ({len(btc)} rows)")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
