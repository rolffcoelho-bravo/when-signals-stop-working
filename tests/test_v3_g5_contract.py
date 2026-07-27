from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"
PARENT_LOCK = ROOT / "V3_G4_SIGNAL_ENGINE_LOCK.json"


def payload() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_parent_v3_g4_is_final_and_immutable_boundary_is_recorded() -> None:
    parent = json.loads(PARENT_LOCK.read_text(encoding="utf-8"))
    assert parent["status"] == "IMPLEMENTATION_VALIDATED_AND_LOCKED"
    assert parent["validated_implementation_commit"] == (
        "ff2e7ecba3fa69f22e0b109437d23b52d30fba2b"
    )
    assert parent["evidence_materialization_commit"] == (
        "705511de9e8ee22a9f8aff34506aebb6c26223e7"
    )
    assert parent["acceptance_evidence"]["registered_signal_count"] == 48
    assert parent["acceptance_evidence"]["observed_feature_rows"] == 584208


def test_v3_g5_partition_preserves_establishment_and_final_reserve() -> None:
    partition = payload()["data_partition"]
    assert partition["development_end_utc"] == "2025-06-30T20:00:00Z"
    assert partition["signal_establishment_start_utc"] == "2025-07-01T00:00:00Z"
    assert partition["signal_establishment_end_utc"] == "2025-12-31T20:00:00Z"
    assert partition["final_framework_reserve_start_utc"] == "2026-01-01T00:00:00Z"
    assert partition["final_framework_reserve_end_utc"] == "2026-07-22T08:00:00Z"
    assert partition["v3_5_may_access_final_framework_reserve"] is False
    assert partition["historically_unseen_claim"] is False


def test_v3_g5_targets_horizons_and_multiplicity_are_frozen() -> None:
    contract = payload()
    assert contract["forecast_horizons"]["candles"] == [1, 2, 3, 6, 12, 18]
    assert contract["forecast_horizons"]["hours"] == [4, 8, 12, 24, 48, 72]
    assert contract["targets"]["direction"]["role"] == "CONFIRMATORY"
    assert contract["targets"]["expected_return"]["role"] == "SECONDARY"
    assert contract["targets"]["large_move_probability"]["role"] == "SECONDARY"
    multiplicity = contract["multiple_testing"]
    assert multiplicity["confirmatory_families"] == [
        "RSI_DIRECTION",
        "BOLLINGER_DIRECTION",
    ]
    assert multiplicity["confirmatory_method"] == "Holm"
    assert multiplicity["confirmatory_familywise_alpha"] == 0.05
    assert multiplicity["within_family_secondary_method"] == "Benjamini-Hochberg"
    assert multiplicity["secondary_fdr_q"] == 0.1


def test_v3_g5_matched_pair_and_candidate_controls_fail_closed() -> None:
    contract = payload()
    matched = contract["matched_pair_controls"]
    assert all(matched.values())
    registry = contract["signal_registry"]
    assert registry["registered_specifications"] == 48
    assert registry["base_specifications"] == 44
    assert registry["explicit_interactions"] == 4
    assert registry["adaptive_templates"] == 2
    assert len(registry["predeclared_family_blocks"]) == 8
    assert registry["full_cartesian_signal_combination_prohibited"] is True
    assert registry["automatic_candidate_deletion_prohibited"] is True
    assert registry["ineligible_candidates_remain_reported"] is True


def test_v3_g5_validation_cost_and_stop_rules_are_frozen() -> None:
    contract = payload()
    validation = contract["validation"]
    assert validation["outer_development_folds"] == 5
    assert validation["inner_selection_folds"] == 3
    assert validation["shuffle"] is False
    assert validation["purge_gap"] == "equal_to_horizon_candles"
    assert validation["minimum_positive_outer_folds"] == 3
    assert validation["maximum_single_fold_share_of_positive_gain"] == 0.6
    economics = contract["economic_assumptions"]
    assert economics["primary_one_way_cost_bps"] == 10
    assert economics["sensitivity_one_way_cost_bps"] == [5, 20]
    assert economics["uncertainty_method"] == "moving_block_bootstrap"
    assert contract["stop_rules"]["no_established_signal"] == (
        "FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED"
    )
    assert contract["stop_rules"]["final_reserve_access_before_v3_9"] == (
        "PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED"
    )


def test_v3_g5_execution_has_not_advanced_beyond_contract_freeze() -> None:
    contract = payload()
    assert contract["implementation_started"] is True
    assert contract["target_accessed"] is False
    assert contract["development_model_fitting_started"] is False
    assert contract["signal_establishment_segment_accessed"] is False
    assert contract["final_framework_reserve_accessed"] is False
    checkpoint = (ROOT / "V3_G5_MATCHED_FORECAST_CHECKPOINT.md").read_text(
        encoding="utf-8"
    )
    assert "failure modelling admissible: false" in checkpoint
    assert "FINAL_FRAMEWORK_RESERVE_NOT_ACCESSED" in checkpoint


def test_standalone_v3_g5_contract_verifier_passes() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/verify_v3_g5_contract.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "Gate V3-5 matched forecast contract verified." in completed.stdout
    assert "Parent V3-4 final lock verified: True" in completed.stdout
    assert "Target access: False" in completed.stdout
    assert "Model fitting started: False" in completed.stdout
