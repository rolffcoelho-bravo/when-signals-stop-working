from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shockbridge_signal_validity.v3.chronology_registry import write_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the locked-independent V3-4B chronology package.")
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("configs/v3_external_chronology_registry.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/v3/g4b_chronology"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry_path = args.registry if args.registry.is_absolute() else ROOT / args.registry
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    hashes = write_outputs(registry_path, output_path)
    manifest = json.loads((output_path / "chronology_manifest.json").read_text(encoding="utf-8"))
    print("Gate V3-4B independent chronology compilation passed.")
    print(f"Canonical events: {manifest['event_count']}")
    print(f"Provenance sources: {manifest['source_count']}")
    print(f"Confirmed timing events: {manifest['confirmed_event_count']}")
    print(f"Boundary-uncertain events: {manifest['boundary_uncertain_event_count']}")
    print("Model outputs accessed: False")
    print("Event alignment executed: False")
    print("Output hashes:")
    for name in sorted(hashes):
        print(f"  {name}: {hashes[name]}")
    print("Next subgate: V3-4C")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(f"Gate V3-4B chronology compilation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
