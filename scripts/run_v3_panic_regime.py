from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from shockbridge_signal_validity.v3.panic_regime_runner import (
    run_panic_regime_engine,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Gate V3-3B panic-consistent probabilistic regime engine."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/v3_panic_regime_example.json"),
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("outputs/v3/panic_regime"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        result = run_panic_regime_engine(config, args.output_directory)
        print("Gate V3-3B probabilistic regime engine completed.")
        print(f"Timestamps: {result.manifest.timestamps}")
        print(f"Probability rows: {result.manifest.rows}")
        print("Registered models:")
        for model_id in result.manifest.model_ids:
            print(f"  - {model_id}")
        print("Automatic model selection performed: False")
        print("Uncertainty status: PENDING_V3_3C")
        print(f"Outputs: {args.output_directory.resolve()}")
        return 0
    except Exception as error:
        print(f"Gate V3-3B failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
