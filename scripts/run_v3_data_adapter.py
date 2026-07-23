from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shockbridge_signal_validity.v3.data_runner import run_data_adapter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Map a source dataset into the Version 3 canonical market-data "
            "contract and emit validation evidence."
        )
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("outputs/v3/data_adapter"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        result = run_data_adapter(config, args.output_directory)
        print("Version 3 canonical data validation passed.")
        print(f"Rows: {len(result.frame)}")
        print(f"Data SHA-256: {result.data_sha256}")
        print(f"Outputs: {args.output_directory.resolve()}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
