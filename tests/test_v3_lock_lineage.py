from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from shockbridge_signal_validity.v3.lock_lineage import (
    LockLineageError,
    audit_lock_lineage,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write(root: Path, path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _commit(root: Path, message: str) -> str:
    _git(root, "add", ".")
    _git(root, "commit", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _blob(root: Path, path: str) -> str:
    return _git(root, "hash-object", path)


def _init_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "audit@example.com")
    _git(root, "config", "user.name", "Audit")
    return root


def test_lineage_accepts_intentional_latest_owner_supersession(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    _write(root, "shared.py", "v1\n")
    _write(root, "a.py", "a\n")
    lock1 = {
        "protected_files": {
            "shared.py": _blob(root, "shared.py"),
            "a.py": _blob(root, "a.py"),
        }
    }
    _write(root, "L1.json", json.dumps(lock1, sort_keys=True))
    _commit(root, "gate one")

    _write(root, "shared.py", "v2\n")
    _write(root, "b.py", "b\n")
    lock2 = {
        "parent_lock": "L1.json",
        "parent_lock_blob_sha": _git(root, "rev-parse", "HEAD:L1.json"),
        "protected_files": {
            "shared.py": _blob(root, "shared.py"),
            "b.py": _blob(root, "b.py"),
        },
    }
    _write(root, "L2.json", json.dumps(lock2, sort_keys=True))
    _commit(root, "gate two")

    result = audit_lock_lineage(root, ("L1.json", "L2.json"))
    assert result.historical_objects_verified == 4
    assert result.current_objects_verified == 3
    assert result.superseded_paths["shared.py"] == ("L1.json", "L2.json")


def test_lineage_rejects_current_latest_owner_mismatch(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _write(root, "x.py", "locked\n")
    lock = {"protected_files": {"x.py": _blob(root, "x.py")}}
    _write(root, "L1.json", json.dumps(lock, sort_keys=True))
    _commit(root, "lock")
    _write(root, "x.py", "changed\n")
    _commit(root, "violate")

    with pytest.raises(LockLineageError, match="latest owning lock"):
        audit_lock_lineage(root, ("L1.json",))


def test_lineage_rejects_modified_lock_file(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _write(root, "x.py", "locked\n")
    lock = {"protected_files": {"x.py": _blob(root, "x.py")}}
    _write(root, "L1.json", json.dumps(lock, sort_keys=True))
    _commit(root, "lock")
    lock["tampered"] = True
    _write(root, "L1.json", json.dumps(lock, sort_keys=True))
    _commit(root, "tamper")

    with pytest.raises(LockLineageError, match="modified after creation"):
        audit_lock_lineage(root, ("L1.json",))


def test_final_acceptance_powershell_wrapper_is_ascii_safe() -> None:
    path = REPOSITORY_ROOT / "RUN_V3_G3_FINAL_ACCEPTANCE.ps1"
    raw = path.read_bytes()
    text = raw.decode("ascii")
    assert "python scripts/run_v3_g3_final_acceptance.py --report $Report" in text
    assert "GATE V3-3D - FINAL ACCEPTANCE AND LOCK AUTHORIZATION" in text
    assert text.count('"') % 2 == 0
