from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import pandas as pd

from .data_contract import KEY_COLUMNS, REQUIRED_COLUMNS
from .signal_bollinger import compute_bollinger_feature
from .signal_math import bollinger_frame, wilder_rsi
from .signal_reporting import build_reports
from .signal_registry import SignalSpec, validate_registry
from .signal_rsi import compute_rsi_feature
from .signal_spectral import compute_spectral_feature
from .signal_fibonacci import compute_fibonacci_feature


class SignalEngineError(ValueError):
    pass


@dataclass(frozen=True)
class SignalFeatureFrame:
    frame: pd.DataFrame
    registry_manifest: Mapping[str, Any]
    feature_manifest: Mapping[str, Any]
    coverage_report: Mapping[str, Any]
    validation_report: Mapping[str, Any]


def _input(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise SignalEngineError(f"Missing canonical columns: {missing}")
    data = frame[list(REQUIRED_COLUMNS)].copy()
    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        utc=True,
        errors="coerce",
    )
    if data["timestamp"].isna().any():
        raise SignalEngineError("Invalid UTC timestamp")
    if data.duplicated(list(KEY_COLUMNS)).any():
        raise SignalEngineError("Duplicate canonical keys are prohibited")
    for column in ("asset", "venue"):
        data[column] = data[column].astype("string").str.strip()
        if data[column].isna().any() or (data[column] == "").any():
            raise SignalEngineError(f"Canonical key {column} is missing")
    for column in ("open", "high", "low", "close", "volume"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
        if data[column].isna().any() or not np.isfinite(data[column]).all():
            raise SignalEngineError(f"Canonical field {column} must be finite")
    if (data[["open", "high", "low", "close"]] <= 0).any().any():
        raise SignalEngineError("OHLC prices must be positive")
    invalid_bounds = (
        (data["low"] > data["high"])
        | (data["open"] < data["low"])
        | (data["open"] > data["high"])
        | (data["close"] < data["low"])
        | (data["close"] > data["high"])
    )
    if invalid_bounds.any():
        raise SignalEngineError("OHLC values violate low/high bounds")
    if (data["volume"] < 0).any():
        raise SignalEngineError("Volume must be non-negative")
    return data.sort_values(
        ["timestamp", "asset", "venue"],
        kind="mergesort",
    ).reset_index(drop=True)


def _context(
    frame: pd.DataFrame | None,
    data: pd.DataFrame,
) -> tuple[pd.DataFrame | None, tuple[str, ...]]:
    if frame is None:
        return None, ()
    missing = [column for column in KEY_COLUMNS if column not in frame.columns]
    if missing:
        raise SignalEngineError(f"Context frame missing keys: {missing}")
    context = frame.copy()
    context["timestamp"] = pd.to_datetime(
        context["timestamp"],
        utc=True,
        errors="coerce",
    )
    if context["timestamp"].isna().any():
        raise SignalEngineError("Invalid context timestamp")
    if context.duplicated(list(KEY_COLUMNS)).any():
        raise SignalEngineError("Duplicate context keys are prohibited")
    columns = tuple(column for column in context.columns if column not in KEY_COLUMNS)
    for column in columns:
        context[column] = pd.to_numeric(context[column], errors="coerce")
        finite = context[column].dropna()
        if not np.isfinite(finite).all():
            raise SignalEngineError(f"Context field {column} must be finite when present")
        if column.startswith("p_") or column == "dominant_eigenvalue_share":
            if ((finite < 0.0) | (finite > 1.0)).any():
                raise SignalEngineError(
                    f"Probability/share context field {column} must be in [0, 1]"
                )
    merged = data[list(KEY_COLUMNS)].merge(
        context[[*KEY_COLUMNS, *columns]],
        on=list(KEY_COLUMNS),
        how="left",
        sort=False,
        validate="one_to_one",
    )
    return merged, columns


def _validate_supplied_parameter_keys(
    specs: tuple[SignalSpec, ...],
    supplied: Mapping[str, Mapping[str, Any]],
) -> None:
    adaptive_keys = {
        spec.feature_key
        for spec in specs
        if spec.parameter_policy == "TRAINING_ONLY_REQUIRED"
        and spec.regime_interaction_policy == "NONE"
    }
    unknown = sorted(set(supplied).difference(adaptive_keys))
    if unknown:
        raise SignalEngineError(
            "Training-only parameters reference unregistered or non-adaptive feature keys"
        )


def _parameters(
    spec: SignalSpec,
    supplied: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any] | None:
    fixed = dict(spec.threshold_or_band_parameter)
    if spec.parameter_policy == "FIXED":
        return fixed
    extra = supplied.get(spec.feature_key)
    if not isinstance(extra, Mapping):
        return None
    value = {**fixed, **dict(extra)}
    if spec.signal_family == "RSI":
        lower = float(value.get("lower", np.nan))
        upper = float(value.get("upper", np.nan))
        if not 0.0 <= lower < upper <= 100.0:
            raise SignalEngineError("Training-only RSI thresholds are invalid")
    else:
        threshold = float(value.get("squeeze_threshold", np.nan))
        if not np.isfinite(threshold) or threshold <= 0.0:
            raise SignalEngineError("Training-only squeeze threshold is invalid")
    return value


def _base(
    data: pd.DataFrame,
    context: pd.DataFrame | None,
    specs: tuple[SignalSpec, ...],
    supplied: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, pd.Series], dict[str, pd.Series]]:
    values: dict[str, pd.Series] = {}
    statuses: dict[str, pd.Series] = {}
    groups = list(
        data.groupby(["asset", "venue"], sort=False, observed=True).groups.items()
    )
    rsi_cache: dict[tuple[str, str, int], pd.Series] = {}
    band_cache: dict[tuple[str, str, int, float], pd.DataFrame] = {}
    for spec in specs:
        if spec.regime_interaction_policy != "NONE":
            continue
        parameters = _parameters(spec, supplied)
        if parameters is None:
            values[spec.signal_id] = pd.Series(
                np.nan,
                index=data.index,
                dtype=float,
            )
            statuses[spec.signal_id] = pd.Series(
                "INELIGIBLE_TRAINING_PARAMETER_REQUIRED",
                index=data.index,
                dtype="string",
            )
            continue
        series = pd.Series(np.nan, index=data.index, dtype=float)
        for (asset, venue), rows in groups:
            index = pd.Index(rows)
            close = data.loc[rows, "close"].astype(float)
            if spec.signal_family == "SPECTRAL":
                if context is None:
                    result = pd.Series(np.nan, index=index, dtype=float)
                else:
                    result = compute_spectral_feature(
                        context.loc[rows],
                        spec,
                        parameters,
                    )
            elif spec.signal_family == "RSI":
                cache_key = (str(asset), str(venue), spec.lookback_or_window)
                if cache_key not in rsi_cache:
                    rsi_cache[cache_key] = wilder_rsi(
                        close,
                        spec.lookback_or_window,
                    )
                result = compute_rsi_feature(
                    close,
                    rsi_cache[cache_key],
                    spec,
                    parameters,
                )
            elif spec.signal_family == "FIBONACCI":
                high_s = data.loc[rows, "high"].astype(float)
                low_s = data.loc[rows, "low"].astype(float)
                result = compute_fibonacci_feature(
                    high_s,
                    low_s,
                    close,
                    spec,
                    parameters,
                )
            else:
                deviations = float(parameters.get("standard_deviations", 2.0))
                if not np.isfinite(deviations) or deviations <= 0.0:
                    raise SignalEngineError("Bollinger deviations must be positive")
                cache_key = (
                    str(asset),
                    str(venue),
                    spec.lookback_or_window,
                    deviations,
                )
                if cache_key not in band_cache:
                    band_cache[cache_key] = bollinger_frame(
                        close,
                        spec.lookback_or_window,
                        deviations,
                    )
                result = compute_bollinger_feature(
                    close,
                    band_cache[cache_key],
                    spec,
                    parameters,
                )
            series.loc[index] = result.to_numpy(dtype=float)
        values[spec.signal_id] = series
        statuses[spec.signal_id] = pd.Series(
            np.where(
                series.notna(),
                "ELIGIBLE",
                "INSUFFICIENT_HISTORY_OR_UNDEFINED",
            ),
            index=data.index,
            dtype="string",
        )
    return values, statuses


