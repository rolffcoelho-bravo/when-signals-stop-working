import pandas as pd
import numpy as np
from shockbridge_signal_validity.v3.signal_engine import compute_signal_feature_frame

data = pd.DataFrame({
    "timestamp": pd.date_range("2020-01-01", periods=10, tz="UTC"),
    "asset": "BTC",
    "venue": "BINANCE",
    "open": 100,
    "high": 110,
    "low": 90,
    "close": 105,
    "volume": 1000
})

context = pd.DataFrame({
    "timestamp": pd.date_range("2020-01-01", periods=10, tz="UTC"),
    "asset": "BTC",
    "venue": "BINANCE",
    "dominant_eigenvalue_share": np.linspace(0.1, 0.9, 10),
    "participation_ratio": np.linspace(0.9, 0.1, 10),
    "normalized_eigenvalue_gap": np.linspace(0.1, 0.9, 10),
})

registry = {
    "registry_version": "v3.signal-interpretation-registry.v1",
    "defaults": {
        "spectral_spike": {
            "signal_family": "SPECTRAL",
            "lookback_or_window": 1,
            "threshold_or_band_parameter": {"threshold": 0.5},
            "orientation": "LONG",
            "interpretation": "SPECTRAL_DOMINANT_EIGENVALUE_SPIKE",
            "crossing_rule": "CROSS",
            "persistence_rule": "NONE",
            "normalisation_rule": "BINARY",
            "parameter_policy": "FIXED"
        }
    },
    "signals": [
        {
            "feature_key": "spectral_spike_1",
            "template": "spectral_spike"
        }
    ]
}

result = compute_signal_feature_frame(
    frame=data,
    registry=registry,
    context_frame=context
)
print("SUCCESS!")
print(result.frame[["timestamp", "feature_key", "feature_value"]])
