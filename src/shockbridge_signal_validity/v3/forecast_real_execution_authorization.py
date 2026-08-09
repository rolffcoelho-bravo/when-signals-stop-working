from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .forecast_contract import ForecastProtocolViolation
from .forecast_model_registry import ForecastPipelineSpec


JOB_ID_FIELDS = (
    "candidate_id",
    "horizon_candles",
    "row_contract_id",
    "target_name",
    "pipeline_spec_id",
    "outer_fold",
)


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _sha256_file(path: str | Path) -> str:
    source = Path(path)
    if not source.is_file():
        raise ForecastProtocolViolation(f"Authorization input is missing: {source}")
    return _sha256_bytes(source.read_bytes())


def _stage_lookup(contract: dict[str, Any]) -> list[dict[str, Any]]:
    schedule = contract.get("stage_schedule")
    if not isinstance(schedule, list) or len(schedule) != 6:
        raise ForecastProtocolViolation("Authorization stage schedule identity changed.")
    ranks = [int(item.get("stage_rank", -1)) for item in schedule]
    if ranks != [1, 2, 3, 4, 5, 6]:
        raise ForecastProtocolViolation("Authorization stage ranks are not 1 through 6.")
    return schedule


def _assign_stage(
    *,
    target_name: str,
    confirmatory_role: str,
    model_family: str,
    schedule: list[dict[str, Any]],
) -> tuple[int, str]:
    matches: list[tuple[int, str]] = []
    for stage in schedule:
        if str(stage["target_name"]) != str(target_name):
            continue
        stage_role = str(stage["confirmatory_role"])
        if stage_role != "ANY" and stage_role != str(confirmatory_role):
            continue
        if str(model_family) not in {str(value) for value in stage["model_families"]}:
            continue
        matches.append((int(stage["stage_rank"]), str(stage["stage_id"])))
    if len(matches) != 1:
        raise ForecastProtocolViolation(
            "Every executable candidate-pipeline job must map to exactly one stage."
        )
    return matches[0]


def _pipeline_frame(specs: Iterable[ForecastPipelineSpec]) -> pd.DataFrame:
    records = [
        {
            "pipeline_spec_id": value.pipeline_spec_id,
            "target_name": value.target_name,
            "task_type": value.task_type,
            "model_family": value.model_family,
            "window_id": value.window_id,
            "window_observations": value.window_observations,
            "complexity_rank": value.complexity_rank,
        }
        for value in specs
        if value.executable
    ]
    frame = pd.DataFrame.from_records(records)
    if len(frame) != 153 or frame["pipeline_spec_id"].duplicated().any():
        raise ForecastProtocolViolation(
            "Authorization requires exactly 153 unique executable pipeline specifications."
        )
    return frame


def _candidate_coverage_frame(
    matched_coverage: pd.DataFrame,
    candidate_inventory: pd.DataFrame,
) -> pd.DataFrame:
    coverage_required = {
        "candidate_id",
        "candidate_kind",
        "signal_family",
        "candidate_block",
        "horizon_candles",
        "matched_rows",
        "coverage_ratio",
        "row_contract_id",
        "coverage_status",
    }
    candidate_required = {"candidate_id", "confirmatory_role"}
    if not coverage_required.issubset(matched_coverage.columns):
        raise ForecastProtocolViolation("Matched coverage lacks authorization columns.")
    if not candidate_required.issubset(candidate_inventory.columns):
        raise ForecastProtocolViolation("Candidate inventory lacks authorization roles.")
    available = matched_coverage.loc[
        matched_coverage["coverage_status"] == "MATCHED_ROWS_AVAILABLE",
        sorted(coverage_required.difference({"coverage_status"})),
    ].copy()
    available = available.merge(
        candidate_inventory[["candidate_id", "confirmatory_role"]],
        on="candidate_id",
        how="left",
        validate="many_to_one",
    )
    if len(available) != 276:
        raise ForecastProtocolViolation(
            f"Authorization requires 276 matched candidate-horizon records, observed {len(available)}."
        )
    if available["confirmatory_role"].isna().any():
        raise ForecastProtocolViolation("Authorization coverage contains an unknown candidate.")
    if available.duplicated(["candidate_id", "horizon_candles"]).any():
        raise ForecastProtocolViolation("Authorization coverage identifiers are not unique.")
    return available


