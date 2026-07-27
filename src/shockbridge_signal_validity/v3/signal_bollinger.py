from __future__ import annotations
from typing import Any, Mapping
import numpy as np
import pandas as pd
from .signal_math import binary, run_length, signed_binary, time_since
from .signal_registry import SignalSpec


def compute_bollinger_feature(close: pd.Series, bands: pd.DataFrame, spec: SignalSpec,
                              parameters: Mapping[str, Any]) -> pd.Series:
    valid = bands["middle"].notna() & bands["half_width"].gt(0.0)
    above, below = close > bands["upper"], close < bands["lower"]
    outside, previous = above | below, close.shift(1)
    prev_upper, prev_lower = bands["upper"].shift(1), bands["lower"].shift(1)
    cross_upper, cross_lower = above & (previous <= prev_upper), below & (previous >= prev_lower)
    reenter_upper = (previous > prev_upper) & (close <= bands["upper"])
    reenter_lower = (previous < prev_lower) & (close >= bands["lower"])
    reentry = reenter_upper | reenter_lower
    squeeze = bands["bandwidth"] <= float(parameters.get("squeeze_threshold", 0.08))
    release = squeeze.shift(1, fill_value=False) & ~squeeze & bands["bandwidth_change"].gt(0.0)
    name = spec.interpretation
    direct = {
        "BB_PERCENT_B": "percent_b", "BB_MIDDLE_DISTANCE": "middle_distance",
        "BB_NEAREST_OUTER_DISTANCE": "nearest_outer_distance",
        "BB_DISTANCE_MAGNITUDE": "distance_magnitude", "BB_BANDWIDTH": "bandwidth",
        "BB_BANDWIDTH_CHANGE": "bandwidth_change",
        "BB_BANDWIDTH_ACCELERATION": "bandwidth_acceleration",
    }
    if name in direct: return bands[direct[name]]
    if name == "BB_UPPER_MEAN_REVERSION": return -binary(above, valid)
    if name == "BB_LOWER_MEAN_REVERSION": return binary(below, valid)
    if name == "BB_REENTRY_AFTER_OUTSIDE": return signed_binary(reenter_lower, reenter_upper, valid)
    if name == "BB_UPPER_BREAKOUT": return binary(cross_upper, valid)
    if name == "BB_LOWER_BREAKDOWN": return -binary(cross_lower, valid)
    if name == "BB_OUTSIDE_CONTINUATION": return signed_binary(above, below, valid)
    if name == "BB_SQUEEZE": return binary(squeeze, valid)
    if name == "BB_POST_SQUEEZE_EXPANSION": return binary(release, valid)
    if name == "BB_EXPANSION_PERSISTENCE": return run_length(bands["bandwidth_change"] > 0).where(valid, np.nan)
    if name == "BB_CROSS_UPPER": return binary(cross_upper, valid)
    if name == "BB_CROSS_LOWER": return -binary(cross_lower, valid)
    if name == "BB_TIME_OUTSIDE": return run_length(outside).where(valid, np.nan)
    if name == "BB_CONSECUTIVE_OUTSIDE": return (run_length(above)-run_length(below)).where(valid, np.nan)
    if name == "BB_REENTRY_TIMING": return time_since(reentry).where(valid, np.nan)
    if name == "BB_TIME_SINCE_SQUEEZE_RELEASE": return time_since(release).where(valid, np.nan)
    raise ValueError(f"Unsupported Bollinger interpretation: {name}")
