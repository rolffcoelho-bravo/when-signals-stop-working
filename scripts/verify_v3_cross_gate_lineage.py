from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shockbridge_signal_validity.v3.cross_gate_lineage import (
    CrossGateLineageError,
    GateLockSpec,
    audit_cross_gate_lineage,
)

SPECS = (
    GateLockSpec(
        path="V3_G3_PANIC_REGIME_LOCK.json",
        authoritative_blob="0e35908c03e36d8caeb832a078ff0566ef4e2ea4",
        protection_commit_field="lock_preparation_commit",
    ),
    GateLockSpec(
        path="V3_G4A_CHRONOLOGY_SIGNAL_USE_CONTRACT_LOCK.json",
        authoritative_blob="d3c4ce27808e60b001e7d58e0c5e36be8d8cac6a",
        protection_commit_field="lock_finalization_preparation_commit",
    ),
    GateLockSpec(
        path="V3_G4B_CHRONOLOGY_PROVENANCE_LOCK.json",
        authoritative_blob="ceee8a9069b48a74db15e7e3da9e23b2bc0fdf91",
        protection_commit_field="lock_preparation_commit",
    ),
)


def main() -> int:
    result = audit_cross_gate_lineage(ROOT, SPECS)
    findings_history = result.superseded_paths.get("Findings.md")
    expected = (
        "V3_G3_PANIC_REGIME_LOCK.json",
        "V3_G4A_CHRONOLOGY_SIGNAL_USE_CONTRACT_LOCK.json",
        "V3_G4B_CHRONOLOGY_PROVENANCE_LOCK.json",
    )
    if findings_history != expected:
        raise CrossGateLineageError(
            f"Findings.md ownership history changed: {findings_history}"
        )
    print("V3 cross-gate lock-lineage verification passed.")
    print(f"Historical protected objects verified: {result.historical_objects_verified}")
    print(
        "Current latest-owner objects verified: "
        f"{result.current_latest_owner_objects_verified}"
    )
    print(f"Governed superseded paths: {len(result.superseded_paths)}")
    print("Findings.md latest owner: V3_G4B_CHRONOLOGY_PROVENANCE_LOCK.json")
    print("V3-3 historical Findings.md object preserved: True")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        CrossGateLineageError,
        KeyError,
        OSError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"V3 cross-gate lock-lineage verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