def _job_id(record: dict[str, object]) -> str:
    payload = {field: record[field] for field in JOB_ID_FIELDS}
    return "v3g5job:" + sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def build_authorization_job_plan(
    *,
    matched_coverage: pd.DataFrame,
    candidate_inventory: pd.DataFrame,
    pipeline_specs: Iterable[ForecastPipelineSpec],
    authorization_contract: dict[str, Any],
) -> pd.DataFrame:
    available = _candidate_coverage_frame(matched_coverage, candidate_inventory)
    pipelines = _pipeline_frame(pipeline_specs)
    available["_join"] = 1
    pipelines["_join"] = 1
    combinations = available.merge(pipelines, on="_join", how="inner").drop(
        columns="_join"
    )
    if len(combinations) != 42228:
        raise ForecastProtocolViolation(
            f"Candidate-pipeline identity failed: expected 42228, observed {len(combinations)}."
        )
    schedule = _stage_lookup(authorization_contract)
    assigned = combinations.apply(
        lambda row: _assign_stage(
            target_name=str(row["target_name"]),
            confirmatory_role=str(row["confirmatory_role"]),
            model_family=str(row["model_family"]),
            schedule=schedule,
        ),
        axis=1,
        result_type="expand",
    )
    combinations["stage_rank"] = assigned[0].astype(int)
    combinations["stage_id"] = assigned[1].astype(str)

    folds = pd.DataFrame({"outer_fold": [1, 2, 3, 4, 5], "_join": 1})
    combinations["_join"] = 1
    plan = combinations.merge(folds, on="_join", how="inner").drop(columns="_join")
    if len(plan) != 211140:
        raise ForecastProtocolViolation(
            f"Outer-fold job identity failed: expected 211140, observed {len(plan)}."
        )

    sort_order = [
        str(value) for value in authorization_contract["batching"]["sort_order"]
    ]
    cols = list(plan.columns)
    sort_indices = [cols.index(c) for c in sort_order]
    
    def _sort_key(row):
        return tuple(row[i] for i in sort_indices)
        
    row_tuples = list(plan.itertuples(index=False))
    row_tuples.sort(key=_sort_key)
    plan = pd.DataFrame(row_tuples, columns=cols)
    job_ids = []
    for row in plan[list(JOB_ID_FIELDS)].itertuples(index=False):
        payload = {
            "candidate_id": str(row.candidate_id),
            "horizon_candles": int(row.horizon_candles),
            "row_contract_id": str(row.row_contract_id) if pd.notna(row.row_contract_id) else None,
            "target_name": str(row.target_name),
            "pipeline_spec_id": str(row.pipeline_spec_id),
            "outer_fold": int(row.outer_fold)
        }
        job_ids.append("v3g5job:" + sha256(_canonical_json(payload).encode("utf-8")).hexdigest())
    plan["job_id"] = job_ids
    if plan["job_id"].duplicated().any():
        raise ForecastProtocolViolation("Authorization job identifiers are not unique.")
    plan["job_ordinal"] = pd.RangeIndex(start=1, stop=len(plan) + 1, step=1)
    plan["batch_state"] = str(
        authorization_contract["resumability"]["initial_batch_state"]
    )
    plan["real_execution_authorized"] = False
    plan["real_development_model_fitting_performed"] = False
    plan["development_pipeline_selection_performed"] = False
    plan["signal_establishment_segment_accessed"] = False
    plan["final_framework_reserve_accessed"] = False
    return plan


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(temporary, "wb") as f:
            chunk_size = 1024 * 1024
            for i in range(0, len(payload), chunk_size):
                f.write(payload[i:i+chunk_size])
        temporary.replace(path)
    except Exception as e:
        raise RuntimeError(f"Failed to write {path}: {e}") from e


