from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from shockbridge_signal_validity.data import read_ohlcv_csv


EXPECTED_INTERVAL = pd.Timedelta(hours=4)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate downloaded SOL and BTC four-hour OHLCV files."
    )
    parser.add_argument(
        "--sol-csv",
        type=Path,
        default=Path("data/raw/sol_usdt_4h.csv"),
    )
    parser.add_argument(
        "--btc-csv",
        type=Path,
        default=Path("data/raw/btc_usdt_4h.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/data_validation.json"),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when any timestamp gap is found.",
    )
    return parser.parse_args()


def inspect(name: str, path: Path) -> dict:
    frame = read_ohlcv_csv(path)
    differences = frame.index.to_series().diff().dropna()
    gaps = differences[differences > EXPECTED_INTERVAL]

    return {
        "name": name,
        "path": str(path),
        "rows": len(frame),
        "start": str(frame.index.min()),
        "end": str(frame.index.max()),
        "duplicate_timestamps": int(frame.index.duplicated().sum()),
        "missing_values": int(frame.isna().sum().sum()),
        "chronological": bool(frame.index.is_monotonic_increasing),
        "expected_interval_hours": 4,
        "nonstandard_intervals": int((differences != EXPECTED_INTERVAL).sum()),
        "large_gaps": int(len(gaps)),
        "largest_gap_hours": (
            float(gaps.max() / pd.Timedelta(hours=1))
            if len(gaps)
            else 0.0
        ),
    }


def main() -> int:
    args = parse_args()
    sol = inspect("SOL", args.sol_csv)
    btc = inspect("BTC", args.btc_csv)

    sol_frame = read_ohlcv_csv(args.sol_csv)
    btc_frame = read_ohlcv_csv(args.btc_csv)
    overlap = sol_frame.index.intersection(btc_frame.index)

    result = {
        "sol": sol,
        "btc": btc,
        "overlapping_timestamps": len(overlap),
        "overlap_start": str(overlap.min()) if len(overlap) else None,
        "overlap_end": str(overlap.max()) if len(overlap) else None,
        "status": "PASS",
        "warnings": [],
    }

    for market in (sol, btc):
        if market["duplicate_timestamps"] > 0:
            result["warnings"].append(
                f"{market['name']} contains duplicate timestamps."
            )
        if market["missing_values"] > 0:
            result["warnings"].append(
                f"{market['name']} contains missing OHLCV values."
            )
        if market["large_gaps"] > 0:
            result["warnings"].append(
                f"{market['name']} contains {market['large_gaps']} gaps "
                "larger than four hours."
            )

    if len(overlap) < 500:
        result["status"] = "FAIL"
        result["warnings"].append(
            "Fewer than 500 overlapping SOL and BTC observations."
        )
    elif args.strict and any(
        market["large_gaps"] > 0 for market in (sol, btc)
    ):
        result["status"] = "FAIL"
    elif result["warnings"]:
        result["status"] = "PASS_WITH_WARNINGS"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    print(f"Validation record: {args.output}")
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
