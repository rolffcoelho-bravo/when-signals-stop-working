from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from .forecast_contract import (
    ForecastContract,
    ForecastProtocolViolation,
    require_utc_index,
)


@dataclass(frozen=True)
class LargeMoveThreshold:
    horizon_candles: int
    quantile: float
    threshold: float
    training_rows: int


def _validate_close(close: pd.Series) -> pd.Series:
    index = require_utc_index(close.index, "target timestamps")
    values = pd.to_numeric(close, errors="coerce")
    values.index = index
    if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ForecastProtocolViolation("Target close series must be finite and complete.")
    if (values <= 0.0).any():
        raise ForecastProtocolViolation("Target close series must be strictly positive.")
    return values.astype(float)


def forward_log_return(close: pd.Series, horizon_candles: int) -> pd.Series:
    if int(horizon_candles) < 1:
        raise ForecastProtocolViolation("Forecast horizon must be at least one candle.")
    values = _validate_close(close)
    horizon = int(horizon_candles)
    return np.log(values.shift(-horizon) / values).rename(
        f"future_log_return_h{horizon}"
    )


def build_development_targets(
    close: pd.Series,
    contract: ForecastContract,
    horizons: Iterable[int] | None = None,
) -> pd.DataFrame:
    values = _validate_close(close)
    development = values.loc[
        (values.index >= contract.development_start)
        & (values.index <= contract.development_end)
    ]
    contract.assert_development_only(development.index)

    requested = contract.horizons if horizons is None else tuple(
        sorted({int(value) for value in horizons})
    )
    if not requested:
        raise ForecastProtocolViolation("At least one forecast horizon is required.")
    if any(horizon not in contract.horizons for horizon in requested):
        raise ForecastProtocolViolation("Unregistered forecast horizon requested.")

    timestamp_series = pd.Series(development.index, index=development.index)
    records: list[pd.DataFrame] = []
    for horizon in requested:
        target_timestamp = timestamp_series.shift(-horizon)
        future = forward_log_return(development, horizon)
        usable = target_timestamp.notna() & target_timestamp.le(contract.development_end)
        frame = pd.DataFrame(
            {
                "timestamp": development.index,
                "target_timestamp": target_timestamp,
                "horizon_candles": int(horizon),
                "horizon_hours": int(horizon * 4),
                "future_log_return": future,
                "direction": future.gt(0.0).astype("Int64"),
            },
            index=development.index,
        ).loc[usable]
        frame["segment"] = "DEVELOPMENT"
        records.append(frame.reset_index(drop=True))

    result = pd.concat(records, ignore_index=True)
    if result.empty:
        raise ForecastProtocolViolation("Development target construction produced no rows.")
    if pd.to_datetime(result["target_timestamp"], utc=True).max() > contract.development_end:
        raise ForecastProtocolViolation("A target crossed the development boundary.")
    if result[["future_log_return", "direction"]].isna().any().any():
        raise ForecastProtocolViolation("Usable development targets contain missing values.")
    return result.sort_values(["horizon_candles", "timestamp"], kind="mergesort").reset_index(
        drop=True
    )


def fit_large_move_threshold(
    training_future_returns: pd.Series,
    horizon_candles: int,
    quantile: float = 0.90,
    minimum_rows: int = 100,
) -> LargeMoveThreshold:
    if int(horizon_candles) < 1:
        raise ForecastProtocolViolation("Large-move horizon must be positive.")
    if not 0.5 < float(quantile) < 1.0:
        raise ForecastProtocolViolation("Large-move quantile must lie in (0.5, 1.0).")
    clean = pd.to_numeric(training_future_returns, errors="coerce").dropna().abs()
    clean = clean[np.isfinite(clean.to_numpy(dtype=float))]
    if len(clean) < int(minimum_rows):
        raise ForecastProtocolViolation(
            f"Large-move threshold requires at least {minimum_rows} training rows."
        )
    return LargeMoveThreshold(
        horizon_candles=int(horizon_candles),
        quantile=float(quantile),
        threshold=float(clean.quantile(float(quantile))),
        training_rows=int(len(clean)),
    )


def apply_large_move_threshold(
    future_returns: pd.Series,
    threshold: LargeMoveThreshold,
) -> pd.Series:
    values = pd.to_numeric(future_returns, errors="coerce")
    output = values.abs().gt(float(threshold.threshold)).astype("Int64")
    return output.where(values.notna()).rename(
        f"large_move_h{threshold.horizon_candles}"
    )


def target_manifest(targets: pd.DataFrame, contract: ForecastContract) -> dict[str, object]:
    required = {
        "timestamp",
        "target_timestamp",
        "horizon_candles",
        "horizon_hours",
        "future_log_return",
        "direction",
        "segment",
    }
    missing = sorted(required.difference(targets.columns))
    if missing:
        raise ForecastProtocolViolation(
            "Target manifest input is missing columns: " + ", ".join(missing)
        )
    return {
        "schema_version": "v3.g5-target-manifest.v1",
        "segment": "DEVELOPMENT",
        "development_start_utc": contract.development_start.isoformat(),
        "development_end_utc": contract.development_end.isoformat(),
        "horizons_candles": list(contract.horizons),
        "rows": int(len(targets)),
        "rows_by_horizon": {
            str(int(horizon)): int(count)
            for horizon, count in targets.groupby("horizon_candles", sort=True).size().items()
        },
        "maximum_target_timestamp_utc": pd.to_datetime(
            targets["target_timestamp"], utc=True
        ).max().isoformat(),
        "signal_establishment_segment_accessed": False,
        "final_framework_reserve_accessed": False,
    }
