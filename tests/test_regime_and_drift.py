from __future__ import annotations

import numpy as np
import pandas as pd

from shockbridge_signal_validity.regimes import FilteredRegimeModel
from shockbridge_signal_validity.structural_change import (
    add_structural_change_monitor,
)

from test_indicators import make_prices
from shockbridge_signal_validity.features import FeatureConfig, build_feature_frame


def test_filtered_regime_probabilities_sum_to_one() -> None:
    data = build_feature_frame(
        make_prices(10, 1400),
        make_prices(11, 1400),
        FeatureConfig(),
    )
    train = data.iloc[:800]
    test = data.iloc[800:900]

    output = FilteredRegimeModel().fit(train).filter(test)
    probabilities = output[
        ["latent_prob_range", "latent_prob_trend", "latent_prob_stress"]
    ].sum(axis=1)

    assert np.allclose(probabilities.to_numpy(), 1.0)
    assert set(output["latent_regime"]).issubset({"range", "trend", "stress"})


def test_online_cusum_detects_sustained_deterioration() -> None:
    index = pd.date_range("2024-01-01", periods=400, freq="4h", tz="UTC")
    frame = pd.DataFrame(
        {
            "incremental_log_loss": np.r_[
                np.full(200, 0.02),
                np.full(200, -0.08),
            ],
            "incremental_net_edge": np.r_[
                np.full(200, 0.001),
                np.full(200, -0.004),
            ],
        },
        index=index,
    )

    monitored = add_structural_change_monitor(
        frame,
        calibration_window=120,
    )
    assert bool(monitored["structural_change_alarm"].iloc[-1])
