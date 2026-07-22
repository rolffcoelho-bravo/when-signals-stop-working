from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "V2_D2B_SELECTION_LOCK.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    for relative_path, expected in payload["protected_files"].items():
        path = ROOT / relative_path
        if not path.exists():
            raise RuntimeError(f"Missing D2B protected file: {relative_path}")
        if sha256(path) != expected:
            raise RuntimeError(f"D2B protected file hash mismatch: {relative_path}")
    print(f"V2 D2B selection lock verified: {payload['lock_id']}")
    print(f"Protected files: {len(payload['protected_files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
