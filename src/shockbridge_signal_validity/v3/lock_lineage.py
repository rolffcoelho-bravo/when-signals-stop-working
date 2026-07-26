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
    lock_finalization_commits: Mapping[str, str]
    authoritative_lock_blobs: Mapping[str, str]
    lock_anchor_sources: Mapping[str, str]


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


def _history_commits(root: Path, path: str) -> tuple[str, ...]:
    commits = tuple(
        value.strip()
        for value in _git(
            root,
            "log",
            "--format=%H",
            "--reverse",
            "--",
            path,
        ).splitlines()
        if value.strip()
    )
    if not commits:
        raise LockLineageError(f"Unable to locate Git history for {path}")
    return commits


def _blob_at(root: Path, commit: str, path: str) -> str | None:
    try:
        return _git(root, "rev-parse", f"{commit}:{path}")
    except subprocess.CalledProcessError:
        return None


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


def _resolve_authoritative_blob(
    root: Path,
    lock_path: str,
    creation_commit: str,
    child_path: str | None,
    child_payload: Mapping[str, object] | None,
) -> tuple[str, str]:
    if child_path is not None and child_payload is not None:
        child_reference = child_payload.get("parent_lock_blob_sha")
        if child_reference is not None:
            return (
                str(child_reference),
                f"child_parent_lock_blob_sha:{child_path}",
            )
    creation_blob = _blob_at(root, creation_commit, lock_path)
    if creation_blob is None:
        raise LockLineageError(
            f"Lock file is absent at its creation commit: {lock_path}"
        )
    return creation_blob, "creation_commit"


def _resolve_finalization_commit(
    root: Path,
    lock_path: str,
    authoritative_blob: str,
) -> str:
    history = _history_commits(root, lock_path)
    observed_history = tuple(
        (commit, _blob_at(root, commit, lock_path)) for commit in history
    )
    matching_positions = [
        index
        for index, (_, blob) in enumerate(observed_history)
        if blob == authoritative_blob
    ]
    if not matching_positions:
        raise LockLineageError(
            f"Authoritative lock blob never appears in history: {lock_path} "
            f"blob={authoritative_blob}"
        )
    finalization_position = matching_positions[0]
    finalization_commit = observed_history[finalization_position][0]
    for commit, blob in observed_history[finalization_position + 1 :]:
        if blob != authoritative_blob:
            raise LockLineageError(
                f"Lock file was modified after finalization: {lock_path} "
                f"finalized={finalization_commit} modified={commit}"
            )
    head_blob = _blob_at(root, "HEAD", lock_path)
    if head_blob != authoritative_blob:
        raise LockLineageError(
            f"Current lock blob differs from its authoritative finalized blob: "
            f"{lock_path} expected={authoritative_blob} observed={head_blob}"
        )
    return finalization_commit


def audit_lock_lineage(
    root: Path,
    lock_order: Iterable[str] = LOCK_ORDER,
) -> LockAuditResult:
    """Verify historical objects at governed lock finalization and latest owners at HEAD."""

    root = root.resolve()
    ordered_paths = tuple(lock_order)
    if not ordered_paths:
        raise LockLineageError("Lock order cannot be empty")

    payloads = {path: _load_lock(root, path) for path in ordered_paths}
    creation_commits = {
        path: _creation_commit(root, path) for path in ordered_paths
    }

    for index, lock_path in enumerate(ordered_paths):
        if index == 0:
            continue
        expected_parent = ordered_paths[index - 1]
        declared_parent = payloads[lock_path].get("parent_lock")
        if declared_parent != expected_parent:
            raise LockLineageError(
                f"Parent-lock chain mismatch for {lock_path}: "
                f"expected={expected_parent} declared={declared_parent}"
            )

    authoritative_blobs: dict[str, str] = {}
    anchor_sources: dict[str, str] = {}
    finalization_commits: dict[str, str] = {}
    for index, lock_path in enumerate(ordered_paths):
        child_path = (
            ordered_paths[index + 1] if index + 1 < len(ordered_paths) else None
        )
        child_payload = payloads[child_path] if child_path is not None else None
        authoritative_blob, anchor_source = _resolve_authoritative_blob(
            root,
            lock_path,
            creation_commits[lock_path],
            child_path,
            child_payload,
        )
        authoritative_blobs[lock_path] = authoritative_blob
        anchor_sources[lock_path] = anchor_source
        finalization_commits[lock_path] = _resolve_finalization_commit(
            root,
            lock_path,
            authoritative_blob,
        )

    for index, lock_path in enumerate(ordered_paths):
        if index == 0:
            continue
        parent_path = ordered_paths[index - 1]
        expected_parent_sha = payloads[lock_path].get("parent_lock_blob_sha")
        if expected_parent_sha is not None and str(expected_parent_sha) != authoritative_blobs[parent_path]:
            raise LockLineageError(
                f"Parent lock blob mismatch for {lock_path}: "
                f"expected={expected_parent_sha} "
                f"authoritative={authoritative_blobs[parent_path]}"
            )

    historical_count = 0
    owners: dict[str, list[tuple[str, str]]] = {}
    for lock_path in ordered_paths:
        payload = payloads[lock_path]
        finalization = finalization_commits[lock_path]
        for relative_path, expected_sha in payload["protected_files"].items():
            observed = _blob_at(root, finalization, str(relative_path))
            if observed is None:
                raise LockLineageError(
                    f"Historical protected object missing at finalization "
                    f"{finalization}: {relative_path}"
                )
            if observed != str(expected_sha):
                raise LockLineageError(
                    f"Historical lock mismatch for {lock_path}: {relative_path} "
                    f"expected={expected_sha} observed={observed} "
                    f"finalization={finalization}"
                )
            historical_count += 1
            owners.setdefault(str(relative_path), []).append(
                (lock_path, str(expected_sha))
            )

    current_count = 0
    superseded: dict[str, tuple[str, ...]] = {}
    for relative_path, history in sorted(owners.items()):
        latest_lock, expected_sha = history[-1]
        observed = _blob_at(root, "HEAD", relative_path)
        if observed != expected_sha:
            raise LockLineageError(
                f"Current object does not match latest owning lock {latest_lock}: "
                f"{relative_path} expected={expected_sha} observed={observed}"
            )
        current_count += 1
        if len(history) > 1:
            superseded[relative_path] = tuple(lock for lock, _ in history)

    return LockAuditResult(
        historical_objects_verified=historical_count,
        current_objects_verified=current_count,
        superseded_paths=superseded,
        lock_creation_commits=creation_commits,
        lock_finalization_commits=finalization_commits,
        authoritative_lock_blobs=authoritative_blobs,
        lock_anchor_sources=anchor_sources,
    )
