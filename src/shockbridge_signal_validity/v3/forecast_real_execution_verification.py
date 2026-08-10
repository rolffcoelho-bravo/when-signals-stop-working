from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .forecast_contract import ForecastProtocolViolation
from .forecast_real_execution_authorization import _sha256_file


def _is_explicit_false(value: object) -> bool:
    if isinstance(value, bool):
        return value is False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) == 0.0
    return str(value).strip().lower() in {"false", "0"}


def verify_authorization_candidate_plan_strict(
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
        "job_count": 229500,
        "stage_count": 6,
        "jobs_per_batch": 250,
        "final_batch_jobs": 250,
        "stage_boundary_alignment_verified": True,
        "candidate_pipeline_target_combinations": 45900,
        "outer_fold_jobs": 229500,
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
    batch_count = int(manifest.get("batch_count", -1))
    minimum = int(authorization_contract["batching"]["expected_batch_count_min"])
    maximum = int(authorization_contract["batching"]["expected_batch_count_max"])
    if not minimum <= batch_count <= maximum:
        raise ForecastProtocolViolation(
            "Authorization candidate manifest batch count is outside the stage-aligned range."
        )

    output_hashes = manifest.get("output_sha256", {})
    if not isinstance(output_hashes, dict) or len(output_hashes) != 4:
        raise ForecastProtocolViolation("Authorization output hash identity changed.")
    for name, expected_hash in output_hashes.items():
        path = destination / str(name)
        if _sha256_file(path) != str(expected_hash):
            raise ForecastProtocolViolation(
                f"Authorization candidate output hash mismatch: {name}"
            )

    plan = pd.read_csv(destination / str(outputs["job_plan"]))
    batches = pd.read_csv(destination / str(outputs["batch_manifest"]))
    stages = pd.read_csv(destination / str(outputs["stage_manifest"]))
    if len(plan) != 229500 or plan["job_id"].duplicated().any():
        raise ForecastProtocolViolation("Authorization job plan identity failed.")
    if len(batches) != batch_count or int(batches["job_count"].sum()) != 229500:
        raise ForecastProtocolViolation("Authorization batch plan identity failed.")
    if len(stages) != 6 or int(stages["job_count"].sum()) != 229500:
        raise ForecastProtocolViolation("Authorization stage plan identity failed.")
    if list(stages["stage_rank"].astype(int)) != [1, 2, 3, 4, 5, 6]:
        raise ForecastProtocolViolation("Authorization declared stage order changed.")
    expected_from_stages = int(
        sum((int(value) + 249) // 250 for value in stages["job_count"] if int(value) > 0)
    )
    if batch_count != expected_from_stages:
        raise ForecastProtocolViolation(
            "Authorization batch count does not equal the sum of stage-specific ceilings."
        )
    if int(batches.iloc[-1]["job_count"]) != 250:
        raise ForecastProtocolViolation("Authorization final batch identity changed.")
    if plan.groupby("batch_ordinal")["stage_rank"].nunique().max() != 1:
        raise ForecastProtocolViolation("Authorization job plan contains a mixed-stage batch.")
    if batches.groupby("batch_ordinal")["stage_rank"].nunique().max() != 1:
        raise ForecastProtocolViolation("Authorization batch manifest contains mixed stages.")
    if not plan["batch_state"].eq("PLANNED_NOT_STARTED").all():
        raise ForecastProtocolViolation("Authorization plan contains a started batch.")
    if not batches["batch_state"].eq("PLANNED_NOT_STARTED").all():
        raise ForecastProtocolViolation("Authorization batch manifest contains a started batch.")

    for frame_name, frame, columns in (
        (
            "job plan",
            plan,
            (
                "real_execution_authorized",
                "real_development_model_fitting_performed",
                "development_pipeline_selection_performed",
                "signal_establishment_segment_accessed",
                "final_framework_reserve_accessed",
            ),
        ),
        (
            "batch manifest",
            batches,
            (
                "real_execution_authorized",
                "real_development_model_fitting_performed",
            ),
        ),
        (
            "stage manifest",
            stages,
            ("real_execution_authorized",),
        ),
    ):
        for column in columns:
            if column not in frame.columns:
                raise ForecastProtocolViolation(
                    f"Authorization {frame_name} is missing state column: {column}"
                )
            if not frame[column].map(_is_explicit_false).all():
                raise ForecastProtocolViolation(
                    f"Authorization {frame_name} advanced execution state: {column}"
                )
    return manifest
