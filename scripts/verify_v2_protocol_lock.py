from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "V2_PROTOCOL_LOCK.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if not LOCK_PATH.exists():
        raise SystemExit("V2 protocol lock is missing.")

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    problems: list[str] = []

    for relative, expected in lock["files"].items():
        path = ROOT / relative
        if not path.exists():
            problems.append(f"missing: {relative}")
            continue
        actual = sha256(path)
        if actual != expected:
            problems.append(f"hash mismatch: {relative}")

    registry = json.loads(
        (ROOT / "configs" / "v2_experiment_registry.json").read_text(encoding="utf-8")
    )
    if registry.get("freeze_status") != "FROZEN_BEFORE_IMPLEMENTATION":
        problems.append("registry freeze status is not frozen")
    if registry.get("parent_release", {}).get("tag") != "v1.2.0":
        problems.append("unexpected parent release")

    if problems:
        print("V2 protocol-lock verification failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print(f"V2 protocol lock verified: {lock['lock_id']}")
    print(f"Protected files: {len(lock['files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
