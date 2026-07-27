from __future__ import annotations
from typing import Any, Mapping
import numpy as np
import pandas as pd
from .signal_math import binary, run_length, signed_binary, time_since
from .signal_registry import SignalSpec


def compute_rsi_feature(close: pd.Series, rsi: pd.Series, spec: SignalSpec,
                        parameters: Mapping[str, Any]) -> pd.Series:
    lower, upper = float(parameters.get("lower", 30.0)), float(parameters.get("upper", 70.0))
    range_window = int(parameters.get("range_window", 6))
    divergence_window = int(parameters.get("divergence_window", spec.lookback_or_window))
    valid, previous = rsi.notna(), rsi.shift(1)
    above, below = rsi >= upper, rsi <= lower
    cross_up = above & (previous < upper)
    cross_down = below & (previous > lower)
    exit_low = (rsi > lower) & (previous <= lower)
    exit_high = (rsi < upper) & (previous >= upper)
    any_cross = cross_up | cross_down | exit_low | exit_high
    name = spec.interpretation
    if name == "RSI_LEVEL": return rsi
    if name == "RSI_CENTERED_SCALED": return (rsi - 50.0) / 50.0
    if name == "RSI_SLOPE": return rsi.diff()
    if name == "RSI_ACCELERATION": return rsi.diff().diff()
    if name == "RSI_ROLLING_RANGE":
        return rsi.rolling(range_window, min_periods=range_window).max() - rsi.rolling(range_window, min_periods=range_window).min()
    price_change, rsi_change = close.pct_change(divergence_window), rsi.diff(divergence_window)
    divergence_valid = valid & price_change.notna() & rsi_change.notna()
    if name == "RSI_BULLISH_DIVERGENCE": return binary((price_change < 0) & (rsi_change > 0), divergence_valid)
    if name == "RSI_BEARISH_DIVERGENCE": return binary((price_change > 0) & (rsi_change < 0), divergence_valid)
    if name == "RSI_OVERSOLD_MEAN_REVERSION": return binary(below, valid)
    if name == "RSI_OVERBOUGHT_MEAN_REVERSION": return -binary(above, valid)
    if name == "RSI_TWO_SIDED_MEAN_REVERSION": return signed_binary(below, above, valid)
    if name == "RSI_OVERBOUGHT_CONTINUATION": return binary(above, valid)
    if name == "RSI_OVERSOLD_CONTINUATION": return -binary(below, valid)
    if name == "RSI_THRESHOLD_BREAK_CONTINUATION": return signed_binary(cross_up, cross_down, valid)
    if name == "RSI_CROSS_UPPER": return binary(cross_up, valid)
    if name == "RSI_CROSS_LOWER": return -binary(cross_down, valid)
    if name == "RSI_TIME_ABOVE_UPPER": return run_length(above).where(valid, np.nan)
    if name == "RSI_TIME_BELOW_LOWER": return run_length(below).where(valid, np.nan)
    if name == "RSI_EXTREME_PERSISTENCE": return (run_length(below)-run_length(above)).where(valid, np.nan)
    if name == "RSI_TIME_SINCE_CROSSING": return time_since(any_cross).where(valid, np.nan)
    if name == "RSI_EXIT_EXTREME": return signed_binary(exit_low, exit_high, valid)
    raise ValueError(f"Unsupported RSI interpretation: {name}")