def write_authorization_candidate_plan(
    *,
    plan: pd.DataFrame,
    batch_manifest: pd.DataFrame,
    stage_manifest: pd.DataFrame,
    output_dir: str | Path,
    authorization_contract: dict[str, Any],
    input_paths: dict[str, str | Path],
    git_commit: str,
    python_version: str,
    pandas_version: str,
    numpy_version: str,
    sklearn_version: str,
    platform_description: str,
) -> dict[str, Any]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    outputs = authorization_contract["planning_outputs"]
    payloads: dict[str, bytes] = {
        str(outputs["job_plan"]): plan.to_csv(
            index=False, lineterminator="\n"
        ).encode("utf-8"),
        str(outputs["batch_manifest"]): batch_manifest.to_csv(
            index=False, lineterminator="\n"
        ).encode("utf-8"),
        str(outputs["stage_manifest"]): stage_manifest.to_csv(
            index=False, lineterminator="\n"
        ).encode("utf-8"),
    }
    output_hashes = {name: _sha256_bytes(value) for name, value in payloads.items()}
    input_hashes = {
        name: _sha256_file(path) for name, path in sorted(input_paths.items())
    }
    input_payload = {
        "schema_version": "v3.g5-real-execution-authorization-inputs.v1",
        "input_sha256": input_hashes,
        "all_inputs_bound": True,
    }
    input_name = str(outputs["input_hash_manifest"])
    input_bytes = (
        json.dumps(input_payload, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    payloads[input_name] = input_bytes
    output_hashes[input_name] = _sha256_bytes(input_bytes)

    manifest = {
        "schema_version": "v3.g5-real-execution-authorization-candidate-manifest.v2",
        "status": "AUTHORIZATION_CANDIDATE_PLAN_MATERIALIZED",
        "git_commit": str(git_commit),
        "environment": {
            "python_version": str(python_version),
            "pandas_version": str(pandas_version),
            "numpy_version": str(numpy_version),
            "scikit_learn_version": str(sklearn_version),
            "platform": str(platform_description),
        },
        "job_count": int(len(plan)),
        "batch_count": int(len(batch_manifest)),
        "stage_count": int(len(stage_manifest)),
        "jobs_per_batch": int(authorization_contract["batching"]["jobs_per_batch"]),
        "final_batch_jobs": int(batch_manifest.iloc[-1]["job_count"]),
        "stage_boundary_alignment_verified": bool(
            plan.groupby("batch_ordinal")["stage_rank"].nunique().eq(1).all()
        ),
        "candidate_pipeline_target_combinations": 42228,
        "outer_fold_jobs": 211140,
        "output_sha256": output_hashes,
        "input_sha256": input_hashes,
        "all_jobs_initially_planned_not_started": bool(
            plan["batch_state"].eq("PLANNED_NOT_STARTED").all()
        ),
        "real_development_execution_authorized": False,
        "real_development_model_fitting_performed": False,
        "development_pipeline_selection_performed": False,
        "signal_establishment_segment_accessed": False,
        "final_framework_reserve_accessed": False,
        "predictive_claims_produced": False,
        "economic_claims_produced": False,
    }
    if manifest["stage_boundary_alignment_verified"] is not True:
        raise ForecastProtocolViolation(
            "Authorization candidate plan contains a mixed-stage batch."
        )
    manifest_name = str(outputs["authorization_candidate_manifest"])
    manifest_bytes = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    for name, payload in payloads.items():
        _atomic_write(destination / name, payload)
    _atomic_write(destination / manifest_name, manifest_bytes)
    return manifest
