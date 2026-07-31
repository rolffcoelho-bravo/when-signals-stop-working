from __future__ import annotations

import copy
from pathlib import Path

import pandas as pd
import pytest

from shockbridge_signal_validity.v3.forecast_contract import ForecastProtocolViolation
from shockbridge_signal_validity.v3.forecast_model_registry import (
    build_pipeline_registry,
    load_contracts,
)
from shockbridge_signal_validity.v3.forecast_real_execution_authorization import (
    build_authorization_job_plan,
)
from shockbridge_signal_validity.v3.forecast_real_execution_batching import (
    align_plan_batches_to_stages,
    build_stage_aligned_batch_manifest,
    load_stage_aligned_authorization_candidate,
)
from shockbridge_signal_validity.v3.forecast_real_execution_stages import (
    build_complete_stage_manifest,
)
from shockbridge_signal_validity.v3.forecast_real_execution_verification import (
    _is_explicit_false,
)

ROOT = Path(__file__).resolve().parents[1]
FORECAST_CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"
MODEL_CONTRACT = ROOT / "configs" / "v3_g5_model_implementation_contract.json"
AUTHORIZATION_CONTRACT = (
    ROOT / "configs" / "v3_g5_real_execution_authorization_candidate.json"
)
HORIZONS = (1, 2, 3, 6, 12, 18)


def _synthetic_inventory_and_coverage() -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates = pd.DataFrame(
        {
            "candidate_id": [f"candidate-{value:02d}" for value in range(47)],
            "confirmatory_role": ["ELIGIBLE_BY_FAMILY"] * 46 + ["SECONDARY_ONLY"],
        }
    )
    records: list[dict[str, object]] = []
    for candidate_index, row in candidates.iterrows():
        for horizon in HORIZONS:
            available = candidate_index < 46
            records.append(
                {
                    "candidate_id": str(row["candidate_id"]),
                    "candidate_kind": (
                        "SINGLE_SIGNAL"
                        if candidate_index < 46
                        else "PREDECLARED_COMBINED_BLOCK"
                    ),
                    "signal_family": "RSI" if candidate_index % 2 == 0 else "BOLLINGER",
                    "candidate_block": f"BLOCK_{candidate_index:02d}",
                    "horizon_candles": horizon,
                    "matched_rows": 9000 if available else 0,
                    "coverage_ratio": 0.9 if available else 0.0,
                    "row_contract_id": (
                        f"row-contract-{candidate_index:02d}-{horizon}"
                        if available
                        else None
                    ),
                    "coverage_status": (
                        "MATCHED_ROWS_AVAILABLE"
                        if available
                        else "INELIGIBLE_SIGNAL_COLUMNS_MISSING"
                    ),
                }
            )
    return candidates, pd.DataFrame.from_records(records)


@pytest.fixture(scope="module")
def authorization_bundle():
    authorization = load_stage_aligned_authorization_candidate(AUTHORIZATION_CONTRACT)
    forecast, implementation = load_contracts(FORECAST_CONTRACT, MODEL_CONTRACT)
    registry = build_pipeline_registry(forecast, implementation)
    candidates, coverage = _synthetic_inventory_and_coverage()
    plan = build_authorization_job_plan(
        matched_coverage=coverage,
        candidate_inventory=candidates,
        pipeline_specs=registry,
        authorization_contract=authorization,
    )
    plan = align_plan_batches_to_stages(plan, authorization)
    batches = build_stage_aligned_batch_manifest(plan, authorization)
    stages = build_complete_stage_manifest(plan, authorization)
    return authorization, registry, candidates, coverage, plan, batches, stages


def test_authorization_candidate_is_planning_only() -> None:
    authorization = load_stage_aligned_authorization_candidate(AUTHORIZATION_CONTRACT)
    assert authorization["planning_and_manifest_generation_authorized"] is True
    assert authorization["real_development_execution_authorized"] is False
    assert authorization["real_development_model_fitting_authorized"] is False
    assert authorization["development_pipeline_selection_authorized"] is False
    assert authorization["batching"]["stage_boundary_alignment_required"] is True


def test_exact_job_plan_identity(authorization_bundle) -> None:
    _, _, _, _, plan, _, _ = authorization_bundle
    assert len(plan) == 211140
    assert plan["job_id"].nunique() == 211140
    assert int(plan["job_ordinal"].min()) == 1
    assert int(plan["job_ordinal"].max()) == 211140
    assert plan["job_id"].str.startswith("v3g5job:").all()


def test_exact_stage_aligned_batch_identity(authorization_bundle) -> None:
    _, _, _, _, plan, batches, _ = authorization_bundle
    assert plan["batch_ordinal"].nunique() == 847
    assert len(batches) == 847
    assert int(batches["job_count"].sum()) == 211140
    assert int(batches.iloc[-1]["job_count"]) == 130
    assert batches.iloc[-1]["batch_id"] == "v3g5batch:0847"
    assert batches.groupby("batch_ordinal")["stage_rank"].nunique().max() == 1


