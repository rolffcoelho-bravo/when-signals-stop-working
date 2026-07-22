import json
from pathlib import Path

import pytest

from shockbridge_signal_validity.v2.contracts import HoldoutAccessError
from shockbridge_signal_validity.v2.locked_evaluation import (
    FrozenEvaluationPipeline,
    validate_d3_authorization,
)
from shockbridge_signal_validity.v2.registry import load_v2_registry


def pipeline() -> FrozenEvaluationPipeline:
    return FrozenEvaluationPipeline(
        pipeline_hash="2f85b54f8f178ec59c2bfb8a06cd8dedb3e053e2bec4da40cb446d380def2851",
        signal_family="bollinger",
        horizon_candles=1,
        horizon_hours=4,
        signal_specification={},
        structural_pipeline={},
        calibration_method="none",
        decision_probability_distance_threshold=0.05,
    )


def authorization() -> dict:
    registry = load_v2_registry()
    return {
        "status": "APPROVED_FOR_SINGLE_ACCESS",
        "authorized": True,
        "single_access": True,
        "protocol_lock_id": "protocol",
        "d2c_lock_id": "d2c",
        "d3_lock_id": "d3",
        "implementation_commit": "abc",
        "pipeline_hash": pipeline().pipeline_hash,
        "signal_family": "bollinger",
        "holdout_start_utc": registry.holdout_start.isoformat(),
        "holdout_end_utc": registry.holdout_end.isoformat(),
        "forbidden_signal_families": ["rsi"],
        "approval_record_created_before_results": True,
    }


def test_d3_authorization_accepts_exact_frozen_contract() -> None:
    registry = load_v2_registry()
    validate_d3_authorization(
        authorization(), "protocol", "d2c", "d3", "abc", pipeline(), registry
    )


def test_d3_authorization_rejects_rsi_reentry_omission() -> None:
    registry = load_v2_registry()
    payload = authorization()
    payload["forbidden_signal_families"] = []
    with pytest.raises(HoldoutAccessError, match="RSI"):
        validate_d3_authorization(
            payload, "protocol", "d2c", "d3", "abc", pipeline(), registry
        )
