from __future__ import annotations

from hashlib import sha1
import json
from pathlib import Path
import subprocess

import pandas as pd

from shockbridge_signal_validity.v3 import (
    SCHEMA_VERSION,
    canonicalize_market_frame,
    stable_frame_hash,
)

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "V3_G1_DATA_ADAPTER_LOCK.json"
HISTORICAL_BOUNDARY = "7a7a5c55184aadfb436774ff1e497ce873a96b6e"
SHARED_EXPORT_SURFACES = {
    "src/shockbridge_signal_validity/v3/__init__.py",
}
REQUIRED_V3_G1_EXPORTS = {
    "CanonicalDataError",
    "CanonicalMarketFrame",
    "CcxtOHLCVAdapter",
    "FileMarketDataAdapter",
    "MarketDataAdapter",
    "OPTIONAL_COLUMNS",
    "OptionalFieldFileAdapter",
    "REQUIRED_COLUMNS",
    "SCHEMA_VERSION",
    "SourceManifest",
    "ValidationIssue",
    "ValidationReport",
    "build_adapter",
    "canonicalize_market_frame",
    "merge_optional_fields",
    "stable_frame_hash",
}


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return sha1(header + data).hexdigest()


def git_object_sha(commit: str, relative_path: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", f"{commit}:{relative_path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(
            f"Unable to resolve historical Gate V3-1 object {relative_path}: {detail}"
        )
    return completed.stdout.strip()


def verify_historical_boundary() -> None:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", HISTORICAL_BOUNDARY, "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Historical Gate V3-1 boundary is not an ancestor of the current branch."
        )


def verify_historical_locked_files(lock: dict[str, object]) -> None:
    protected = lock.get("protected_files")
    if not isinstance(protected, dict):
        raise RuntimeError("Gate V3-1 lock has no protected_files mapping.")
    failures: list[str] = []
    for relative_path, expected_sha in protected.items():
        actual_sha = git_object_sha(HISTORICAL_BOUNDARY, str(relative_path))
        if actual_sha != expected_sha:
            failures.append(
                f"historical hash mismatch: {relative_path} "
                f"expected={expected_sha} actual={actual_sha}"
            )
    if failures:
        raise RuntimeError(
            "Gate V3-1 historical lock verification failed:\n" + "\n".join(failures)
        )


def verify_current_direct_files(lock: dict[str, object]) -> None:
    protected = lock.get("protected_files")
    if not isinstance(protected, dict):
        raise RuntimeError("Gate V3-1 lock has no protected_files mapping.")
    failures: list[str] = []
    for relative_path, expected_sha in protected.items():
        relative = str(relative_path)
        if relative in SHARED_EXPORT_SURFACES:
            continue
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing current direct implementation: {relative}")
            continue
        actual_sha = git_blob_sha(path)
        if actual_sha != expected_sha:
            failures.append(
                f"current direct hash mismatch: {relative} "
                f"expected={expected_sha} actual={actual_sha}"
            )
    if failures:
        raise RuntimeError(
            "Gate V3-1 current direct implementation verification failed:\n"
            + "\n".join(failures)
        )


def verify_current_export_compatibility() -> None:
    import shockbridge_signal_validity.v3 as v3

    exported = set(getattr(v3, "__all__", ()))
    missing = sorted(
        name
        for name in REQUIRED_V3_G1_EXPORTS
        if name not in exported or not hasattr(v3, name)
    )
    if missing:
        raise RuntimeError(
            "Current shared Version 3 export surface no longer preserves Gate V3-1 "
            f"compatibility: {missing}"
        )


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

    verify_historical_boundary()
    verify_historical_locked_files(lock)
    verify_current_direct_files(lock)
    verify_current_export_compatibility()
    verify_contract_behaviour(lock)

    print(
        "Gate V3-1 historical lock objects verified at "
        f"{HISTORICAL_BOUNDARY}."
    )
    print("Gate V3-1 current direct implementation objects verified.")
    print("Current shared Version 3 exports preserve Gate V3-1 compatibility.")
    print("Gate V3-1 canonical data and adapter lock verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
