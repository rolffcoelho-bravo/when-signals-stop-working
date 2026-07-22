from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder-style Relative Strength Index."""
    delta = close.diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)

    average_gain = gains.ewm(
        alpha=1.0 / period,
        adjust=False,
        min_periods=period,
    ).mean()
    average_loss = losses.ewm(
        alpha=1.0 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    relative_strength = average_gain / average_loss.replace(0.0, np.nan)
    return (100.0 - 100.0 / (1.0 + relative_strength)).clip(0.0, 100.0)


def add_rsi_features(
    frame: pd.DataFrame,
    period: int = 14,
    lower: float = 30.0,
    upper: float = 70.0,
) -> pd.DataFrame:
    data = frame.copy()
    data["rsi"] = calculate_rsi(data["sol_Close"], period)
    data["rsi_norm"] = (data["rsi"] - 50.0) / 50.0
    data["rsi_slope"] = data["rsi"].diff(3) / 100.0
    data["rsi_reversal_score"] = -data["rsi_norm"]

    crossed_below = data["rsi"].lt(lower) & data["rsi"].shift(1).ge(lower)
    crossed_above = data["rsi"].gt(upper) & data["rsi"].shift(1).le(upper)

    data["rsi_long_event"] = crossed_below.astype(float)
    data["rsi_short_event"] = crossed_above.astype(float)
    data["rsi_event_position"] = (
        data["rsi_long_event"] - data["rsi_short_event"]
    )

    data["rsi_extreme"] = (
        data["rsi"].lt(lower) | data["rsi"].gt(upper)
    ).astype(float)

    data["rsi_x_trend"] = data["rsi_norm"] * data["trend_12"]
    data["rsi_x_volatility"] = data["rsi_norm"] * data["vol_20"]
    data["rsi_x_range"] = data["rsi_norm"] * data["regime_range"]
    data["rsi_x_stress"] = data["rsi_norm"] * data["regime_stress"]
    return data


def add_bollinger_features(
    frame: pd.DataFrame,
    period: int = 20,
    standard_deviations: float = 2.0,
) -> pd.DataFrame:
    data = frame.copy()
    middle = data["sol_Close"].rolling(period).mean()
    rolling_std = data["sol_Close"].rolling(period).std(ddof=0)
    upper = middle + standard_deviations * rolling_std
    lower = middle - standard_deviations * rolling_std
    width = (upper - lower).replace(0.0, np.nan)

    data["bb_middle"] = middle
    data["bb_upper"] = upper
    data["bb_lower"] = lower
    data["bb_percent_b"] = (data["sol_Close"] - lower) / width
    data["bb_bandwidth"] = width / middle.replace(0.0, np.nan)
    data["bb_reversal_score"] = 0.5 - data["bb_percent_b"]

    crossed_below = (
        data["sol_Close"].lt(lower)
        & data["sol_Close"].shift(1).ge(lower.shift(1))
    )
    crossed_above = (
        data["sol_Close"].gt(upper)
        & data["sol_Close"].shift(1).le(upper.shift(1))
    )

    data["bb_long_event"] = crossed_below.astype(float)
    data["bb_short_event"] = crossed_above.astype(float)
    data["bb_event_position"] = data["bb_long_event"] - data["bb_short_event"]

    data["bb_extreme"] = (
        data["bb_percent_b"].lt(0.0) | data["bb_percent_b"].gt(1.0)
    ).astype(float)
    data["bb_distance_upper"] = data["sol_Close"] / upper - 1.0
    data["bb_distance_lower"] = data["sol_Close"] / lower - 1.0

    data["bb_x_trend"] = data["bb_reversal_score"] * data["trend_12"]
    data["bb_x_volatility"] = data["bb_reversal_score"] * data["vol_20"]
    data["bb_x_range"] = data["bb_reversal_score"] * data["regime_range"]
    data["bb_x_stress"] = data["bb_reversal_score"] * data["regime_stress"]
    return data


def add_bridge_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create cross-indicator features without redefining either indicator."""
    data = frame.copy()

    rsi_direction = np.sign(data["rsi_reversal_score"])
    bb_direction = np.sign(data["bb_reversal_score"])

    data["bridge_direction_agreement"] = (
        (rsi_direction == bb_direction)
        & data["rsi_extreme"].eq(1.0)
        & data["bb_extreme"].eq(1.0)
    ).astype(float)

    data["bridge_event_position"] = np.where(
        data["bridge_direction_agreement"].eq(1.0),
        rsi_direction,
        0.0,
    )
    data["bridge_score_product"] = (
        data["rsi_reversal_score"] * data["bb_reversal_score"]
    )
    data["bridge_score_difference"] = (
        data["rsi_reversal_score"] - data["bb_reversal_score"]
    )
    return data
