from __future__ import annotations

from hashlib import sha1
import json
from pathlib import Path

import pandas as pd

from shockbridge_signal_validity.v3 import (
    SCHEMA_VERSION,
    canonicalize_market_frame,
    stable_frame_hash,
)

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "V3_G1_DATA_ADAPTER_LOCK.json"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return sha1(header + data).hexdigest()


def verify_locked_files(lock: dict[str, object]) -> None:
    protected = lock.get("protected_files")
    if not isinstance(protected, dict):
        raise RuntimeError("Gate V3-1 lock has no protected_files mapping.")
    failures: list[str] = []
    for relative_path, expected_sha in protected.items():
        path = ROOT / str(relative_path)
        if not path.is_file():
            failures.append(f"missing: {relative_path}")
            continue
        actual_sha = git_blob_sha(path)
        if actual_sha != expected_sha:
            failures.append(
                f"hash mismatch: {relative_path} expected={expected_sha} actual={actual_sha}"
            )
    if failures:
        raise RuntimeError("Gate V3-1 lock verification failed:\n" + "\n".join(failures))


def verify_contract_behaviour(lock: dict[str, object]) -> None:
    if lock.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeError("Gate lock and implementation schema versions differ.")

    raw = pd.DataFrame(
        {
            "timestamp": ["2026-01-01T04:00:00Z", "2026-01-01T00:00:00Z"],
            "asset": ["SOL/USDT", "SOL/USDT"],
            "venue": ["fixture", "fixture"],
            "open": [101.0, 100.0],
            "high": [103.0, 102.0],
            "low": [100.0, 99.0],
            "close": [102.0, 101.0],
            "volume": [12.0, 10.0],
        }
    )
    canonical, report = canonicalize_market_frame(raw)
    if not report.valid:
        raise RuntimeError("Registered synthetic canonical fixture did not validate.")
    reversed_frame, reversed_report = canonicalize_market_frame(
        raw.iloc[::-1].reset_index(drop=True)
    )
    if not reversed_report.valid:
        raise RuntimeError("Reordered synthetic fixture did not validate.")
    if stable_frame_hash(canonical) != stable_frame_hash(reversed_frame):
        raise RuntimeError("Canonical data hashing is not order deterministic.")


def main() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("gate") != "V3-1":
        raise RuntimeError("Unexpected gate identifier in Version 3 lock.")
    verify_locked_files(lock)
    verify_contract_behaviour(lock)
    print("Gate V3-1 canonical data and adapter lock verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
