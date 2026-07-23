from __future__ import annotations

import json
from pathlib import Path

import pytest

from shockbridge_signal_validity.v2.contracts import HoldoutAccessError
from shockbridge_signal_validity.v2.partitions import authorize_holdout_access


def test_holdout_guard_rejects_missing_environment_authorization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    approval = tmp_path / "approval.json"
    approval.write_text(
        json.dumps(
            {
                "protocol_lock_id": "lock",
                "implementation_commit": "commit",
                "status": "APPROVED_FOR_SINGLE_ACCESS",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("SHOCKBRIDGE_V2_HOLDOUT_AUTHORIZED", raising=False)
    with pytest.raises(HoldoutAccessError):
        authorize_holdout_access(approval, "lock", "commit")


def test_holdout_guard_rejects_wrong_approval_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    approval = tmp_path / "approval.json"
    approval.write_text(
        json.dumps(
            {
                "protocol_lock_id": "wrong",
                "implementation_commit": "commit",
                "status": "APPROVED_FOR_SINGLE_ACCESS",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SHOCKBRIDGE_V2_HOLDOUT_AUTHORIZED", "YES")
    with pytest.raises(HoldoutAccessError):
        authorize_holdout_access(approval, "lock", "commit")
