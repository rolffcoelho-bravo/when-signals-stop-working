from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v2.causal_features import (
    BASELINE_FEATURES,
    build_causal_base_features,
    build_registered_signal_features,
    causal_event_persistence,
    prefix_invariance_error,
)


def _aligned(rows: int = 500) -> pd.DataFrame:
    index = pd.date_range("2023-01-01", periods=rows, freq="4h", tz="UTC")
    rng = np.random.default_rng(17)
    sol = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, rows)))
    btc = 20000.0 * np.exp(np.cumsum(rng.normal(0.0, 0.006, rows)))
    return pd.DataFrame(
        {
            "sol_High": sol * 1.01,
            "sol_Low": sol * 0.99,
            "sol_Close": sol,
            "sol_Volume": rng.lognormal(10.0, 0.4, rows),
            "btc_Close": btc,
        },
        index=index,
    )


def test_causal_base_features_preserve_declared_information_set() -> None:
    features = build_causal_base_features(_aligned())
    assert tuple(features.columns) == BASELINE_FEATURES
    assert not any("future" in column or "target" in column for column in features)


def test_causal_base_features_are_prefix_invariant() -> None:
    aligned = _aligned()
    full = build_causal_base_features(aligned)
    prefix = build_causal_base_features(aligned.iloc[:350])
    pd.testing.assert_frame_equal(full.loc[prefix.index], prefix)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"signal_family": "rsi", "interpretation": "contrarian", "period": 14, "lower_threshold": 30.0, "upper_threshold": 70.0},
        {"signal_family": "rsi", "interpretation": "continuation", "period": 7, "lower_threshold": 20.0, "upper_threshold": 80.0},
        {"signal_family": "bollinger", "interpretation": "continuous", "period": 20, "standard_deviations": 2.0},
        {"signal_family": "bollinger", "interpretation": "contrarian", "period": 10, "standard_deviations": 1.5},
    ],
)
def test_registered_signal_features_are_prefix_invariant(kwargs: dict[str, object]) -> None:
    aligned = _aligned()
    close = aligned["sol_Close"]
    builder = lambda values: build_registered_signal_features(values, **kwargs)
    assert prefix_invariance_error(builder, close, 350) <= 1e-12


def test_event_persistence_uses_no_future_event() -> None:
    index = pd.date_range("2025-01-01", periods=12, freq="4h", tz="UTC")
    events = pd.Series([0, 1, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0], index=index)
    persistence = causal_event_persistence(events, max_age=4)
    assert persistence.iloc[0] == 0.0
    assert persistence.iloc[1] == 1.0
    assert persistence.iloc[2] == 0.75
    assert persistence.iloc[7] == 0.0
    assert persistence.iloc[8] == -1.0
