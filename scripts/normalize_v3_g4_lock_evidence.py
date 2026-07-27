from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "V3_G4_SIGNAL_ENGINE_LOCK.json"
EVIDENCE_DIRECTORY = ROOT / "evidence" / "v3" / "g4_signal_lock"


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def write_portable_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    if not LOCK_PATH.is_file():
        raise FileNotFoundError(LOCK_PATH)
    if not EVIDENCE_DIRECTORY.is_dir():
        raise FileNotFoundError(EVIDENCE_DIRECTORY)

    hashes: dict[str, str] = {}
    for path in sorted(EVIDENCE_DIRECTORY.glob("*.json")):
        payload = read_object(path)
        write_portable_json(path, payload)
        hashes[str(path.relative_to(ROOT)).replace("\\", "/")] = sha256_file(path)
    if not hashes:
        raise RuntimeError("No curated Gate V3-4 JSON evidence was found.")

    lock = read_object(LOCK_PATH)
    lock["curated_evidence_sha256"] = hashes
    write_portable_json(LOCK_PATH, lock)

    print("Gate V3-4 curated evidence normalized to portable LF JSON.")
    print(f"curated_files: {len(hashes)}")
    print("lock curated hashes refreshed: True")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"Gate V3-4 lock-evidence normalization failed: {error}", file=sys.stderr)
        raise SystemExit(1)
