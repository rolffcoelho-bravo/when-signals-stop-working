from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .contracts import ProtocolViolation, repository_relative


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dataframe_sha256(frame: pd.DataFrame) -> str:
    csv_bytes = frame.to_csv(index=True, lineterminator="\n").encode("utf-8")
    return hashlib.sha256(csv_bytes).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True)
    if "\\Users\\" in serialized or ":\\" in serialized or "/home/" in serialized:
        raise ProtocolViolation("Manifest contains an absolute local path.")
    path.write_text(serialized + "\n", encoding="utf-8")


def file_record(path: Path, root: Path) -> dict[str, object]:
    return {
        "path": repository_relative(path, root),
        "sha256": sha256_file(path),
        "bytes": int(path.stat().st_size),
    }