def test_declared_empty_stage_is_preserved(authorization_bundle) -> None:
    _, _, _, _, plan, _, stages = authorization_bundle
    assert set(plan["stage_rank"]) == {1, 2, 3, 5, 6}
    assert list(stages["stage_rank"]) == [1, 2, 3, 4, 5, 6]
    stage_four = stages.loc[stages["stage_rank"] == 4].iloc[0]
    assert int(stage_four["job_count"]) == 0
    assert bool(stage_four["empty_stage_preserved"]) is True
    assert int(stages["job_count"].sum()) == 211140


def test_all_jobs_remain_unstarted_and_unauthorized(authorization_bundle) -> None:
    _, _, _, _, plan, batches, stages = authorization_bundle
    assert plan["batch_state"].eq("PLANNED_NOT_STARTED").all()
    assert batches["batch_state"].eq("PLANNED_NOT_STARTED").all()
    for column in (
        "real_execution_authorized",
        "real_development_model_fitting_performed",
        "development_pipeline_selection_performed",
        "signal_establishment_segment_accessed",
        "final_framework_reserve_accessed",
    ):
        assert plan[column].eq(False).all()
    assert batches["real_execution_authorized"].eq(False).all()
    assert stages["real_execution_authorized"].eq(False).all()


def test_authorization_stage_order_is_deterministic(authorization_bundle) -> None:
    _, _, _, _, plan, _, _ = authorization_bundle
    observed = plan.loc[
        :,
        [
            "stage_rank",
            "target_name",
            "horizon_candles",
            "candidate_id",
            "model_family",
            "window_id",
            "pipeline_spec_id",
            "outer_fold",
        ],
    ]
    expected = observed.sort_values(list(observed.columns), kind="mergesort").reset_index(
        drop=True
    )
    pd.testing.assert_frame_equal(observed.reset_index(drop=True), expected)


def test_authorization_rejects_execution_flag() -> None:
    authorization = load_stage_aligned_authorization_candidate(AUTHORIZATION_CONTRACT)
    changed = copy.deepcopy(authorization)
    changed["real_development_execution_authorized"] = True
    temporary = ROOT / "outputs" / "v3" / "test_authorization_candidate.json"
    temporary.parent.mkdir(parents=True, exist_ok=True)
    try:
        temporary.write_text(__import__("json").dumps(changed), encoding="utf-8")
        with pytest.raises(ForecastProtocolViolation, match="advanced prematurely"):
            load_stage_aligned_authorization_candidate(temporary)
    finally:
        temporary.unlink(missing_ok=True)


def test_authorization_rejects_wrong_available_coverage_count(authorization_bundle) -> None:
    authorization, registry, candidates, coverage, _, _, _ = authorization_bundle
    available_index = coverage.index[
        coverage["coverage_status"] == "MATCHED_ROWS_AVAILABLE"
    ][0]
    reduced = coverage.drop(index=available_index).copy()
    with pytest.raises(ForecastProtocolViolation, match="276 matched"):
        build_authorization_job_plan(
            matched_coverage=reduced,
            candidate_inventory=candidates,
            pipeline_specs=registry,
            authorization_contract=authorization,
        )


def test_job_ids_bind_outer_fold(authorization_bundle) -> None:
    _, _, _, _, plan, _, _ = authorization_bundle
    group = plan.groupby(
        ["candidate_id", "horizon_candles", "pipeline_spec_id"], sort=False
    ).head(5)
    sample = group.iloc[:5]
    assert sample["outer_fold"].nunique() == 5
    assert sample["job_id"].nunique() == 5


def test_batch_hashes_are_unique(authorization_bundle) -> None:
    _, _, _, _, _, batches, _ = authorization_bundle
    assert batches["job_ids_sha256"].nunique() == 847
    assert batches["attempt_count"].eq(0).all()


def test_strict_false_state_parser() -> None:
    for value in (False, "False", "false", 0, 0.0, "0"):
        assert _is_explicit_false(value) is True
    for value in (True, "True", "started", 1, 1.0, "1"):
        assert _is_explicit_false(value) is False


def test_authorization_validation_produces_no_empirical_claims(authorization_bundle) -> None:
    authorization, _, _, _, _, _, _ = authorization_bundle
    prohibited = authorization["prohibited_during_candidate_validation"]
    assert prohibited["real_development_model_fit"] is True
    assert prohibited["real_development_prediction"] is True
    assert prohibited["pipeline_ranking"] is True
    assert prohibited["pipeline_admission"] is True
    assert prohibited["empirical_claims"] is True
