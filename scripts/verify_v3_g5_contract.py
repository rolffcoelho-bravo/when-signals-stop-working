from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "configs" / "v3_g5_forecast_contract.json"
PARENT_LOCK_PATH = ROOT / "V3_G4_SIGNAL_ENGINE_LOCK.json"
SCOPE_PATH = ROOT / "docs" / "V3_G5_MATCHED_FORECAST_SCOPE.md"
CHECKPOINT_PATH = ROOT / "V3_G5_MATCHED_FORECAST_CHECKPOINT.md"


class V3G5ContractError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise V3G5ContractError(message)


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"Required Gate V3-5 file is missing: {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"Expected JSON object: {path.relative_to(ROOT)}")
    return value


def require_parent_lock() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "scripts/verify_v3_g4_lock.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        fail(f"Gate V3-4 parent lock verification failed: {detail}")
    parent = read_json(PARENT_LOCK_PATH)
    if parent.get("status") != "IMPLEMENTATION_VALIDATED_AND_LOCKED":
        fail("Gate V3-4 parent lock is not final.")
    if parent.get("validated_implementation_commit") != (
        "ff2e7ecba3fa69f22e0b109437d23b52d30fba2b"
    ):
        fail("Gate V3-4 validated implementation commit changed.")
    if parent.get("evidence_materialization_commit") != (
        "705511de9e8ee22a9f8aff34506aebb6c26223e7"
    ):
        fail("Gate V3-4 evidence materialization commit changed.")
    return parent


