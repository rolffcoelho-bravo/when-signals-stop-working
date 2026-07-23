from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ProtocolViolation(RuntimeError):
    """Raised when Version 2 execution conflicts with the frozen protocol."""


class HoldoutAccessError(ProtocolViolation):
    """Raised when locked-evaluation access is attempted without approval."""


@dataclass(frozen=True)
class FileHash:
    path: str
    sha256: str
    bytes: int


@dataclass(frozen=True)
class HoldoutApproval:
    protocol_lock_id: str
    implementation_commit: str
    approved_at_utc: str
    approving_owner: str
    selected_rsi_pipeline: str
    selected_bollinger_pipeline: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "HoldoutApproval":
        required = {
            "protocol_lock_id",
            "implementation_commit",
            "approved_at_utc",
            "approving_owner",
            "selected_rsi_pipeline",
            "selected_bollinger_pipeline",
        }
        missing = sorted(required.difference(value))
        if missing:
            raise HoldoutAccessError(
                "Holdout approval record is incomplete: " + ", ".join(missing)
            )
        return cls(**{key: str(value[key]) for key in required})


def repository_relative(path: Path, root: Path) -> str:
    """Return a normalized repository-relative path or reject the path."""
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ProtocolViolation(
            f"Path is outside the repository boundary: {resolved_path}"
        ) from exc
    return relative.as_posix()
