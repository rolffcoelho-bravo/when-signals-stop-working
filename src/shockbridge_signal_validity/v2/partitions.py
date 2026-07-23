from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Mapping

import pandas as pd

from .contracts import HoldoutAccessError, ProtocolViolation
from .registry import V2Registry


@dataclass(frozen=True)
class DevelopmentPartition:
    frame: pd.DataFrame
    start: pd.Timestamp
    end: pd.Timestamp
    holdout_start: pd.Timestamp
    source_rows: int

    @property
    def rows(self) -> int:
        return int(len(self.frame))


def _require_utc_index(frame: pd.DataFrame) -> pd.DatetimeIndex:
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise ProtocolViolation("Version 2 data require a DatetimeIndex.")
    index = pd.DatetimeIndex(frame.index)
    if index.tz is None:
        raise ProtocolViolation("Version 2 timestamps must be timezone-aware UTC.")
    index = index.tz_convert("UTC")
    if not index.is_monotonic_increasing:
        raise ProtocolViolation("Version 2 timestamps must be chronological.")
    if index.has_duplicates:
        raise ProtocolViolation("Version 2 timestamps must be unique.")
    return index


def build_development_partition(
    frame: pd.DataFrame,
    registry: V2Registry,
) -> DevelopmentPartition:
    index = _require_utc_index(frame)
    data = frame.copy()
    data.index = index
    mask = (index >= registry.development_start) & (
        index <= registry.development_end
    )
    development = data.loc[mask].copy()
    if development.empty:
        raise ProtocolViolation("The declared Version 2 development partition is empty.")
    if development.index.max() >= registry.holdout_start:
        raise ProtocolViolation("Locked-evaluation rows entered development data.")
    return DevelopmentPartition(
        frame=development,
        start=development.index.min(),
        end=development.index.max(),
        holdout_start=registry.holdout_start,
        source_rows=int(len(frame)),
    )


def assert_development_only(
    frame: pd.DataFrame,
    registry: V2Registry,
) -> None:
    index = _require_utc_index(frame)
    if len(index) and index.max() >= registry.holdout_start:
        raise HoldoutAccessError(
            "Development-only execution received locked-evaluation rows."
        )


def authorize_holdout_access(
    approval_path: Path,
    protocol_lock_id: str,
    implementation_commit: str,
) -> Mapping[str, str]:
    """Validate an explicit pre-holdout approval record.

    This function is intentionally unused by the development scaffold. It
    defines the minimum interface required by the later single-access runner.
    """
    if os.environ.get("SHOCKBRIDGE_V2_HOLDOUT_AUTHORIZED") != "YES":
        raise HoldoutAccessError(
            "Holdout access requires SHOCKBRIDGE_V2_HOLDOUT_AUTHORIZED=YES."
        )
    if not approval_path.exists():
        raise HoldoutAccessError("Pre-holdout approval record was not found.")
    payload = json.loads(approval_path.read_text(encoding="utf-8"))
    if payload.get("protocol_lock_id") != protocol_lock_id:
        raise HoldoutAccessError("Approval record has the wrong protocol lock.")
    if payload.get("implementation_commit") != implementation_commit:
        raise HoldoutAccessError("Approval record has the wrong implementation commit.")
    if payload.get("status") != "APPROVED_FOR_SINGLE_ACCESS":
        raise HoldoutAccessError("Approval record does not authorize single access.")
    return {str(key): str(value) for key, value in payload.items()}
