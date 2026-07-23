from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from .contracts import ProtocolViolation


@dataclass(frozen=True)
class LargeMoveThreshold:
    horizon_candles: int
    quantile: float
    threshold: float
    training_rows: int


def _validate_close(close: pd.Series) -> pd.Series:
    if not isinstance(close.index, pd.DatetimeIndex):
        raise ProtocolViolation("Target construction requires a DatetimeIndex.")
    if close.index.tz is None:
        raise ProtocolViolation("Target timestamps must be timezone-aware UTC.")
    values = pd.to_numeric(close, errors="coerce")
    if values.isna().any() or (values <= 0.0).any():
        raise ProtocolViolation("Target close series must be positive and complete.")
    return values.astype(float)


def forward_log_return(close: pd.Series, horizon_candles: int) -> pd.Series:
    if horizon_candles < 1:
        raise ProtocolViolation("Forecast horizon must be at least one candle.")
    values = _validate_close(close)
    return np.log(values.shift(-horizon_candles) / values).rename(
        f"future_log_return_h{horizon_candles}"
    )


def build_development_targets(
    close: pd.Series,
    horizons: Iterable[int],
    development_end: pd.Timestamp,
) -> pd.DataFrame:
    values = _validate_close(close)
    end = pd.Timestamp(development_end)
    if end.tzinfo is None:
        raise ProtocolViolation("Development boundary must be timezone-aware UTC.")
    result = pd.DataFrame(index=values.index)
    for horizon in sorted({int(value) for value in horizons}):
        future = forward_log_return(values, horizon)
        target_timestamp = values.index.to_series().shift(-horizon)
        usable = target_timestamp.le(end)
        result[f"target_timestamp_h{horizon}"] = target_timestamp.where(usable)
        result[f"future_log_return_h{horizon}"] = future.where(usable)
        result[f"direction_h{horizon}"] = (
            future.gt(0.0).astype("Int64").where(usable)
        )
    return result.loc[result.index <= end]


def fit_large_move_threshold(
    future_returns: pd.Series,
    horizon_candles: int,
    quantile: float = 0.90,
) -> LargeMoveThreshold:
    if not 0.5 < quantile < 1.0:
        raise ProtocolViolation("Large-move quantile must lie between 0.5 and 1.0.")
    clean = pd.to_numeric(future_returns, errors="coerce").dropna().abs()
    if len(clean) < 100:
        raise ProtocolViolation(
            "At least 100 training observations are required for a large-move threshold."
        )
    return LargeMoveThreshold(
        horizon_candles=int(horizon_candles),
        quantile=float(quantile),
        threshold=float(clean.quantile(quantile)),
        training_rows=int(len(clean)),
    )


def apply_large_move_threshold(
    future_returns: pd.Series,
    threshold: LargeMoveThreshold,
) -> pd.Series:
    clean = pd.to_numeric(future_returns, errors="coerce")
    return clean.abs().gt(threshold.threshold).astype("Int64").where(clean.notna())
