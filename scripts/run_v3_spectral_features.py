from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shockbridge_signal_validity.v3.spectral_runner import run_spectral_features


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build Version 3 causal multi-asset and spectral market-structure "
            "features."
        )
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("outputs/v3/spectral"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        result = run_spectral_features(config, args.output_directory)
        print("Version 3 Gate V3-2 spectral feature engine")
        print("=" * 45)
        print(f"Rows: {len(result.frame)}")
        print(f"Timestamps: {result.manifest.timestamps}")
        print(f"Panel: {', '.join(result.manifest.panel_members)}")
        print(f"Estimator: {result.manifest.estimator}")
        print(f"Output hash: {result.manifest.output_sha256}")
        print(f"Outputs: {args.output_directory.resolve()}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
