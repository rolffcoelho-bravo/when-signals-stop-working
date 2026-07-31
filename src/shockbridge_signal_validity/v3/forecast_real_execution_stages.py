from __future__ import annotations

from typing import Any

import pandas as pd

from .forecast_contract import ForecastProtocolViolation


def build_complete_stage_manifest(
    plan: pd.DataFrame,
    authorization_contract: dict[str, Any],
) -> pd.DataFrame:
    schedule = authorization_contract.get("stage_schedule")
    if not isinstance(schedule, list) or len(schedule) != 6:
        raise ForecastProtocolViolation("Authorization stage schedule identity changed.")
    records: list[dict[str, object]] = []
    for declared in schedule:
        stage_rank = int(declared["stage_rank"])
        stage_id = str(declared["stage_id"])
        group = plan.loc[
            (plan["stage_rank"] == stage_rank) & (plan["stage_id"] == stage_id)
        ]
        records.append(
            {
                "stage_rank": stage_rank,
                "stage_id": stage_id,
                "job_count": int(len(group)),
                "candidate_count": int(group["candidate_id"].nunique()) if len(group) else 0,
                "horizon_count": int(group["horizon_candles"].nunique()) if len(group) else 0,
                "pipeline_specification_count": int(
                    group["pipeline_spec_id"].nunique()
                )
                if len(group)
                else 0,
                "outer_fold_count": int(group["outer_fold"].nunique()) if len(group) else 0,
                "first_job_ordinal": int(group["job_ordinal"].min()) if len(group) else None,
                "last_job_ordinal": int(group["job_ordinal"].max()) if len(group) else None,
                "empty_stage_preserved": bool(len(group) == 0),
                "real_execution_authorized": False,
            }
        )
    manifest = pd.DataFrame.from_records(records)
    if list(manifest["stage_rank"]) != [1, 2, 3, 4, 5, 6]:
        raise ForecastProtocolViolation("Authorization stage manifest identity failed.")
    if int(manifest["job_count"].sum()) != 211140:
        raise ForecastProtocolViolation("Authorization stage jobs do not sum to 211140.")
    if not manifest["stage_id"].is_unique:
        raise ForecastProtocolViolation("Authorization stage identifiers are not unique.")
    return manifest
