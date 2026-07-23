from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "V2_D1_ENGINE_LOCK.json"


def main() -> int:
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    for relative, expected_hash in payload["protected_files"].items():
        path = ROOT / relative
        if not path.exists():
            raise RuntimeError(f"D1 protected file is missing: {relative}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected_hash:
            raise RuntimeError(f"D1 protected file hash mismatch: {relative}")
    print(f"V2 D1 engine lock verified: {payload['lock_id']}")
    print(f"Protected files: {len(payload['protected_files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
