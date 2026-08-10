from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .forecast_contract import ForecastProtocolViolation


def load_stage_aligned_authorization_candidate(path: str | Path) -> dict[str, Any]:
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
    if batching.get("stage_boundary_alignment_required") is not True:
        raise ForecastProtocolViolation("Authorization batches must align to stage boundaries.")
    expected = {
        "jobs_per_batch": 250,
        "expected_batch_count_min": 918,
        "expected_batch_count_max": 919,
        "expected_final_batch_jobs": 130,
        "maximum_parallel_batches": 1,
        "maximum_worker_processes": 1,
        "blas_threads_per_process": 1,
    }
    for field, value in expected.items():
        if batching.get(field) != value:
            raise ForecastProtocolViolation(
                f"Authorization stage-aligned batching identity changed: {field}"
            )
    return payload


def align_plan_batches_to_stages(
    plan: pd.DataFrame,
    authorization_contract: dict[str, Any],
) -> pd.DataFrame:
    required = {
        "stage_rank",
        "stage_id",
        "job_ordinal",
        "job_id",
        "batch_state",
    }
    if not required.issubset(plan.columns):
        raise ForecastProtocolViolation("Authorization plan lacks stage-alignment columns.")
    jobs_per_batch = int(authorization_contract["batching"]["jobs_per_batch"])
    aligned = plan.copy()
    aligned["stage_job_ordinal"] = (
        aligned.groupby(["stage_rank", "stage_id"], sort=True).cumcount() + 1
    )
    aligned["stage_batch_ordinal"] = (
        (aligned["stage_job_ordinal"] - 1) // jobs_per_batch
    ) + 1

    stage_batch_counts = (
        aligned.groupby(["stage_rank", "stage_id"], sort=True)["stage_batch_ordinal"]
        .max()
        .astype(int)
    )
    offsets: dict[tuple[int, str], int] = {}
    cumulative = 0
    for key, count in stage_batch_counts.items():
        offsets[(int(key[0]), str(key[1]))] = cumulative
        cumulative += int(count)
    aligned["batch_ordinal"] = aligned.apply(
        lambda row: offsets[(int(row["stage_rank"]), str(row["stage_id"]))] + int(row["stage_batch_ordinal"]),
        axis=1
    )
    aligned["batch_id"] = "v3g5batch:" + aligned["batch_ordinal"].astype(str).str.zfill(4)
    aligned["stage_batch_id"] = (
        aligned["stage_id"].astype(str) + ":batch:" + aligned["stage_batch_ordinal"].astype(str).str.zfill(4)
    )
    batch_count = int(aligned["batch_ordinal"].max())
    minimum = int(authorization_contract["batching"]["expected_batch_count_min"])
    maximum = int(authorization_contract["batching"]["expected_batch_count_max"])
    if not minimum <= batch_count <= maximum:
        raise ForecastProtocolViolation(
            f"Stage-aligned batch count must lie in [{minimum},{maximum}], observed {batch_count}."
        )
    final_jobs = int((aligned["batch_ordinal"] == batch_count).sum())
    if final_jobs != int(
        authorization_contract["batching"]["expected_final_batch_jobs"]
    ):
        raise ForecastProtocolViolation(
            "Stage-aligned final batch does not contain 130 jobs."
        )
    mixed = aligned.groupby("batch_ordinal", sort=True)["stage_rank"].nunique()
    if not mixed.eq(1).all():
        raise ForecastProtocolViolation("An authorization batch crosses a stage boundary.")
    return aligned


def build_stage_aligned_batch_manifest(
    plan: pd.DataFrame,
    authorization_contract: dict[str, Any],
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for batch_ordinal, group in plan.groupby("batch_ordinal", sort=True):
        if group["stage_rank"].nunique() != 1 or group["stage_id"].nunique() != 1:
            raise ForecastProtocolViolation("Authorization batch contains mixed stages.")
        job_material = "\n".join(group["job_id"].astype(str)) + "\n"
        records.append(
            {
                "batch_ordinal": int(batch_ordinal),
                "batch_id": str(group["batch_id"].iloc[0]),
                "stage_rank": int(group["stage_rank"].iloc[0]),
                "stage_id": str(group["stage_id"].iloc[0]),
                "stage_batch_ordinal": int(group["stage_batch_ordinal"].iloc[0]),
                "stage_batch_id": str(group["stage_batch_id"].iloc[0]),
                "job_count": int(len(group)),
                "first_job_ordinal": int(group["job_ordinal"].min()),
                "last_job_ordinal": int(group["job_ordinal"].max()),
                "job_ids_sha256": sha256(job_material.encode("utf-8")).hexdigest(),
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
    minimum = int(authorization_contract["batching"]["expected_batch_count_min"])
    maximum = int(authorization_contract["batching"]["expected_batch_count_max"])
    if not minimum <= len(manifest) <= maximum:
        raise ForecastProtocolViolation("Stage-aligned batch manifest count changed.")
    if int(manifest["job_count"].sum()) != 229500:
        raise ForecastProtocolViolation("Stage-aligned batch jobs do not sum to 229500.")
    if int(manifest.iloc[-1]["job_count"]) != 130:
        raise ForecastProtocolViolation("Stage-aligned final batch identity changed.")
    if manifest.groupby("batch_ordinal")["stage_rank"].nunique().max() != 1:
        raise ForecastProtocolViolation("Stage-aligned batch manifest mixes stages.")
    return manifest
