from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from shockbridge_signal_validity.v3.cross_gate_lineage import (
    CrossGateLineageError,
    GateLockSpec,
    audit_cross_gate_lineage,
)


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def write(root: Path, path: str, value: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def commit(root: Path, message: str) -> str:
    git(root, "add", ".")
    git(root, "commit", "-m", message)
    return git(root, "rev-parse", "HEAD")


def blob(root: Path, path: str) -> str:
    return git(root, "hash-object", path)


def make_repo(tmp_path: Path) -> tuple[Path, tuple[GateLockSpec, ...]]:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init")
    git(root, "config", "user.email", "audit@example.com")
    git(root, "config", "user.name", "Audit")

    write(root, "Findings.md", "g3\n")
    write(root, "g3.py", "g3\n")
    preparation1 = commit(root, "prepare g3")
    lock1 = {
        "lock_preparation_commit": preparation1,
        "protected_files": {
            "Findings.md": git(root, "rev-parse", f"{preparation1}:Findings.md"),
            "g3.py": git(root, "rev-parse", f"{preparation1}:g3.py"),
        },
    }
    write(root, "L1.json", json.dumps(lock1, sort_keys=True))
    commit(root, "lock g3")
    lock1_blob = git(root, "rev-parse", "HEAD:L1.json")

    write(root, "Findings.md", "g4a\n")
    write(root, "g4a.py", "g4a\n")
    preparation2 = commit(root, "prepare g4a")
    lock2 = {
        "parent_lock": "L1.json",
        "parent_lock_blob_sha": lock1_blob,
        "lock_finalization_preparation_commit": preparation2,
        "protected_files": {
            "Findings.md": git(root, "rev-parse", f"{preparation2}:Findings.md"),
            "g4a.py": git(root, "rev-parse", f"{preparation2}:g4a.py"),
        },
    }
    write(root, "L2.json", json.dumps(lock2, sort_keys=True))
    commit(root, "lock g4a")
    lock2_blob = git(root, "rev-parse", "HEAD:L2.json")

    write(root, "Findings.md", "g4b\n")
    write(root, "g4b.py", "g4b\n")
    preparation3 = commit(root, "prepare g4b")
    lock3 = {
        "parent_lock": "L2.json",
        "parent_lock_blob_sha": lock2_blob,
        "lock_preparation_commit": preparation3,
        "protected_files": {
            "Findings.md": git(root, "rev-parse", f"{preparation3}:Findings.md"),
            "g4b.py": git(root, "rev-parse", f"{preparation3}:g4b.py"),
        },
    }
    write(root, "L3.json", json.dumps(lock3, sort_keys=True))
    commit(root, "lock g4b")
    lock3_blob = git(root, "rev-parse", "HEAD:L3.json")
    specs = (
        GateLockSpec("L1.json", lock1_blob, "lock_preparation_commit"),
        GateLockSpec("L2.json", lock2_blob, "lock_finalization_preparation_commit"),
        GateLockSpec("L3.json", lock3_blob, "lock_preparation_commit"),
    )
    return root, specs


def test_cross_gate_audit_accepts_governed_findings_supersession(tmp_path: Path) -> None:
    root, specs = make_repo(tmp_path)
    result = audit_cross_gate_lineage(root, specs)
    assert result.historical_objects_verified == 6
    assert result.current_latest_owner_objects_verified == 4
    assert result.superseded_paths["Findings.md"] == ("L1.json", "L2.json", "L3.json")


def test_cross_gate_audit_rejects_current_latest_owner_change(tmp_path: Path) -> None:
    root, specs = make_repo(tmp_path)
    write(root, "Findings.md", "ungoverned\n")
    commit(root, "ungoverned findings change")
    with pytest.raises(CrossGateLineageError, match="latest owner"):
        audit_cross_gate_lineage(root, specs)


def test_cross_gate_audit_rejects_parent_blob_mismatch(tmp_path: Path) -> None:
    root, specs = make_repo(tmp_path)
    payload = json.loads((root / "L3.json").read_text(encoding="utf-8"))
    payload["parent_lock_blob_sha"] = "bad"
    write(root, "L3.json", json.dumps(payload, sort_keys=True))
    commit(root, "tamper parent reference")
    modified = (
        specs[0],
        specs[1],
        GateLockSpec("L3.json", git(root, "rev-parse", "HEAD:L3.json"), "lock_preparation_commit"),
    )
    with pytest.raises(CrossGateLineageError, match="Parent lock blob"):
        audit_cross_gate_lineage(root, modified)
