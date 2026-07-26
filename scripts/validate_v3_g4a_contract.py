from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from shockbridge_signal_validity.v3.chronology_signal_use_contract import (
    EXPECTED_PARENT_BLOB,
    EXPECTED_PARENT_LOCK,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "v3_external_chronology_signal_use_contract.json"
PARENT_LOCK = ROOT / EXPECTED_PARENT_LOCK


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    validate_contract(contract)

    observed_parent = git("rev-parse", f"HEAD:{PARENT_LOCK.name}")
    if observed_parent != EXPECTED_PARENT_BLOB:
        raise RuntimeError(
            "Final Gate V3-3 parent lock changed: "
            f"expected={EXPECTED_PARENT_BLOB} observed={observed_parent}"
        )

    print("Gate V3-4A chronology and signal-use contract validation passed.")
    print("Status: INDEPENDENT_CHRONOLOGY_AND_SIGNAL_USE_CONTRACT_FROZEN")
    print("Parent Gate V3-3 lock verified: True")
    print("Model outputs permitted during chronology compilation: False")
    print("RSI conditional rescue permitted: False")
    print("Bollinger conditional rescue permitted: False")
    print("Next subgate: V3-4B")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        KeyError,
        OSError,
        RuntimeError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"Gate V3-4A contract validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
