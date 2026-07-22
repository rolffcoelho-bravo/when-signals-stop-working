from __future__ import annotations

from collections.abc import Callable
import math

import numpy as np
import pandas as pd

from .contracts import ProtocolViolation
from .signals import build_bollinger_signal_features, build_rsi_signal_features


BASELINE_FEATURES = (
    "sol_ret_1",
    "sol_ret_3",
    "btc_ret_1",
    "btc_ret_3",
    "trend_12",
    "vol_20",
    "range_12",
    "volume_z",
)

STATE_INPUT_FEATURES = ("sol_ret_1", "vol_20", "trend_12")

_REQUIRED_ALIGNED_COLUMNS = (
    "sol_High",
    "sol_Low",
    "sol_Close",
    "sol_Volume",
    "btc_Close",
)


def _require_utc_index(frame: pd.DataFrame | pd.Series) -> pd.DatetimeIndex:
    index = frame.index
    if not isinstance(index, pd.DatetimeIndex):
        raise ProtocolViolation("Causal feature construction requires a DatetimeIndex.")
    if index.tz is None:
        raise ProtocolViolation("Causal feature timestamps must be timezone-aware UTC.")
    converted = pd.DatetimeIndex(index).tz_convert("UTC")
    if not converted.is_monotonic_increasing or converted.has_duplicates:
        raise ProtocolViolation("Feature timestamps must be unique and chronological.")
    return converted


def build_causal_base_features(aligned: pd.DataFrame) -> pd.DataFrame:
    """Build the frozen benchmark information set using trailing data only."""
    index = _require_utc_index(aligned)
    missing = [column for column in _REQUIRED_ALIGNED_COLUMNS if column not in aligned]
    if missing:
        raise ProtocolViolation("Aligned development data are missing: " + ", ".join(missing))

    data = aligned.copy()
    data.index = index
    numeric = data[list(_REQUIRED_ALIGNED_COLUMNS)].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        raise ProtocolViolation("Aligned OHLCV inputs must be complete and numeric.")
    if (numeric[["sol_High", "sol_Low", "sol_Close", "btc_Close"]] <= 0.0).any().any():
        raise ProtocolViolation("Price inputs must be strictly positive.")
    if (numeric["sol_Volume"] < 0.0).any():
        raise ProtocolViolation("Volume cannot be negative.")

    features = pd.DataFrame(index=index)
    sol_log = np.log(numeric["sol_Close"])
    btc_log = np.log(numeric["btc_Close"])
    features["sol_ret_1"] = sol_log.diff(1)
    features["sol_ret_3"] = sol_log.diff(3)
    features["btc_ret_1"] = btc_log.diff(1)
    features["btc_ret_3"] = btc_log.diff(3)
    features["trend_12"] = sol_log.diff(12) / 12.0
    features["vol_20"] = features["sol_ret_1"].rolling(20, min_periods=20).std(ddof=1) * math.sqrt(20.0)
    features["range_12"] = (
        numeric["sol_High"].rolling(12, min_periods=12).max()
        / numeric["sol_Low"].rolling(12, min_periods=12).min()
        - 1.0
    )
    log_volume = np.log1p(numeric["sol_Volume"])
    rolling_mean = log_volume.rolling(30, min_periods=30).mean()
    rolling_std = log_volume.rolling(30, min_periods=30).std(ddof=1)
    features["volume_z"] = (log_volume - rolling_mean) / rolling_std.replace(0.0, np.nan)
    return features.replace([np.inf, -np.inf], np.nan)


def causal_event_persistence(events: pd.Series, max_age: int = 6) -> pd.Series:
    """Return a bounded signed decay after each registered event.

    The event candle receives +/-1. The magnitude then decays linearly to zero
    over the next ``max_age`` candles. No future event contributes to an earlier
    observation.
    """
    if max_age < 1:
        raise ProtocolViolation("Event-persistence age must be positive.")
    index = _require_utc_index(events)
    values = pd.to_numeric(events, errors="coerce").fillna(0.0).to_numpy(dtype=float)
    output = np.zeros(len(values), dtype=float)
    active_sign = 0.0
    age = max_age + 1
    for position, value in enumerate(values):
        if value != 0.0:
            active_sign = float(np.sign(value))
            age = 0
        if active_sign != 0.0 and age < max_age:
            output[position] = active_sign * (1.0 - age / max_age)
            age += 1
        else:
            output[position] = 0.0
            if age >= max_age:
                active_sign = 0.0
    return pd.Series(output, index=index, name="event_persistence")


