from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from shockbridge_signal_validity.indicators import calculate_rsi

from .contracts import ProtocolViolation


Interpretation = Literal["continuous", "contrarian", "continuation"]


def build_rsi_signal_features(
    close: pd.Series,
    period: int,
    lower: float,
    upper: float,
    interpretation: Interpretation,
) -> pd.DataFrame:
    if not 0.0 < lower < 50.0 < upper < 100.0:
        raise ProtocolViolation("RSI thresholds must bracket 50 within (0, 100).")
    rsi = calculate_rsi(close, period=int(period))
    normalized = (rsi - 50.0) / 50.0
    lower_event = rsi.lt(lower) & rsi.shift(1).ge(lower)
    upper_event = rsi.gt(upper) & rsi.shift(1).le(upper)
    contrarian_event = lower_event.astype(float) - upper_event.astype(float)
    continuation_event = -contrarian_event
    if interpretation == "continuous":
        score = normalized
        event = pd.Series(0.0, index=close.index)
    elif interpretation == "contrarian":
        score = -normalized
        event = contrarian_event
    elif interpretation == "continuation":
        score = normalized
        event = continuation_event
    else:
        raise ProtocolViolation(f"Unsupported RSI interpretation: {interpretation}")
    return pd.DataFrame(
        {
            "rsi_value": rsi,
            "rsi_normalized": normalized,
            "rsi_signal_score": score,
            "rsi_signal_event": event,
            "rsi_extreme": (rsi.lt(lower) | rsi.gt(upper)).astype(float),
        },
        index=close.index,
    )


def build_bollinger_signal_features(
    close: pd.Series,
    period: int,
    standard_deviations: float,
    interpretation: Interpretation,
) -> pd.DataFrame:
    if period < 2 or standard_deviations <= 0.0:
        raise ProtocolViolation("Invalid Bollinger specification.")
    middle = close.rolling(int(period)).mean()
    rolling_std = close.rolling(int(period)).std(ddof=0)
    upper = middle + float(standard_deviations) * rolling_std
    lower = middle - float(standard_deviations) * rolling_std
    width = (upper - lower).replace(0.0, np.nan)
    percent_b = (close - lower) / width
    centered = percent_b - 0.5
    lower_event = close.lt(lower) & close.shift(1).ge(lower.shift(1))
    upper_event = close.gt(upper) & close.shift(1).le(upper.shift(1))
    contrarian_event = lower_event.astype(float) - upper_event.astype(float)
    continuation_event = -contrarian_event
    if interpretation == "continuous":
        score = centered
        event = pd.Series(0.0, index=close.index)
    elif interpretation == "contrarian":
        score = -centered
        event = contrarian_event
    elif interpretation == "continuation":
        score = centered
        event = continuation_event
    else:
        raise ProtocolViolation(
            f"Unsupported Bollinger interpretation: {interpretation}"
        )
    return pd.DataFrame(
        {
            "bb_middle": middle,
            "bb_upper": upper,
            "bb_lower": lower,
            "bb_percent_b": percent_b,
            "bb_bandwidth": width / middle.replace(0.0, np.nan),
            "bb_signal_score": score,
            "bb_signal_event": event,
            "bb_extreme": (percent_b.lt(0.0) | percent_b.gt(1.0)).astype(float),
        },
        index=close.index,
    )


def add_soft_state_interactions(
    signal: pd.Series,
    state_probabilities: pd.DataFrame,
) -> pd.DataFrame:
    required = ["state_p_range", "state_p_trend", "state_p_stress"]
    missing = [column for column in required if column not in state_probabilities]
    if missing:
        raise ProtocolViolation(
            "Missing filtered state probabilities: " + ", ".join(missing)
        )
    probabilities = state_probabilities[required].astype(float)
    row_sums = probabilities.sum(axis=1)
    if ((row_sums - 1.0).abs().dropna() > 1e-6).any():
        raise ProtocolViolation("Filtered state probabilities must sum to one.")
    aligned_signal = signal.reindex(probabilities.index)
    return pd.DataFrame(
        {
            "signal_x_range": aligned_signal * probabilities["state_p_range"],
            "signal_x_trend": aligned_signal * probabilities["state_p_trend"],
            "signal_x_stress": aligned_signal * probabilities["state_p_stress"],
        },
        index=probabilities.index,
    )
