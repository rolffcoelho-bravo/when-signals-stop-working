from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


class ForecastProtocolViolation(RuntimeError):
    """Raised when Gate V3-5 execution conflicts with the frozen contract."""


class ReservedSegmentAccessError(ForecastProtocolViolation):
    """Raised when Gate V3-5 receives establishment or final-reserve rows early."""


def parse_utc(value: object, label: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ForecastProtocolViolation(f"{label} must be timezone-aware UTC.")
    return timestamp.tz_convert("UTC")


def require_utc_index(index: pd.Index, label: str = "timestamps") -> pd.DatetimeIndex:
    if not isinstance(index, pd.DatetimeIndex):
        raise ForecastProtocolViolation(f"{label} require a DatetimeIndex.")
    converted = pd.DatetimeIndex(index)
    if converted.tz is None:
        raise ForecastProtocolViolation(f"{label} must be timezone-aware UTC.")
    converted = converted.tz_convert("UTC")
    if converted.has_duplicates:
        raise ForecastProtocolViolation(f"{label} must be unique.")
    if not converted.is_monotonic_increasing:
        raise ForecastProtocolViolation(f"{label} must be chronological.")
    return converted


@dataclass(frozen=True)
class ForecastContract:
    payload: dict[str, Any]

    @classmethod
    def from_path(cls, path: str | Path) -> "ForecastContract":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ForecastProtocolViolation("Forecast contract must be a JSON object.")
        contract = cls(payload=payload)
        contract.validate()
        return contract

    def validate(self) -> None:
        expected = {
            "schema_version": "v3.matched-forecast-contract.v1",
            "gate": "V3-5",
            "status": "APPROVED_IMPLEMENTATION_STARTED_CONTRACT_FROZEN",
            "parent_lock_status_required": "IMPLEMENTATION_VALIDATED_AND_LOCKED",
        }
        for field, value in expected.items():
            if self.payload.get(field) != value:
                raise ForecastProtocolViolation(
                    f"Unexpected forecast contract field {field}: {self.payload.get(field)!r}"
                )
        partition = self.payload.get("data_partition")
        if not isinstance(partition, dict):
            raise ForecastProtocolViolation("Forecast contract has no data partition.")
        ordered = [
            self.development_start,
            self.development_end,
            self.establishment_start,
            self.establishment_end,
            self.final_reserve_start,
            self.final_reserve_end,
        ]
        if any(left >= right for left, right in zip(ordered, ordered[1:])):
            raise ForecastProtocolViolation("Forecast partition boundaries are not ordered.")
        if partition.get("v3_5_may_access_final_framework_reserve") is not False:
            raise ForecastProtocolViolation("Gate V3-5 final-reserve prohibition changed.")
        horizons = self.horizons
        if horizons != (1, 2, 3, 6, 12, 18):
            raise ForecastProtocolViolation("Forecast horizon registry changed.")
        validation = self.payload.get("validation", {})
        if validation.get("outer_development_folds") != 5:
            raise ForecastProtocolViolation("Outer-fold count changed.")
        if validation.get("inner_selection_folds") != 3:
            raise ForecastProtocolViolation("Inner-fold count changed.")
        if validation.get("shuffle") is not False:
            raise ForecastProtocolViolation("Random shuffling is prohibited.")

    @property
    def data_partition(self) -> dict[str, Any]:
        value = self.payload["data_partition"]
        if not isinstance(value, dict):
            raise ForecastProtocolViolation("Invalid data partition.")
        return value

    @property
    def development_start(self) -> pd.Timestamp:
        return parse_utc(self.data_partition["development_start_utc"], "development_start")

    @property
    def development_end(self) -> pd.Timestamp:
        return parse_utc(self.data_partition["development_end_utc"], "development_end")

    @property
    def establishment_start(self) -> pd.Timestamp:
        return parse_utc(
            self.data_partition["signal_establishment_start_utc"],
            "signal_establishment_start",
        )

    @property
    def establishment_end(self) -> pd.Timestamp:
        return parse_utc(
            self.data_partition["signal_establishment_end_utc"],
            "signal_establishment_end",
        )

    @property
    def final_reserve_start(self) -> pd.Timestamp:
        return parse_utc(
            self.data_partition["final_framework_reserve_start_utc"],
            "final_framework_reserve_start",
        )

    @property
    def final_reserve_end(self) -> pd.Timestamp:
        return parse_utc(
            self.data_partition["final_framework_reserve_end_utc"],
            "final_framework_reserve_end",
        )

    @property
    def horizons(self) -> tuple[int, ...]:
        values = self.payload.get("forecast_horizons", {}).get("candles", [])
        return tuple(sorted({int(value) for value in values}))

    @property
    def outer_folds(self) -> int:
        return int(self.payload["validation"]["outer_development_folds"])

    @property
    def inner_folds(self) -> int:
        return int(self.payload["validation"]["inner_selection_folds"])

    def classify_timestamp(self, value: object) -> str:
        timestamp = parse_utc(value, "timestamp")
        if self.development_start <= timestamp <= self.development_end:
            return "DEVELOPMENT"
        if self.establishment_start <= timestamp <= self.establishment_end:
            return "SIGNAL_ESTABLISHMENT"
        if self.final_reserve_start <= timestamp <= self.final_reserve_end:
            return "FINAL_FRAMEWORK_RESERVE"
        return "OUTSIDE_REGISTERED_PARTITION"

    def assert_development_only(self, index: pd.Index) -> pd.DatetimeIndex:
        timestamps = require_utc_index(index)
        if len(timestamps) == 0:
            raise ForecastProtocolViolation("Development execution received no rows.")
        if timestamps.min() < self.development_start:
            raise ForecastProtocolViolation("Rows precede the registered development start.")
        if timestamps.max() > self.development_end:
            segment = self.classify_timestamp(timestamps.max())
            if segment == "FINAL_FRAMEWORK_RESERVE":
                raise ReservedSegmentAccessError(
                    "PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED"
                )
            if segment == "SIGNAL_ESTABLISHMENT":
                raise ReservedSegmentAccessError(
                    "SIGNAL_ESTABLISHMENT_SEGMENT_REQUIRES_AUTHORIZATION"
                )
            raise ForecastProtocolViolation("Rows exceed the registered development end.")
        return timestamps

    def assert_no_forbidden_timestamps(self, values: Iterable[object]) -> None:
        for value in values:
            segment = self.classify_timestamp(value)
            if segment == "FINAL_FRAMEWORK_RESERVE":
                raise ReservedSegmentAccessError(
                    "PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED"
                )
            if segment == "SIGNAL_ESTABLISHMENT":
                raise ReservedSegmentAccessError(
                    "SIGNAL_ESTABLISHMENT_SEGMENT_REQUIRES_AUTHORIZATION"
                )
