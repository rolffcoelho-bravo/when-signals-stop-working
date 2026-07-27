from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

import numpy as np
import pandas as pd

from .forecast_contract import ForecastContract, ForecastProtocolViolation, require_utc_index


@dataclass(frozen=True)
class MatchedPair:
    benchmark: pd.DataFrame
    candidate: pd.DataFrame
    target: pd.Series
    candidate_id: str
    horizon_candles: int
    row_contract_id: str

    @property
    def rows(self) -> int:
        return int(len(self.target))


def _numeric_frame(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    index = require_utc_index(frame.index, f"{label} timestamps")
    if frame.columns.duplicated().any():
        raise ForecastProtocolViolation(f"{label} columns must be unique.")
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    numeric.index = index
    finite_or_missing = numeric.isna() | np.isfinite(numeric.to_numpy(dtype=float))
    if not np.asarray(finite_or_missing).all():
        raise ForecastProtocolViolation(f"{label} contains infinite values.")
    return numeric


def build_matched_pair(
    *,
    benchmark_features: pd.DataFrame,
    candidate_features: pd.DataFrame,
    target: pd.Series,
    candidate_id: str,
    horizon_candles: int,
    contract: ForecastContract,
) -> MatchedPair:
    if int(horizon_candles) not in contract.horizons:
        raise ForecastProtocolViolation("Matched pair uses an unregistered horizon.")
    if not str(candidate_id).startswith("v3g5:"):
        raise ForecastProtocolViolation("Matched pair candidate identifier is malformed.")

    benchmark = _numeric_frame(benchmark_features, "benchmark feature")
    candidate_block = _numeric_frame(candidate_features, "candidate feature")
    overlap = sorted(set(benchmark.columns).intersection(candidate_block.columns))
    if overlap:
        raise ForecastProtocolViolation(
            "Candidate columns duplicate benchmark information: " + ", ".join(overlap)
        )
    target_index = require_utc_index(target.index, "target timestamps")
    target_values = pd.to_numeric(target, errors="coerce")
    target_values.index = target_index

    common = benchmark.index.intersection(candidate_block.index).intersection(target_values.index)
    common = common.sort_values()
    contract.assert_development_only(common)
    joined = pd.concat(
        [
            benchmark.reindex(common).add_prefix("benchmark::"),
            candidate_block.reindex(common).add_prefix("candidate::"),
            target_values.reindex(common).rename("target"),
        ],
        axis=1,
    )
    complete = joined.dropna(axis=0, how="any")
    if complete.empty:
        raise ForecastProtocolViolation("Matched row intersection contains no complete rows.")

    benchmark_columns = [column for column in complete if column.startswith("benchmark::")]
    candidate_columns = [column for column in complete if column.startswith("candidate::")]
    benchmark_matched = complete[benchmark_columns].copy()
    benchmark_matched.columns = [column.split("::", 1)[1] for column in benchmark_columns]
    signal_matched = complete[candidate_columns].copy()
    signal_matched.columns = [column.split("::", 1)[1] for column in candidate_columns]
    candidate_matched = pd.concat([benchmark_matched, signal_matched], axis=1)
    target_matched = complete["target"].copy()

    if not benchmark_matched.index.equals(candidate_matched.index):
        raise ForecastProtocolViolation("Benchmark and candidate row identities differ.")
    if not benchmark_matched.index.equals(target_matched.index):
        raise ForecastProtocolViolation("Matched target row identity differs.")
    if not set(benchmark_matched.columns).issubset(candidate_matched.columns):
        raise ForecastProtocolViolation("Candidate does not contain the complete benchmark.")

    row_material = "|".join(timestamp.isoformat() for timestamp in target_matched.index)
    row_contract_id = sha256(
        (
            f"{candidate_id}|h={int(horizon_candles)}|"
            f"benchmark={','.join(benchmark_matched.columns)}|"
            f"candidate={','.join(signal_matched.columns)}|rows={row_material}"
        ).encode("utf-8")
    ).hexdigest()

    return MatchedPair(
        benchmark=benchmark_matched,
        candidate=candidate_matched,
        target=target_matched,
        candidate_id=str(candidate_id),
        horizon_candles=int(horizon_candles),
        row_contract_id=row_contract_id,
    )


def matched_pair_manifest(pair: MatchedPair) -> dict[str, object]:
    signal_columns = [
        column for column in pair.candidate.columns if column not in pair.benchmark.columns
    ]
    return {
        "schema_version": "v3.g5-matched-row-contract.v1",
        "candidate_id": pair.candidate_id,
        "horizon_candles": pair.horizon_candles,
        "horizon_hours": pair.horizon_candles * 4,
        "row_contract_id": pair.row_contract_id,
        "matched_rows": pair.rows,
        "start_utc": pair.target.index.min().isoformat(),
        "end_utc": pair.target.index.max().isoformat(),
        "benchmark_columns": list(pair.benchmark.columns),
        "candidate_only_columns": signal_columns,
        "identical_training_rows_required": True,
        "identical_test_rows_required": True,
        "candidate_definition": "BENCHMARK_PLUS_REGISTERED_SIGNAL_INFORMATION_ONLY",
        "signal_establishment_segment_accessed": False,
        "final_framework_reserve_accessed": False,
    }


def assert_pair_identity(pairs: Iterable[MatchedPair]) -> None:
    for pair in pairs:
        if not pair.benchmark.index.equals(pair.candidate.index):
            raise ForecastProtocolViolation(
                f"Matched row drift detected for {pair.candidate_id}."
            )
        if not pair.benchmark.index.equals(pair.target.index):
            raise ForecastProtocolViolation(
                f"Matched target drift detected for {pair.candidate_id}."
            )
