from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shockbridge_signal_validity.v3.market_structure_runner import run_market_structure


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the Version 3 causal spectral and network market-structure "
            "evidence package."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/v3_market_structure_example.json"),
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("outputs/v3/market_structure"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        result = run_market_structure(config, args.output_directory)
        print("Version 3 market-structure extension completed.")
        print(f"Rows: {result.manifest.rows}")
        print(f"Timestamps: {result.manifest.timestamps}")
        print(f"Output SHA-256: {result.manifest.output_sha256}")
        print(f"Outputs: {args.output_directory.resolve()}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
