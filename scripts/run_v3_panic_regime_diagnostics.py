from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from shockbridge_signal_validity.v3.panic_regime_diagnostics_runner import (
    run_panic_regime_diagnostics,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Gate V3-3C panic-regime governance and diagnostics."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/v3_panic_regime_diagnostics_example.json"),
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("outputs/v3/panic_regime_governance"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        result = run_panic_regime_diagnostics(config, args.output_directory)
        print("Gate V3-3C governance and diagnostics completed.")
        print(f"Timestamps: {result.manifest.timestamps}")
        print(f"Probability rows: {result.manifest.probability_rows}")
        print("Probability intervals: GOVERNED_PUBLICATION_GATE_APPLIED")
        print("Transition, occupancy and duration evidence: COMPLETE")
        print("Mechanism contributions and disagreement diagnostics: COMPLETE")
        print("Automatic model selection performed: False")
        print("Final V3-3 lock permitted: False")
        print("Next subgate: V3-3D")
        print(f"Outputs: {args.output_directory.resolve()}")
        return 0
    except Exception as error:
        print(f"Gate V3-3C failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
