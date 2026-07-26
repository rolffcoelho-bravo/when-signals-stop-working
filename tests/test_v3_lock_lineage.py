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
    assert result.lock_anchor_sources["L1.json"] == (
        "child_parent_lock_blob_sha:L2.json"
    )


def test_lineage_accepts_draft_lock_finalized_before_child_freeze(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    _write(root, "a.py", "final\n")
    draft = {"protected_files": {"a.py": "draft-placeholder"}}
    _write(root, "L1.json", json.dumps(draft, sort_keys=True))
    creation = _commit(root, "create draft lock")

    finalized = {"protected_files": {"a.py": _blob(root, "a.py")}}
    _write(root, "L1.json", json.dumps(finalized, sort_keys=True))
    finalization = _commit(root, "finalize lock")

    _write(root, "b.py", "b\n")
    child = {
        "parent_lock": "L1.json",
        "parent_lock_blob_sha": _git(root, "rev-parse", "HEAD:L1.json"),
        "protected_files": {"b.py": _blob(root, "b.py")},
    }
    _write(root, "L2.json", json.dumps(child, sort_keys=True))
    _commit(root, "freeze finalized parent")

    result = audit_lock_lineage(root, ("L1.json", "L2.json"))
    assert result.lock_creation_commits["L1.json"] == creation
    assert result.lock_finalization_commits["L1.json"] == finalization
    assert result.authoritative_lock_blobs["L1.json"] == child[
        "parent_lock_blob_sha"
    ]


def test_lineage_rejects_lock_modified_after_child_freeze(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _write(root, "a.py", "a\n")
    parent = {"protected_files": {"a.py": _blob(root, "a.py")}}
    _write(root, "L1.json", json.dumps(parent, sort_keys=True))
    _commit(root, "parent lock")

    _write(root, "b.py", "b\n")
    child = {
        "parent_lock": "L1.json",
        "parent_lock_blob_sha": _git(root, "rev-parse", "HEAD:L1.json"),
        "protected_files": {"b.py": _blob(root, "b.py")},
    }
    _write(root, "L2.json", json.dumps(child, sort_keys=True))
    _commit(root, "child freezes parent")

    parent["tampered_after_child"] = True
    _write(root, "L1.json", json.dumps(parent, sort_keys=True))
    _commit(root, "modify frozen parent")

    with pytest.raises(LockLineageError, match="modified after finalization"):
        audit_lock_lineage(root, ("L1.json", "L2.json"))


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


def test_lineage_rejects_modified_latest_lock_file(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _write(root, "x.py", "locked\n")
    lock = {"protected_files": {"x.py": _blob(root, "x.py")}}
    _write(root, "L1.json", json.dumps(lock, sort_keys=True))
    _commit(root, "lock")
    lock["tampered"] = True
    _write(root, "L1.json", json.dumps(lock, sort_keys=True))
    _commit(root, "tamper")

    with pytest.raises(LockLineageError, match="modified after finalization"):
        audit_lock_lineage(root, ("L1.json",))


def test_final_acceptance_wrappers_preserve_active_python_environment() -> None:
    powershell_path = REPOSITORY_ROOT / "RUN_V3_G3_FINAL_ACCEPTANCE.ps1"
    powershell_raw = powershell_path.read_bytes()
    powershell = powershell_raw.decode("ascii")
    assert "python scripts/run_v3_g3_final_acceptance.py --report $Report" in powershell
    assert "GATE V3-3D - FINAL ACCEPTANCE AND LOCK AUTHORIZATION" in powershell
    assert 'SetEnvironmentVariable("PYTHONNOUSERSITE", $null, "Process")' in powershell
    assert '$env:PYTHONNOUSERSITE = "1"' not in powershell
    assert powershell.count('"') % 2 == 0

    shell = (REPOSITORY_ROOT / "RUN_V3_G3_FINAL_ACCEPTANCE.sh").read_text(
        encoding="ascii"
    )
    assert "unset PYTHONNOUSERSITE" in shell
    assert "export PYTHONNOUSERSITE=1" not in shell
    assert 'python scripts/run_v3_g3_final_acceptance.py --report "$REPORT"' in shell


def test_repository_lock_lineage_passes_current_chain() -> None:
    result = audit_lock_lineage(REPOSITORY_ROOT)
    assert result.historical_objects_verified > 0
    assert result.current_objects_verified > 0
    assert result.lock_anchor_sources["V3_G2_SPECTRAL_ENGINE_LOCK.json"] == (
        "child_parent_lock_blob_sha:V3_G2B_MARKET_STRUCTURE_LOCK.json"
    )
    assert result.lock_finalization_commits["V3_G2_SPECTRAL_ENGINE_LOCK.json"]
