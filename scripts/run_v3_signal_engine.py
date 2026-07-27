from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shockbridge_signal_validity.v3.signal_runner import run_signal_engine


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Gate V3-4 unified RSI and Bollinger signal engine."
    )
    parser.add_argument(
        "--config",
        default="configs/v3_signal_engine_example.json",
        help="Path to the Gate V3-4 runner configuration.",
    )
    parser.add_argument(
        "--output-directory",
        default="outputs/v3/signal_engine",
        help="Directory for deterministic Gate V3-4 evidence outputs.",
    )
    arguments = parser.parse_args()
    config_path = Path(arguments.config)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    result = run_signal_engine(config, arguments.output_directory)
    print("Gate V3-4 unified RSI and Bollinger signal engine passed.")
    print(f"Registered signals: {result.feature_manifest['signal_count']}")
    print(f"Source rows: {result.feature_manifest['source_rows']}")
    print(f"Feature rows: {result.feature_manifest['rows']}")
    print("Automatic selection performed: False")
    print("Target accessed: False")
    print("Chronology accessed: False")
    print("Predictive/economic/failure claims produced: False")
    print("Next core gate: V3-5")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, KeyError, OSError, TypeError, ValueError) as error:
        print(f"Gate V3-4 signal engine failed: {error}", file=sys.stderr)
        raise SystemExit(1)
