from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .data import fetch_ccxt_ohlcv, read_ohlcv_csv
from .features import FeatureConfig
from .framework import ValidationConfig, run_framework


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "ShockBridge three-stage validation of RSI and Bollinger Bands "
            "for SOL."
        )
    )
    parser.add_argument(
        "--signals",
        nargs="+",
        choices=["rsi", "bollinger", "combined"],
        default=["rsi", "bollinger", "combined"],
    )
    parser.add_argument(
        "--primary-signal",
        choices=["rsi", "bollinger", "combined"],
        default="bollinger",
    )
    parser.add_argument("--exchange", default="binance")
    parser.add_argument("--sol-symbol", default="SOL/USDT")
    parser.add_argument("--btc-symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="4h")
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--end", default=None)
    parser.add_argument("--sol-csv", type=Path, default=None)
    parser.add_argument("--btc-csv", type=Path, default=None)

    parser.add_argument("--horizon", type=int, default=1)
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument("--rsi-period", type=int, default=14)
    parser.add_argument("--rsi-lower", type=float, default=30.0)
    parser.add_argument("--rsi-upper", type=float, default=70.0)
    parser.add_argument("--bollinger-period", type=int, default=20)
    parser.add_argument("--bollinger-std", type=float, default=2.0)

    parser.add_argument("--splits", type=int, default=5)
    parser.add_argument("--lower-probability", type=float, default=0.45)
    parser.add_argument("--upper-probability", type=float, default=0.55)
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--block-size", type=int, default=10)
    parser.add_argument("--monitor-window", type=int, default=180)
    parser.add_argument("--failure-windows", type=int, default=3)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("outputs"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if (args.sol_csv is None) != (args.btc_csv is None):
            raise ValueError(
                "Provide both --sol-csv and --btc-csv, or neither."
            )

        if args.sol_csv is not None:
            sol = read_ohlcv_csv(args.sol_csv)
            btc = read_ohlcv_csv(args.btc_csv)
        else:
            sol = fetch_ccxt_ohlcv(
                symbol=args.sol_symbol,
                timeframe=args.timeframe,
                start=args.start,
                end=args.end,
                exchange_id=args.exchange,
            )
            btc = fetch_ccxt_ohlcv(
                symbol=args.btc_symbol,
                timeframe=args.timeframe,
                start=args.start,
                end=args.end,
                exchange_id=args.exchange,
            )

        feature_config = FeatureConfig(
            horizon=args.horizon,
            cost_bps=args.cost_bps,
            rsi_period=args.rsi_period,
            rsi_lower=args.rsi_lower,
            rsi_upper=args.rsi_upper,
            bollinger_period=args.bollinger_period,
            bollinger_std=args.bollinger_std,
        )
        validation_config = ValidationConfig(
            feature=feature_config,
            signals=tuple(args.signals),
            primary_signal=args.primary_signal,
            splits=args.splits,
            lower_probability=args.lower_probability,
            upper_probability=args.upper_probability,
            bootstrap_samples=args.bootstrap_samples,
            block_size=args.block_size,
            monitor_window=args.monitor_window,
            failure_windows=args.failure_windows,
        )

        result = run_framework(
            sol=sol,
            btc=btc,
            config=validation_config,
            output_directory=args.output_directory,
        )

        print("\nShockBridge Technical Signal Validity Framework")
        print("=" * 49)
        print(f"Observations: {result['observations']}")
        print(f"Primary signal: {result['primary_signal']}")
        print(
            "Primary model status: "
            f"{result['primary_verdict']['status']}"
        )
        print(result["primary_verdict"]["explanation"])
        print(f"Outputs: {args.output_directory.resolve()}")
        print("\nComplete model determinations:")
        print(json.dumps(result["verdicts"], indent=2))
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
