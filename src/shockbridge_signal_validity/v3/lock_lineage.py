from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Iterable, Mapping

LOCK_ORDER = (
    "V3_G1_DATA_ADAPTER_LOCK.json",
    "V3_G2_SPECTRAL_ENGINE_LOCK.json",
    "V3_G2B_MARKET_STRUCTURE_LOCK.json",
    "V3_G3A_PANIC_REGIME_IDENTIFICATION_LOCK.json",
    "V3_G3B_PROBABILISTIC_ENGINE_LOCK.json",
    "V3_G3C_GOVERNANCE_LOCK.json",
)


class LockLineageError(RuntimeError):
    """Raised when a historical or current Version 3 lock object is invalid."""


@dataclass(frozen=True)
class LockAuditResult:
    historical_objects_verified: int
    current_objects_verified: int
    superseded_paths: Mapping[str, tuple[str, ...]]
    lock_creation_commits: Mapping[str, str]


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _load_lock(root: Path, path: str) -> dict:
    value = json.loads((root / path).read_text(encoding="utf-8"))
    protected = value.get("protected_files")
    if not isinstance(protected, dict) or not protected:
        raise LockLineageError(f"{path} has no protected_files mapping")
    return value


def _creation_commit(root: Path, path: str) -> str:
    commits = _git(
        root,
        "log",
        "--diff-filter=A",
        "--format=%H",
        "--reverse",
        "--",
        path,
    ).splitlines()
    if not commits:
        raise LockLineageError(f"Unable to locate creation commit for {path}")
    return commits[0].strip()


def audit_lock_lineage(
    root: Path,
    lock_order: Iterable[str] = LOCK_ORDER,
) -> LockAuditResult:
    """Verify historical objects at lock creation and latest owners at HEAD."""

    root = root.resolve()
    locks: list[tuple[str, dict, str]] = []
    historical_count = 0
    owners: dict[str, list[tuple[str, str]]] = {}
    creation_commits: dict[str, str] = {}

    for lock_path in lock_order:
        payload = _load_lock(root, lock_path)
        creation = _creation_commit(root, lock_path)
        creation_commits[lock_path] = creation

        lock_blob_at_creation = _git(root, "rev-parse", f"{creation}:{lock_path}")
        lock_blob_now = _git(root, "rev-parse", f"HEAD:{lock_path}")
        if lock_blob_at_creation != lock_blob_now:
            raise LockLineageError(f"Lock file was modified after creation: {lock_path}")

        for relative_path, expected_sha in payload["protected_files"].items():
            try:
                observed = _git(root, "rev-parse", f"{creation}:{relative_path}")
            except subprocess.CalledProcessError as exc:
                raise LockLineageError(
                    f"Historical protected object missing at {creation}: {relative_path}"
                ) from exc
            if observed != str(expected_sha):
                raise LockLineageError(
                    f"Historical lock mismatch for {lock_path}: {relative_path} "
                    f"expected={expected_sha} observed={observed}"
                )
            historical_count += 1
            owners.setdefault(str(relative_path), []).append(
                (lock_path, str(expected_sha))
            )
        locks.append((lock_path, payload, creation))

    current_count = 0
    superseded: dict[str, tuple[str, ...]] = {}
    for relative_path, history in sorted(owners.items()):
        latest_lock, expected_sha = history[-1]
        observed = _git(root, "rev-parse", f"HEAD:{relative_path}")
        if observed != expected_sha:
            raise LockLineageError(
                f"Current object does not match latest owning lock {latest_lock}: "
                f"{relative_path} expected={expected_sha} observed={observed}"
            )
        current_count += 1
        if len(history) > 1:
            superseded[relative_path] = tuple(lock for lock, _ in history)

    for index, (lock_path, payload, _) in enumerate(locks):
        if index == 0:
            continue
        expected_parent = locks[index - 1][0]
        declared_parent = payload.get("parent_lock")
        if declared_parent != expected_parent:
            raise LockLineageError(
                f"Parent-lock chain mismatch for {lock_path}: "
                f"expected={expected_parent} declared={declared_parent}"
            )
        expected_parent_sha = payload.get("parent_lock_blob_sha")
        if expected_parent_sha is not None:
            observed_parent_sha = _git(root, "rev-parse", f"HEAD:{expected_parent}")
            if observed_parent_sha != str(expected_parent_sha):
                raise LockLineageError(
                    f"Parent lock blob mismatch for {lock_path}: "
                    f"expected={expected_parent_sha} observed={observed_parent_sha}"
                )

    return LockAuditResult(
        historical_objects_verified=historical_count,
        current_objects_verified=current_count,
        superseded_paths=superseded,
        lock_creation_commits=creation_commits,
    )
