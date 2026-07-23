from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

SCHEMA_VERSION = "v3.canonical-market.v1"
KEY_COLUMNS = ("timestamp", "asset", "venue")
REQUIRED_COLUMNS = (
    "timestamp",
    "asset",
    "venue",
    "open",
    "high",
    "low",
    "close",
    "volume",
)
OPTIONAL_COLUMNS = (
    "benchmark_asset_returns",
    "funding_rate",
    "open_interest",
    "long_liquidations",
    "short_liquidations",
    "bid_ask_spread",
    "order_book_depth",
    "order_book_imbalance",
    "exchange_inflows",
    "exchange_outflows",
    "stablecoin_flow",
    "cross_venue_price_dispersion",
    "realised_volatility",
)
NUMERIC_COLUMNS = tuple(
    column for column in REQUIRED_COLUMNS + OPTIONAL_COLUMNS if column not in KEY_COLUMNS
)


class CanonicalDataError(ValueError):
    """Raised when market data cannot satisfy the Version 3 contract."""


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: str
    message: str
    field: str | None = None
    rows: int | None = None


@dataclass(frozen=True)
class ValidationReport:
    schema_version: str
    valid: bool
    issues: tuple[ValidationIssue, ...] = ()
    metrics: Mapping[str, Any] = field(default_factory=dict)

    @property
    def critical_count(self) -> int:
        return sum(issue.severity == "CRITICAL" for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(issue.severity == "WARNING" for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "valid": self.valid,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "issues": [asdict(issue) for issue in self.issues],
            "metrics": dict(self.metrics),
        }


@dataclass(frozen=True)
class SourceManifest:
    adapter_id: str
    source_uri: str
    source_format: str
    source_sha256: str
    config_sha256: str
    schema_version: str
    loaded_rows: int
    data_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def manifest_sha256(self) -> str:
        payload = json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        return sha256(payload).hexdigest()


@dataclass(frozen=True)
class CanonicalMarketFrame:
    frame: pd.DataFrame
    validation: ValidationReport
    manifest: SourceManifest

    @property
    def data_sha256(self) -> str:
        return self.manifest.data_sha256

    def require_valid(self) -> "CanonicalMarketFrame":
        if not self.validation.valid:
            details = "; ".join(
                f"{issue.code}: {issue.message}"
                for issue in self.validation.issues
                if issue.severity == "CRITICAL"
            )
            raise CanonicalDataError(details or "Canonical data validation failed.")
        return self


def stable_mapping_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=True
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def file_sha256(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stable_scalar(value: Any) -> str:
    if pd.isna(value):
        return "<NA>"
    if isinstance(value, pd.Timestamp):
        return value.tz_convert("UTC").isoformat().replace("+00:00", "Z")
    if isinstance(value, (float, np.floating)):
        return format(float(value), ".17g")
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def stable_frame_hash(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    digest = sha256()
    digest.update(("\x1f".join(columns) + "\x1e").encode("utf-8"))
    for row in frame.itertuples(index=False, name=None):
        digest.update(
            ("\x1f".join(_stable_scalar(value) for value in row) + "\x1e").encode(
                "utf-8"
            )
        )
    return digest.hexdigest()


def _parse_timestamp(
    values: pd.Series,
    *,
    timezone: str,
    timestamp_unit: str | None,
) -> pd.Series:
    if timestamp_unit:
        parsed = pd.to_datetime(values, unit=timestamp_unit, utc=True, errors="coerce")
    else:
        parsed = pd.to_datetime(values, errors="coerce")
        if isinstance(parsed.dtype, pd.DatetimeTZDtype):
            parsed = parsed.dt.tz_convert("UTC")
        else:
            parsed = (
                parsed.dt.tz_localize(
                    timezone, ambiguous="NaT", nonexistent="NaT"
                ).dt.tz_convert("UTC")
            )
    return parsed


def canonicalize_market_frame(
    frame: pd.DataFrame,
    *,
    timezone: str = "UTC",
    timestamp_unit: str | None = None,
) -> tuple[pd.DataFrame, ValidationReport]:
    data = frame.copy()
    issues: list[ValidationIssue] = []

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing_columns:
        issues.append(
            ValidationIssue(
                code="MISSING_REQUIRED_COLUMNS",
                severity="CRITICAL",
                message=f"Missing required columns: {missing_columns}",
                rows=len(data),
            )
        )
        return data, ValidationReport(
            schema_version=SCHEMA_VERSION,
            valid=False,
            issues=tuple(issues),
            metrics={"rows": int(len(data))},
        )

    extra_columns = [
        column
        for column in data.columns
        if column not in REQUIRED_COLUMNS and column not in OPTIONAL_COLUMNS
    ]
    if extra_columns:
        issues.append(
            ValidationIssue(
                code="UNREGISTERED_COLUMNS_DROPPED",
                severity="WARNING",
                message=f"Dropped unregistered columns: {extra_columns}",
            )
        )

    ordered_columns = list(REQUIRED_COLUMNS) + [
        column for column in OPTIONAL_COLUMNS if column in data.columns
    ]
    data = data.loc[:, ordered_columns]
    data["timestamp"] = _parse_timestamp(
        data["timestamp"], timezone=timezone, timestamp_unit=timestamp_unit
    )
    invalid_timestamps = int(data["timestamp"].isna().sum())
    if invalid_timestamps:
        issues.append(
            ValidationIssue(
                code="INVALID_TIMESTAMP",
                severity="CRITICAL",
                message="Timestamp values could not be converted to UTC.",
                field="timestamp",
                rows=invalid_timestamps,
            )
        )

    for column in ("asset", "venue"):
        data[column] = data[column].astype("string").str.strip()
        missing_keys = int(data[column].isna().sum() + (data[column] == "").sum())
        if missing_keys:
            issues.append(
                ValidationIssue(
                    code="MISSING_KEY_VALUE",
                    severity="CRITICAL",
                    message=f"Missing canonical key values in {column}.",
                    field=column,
                    rows=missing_keys,
                )
            )

    for column in NUMERIC_COLUMNS:
        if column not in data.columns:
            continue
        data[column] = pd.to_numeric(data[column], errors="coerce")

    required_numeric = ["open", "high", "low", "close", "volume"]
    for column in required_numeric:
        missing_numeric = int(data[column].isna().sum())
        if missing_numeric:
            issues.append(
                ValidationIssue(
                    code="MISSING_REQUIRED_NUMERIC",
                    severity="CRITICAL",
                    message=f"Missing or non-numeric values in {column}.",
                    field=column,
                    rows=missing_numeric,
                )
            )

    nonpositive_prices = int(
        (data[["open", "high", "low", "close"]] <= 0).any(axis=1).sum()
    )
    if nonpositive_prices:
        issues.append(
            ValidationIssue(
                code="NONPOSITIVE_PRICE",
                severity="CRITICAL",
                message="OHLC prices must be strictly positive.",
                rows=nonpositive_prices,
            )
        )

    negative_volume = int((data["volume"] < 0).sum())
    if negative_volume:
        issues.append(
            ValidationIssue(
                code="NEGATIVE_VOLUME",
                severity="CRITICAL",
                message="Volume must be non-negative.",
                field="volume",
                rows=negative_volume,
            )
        )

    invalid_bounds = int(
        (
            (data["low"] > data["high"])
            | (data["open"] < data["low"])
            | (data["open"] > data["high"])
            | (data["close"] < data["low"])
            | (data["close"] > data["high"])
        ).sum()
    )
    if invalid_bounds:
        issues.append(
            ValidationIssue(
                code="INVALID_OHLC_BOUNDS",
                severity="CRITICAL",
                message="OHLC values violate low/high bounds.",
                rows=invalid_bounds,
            )
        )

    duplicate_rows = int(data.duplicated(list(KEY_COLUMNS), keep=False).sum())
    if duplicate_rows:
        issues.append(
            ValidationIssue(
                code="DUPLICATE_CANONICAL_KEY",
                severity="CRITICAL",
                message="Duplicate timestamp, asset, venue keys are prohibited.",
                rows=duplicate_rows,
            )
        )

    was_sorted = data[list(KEY_COLUMNS)].reset_index(drop=True).equals(
        data.sort_values(list(KEY_COLUMNS), kind="mergesort")[
            list(KEY_COLUMNS)
        ].reset_index(drop=True)
    )
    if not was_sorted:
        issues.append(
            ValidationIssue(
                code="SOURCE_ORDER_NORMALIZED",
                severity="WARNING",
                message=(
                    "Rows were deterministically sorted by timestamp, asset, and venue."
                ),
            )
        )

    data = data.sort_values(list(KEY_COLUMNS), kind="mergesort").reset_index(drop=True)

    interval_gap_count = 0
    inferred_intervals: dict[str, str] = {}
    for (asset, venue), group in data.groupby(["asset", "venue"], sort=True):
        differences = group["timestamp"].diff().dropna()
        if differences.empty:
            continue
        mode = differences.mode()
        expected = mode.iloc[0] if not mode.empty else differences.median()
        inferred_intervals[f"{asset}@{venue}"] = str(expected)
        interval_gap_count += int((differences > expected * 1.5).sum())
    if interval_gap_count:
        issues.append(
            ValidationIssue(
                code="INTERVAL_GAPS_DETECTED",
                severity="WARNING",
                message="One or more asset/venue series contain interval gaps.",
                rows=interval_gap_count,
            )
        )

    panel_alignment_gaps = 0
    if data[["asset", "venue"]].drop_duplicates().shape[0] > 1:
        expected_panel = int(data[["asset", "venue"]].drop_duplicates().shape[0])
        counts = data.groupby("timestamp").size()
        panel_alignment_gaps = int((expected_panel - counts).clip(lower=0).sum())
        if panel_alignment_gaps:
            issues.append(
                ValidationIssue(
                    code="PANEL_ALIGNMENT_GAPS",
                    severity="WARNING",
                    message="Not every timestamp contains the full declared panel.",
                    rows=panel_alignment_gaps,
                )
            )

    critical_count = sum(issue.severity == "CRITICAL" for issue in issues)
    metrics = {
        "rows": int(len(data)),
        "assets": int(data["asset"].nunique(dropna=True)),
        "venues": int(data["venue"].nunique(dropna=True)),
        "start_timestamp": (
            None
            if data["timestamp"].isna().all()
            else data["timestamp"].min().isoformat()
        ),
        "end_timestamp": (
            None
            if data["timestamp"].isna().all()
            else data["timestamp"].max().isoformat()
        ),
        "interval_gap_count": interval_gap_count,
        "panel_alignment_gap_count": panel_alignment_gaps,
        "inferred_intervals": inferred_intervals,
        "missingness": {
            column: int(data[column].isna().sum()) for column in data.columns
        },
    }
    return data, ValidationReport(
        schema_version=SCHEMA_VERSION,
        valid=critical_count == 0,
        issues=tuple(issues),
        metrics=metrics,
    )


def select_registered_columns(columns: Iterable[str]) -> tuple[str, ...]:
    selected = tuple(columns)
    unregistered = [
        column
        for column in selected
        if column not in REQUIRED_COLUMNS and column not in OPTIONAL_COLUMNS
    ]
    if unregistered:
        raise CanonicalDataError(f"Unregistered canonical columns: {unregistered}")
    return selected
