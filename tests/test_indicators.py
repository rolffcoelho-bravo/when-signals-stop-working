from __future__ import annotations

import numpy as np
import pandas as pd

from shockbridge_signal_validity.features import FeatureConfig, build_feature_frame


def make_prices(seed: int, observations: int = 1000) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    index = pd.date_range(
        "2022-01-01",
        periods=observations,
        freq="4h",
        tz="UTC",
    )
    returns = rng.normal(0.0002, 0.02, observations)
    close = 100.0 * np.exp(np.cumsum(returns))
    open_price = close * np.exp(rng.normal(0.0, 0.002, observations))
    high = np.maximum(open_price, close) * (
        1.0 + rng.uniform(0.001, 0.015, observations)
    )
    low = np.minimum(open_price, close) * (
        1.0 - rng.uniform(0.001, 0.015, observations)
    )
    volume = rng.lognormal(14.0, 0.35, observations)
    return pd.DataFrame(
        {
            "Open": open_price,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=index,
    )


def test_both_indicator_families_are_built() -> None:
    data = build_feature_frame(
        make_prices(1),
        make_prices(2),
        FeatureConfig(),
    )

    required = {
        "rsi",
        "rsi_event_position",
        "bb_percent_b",
        "bb_bandwidth",
        "bb_event_position",
        "bridge_direction_agreement",
        "future_return",
        "target_up",
    }
    assert required.issubset(data.columns)
    assert len(data) > 500
    assert data.index.is_monotonic_increasing
