from __future__ import annotations
from typing import Any, Mapping

import numpy as np
import pandas as pd

from .signal_math import binary
from .signal_registry import SignalSpec

def compute_fibonacci_feature(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    spec: SignalSpec,
    parameters: Mapping[str, Any],
) -> pd.Series:
    """
    Computes a Fibonacci retracement signal.
    """
    name = spec.interpretation
    lookback = spec.lookback_or_window
    level = float(parameters.get("retracement_level", 0.618))

    rolling_high = high.rolling(lookback, min_periods=lookback).max()
    rolling_low = low.rolling(lookback, min_periods=lookback).min()
    
    range_dist = rolling_high - rolling_low
    relative_pos = (close - rolling_low) / range_dist.replace(0, np.nan)
    
    if name == "FIBONACCI_DISTANCE":
        return relative_pos - level
        
    if name == "FIBONACCI_CROSS_ABOVE":
        valid = relative_pos.notna()
        previous = relative_pos.shift(1)
        cross_up = (relative_pos > level) & (previous <= level)
        return binary(cross_up, valid)
        
    if name == "FIBONACCI_CROSS_BELOW":
        valid = relative_pos.notna()
        previous = relative_pos.shift(1)
        cross_down = (relative_pos < level) & (previous >= level)
        return binary(cross_down, valid)

    return pd.Series(np.nan, index=close.index, dtype=float)
