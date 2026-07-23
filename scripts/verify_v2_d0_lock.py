from __future__ import annotations

import hashlib
import json
from pathlib import Path


LOCK_PATH = Path("V2_D0_IMPLEMENTATION_LOCK.json")


def main() -> int:
    payload = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    problems: list[str] = []
    for relative, expected_hash in payload["protected_files"].items():
        path = Path(relative)
        if not path.exists():
            problems.append(f"missing:{relative}")
            continue
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            problems.append(f"hash_mismatch:{relative}")
    if problems:
        print(json.dumps({"status": "FAIL", "problems": problems}, indent=2))
        return 1
    print(f"V2 D0 implementation lock verified: {payload['lock_id']}")
    print(f"Protected files: {len(payload['protected_files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
