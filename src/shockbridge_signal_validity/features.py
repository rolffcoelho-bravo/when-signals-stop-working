from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd

from .indicators import (
    add_bollinger_features,
    add_bridge_features,
    add_rsi_features,
)


@dataclass(frozen=True)
class FeatureConfig:
    horizon: int = 1
    cost_bps: float = 10.0
    rsi_period: int = 14
    rsi_lower: float = 30.0
    rsi_upper: float = 70.0
    bollinger_period: int = 20
    bollinger_std: float = 2.0
    regime_lookback: int = 180


BASELINE_FEATURES = [
    "sol_ret_1",
    "sol_ret_3",
    "btc_ret_1",
    "btc_ret_3",
    "trend_12",
    "vol_20",
    "range_12",
    "volume_z",
    "regime_range",
    "regime_trend",
    "regime_stress",
]

RSI_FEATURES = BASELINE_FEATURES + [
    "rsi_norm",
    "rsi_slope",
    "rsi_reversal_score",
    "rsi_extreme",
    "rsi_x_trend",
    "rsi_x_volatility",
    "rsi_x_range",
    "rsi_x_stress",
]

BOLLINGER_FEATURES = BASELINE_FEATURES + [
    "bb_percent_b",
    "bb_bandwidth",
    "bb_reversal_score",
    "bb_extreme",
    "bb_distance_upper",
    "bb_distance_lower",
    "bb_x_trend",
    "bb_x_volatility",
    "bb_x_range",
    "bb_x_stress",
]

COMBINED_FEATURES = sorted(
    set(
        RSI_FEATURES
        + BOLLINGER_FEATURES
        + [
            "bridge_direction_agreement",
            "bridge_score_product",
            "bridge_score_difference",
        ]
    )
)


def build_feature_frame(
    sol: pd.DataFrame,
    btc: pd.DataFrame,
    config: FeatureConfig,
) -> pd.DataFrame:
    data = sol.add_prefix("sol_").join(
        btc[["Close", "Volume"]].add_prefix("btc_"),
        how="inner",
    )

    data["sol_ret_1"] = np.log(data["sol_Close"]).diff()
    data["sol_ret_3"] = np.log(data["sol_Close"]).diff(3)
    data["btc_ret_1"] = np.log(data["btc_Close"]).diff()
    data["btc_ret_3"] = np.log(data["btc_Close"]).diff(3)

    data["trend_12"] = np.log(data["sol_Close"]).diff(12) / 12.0
    data["vol_20"] = data["sol_ret_1"].rolling(20).std() * math.sqrt(20)
    data["range_12"] = (
        data["sol_High"].rolling(12).max()
        / data["sol_Low"].rolling(12).min()
        - 1.0
    )

    log_volume = np.log1p(data["sol_Volume"])
    data["volume_z"] = (
        log_volume - log_volume.rolling(30).mean()
    ) / log_volume.rolling(30).std()

    # All state thresholds are based on lagged information.
    trend_threshold = (
        data["trend_12"]
        .abs()
        .rolling(config.regime_lookback)
        .quantile(0.75)
        .shift(1)
    )
    volatility_threshold = (
        data["vol_20"]
        .rolling(config.regime_lookback)
        .quantile(0.75)
        .shift(1)
    )

    data["regime_stress"] = (
        data["vol_20"] > volatility_threshold
    ).astype(float)
    data["regime_trend"] = (
        data["regime_stress"].eq(0.0)
        & data["trend_12"].abs().gt(trend_threshold)
    ).astype(float)
    data["regime_range"] = (
        data["regime_stress"].eq(0.0)
        & data["regime_trend"].eq(0.0)
    ).astype(float)

    data = add_rsi_features(
        data,
        period=config.rsi_period,
        lower=config.rsi_lower,
        upper=config.rsi_upper,
    )
    data = add_bollinger_features(
        data,
        period=config.bollinger_period,
        standard_deviations=config.bollinger_std,
    )
    data = add_bridge_features(data)

    data["future_return"] = np.log(
        data["sol_Close"].shift(-config.horizon) / data["sol_Close"]
    )
    data["target_up"] = (data["future_return"] > 0.0).astype(int)

    return data.replace([np.inf, -np.inf], np.nan).dropna()