def build_registered_signal_features(
    close: pd.Series,
    signal_family: str,
    interpretation: str,
    period: int,
    lower_threshold: float | None = None,
    upper_threshold: float | None = None,
    standard_deviations: float | None = None,
    event_persistence_candles: int = 6,
) -> pd.DataFrame:
    """Build one registered signal-information block without future inputs."""
    index = _require_utc_index(close)
    values = pd.to_numeric(close, errors="coerce")
    if values.isna().any() or (values <= 0.0).any():
        raise ProtocolViolation("Signal close series must be positive and complete.")
    values.index = index

    if signal_family == "rsi":
        if lower_threshold is None or upper_threshold is None:
            raise ProtocolViolation("RSI thresholds are required.")
        frame = build_rsi_signal_features(
            values,
            int(period),
            float(lower_threshold),
            float(upper_threshold),
            interpretation,  # type: ignore[arg-type]
        )
        frame["rsi_slope_1"] = frame["rsi_value"].diff(1) / 100.0
        frame["rsi_distance_50"] = (frame["rsi_value"] - 50.0) / 50.0
        frame["rsi_distance_lower"] = (frame["rsi_value"] - float(lower_threshold)) / 100.0
        frame["rsi_distance_upper"] = (float(upper_threshold) - frame["rsi_value"]) / 100.0
        frame["rsi_threshold_distance"] = pd.concat(
            [frame["rsi_distance_lower"].abs(), frame["rsi_distance_upper"].abs()],
            axis=1,
        ).min(axis=1)
        frame["rsi_event_persistence"] = causal_event_persistence(
            frame["rsi_signal_event"], max_age=event_persistence_candles
        )
        return frame.replace([np.inf, -np.inf], np.nan)

    if signal_family == "bollinger":
        if standard_deviations is None:
            raise ProtocolViolation("Bollinger standard-deviation multiplier is required.")
        frame = build_bollinger_signal_features(
            values,
            int(period),
            float(standard_deviations),
            interpretation,  # type: ignore[arg-type]
        )
        rolling_std = values.rolling(int(period), min_periods=int(period)).std(ddof=0)
        denominator = rolling_std.replace(0.0, np.nan)
        frame["bb_distance_upper"] = (values - frame["bb_upper"]) / denominator
        frame["bb_distance_lower"] = (values - frame["bb_lower"]) / denominator
        frame["bb_bandwidth_change_1"] = frame["bb_bandwidth"].diff(1)
        frame["bb_event_persistence"] = causal_event_persistence(
            frame["bb_signal_event"], max_age=event_persistence_candles
        )
        return frame.replace([np.inf, -np.inf], np.nan)

    raise ProtocolViolation(f"Unsupported registered signal family: {signal_family}")


def prefix_invariance_error(
    builder: Callable[[pd.Series], pd.DataFrame],
    close: pd.Series,
    cutoff_position: int,
) -> float:
    """Measure whether adding later observations changes earlier features."""
    if cutoff_position < 1 or cutoff_position >= len(close):
        raise ProtocolViolation("Prefix-invariance cutoff is outside the series.")
    full = builder(close)
    prefix_close = close.iloc[: cutoff_position + 1]
    prefix = builder(prefix_close)
    shared = full.loc[prefix.index, prefix.columns]
    differences: list[float] = []
    for column in prefix.columns:
        left = pd.to_numeric(shared[column], errors="coerce")
        right = pd.to_numeric(prefix[column], errors="coerce")
        mask = left.notna() & right.notna()
        if mask.any():
            differences.append(float((left[mask] - right[mask]).abs().max()))
        mismatch = left.isna() ^ right.isna()
        if mismatch.any():
            return float("inf")
    return max(differences, default=0.0)


def feature_dictionary() -> pd.DataFrame:
    records = [
        ("benchmark", "sol_ret_1", "One-candle SOL log return", "trailing", True),
        ("benchmark", "sol_ret_3", "Three-candle SOL log return", "trailing", False),
        ("benchmark", "btc_ret_1", "One-candle BTC log return", "trailing", False),
        ("benchmark", "btc_ret_3", "Three-candle BTC log return", "trailing", False),
        ("benchmark", "trend_12", "Twelve-candle SOL log trend divided by twelve", "trailing", True),
        ("benchmark", "vol_20", "Annualisation-free twenty-candle realised scale", "trailing", True),
        ("benchmark", "range_12", "Trailing twelve-candle high-low range", "trailing", False),
        ("benchmark", "volume_z", "Trailing thirty-candle log-volume standard score", "trailing", False),
        ("rsi", "rsi_value", "Registered RSI level", "trailing", False),
        ("rsi", "rsi_slope_1", "One-candle RSI slope", "trailing", False),
        ("rsi", "rsi_distance_50", "Signed RSI distance from fifty", "trailing", False),
        ("rsi", "rsi_threshold_distance", "Nearest registered threshold distance", "trailing", False),
        ("rsi", "rsi_event_persistence", "Six-candle causal decay after a threshold crossing", "trailing", False),
        ("bollinger", "bb_percent_b", "Registered Bollinger percent-B", "trailing", False),
        ("bollinger", "bb_bandwidth", "Registered Bollinger bandwidth", "trailing", False),
        ("bollinger", "bb_distance_upper", "Price distance from upper band in rolling-standard-deviation units", "trailing", False),
        ("bollinger", "bb_distance_lower", "Price distance from lower band in rolling-standard-deviation units", "trailing", False),
        ("bollinger", "bb_bandwidth_change_1", "One-candle bandwidth change", "trailing", False),
        ("bollinger", "bb_event_persistence", "Six-candle causal decay after a band crossing", "trailing", False),
        ("state", "state_p_range", "Forward-filtered range-state probability", "fold_training_then_forward", False),
        ("state", "state_p_trend", "Forward-filtered trend-state probability", "fold_training_then_forward", False),
        ("state", "state_p_stress", "Forward-filtered stress-state probability", "fold_training_then_forward", False),
    ]
    return pd.DataFrame.from_records(
        records,
        columns=["feature_family", "feature_name", "definition", "information_rule", "state_input"],
    ).assign(available_at_forecast_origin=True)
