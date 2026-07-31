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


def load_authorization_candidate(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ForecastProtocolViolation("Execution authorization candidate must be an object.")
    if payload.get("status") != "AUTHORIZATION_CANDIDATE_FROZEN":
        raise ForecastProtocolViolation("Execution authorization candidate is not frozen.")
    if payload.get("planning_and_manifest_generation_authorized") is not True:
        raise ForecastProtocolViolation("Authorization planning is not enabled.")
    for field in (
        "real_development_execution_authorized",
        "real_development_model_fitting_authorized",
        "development_pipeline_selection_authorized",
        "development_pipeline_admission_authorized",
        "signal_establishment_segment_access_authorized",
        "final_framework_reserve_access_authorized",
    ):
        if payload.get(field) is not False:
            raise ForecastProtocolViolation(
                f"Execution authorization candidate advanced prematurely: {field}"
            )
    batching = payload.get("batching", {})
    expected = {
        "jobs_per_batch": 250,
        "expected_batch_count": 845,
        "expected_final_batch_jobs": 140,
        "maximum_parallel_batches": 1,
        "maximum_worker_processes": 1,
        "blas_threads_per_process": 1,
    }
    for field, value in expected.items():
        if batching.get(field) != value:
            raise ForecastProtocolViolation(
                f"Authorization batching identity changed: {field}"
            )
    return payload


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
    combinations = available.merge(pipelines, on="_join", how="inner").drop(columns="_join")
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

    sort_order = [str(value) for value in authorization_contract["batching"]["sort_order"]]
    plan = plan.sort_values(sort_order, kind="mergesort").reset_index(drop=True)
    job_records = plan.loc[:, list(JOB_ID_FIELDS)].to_dict(orient="records")
    plan["job_id"] = [_job_id(record) for record in job_records]
    if plan["job_id"].duplicated().any():
        raise ForecastProtocolViolation("Authorization job identifiers are not unique.")
    plan["job_ordinal"] = pd.RangeIndex(start=1, stop=len(plan) + 1, step=1)
    jobs_per_batch = int(authorization_contract["batching"]["jobs_per_batch"])
    plan["batch_ordinal"] = ((plan["job_ordinal"] - 1) // jobs_per_batch) + 1
    plan["batch_id"] = plan["batch_ordinal"].map(
        lambda value: f"v3g5batch:{int(value):04d}"
    )
    plan["batch_state"] = str(
        authorization_contract["resumability"]["initial_batch_state"]
    )
    plan["real_execution_authorized"] = False
    plan["real_development_model_fitting_performed"] = False
    plan["development_pipeline_selection_performed"] = False
    plan["signal_establishment_segment_accessed"] = False
    plan["final_framework_reserve_accessed"] = False

    if int(plan["batch_ordinal"].max()) != 845:
        raise ForecastProtocolViolation("Authorization batch count is not 845.")
    final_jobs = int((plan["batch_ordinal"] == 845).sum())
    if final_jobs != 140:
        raise ForecastProtocolViolation("Authorization final batch does not contain 140 jobs.")
    return plan


def build_batch_manifest(
    plan: pd.DataFrame,
    authorization_contract: dict[str, Any],
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for batch_ordinal, group in plan.groupby("batch_ordinal", sort=True):
        job_material = "\n".join(group["job_id"].astype(str)) + "\n"
        records.append(
            {
                "batch_ordinal": int(batch_ordinal),
                "batch_id": str(group["batch_id"].iloc[0]),
                "job_count": int(len(group)),
                "first_job_ordinal": int(group["job_ordinal"].min()),
                "last_job_ordinal": int(group["job_ordinal"].max()),
                "first_stage_rank": int(group["stage_rank"].min()),
                "last_stage_rank": int(group["stage_rank"].max()),
                "job_ids_sha256": _sha256_bytes(job_material.encode("utf-8")),
                "batch_state": str(
                    authorization_contract["resumability"]["initial_batch_state"]
                ),
                "attempt_count": 0,
                "checkpoint_path": None,
                "output_hash_manifest_path": None,
                "real_execution_authorized": False,
                "real_development_model_fitting_performed": False,
            }
        )
    manifest = pd.DataFrame.from_records(records)
    if len(manifest) != 845 or int(manifest["job_count"].sum()) != 211140:
        raise ForecastProtocolViolation("Authorization batch manifest identity failed.")
    if int(manifest.iloc[-1]["job_count"]) != 140:
        raise ForecastProtocolViolation("Authorization final batch manifest identity failed.")
    return manifest


def build_stage_manifest(plan: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for (stage_rank, stage_id), group in plan.groupby(
        ["stage_rank", "stage_id"], sort=True
    ):
        records.append(
            {
                "stage_rank": int(stage_rank),
                "stage_id": str(stage_id),
                "job_count": int(len(group)),
                "candidate_count": int(group["candidate_id"].nunique()),
                "horizon_count": int(group["horizon_candles"].nunique()),
                "pipeline_specification_count": int(
                    group["pipeline_spec_id"].nunique()
                ),
                "outer_fold_count": int(group["outer_fold"].nunique()),
                "first_job_ordinal": int(group["job_ordinal"].min()),
                "last_job_ordinal": int(group["job_ordinal"].max()),
                "real_execution_authorized": False,
            }
        )
    manifest = pd.DataFrame.from_records(records)
    if list(manifest["stage_rank"]) != [1, 2, 3, 4, 5, 6]:
        raise ForecastProtocolViolation("Authorization stage manifest identity failed.")
    if int(manifest["job_count"].sum()) != 211140:
        raise ForecastProtocolViolation("Authorization stage jobs do not sum to 211140.")
    return manifest


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


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
    sklearn_version: str,
) -> dict[str, Any]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    outputs = authorization_contract["planning_outputs"]
    payloads: dict[str, bytes] = {
        str(outputs["job_plan"]): plan.to_csv(index=False, lineterminator="\n").encode("utf-8"),
        str(outputs["batch_manifest"]): batch_manifest.to_csv(
            index=False, lineterminator="\n"
        ).encode("utf-8"),
        str(outputs["stage_manifest"]): stage_manifest.to_csv(
            index=False, lineterminator="\n"
        ).encode("utf-8"),
    }
    output_hashes = {name: _sha256_bytes(value) for name, value in payloads.items()}
    input_hashes = {name: _sha256_file(path) for name, path in sorted(input_paths.items())}
    input_payload = {
        "schema_version": "v3.g5-real-execution-authorization-inputs.v1",
        "input_sha256": input_hashes,
        "all_inputs_bound": True,
    }
    input_name = str(outputs["input_hash_manifest"])
    input_bytes = (json.dumps(input_payload, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    payloads[input_name] = input_bytes
    output_hashes[input_name] = _sha256_bytes(input_bytes)

    manifest = {
        "schema_version": "v3.g5-real-execution-authorization-candidate-manifest.v1",
        "status": "AUTHORIZATION_CANDIDATE_PLAN_MATERIALIZED",
        "git_commit": str(git_commit),
        "python_version": str(python_version),
        "scikit_learn_version": str(sklearn_version),
        "job_count": int(len(plan)),
        "batch_count": int(len(batch_manifest)),
        "stage_count": int(len(stage_manifest)),
        "jobs_per_batch": int(authorization_contract["batching"]["jobs_per_batch"]),
        "final_batch_jobs": int(batch_manifest.iloc[-1]["job_count"]),
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
    manifest_name = str(outputs["authorization_candidate_manifest"])
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    for name, payload in payloads.items():
        _atomic_write(destination / name, payload)
    _atomic_write(destination / manifest_name, manifest_bytes)
    return manifest


def verify_authorization_candidate_plan(
    *,
    output_dir: str | Path,
    authorization_contract: dict[str, Any],
) -> dict[str, Any]:
    destination = Path(output_dir)
    outputs = authorization_contract["planning_outputs"]
    manifest_path = destination / str(outputs["authorization_candidate_manifest"])
    if not manifest_path.is_file():
        raise ForecastProtocolViolation("Authorization candidate manifest is missing.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "AUTHORIZATION_CANDIDATE_PLAN_MATERIALIZED":
        raise ForecastProtocolViolation("Authorization candidate manifest status changed.")
    expected = {
        "job_count": 211140,
        "batch_count": 845,
        "stage_count": 6,
        "jobs_per_batch": 250,
        "final_batch_jobs": 140,
        "candidate_pipeline_target_combinations": 42228,
        "outer_fold_jobs": 211140,
        "all_jobs_initially_planned_not_started": True,
        "real_development_execution_authorized": False,
        "real_development_model_fitting_performed": False,
        "development_pipeline_selection_performed": False,
        "signal_establishment_segment_accessed": False,
        "final_framework_reserve_accessed": False,
    }
    for field, value in expected.items():
        if manifest.get(field) != value:
            raise ForecastProtocolViolation(
                f"Authorization candidate manifest identity failed: {field}"
            )
    output_hashes = manifest.get("output_sha256", {})
    for name, expected_hash in output_hashes.items():
        path = destination / str(name)
        if _sha256_file(path) != str(expected_hash):
            raise ForecastProtocolViolation(
                f"Authorization candidate output hash mismatch: {name}"
            )
    plan = pd.read_csv(destination / str(outputs["job_plan"]))
    batches = pd.read_csv(destination / str(outputs["batch_manifest"]))
    stages = pd.read_csv(destination / str(outputs["stage_manifest"]))
    if len(plan) != 211140 or plan["job_id"].duplicated().any():
        raise ForecastProtocolViolation("Authorization job plan identity failed.")
    if len(batches) != 845 or int(batches["job_count"].sum()) != 211140:
        raise ForecastProtocolViolation("Authorization batch plan identity failed.")
    if len(stages) != 6 or int(stages["job_count"].sum()) != 211140:
        raise ForecastProtocolViolation("Authorization stage plan identity failed.")
    for column in (
        "real_execution_authorized",
        "real_development_model_fitting_performed",
        "development_pipeline_selection_performed",
        "signal_establishment_segment_accessed",
        "final_framework_reserve_accessed",
    ):
        if plan[column].astype(bool).any():
            raise ForecastProtocolViolation(
                f"Authorization plan advanced execution state: {column}"
            )
    if not plan["batch_state"].eq("PLANNED_NOT_STARTED").all():
        raise ForecastProtocolViolation("Authorization plan contains a started batch.")
    return manifest
