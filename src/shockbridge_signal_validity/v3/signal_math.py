from __future__ import annotations
import numpy as np
import pandas as pd


def binary(condition: pd.Series, valid: pd.Series) -> pd.Series:
    return condition.astype(float).where(valid, np.nan)


def signed_binary(positive: pd.Series, negative: pd.Series, valid: pd.Series) -> pd.Series:
    return (positive.astype(float) - negative.astype(float)).where(valid, np.nan)


def run_length(condition: pd.Series) -> pd.Series:
    values = condition.fillna(False).to_numpy(dtype=bool)
    output = np.zeros(len(values), dtype=float)
    count = 0
    for index, active in enumerate(values):
        count = count + 1 if active else 0
        output[index] = count
    return pd.Series(output, index=condition.index, dtype=float)


def time_since(event: pd.Series) -> pd.Series:
    values = event.fillna(False).to_numpy(dtype=bool)
    output = np.full(len(values), np.nan, dtype=float)
    elapsed: int | None = None
    for index, active in enumerate(values):
        if active:
            elapsed = 0
        elif elapsed is not None:
            elapsed += 1
        if elapsed is not None:
            output[index] = float(elapsed)
    return pd.Series(output, index=event.index, dtype=float)


def wilder_rsi(close: pd.Series, lookback: int) -> pd.Series:
    delta = close.diff()
    gains, losses = delta.clip(lower=0.0), -delta.clip(upper=0.0)
    gain = gains.ewm(alpha=1.0/lookback, adjust=False, min_periods=lookback).mean()
    loss = losses.ewm(alpha=1.0/lookback, adjust=False, min_periods=lookback).mean()
    ratio = gain / loss.replace(0.0, np.nan)
    rsi = 100.0 - 100.0 / (1.0 + ratio)
    rsi = rsi.mask((loss == 0.0) & (gain > 0.0), 100.0)
    rsi = rsi.mask((gain == 0.0) & (loss > 0.0), 0.0)
    return rsi.mask((gain == 0.0) & (loss == 0.0), 50.0).astype(float)


def bollinger_frame(close: pd.Series, window: int, deviations: float) -> pd.DataFrame:
    middle = close.rolling(window, min_periods=window).mean()
    std = close.rolling(window, min_periods=window).std(ddof=0)
    half = deviations * std
    upper, lower = middle + half, middle - half
    width = (upper - lower).replace(0.0, np.nan)
    half_safe = half.replace(0.0, np.nan)
    middle_distance = (close - middle) / half_safe
    bandwidth = (upper - lower) / middle.abs().replace(0.0, np.nan)
    return pd.DataFrame({
        "middle": middle, "half_width": half, "upper": upper, "lower": lower,
        "percent_b": (close - lower) / width,
        "middle_distance": middle_distance,
        "nearest_outer_distance": np.sign(close-middle) * (np.abs(close-middle)-half) / half_safe,
        "distance_magnitude": middle_distance.abs(),
        "bandwidth": bandwidth,
        "bandwidth_change": bandwidth.diff(),
        "bandwidth_acceleration": bandwidth.diff().diff(),
    }, index=close.index)
