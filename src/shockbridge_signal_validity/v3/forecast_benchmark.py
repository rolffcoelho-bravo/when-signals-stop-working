from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd

from .forecast_contract import ForecastContract, ForecastProtocolViolation, require_utc_index


BASE_BENCHMARK_FEATURES = (
    "sol_ret_1",
    "sol_ret_3",
    "btc_ret_1",
    "btc_ret_3",
    "trend_12",
    "vol_20",
    "range_12",
    "volume_z",
)


def _market_frame(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    if "timestamp" in data.columns:
        data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="raise")
        data = data.set_index("timestamp")
    data.index = require_utc_index(data.index, "benchmark market timestamps")
    required = {"high", "low", "close", "volume"}
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ForecastProtocolViolation(
            "Canonical SOL market frame is missing: " + ", ".join(missing)
        )
    numeric = data[list(required)].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ForecastProtocolViolation("Canonical SOL OHLCV values must be finite.")
    if (numeric[["high", "low", "close"]] <= 0.0).any().any():
        raise ForecastProtocolViolation("Canonical SOL prices must be positive.")
    if (numeric["volume"] < 0.0).any():
        raise ForecastProtocolViolation("Canonical SOL volume cannot be negative.")
    if (numeric["low"] > numeric["high"]).any():
        raise ForecastProtocolViolation("Canonical SOL low exceeds high.")
    return numeric.sort_index(kind="mergesort")


def _btc_series(close: pd.Series) -> pd.Series:
    index = require_utc_index(close.index, "BTC benchmark timestamps")
    values = pd.to_numeric(close, errors="coerce")
    values.index = index
    if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ForecastProtocolViolation("BTC close series must be finite and complete.")
    if (values <= 0.0).any():
        raise ForecastProtocolViolation("BTC close series must be positive.")
    return values.astype(float).sort_index(kind="mergesort")


def build_continuity_benchmark(
    sol_market: pd.DataFrame,
    btc_close: pd.Series,
    contract: ForecastContract,
    context_features: pd.DataFrame | None = None,
) -> pd.DataFrame:
    sol = _market_frame(sol_market)
    sol = sol.loc[
        (sol.index >= contract.development_start)
        & (sol.index <= contract.development_end)
    ]
    contract.assert_development_only(sol.index)

    btc = _btc_series(btc_close).reindex(sol.index)
    if btc.isna().any():
        raise ForecastProtocolViolation(
            "BTC benchmark history must align exactly; imputation is prohibited."
        )

    sol_log = np.log(sol["close"])
    btc_log = np.log(btc)
    features = pd.DataFrame(index=sol.index)
    features["sol_ret_1"] = sol_log.diff(1)
    features["sol_ret_3"] = sol_log.diff(3)
    features["btc_ret_1"] = btc_log.diff(1)
    features["btc_ret_3"] = btc_log.diff(3)
    features["trend_12"] = sol_log.diff(12) / 12.0
    features["vol_20"] = (
        features["sol_ret_1"].rolling(20, min_periods=20).std(ddof=1)
        * math.sqrt(20.0)
    )
    features["range_12"] = (
        sol["high"].rolling(12, min_periods=12).max()
        / sol["low"].rolling(12, min_periods=12).min()
        - 1.0
    )
    log_volume = np.log1p(sol["volume"])
    mean = log_volume.rolling(30, min_periods=30).mean()
    std = log_volume.rolling(30, min_periods=30).std(ddof=1)
    features["volume_z"] = (log_volume - mean) / std.replace(0.0, np.nan)

    if context_features is not None:
        context = context_features.copy()
        if "timestamp" in context.columns:
            context["timestamp"] = pd.to_datetime(
                context["timestamp"], utc=True, errors="raise"
            )
            context = context.set_index("timestamp")
        context.index = require_utc_index(context.index, "context timestamps")
        context = context.reindex(features.index)
        if context.columns.duplicated().any():
            raise ForecastProtocolViolation("Context feature names must be unique.")
        overlap = sorted(set(features.columns).intersection(context.columns))
        if overlap:
            raise ForecastProtocolViolation(
                "Context duplicates benchmark columns: " + ", ".join(overlap)
            )
        numeric_context = context.apply(pd.to_numeric, errors="coerce")
        invalid = numeric_context.notna() & ~np.isfinite(
            numeric_context.to_numpy(dtype=float)
        )
        if np.asarray(invalid).any():
            raise ForecastProtocolViolation("Context features contain non-finite values.")
        features = pd.concat([features, numeric_context], axis=1)

    return features.replace([np.inf, -np.inf], np.nan)


def benchmark_manifest(
    features: pd.DataFrame,
    contract: ForecastContract,
    context_columns: Iterable[str] = (),
) -> dict[str, object]:
    index = contract.assert_development_only(features.index)
    missing_base = sorted(set(BASE_BENCHMARK_FEATURES).difference(features.columns))
    if missing_base:
        raise ForecastProtocolViolation(
            "Benchmark feature frame is incomplete: " + ", ".join(missing_base)
        )
    return {
        "schema_version": "v3.g5-benchmark-manifest.v1",
        "benchmark_contract": "VERSION_2_NON_INDICATOR_CONTINUITY_BENCHMARK",
        "rows": int(len(features)),
        "start_utc": index.min().isoformat(),
        "end_utc": index.max().isoformat(),
        "base_features": list(BASE_BENCHMARK_FEATURES),
        "context_features": sorted(str(value) for value in context_columns),
        "training_only_preprocessing_required": True,
        "ohlcv_imputation_performed": False,
        "signal_establishment_segment_accessed": False,
        "final_framework_reserve_accessed": False,
    }