def _record(
    data: pd.DataFrame,
    spec: SignalSpec,
    value: pd.Series,
    status: pd.Series,
    base: pd.Series | None = None,
    context: pd.Series | None = None,
) -> pd.DataFrame:
    result = data[list(KEY_COLUMNS)].copy()
    result["signal_id"] = spec.signal_id
    result["feature_key"] = spec.feature_key
    result["signal_family"] = spec.signal_family
    result["interpretation"] = spec.interpretation
    result["orientation"] = spec.orientation
    result["parameter_policy"] = spec.parameter_policy
    result["regime_interaction_policy"] = spec.regime_interaction_policy
    result["feature_value"] = value.astype(float)
    result["eligibility_status"] = status.astype("string")
    result["base_signal_value"] = np.nan if base is None else base.astype(float)
    result["context_value"] = np.nan if context is None else context.astype(float)
    return result


def compute_signal_feature_frame(
    frame: pd.DataFrame,
    registry: Mapping[str, Any],
    *,
    training_only_parameters: Mapping[str, Mapping[str, Any]] | None = None,
    context_frame: pd.DataFrame | None = None,
) -> SignalFeatureFrame:
    specs = validate_registry(registry)
    data = _input(frame)
    supplied = training_only_parameters or {}
    if not isinstance(supplied, Mapping):
        raise SignalEngineError("training_only_parameters must be a mapping")
    _validate_supplied_parameter_keys(specs, supplied)
    context, context_columns = _context(context_frame, data)
    values, statuses = _base(data, context, specs, supplied)
    records: list[pd.DataFrame] = []
    for spec in specs:
        if spec.regime_interaction_policy == "NONE":
            records.append(
                _record(
                    data,
                    spec,
                    values[spec.signal_id],
                    statuses[spec.signal_id],
                )
            )
            continue
        base = values[spec.base_signal_id or ""]
        if context is None or spec.context_feature not in context.columns:
            context_value = pd.Series(np.nan, index=data.index, dtype=float)
            value = base * context_value
            status = pd.Series(
                "INELIGIBLE_CONTEXT_UNAVAILABLE",
                index=data.index,
                dtype="string",
            )
        else:
            context_value = pd.to_numeric(
                context[spec.context_feature],
                errors="coerce",
            ).astype(float)
            value = base * context_value
            status = pd.Series(
                np.where(
                    base.notna() & context_value.notna(),
                    "ELIGIBLE",
                    "INSUFFICIENT_BASE_OR_CONTEXT",
                ),
                index=data.index,
                dtype="string",
            )
        values[spec.signal_id] = value
        statuses[spec.signal_id] = status
        records.append(
            _record(
                data,
                spec,
                value,
                status,
                base,
                context_value,
            )
        )
    output = pd.concat(records, ignore_index=True).sort_values(
        ["timestamp", "asset", "venue", "signal_id"],
        kind="mergesort",
    ).reset_index(drop=True)
    reports = build_reports(
        data,
        output,
        registry,
        specs,
        statuses,
        context_columns,
        len(supplied),
    )
    return SignalFeatureFrame(output, *reports)
