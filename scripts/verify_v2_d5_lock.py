from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    lock_path = ROOT / "V2_D5_ROBUSTNESS_LOCK.json"
    if not lock_path.exists():
        raise RuntimeError("V2 D5 robustness lock is missing.")

    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    if payload.get("checkpoint") != "V2_D5_ROBUSTNESS_AND_PUBLICATION":
        raise RuntimeError("Unexpected D5 checkpoint.")
    if payload.get("expected_parent_commit") != "69f1c40":
        raise RuntimeError("Unexpected D5 parent commit.")
    if payload.get("expected_d4_evidence_grade") != "NO_INCREMENTAL_EVIDENCE":
        raise RuntimeError("Unexpected D5 source evidence grade.")
    if payload.get("pipeline_retuning_permitted") is not False:
        raise RuntimeError("D5 lock permits pipeline retuning.")
    if payload.get("rsi_reentry_permitted") is not False:
        raise RuntimeError("D5 lock permits RSI re-entry.")
    if payload.get("panic_state_extension_used") is not False:
        raise RuntimeError("D5 lock includes the panic-state extension.")

    protected = payload.get("protected_files", {})
    if not protected:
        raise RuntimeError("D5 lock has no protected files.")

    for relative_path, expected_hash in protected.items():
        path = ROOT / relative_path
        if not path.exists():
            raise RuntimeError(f"Protected D5 file is missing: {relative_path}")
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"Protected D5 file changed: {relative_path}"
            )

    print(f"V2 D5 robustness lock verified: {payload['lock_id']}")
    print(f"Protected files: {len(protected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
