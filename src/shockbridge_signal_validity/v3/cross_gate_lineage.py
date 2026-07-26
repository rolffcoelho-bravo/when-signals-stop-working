from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Mapping, Sequence


class CrossGateLineageError(RuntimeError):
    """Raised when historical integrity or current latest ownership fails."""


@dataclass(frozen=True)
class GateLockSpec:
    path: str
    authoritative_blob: str
    protection_commit_field: str


@dataclass(frozen=True)
class CrossGateAuditResult:
    historical_objects_verified: int
    current_latest_owner_objects_verified: int
    superseded_paths: Mapping[str, tuple[str, ...]]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def audit_cross_gate_lineage(
    root: Path,
    specs: Sequence[GateLockSpec],
) -> CrossGateAuditResult:
    if not specs:
        raise CrossGateLineageError("At least one gate lock is required")
    root = root.resolve()
    payloads: list[dict] = []
    historical_count = 0
    owners: dict[str, list[tuple[str, str]]] = {}

    for index, spec in enumerate(specs):
        lock_path = root / spec.path
        if not lock_path.exists():
            raise CrossGateLineageError(f"Missing gate lock: {spec.path}")
        observed_lock_blob = _git(root, "rev-parse", f"HEAD:{spec.path}")
        if observed_lock_blob != spec.authoritative_blob:
            raise CrossGateLineageError(
                f"Authoritative lock blob changed: {spec.path} "
                f"expected={spec.authoritative_blob} observed={observed_lock_blob}"
            )
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        protected = payload.get("protected_files")
        if not isinstance(protected, dict) or not protected:
            raise CrossGateLineageError(f"Protected inventory missing: {spec.path}")
        protection_commit = payload.get(spec.protection_commit_field)
        if not isinstance(protection_commit, str) or not protection_commit:
            raise CrossGateLineageError(
                f"Protection commit field missing: {spec.path}/{spec.protection_commit_field}"
            )
        if index > 0:
            parent_spec = specs[index - 1]
            if payload.get("parent_lock") != parent_spec.path:
                raise CrossGateLineageError(f"Parent lock path changed: {spec.path}")
            if payload.get("parent_lock_blob_sha") != parent_spec.authoritative_blob:
                raise CrossGateLineageError(f"Parent lock blob changed: {spec.path}")
        for relative_path, expected_blob in protected.items():
            try:
                observed = _git(root, "rev-parse", f"{protection_commit}:{relative_path}")
            except subprocess.CalledProcessError as exc:
                raise CrossGateLineageError(
                    f"Historical protected object missing: {spec.path}/{relative_path}"
                ) from exc
            if observed != expected_blob:
                raise CrossGateLineageError(
                    f"Historical protected object changed: {spec.path}/{relative_path} "
                    f"expected={expected_blob} observed={observed}"
                )
            historical_count += 1
            owners.setdefault(str(relative_path), []).append((spec.path, str(expected_blob)))
        payloads.append(payload)

    current_count = 0
    superseded: dict[str, tuple[str, ...]] = {}
    for relative_path, history in sorted(owners.items()):
        latest_lock, expected_blob = history[-1]
        try:
            observed = _git(root, "rev-parse", f"HEAD:{relative_path}")
        except subprocess.CalledProcessError as exc:
            raise CrossGateLineageError(
                f"Current latest-owner object missing: {relative_path}"
            ) from exc
        if observed != expected_blob:
            raise CrossGateLineageError(
                f"Current object does not match latest owner {latest_lock}: "
                f"{relative_path} expected={expected_blob} observed={observed}"
            )
        current_count += 1
        if len(history) > 1:
            superseded[relative_path] = tuple(lock for lock, _ in history)

    return CrossGateAuditResult(
        historical_objects_verified=historical_count,
        current_latest_owner_objects_verified=current_count,
        superseded_paths=superseded,
    )