def verify_contract(payload: dict[str, Any]) -> None:
    expected_identity = {
        "schema_version": "v3.matched-forecast-contract.v1",
        "gate": "V3-5",
        "title": "Matched Benchmark-versus-Signal Forecast Selection",
        "status": "APPROVED_IMPLEMENTATION_STARTED_CONTRACT_FROZEN",
        "branch": "research/v3-adaptive-signal-validity",
        "baseline_release": "v2.0.0",
        "baseline_commit": "5a07299367b80c3940e652e7bbdd208ce86ba5ef",
        "parent_gate": "V3-4",
        "parent_lock": "V3_G4_SIGNAL_ENGINE_LOCK.json",
        "parent_lock_status_required": "IMPLEMENTATION_VALIDATED_AND_LOCKED",
        "parent_validated_implementation_commit": (
            "ff2e7ecba3fa69f22e0b109437d23b52d30fba2b"
        ),
        "parent_evidence_materialization_commit": (
            "705511de9e8ee22a9f8aff34506aebb6c26223e7"
        ),
        "frozen_v1_v2_determinations_modified": False,
    }
    for field, expected in expected_identity.items():
        if payload.get(field) != expected:
            fail(f"Gate V3-5 identity changed: {field}")

    partition = payload.get("data_partition", {})
    expected_partition = {
        "development_start_utc": "2021-01-01T00:00:00Z",
        "development_end_utc": "2025-06-30T20:00:00Z",
        "signal_establishment_start_utc": "2025-07-01T00:00:00Z",
        "signal_establishment_end_utc": "2025-12-31T20:00:00Z",
        "final_framework_reserve_start_utc": "2026-01-01T00:00:00Z",
        "final_framework_reserve_end_utc": "2026-07-22T08:00:00Z",
    }
    for field, expected in expected_partition.items():
        if partition.get(field) != expected:
            fail(f"Gate V3-5 data partition changed: {field}")
    if partition.get("v3_5_may_access_final_framework_reserve") is not False:
        fail("Gate V3-5 final-framework reserve prohibition changed.")
    if partition.get("historically_unseen_claim") is not False:
        fail("Gate V3-5 improperly claims a historically unseen partition.")

    horizons = payload.get("forecast_horizons", {})
    if horizons.get("candles") != [1, 2, 3, 6, 12, 18]:
        fail("Gate V3-5 horizon-candle set changed.")
    if horizons.get("hours") != [4, 8, 12, 24, 48, 72]:
        fail("Gate V3-5 horizon-hour set changed.")

    targets = payload.get("targets", {})
    if set(targets) != {"direction", "expected_return", "large_move_probability"}:
        fail("Gate V3-5 target family changed.")
    if targets.get("direction", {}).get("role") != "CONFIRMATORY":
        fail("Direction is no longer the confirmatory target.")
    for name in ("expected_return", "large_move_probability"):
        if targets.get(name, {}).get("role") != "SECONDARY":
            fail(f"Gate V3-5 target role changed: {name}")

    signal_registry = payload.get("signal_registry", {})
    expected_counts = {
        "registered_specifications": 48,
        "base_specifications": 44,
        "explicit_interactions": 4,
        "adaptive_templates": 2,
    }
    for field, expected in expected_counts.items():
        if signal_registry.get(field) != expected:
            fail(f"Gate V3-5 parent signal count changed: {field}")
    if len(signal_registry.get("predeclared_family_blocks", [])) != 8:
        fail("Gate V3-5 family-block registry must contain eight blocks.")
    for field in (
        "full_cartesian_signal_combination_prohibited",
        "automatic_candidate_deletion_prohibited",
        "ineligible_candidates_remain_reported",
    ):
        if signal_registry.get(field) is not True:
            fail(f"Gate V3-5 signal-registry control changed: {field}")

    matched = payload.get("matched_pair_controls", {})
    required_true = (
        "identical_model_class",
        "identical_training_rows",
        "identical_test_rows",
        "identical_preprocessing",
        "identical_hyperparameter_selection",
        "identical_calibration",
        "identical_target_and_horizon",
        "identical_cost_and_decision_policy",
        "candidate_specific_matched_row_intersection",
        "cross_candidate_raw_metric_ranking_prohibited",
    )
    for field in required_true:
        if matched.get(field) is not True:
            fail(f"Gate V3-5 matched-pair control changed: {field}")

    validation = payload.get("validation", {})
    expected_validation = {
        "outer_development_folds": 5,
        "inner_selection_folds": 3,
        "shuffle": False,
        "purge_gap": "equal_to_horizon_candles",
        "training_only_preprocessing": True,
        "training_only_regime_estimation": True,
        "training_only_large_move_threshold": True,
        "training_only_calibration": True,
        "minimum_positive_outer_folds": 3,
        "maximum_single_fold_share_of_positive_gain": 0.6,
        "one_standard_error_complexity_preference": True,
    }
    for field, expected in expected_validation.items():
        if validation.get(field) != expected:
            fail(f"Gate V3-5 validation contract changed: {field}")

    economics = payload.get("economic_assumptions", {})
    if economics.get("primary_one_way_cost_bps") != 10:
        fail("Gate V3-5 primary cost changed.")
    if economics.get("sensitivity_one_way_cost_bps") != [5, 20]:
        fail("Gate V3-5 cost sensitivity changed.")
    if economics.get("uncertainty_method") != "moving_block_bootstrap":
        fail("Gate V3-5 economic uncertainty method changed.")

    multiplicity = payload.get("multiple_testing", {})
    if multiplicity.get("confirmatory_families") != [
        "RSI_DIRECTION",
        "BOLLINGER_DIRECTION",
    ]:
        fail("Gate V3-5 confirmatory family changed.")
    if multiplicity.get("confirmatory_method") != "Holm":
        fail("Gate V3-5 confirmatory multiplicity method changed.")
    if multiplicity.get("confirmatory_familywise_alpha") != 0.05:
        fail("Gate V3-5 confirmatory alpha changed.")
    if multiplicity.get("within_family_secondary_method") != "Benjamini-Hochberg":
        fail("Gate V3-5 secondary multiplicity method changed.")

    reserve = payload.get("final_framework_reserve", {})
    if reserve.get("reserved_for_gate") != "V3-9":
        fail("Gate V3-5 final reserve owner changed.")
    if reserve.get("v3_5_access_prohibited") is not True:
        fail("Gate V3-5 final reserve prohibition changed.")

    stop_rules = payload.get("stop_rules", {})
    if stop_rules.get("no_established_signal") != (
        "FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED"
    ):
        fail("Gate V3-5 establishment stop rule changed.")
    if stop_rules.get("final_reserve_access_before_v3_9") != (
        "PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED"
    ):
        fail("Gate V3-5 final reserve fail-closed rule changed.")

    if payload.get("implementation_started") is not True:
        fail("Gate V3-5 implementation is not recorded as started.")
    for field in (
        "target_accessed",
        "development_model_fitting_started",
        "signal_establishment_segment_accessed",
        "final_framework_reserve_accessed",
    ):
        if payload.get(field) is not False:
            fail(f"Gate V3-5 execution state advanced prematurely: {field}")


def verify_documents() -> None:
    required = {
        SCOPE_PATH: (
            "PARENT_V3_4_VALIDATED_AND_LOCKED",
            "Matched Benchmark-versus-Signal Forecast Selection",
            "PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED",
        ),
        CHECKPOINT_PATH: (
            "CONTRACT_FROZEN",
            "TARGET_ACCESS_NOT_STARTED",
            "failure modelling admissible: false",
        ),
    }
    for path, phrases in required.items():
        if not path.is_file():
            fail(f"Required Gate V3-5 document is missing: {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                fail(f"Required phrase missing from {path.relative_to(ROOT)}: {phrase}")


def main() -> int:
    require_parent_lock()
    payload = read_json(CONTRACT_PATH)
    verify_contract(payload)
    verify_documents()
    print("Gate V3-5 matched forecast contract verified.")
    print("Parent V3-4 final lock verified: True")
    print("Registered parent signal specifications: 48")
    print("Forecast horizons: 4h/8h/12h/24h/48h/72h")
    print("Development folds: 5 outer / 3 inner")
    print("Signal-establishment segment access: False")
    print("V3-9 final-framework reserve access: False")
    print("Target access: False")
    print("Model fitting started: False")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, KeyError, OSError, TypeError, ValueError, V3G5ContractError) as error:
        print(f"Gate V3-5 contract verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
