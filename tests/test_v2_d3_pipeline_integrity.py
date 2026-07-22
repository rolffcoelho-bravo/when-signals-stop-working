import copy
import json
from pathlib import Path

import pytest

from shockbridge_signal_validity.v2.contracts import ProtocolViolation
from shockbridge_signal_validity.v2.locked_evaluation import (
    EXPECTED_D3_PIPELINE_HASH,
    canonical_pipeline_hash,
    load_single_frozen_pipeline,
)


def frozen_pipeline_payload() -> dict:
    pipeline = {
        "calibration_method": "none",
        "decision_probability_distance_threshold": 0.05,
        "development_selection_evidence": {
            "calibration_mean_inner_incremental_log_loss": 0.00347862861348572,
            "family_horizon_mean_incremental_log_loss": 0.0014348484900428798,
            "family_horizon_positive_outer_folds": 5,
            "policy_mean_inner_coverage": 0.25722878317776077,
            "policy_mean_inner_net_edge_diagnostic": -0.0001690990416267267,
            "policy_total_inner_decisions": 4449,
            "signal_mean_inner_incremental_log_loss": -0.0006322326894520732,
            "structural_mean_inner_incremental_log_loss": 0.0022872681877837402,
        },
        "economic_gate_evaluated": False,
        "holdout_performance_accessed": False,
        "horizon_candles": 1,
        "horizon_hours": 4,
        "signal_family": "bollinger",
        "signal_specification": {
            "interpretation": "continuation",
            "lower_threshold": None,
            "period": 10,
            "signal_family": "bollinger",
            "signal_spec_id": "bollinger-p10-k2.5-continuation",
            "standard_deviations": 2.5,
            "upper_threshold": None,
        },
        "structural_pipeline": {
            "model_family": "shallow_hist_gradient_boosting",
            "parameters": {
                "l2_regularization": 0.0,
                "learning_rate": 0.05,
                "max_iter": 100,
                "max_leaf_nodes": 15,
                "min_samples_leaf": 100,
            },
            "pipeline_id": "shallow_hist_gradient_boosting-l2_regularization0p0-learning_rate0p05-max_iter100-max_leaf_nodes15-min_samples_leaf100-expanding-softstate",
            "regime_conditioned": True,
            "window_scheme": "expanding",
        },
        "target": "future_return_direction",
    }
    pipeline["pipeline_hash"] = canonical_pipeline_hash(pipeline)
    return pipeline


def test_canonical_pipeline_hash_matches_d2c() -> None:
    pipeline = frozen_pipeline_payload()
    assert pipeline["pipeline_hash"] == EXPECTED_D3_PIPELINE_HASH


def test_single_frozen_pipeline_loader_rejects_rsi_or_multiple(tmp_path: Path) -> None:
    pipeline = frozen_pipeline_payload()
    registry = {
        "family_level_pipeline_freeze_completed": True,
        "holdout_authorization_enabled": False,
        "frozen_pipelines": [pipeline],
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    loaded = load_single_frozen_pipeline(path)
    assert loaded.signal_family == "bollinger"

    duplicated = copy.deepcopy(registry)
    duplicated["frozen_pipelines"].append(copy.deepcopy(pipeline))
    path.write_text(json.dumps(duplicated), encoding="utf-8")
    with pytest.raises(ProtocolViolation, match="exactly one"):
        load_single_frozen_pipeline(path)
