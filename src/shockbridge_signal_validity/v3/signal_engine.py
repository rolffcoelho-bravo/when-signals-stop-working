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
    missing = [x for x in REQUIRED_COLUMNS if x not in frame.columns]
    if missing: raise SignalEngineError(f"Missing canonical columns: {missing}")
    data = frame[list(REQUIRED_COLUMNS)].copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    if data["timestamp"].isna().any(): raise SignalEngineError("Invalid UTC timestamp")
    if data.duplicated(list(KEY_COLUMNS)).any(): raise SignalEngineError("Duplicate canonical keys are prohibited")
    for column in ("open", "high", "low", "close", "volume"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
        if data[column].isna().any() or not np.isfinite(data[column]).all():
            raise SignalEngineError(f"Canonical field {column} must be finite")
    if (data[["open", "high", "low", "close"]] <= 0).any().any():
        raise SignalEngineError("OHLC prices must be positive")
    if (data["volume"] < 0).any(): raise SignalEngineError("Volume must be non-negative")
    return data.sort_values(["timestamp", "asset", "venue"], kind="mergesort").reset_index(drop=True)


def _context(frame: pd.DataFrame | None, data: pd.DataFrame):
    if frame is None: return None, ()
    missing = [x for x in KEY_COLUMNS if x not in frame.columns]
    if missing: raise SignalEngineError(f"Context frame missing keys: {missing}")
    context = frame.copy(); context["timestamp"] = pd.to_datetime(context["timestamp"], utc=True, errors="coerce")
    if context["timestamp"].isna().any(): raise SignalEngineError("Invalid context timestamp")
    if context.duplicated(list(KEY_COLUMNS)).any(): raise SignalEngineError("Duplicate context keys are prohibited")
    columns = tuple(x for x in context.columns if x not in KEY_COLUMNS)
    for column in columns: context[column] = pd.to_numeric(context[column], errors="coerce")
    merged = data[list(KEY_COLUMNS)].merge(context[[*KEY_COLUMNS, *columns]], on=list(KEY_COLUMNS),
                                           how="left", sort=False, validate="one_to_one")
    return merged, columns


def _parameters(spec: SignalSpec, supplied: Mapping[str, Mapping[str, Any]]):
    fixed = dict(spec.threshold_or_band_parameter)
    if spec.parameter_policy == "FIXED": return fixed
    extra = supplied.get(spec.signal_id)
    if not isinstance(extra, Mapping): return None
    value = {**fixed, **dict(extra)}
    if spec.signal_family == "RSI":
        lower, upper = float(value.get("lower", np.nan)), float(value.get("upper", np.nan))
        if not 0 <= lower < upper <= 100: raise SignalEngineError("Training-only RSI thresholds are invalid")
    else:
        threshold = float(value.get("squeeze_threshold", np.nan))
        if not np.isfinite(threshold) or threshold <= 0: raise SignalEngineError("Training-only squeeze threshold is invalid")
    return value


def _base(data: pd.DataFrame, specs: tuple[SignalSpec, ...], supplied):
    values, statuses = {}, {}
    groups = list(data.groupby(["asset", "venue"], sort=False, observed=True).groups.items())
    rsi_cache, band_cache = {}, {}
    for spec in specs:
        if spec.regime_interaction_policy != "NONE": continue
        params = _parameters(spec, supplied)
        if params is None:
            values[spec.signal_id] = pd.Series(np.nan, index=data.index, dtype=float)
            statuses[spec.signal_id] = pd.Series("INELIGIBLE_TRAINING_PARAMETER_REQUIRED", index=data.index, dtype="string")
            continue
        series = pd.Series(np.nan, index=data.index, dtype=float)
        for (asset, venue), rows in groups:
            index, close = pd.Index(rows), data.loc[rows, "close"].astype(float)
            if spec.signal_family == "RSI":
                key = (str(asset), str(venue), spec.lookback_or_window)
                if key not in rsi_cache: rsi_cache[key] = wilder_rsi(close, spec.lookback_or_window)
                result = compute_rsi_feature(close, rsi_cache[key], spec, params)
            else:
                deviations = float(params.get("standard_deviations", 2.0))
                if deviations <= 0: raise SignalEngineError("Bollinger deviations must be positive")
                key = (str(asset), str(venue), spec.lookback_or_window, deviations)
                if key not in band_cache: band_cache[key] = bollinger_frame(close, spec.lookback_or_window, deviations)
                result = compute_bollinger_feature(close, band_cache[key], spec, params)
            series.loc[index] = result.to_numpy(dtype=float)
        values[spec.signal_id] = series
        statuses[spec.signal_id] = pd.Series(np.where(series.notna(), "ELIGIBLE", "INSUFFICIENT_HISTORY_OR_UNDEFINED"),
                                             index=data.index, dtype="string")
    return values, statuses


def _record(data, spec, value, status, base=None, context=None):
    result = data[list(KEY_COLUMNS)].copy()
    result["signal_id"], result["signal_family"] = spec.signal_id, spec.signal_family
    result["interpretation"], result["orientation"] = spec.interpretation, spec.orientation
    result["parameter_policy"] = spec.parameter_policy
    result["regime_interaction_policy"] = spec.regime_interaction_policy
    result["feature_value"], result["eligibility_status"] = value.astype(float), status.astype("string")
    result["base_signal_value"] = np.nan if base is None else base.astype(float)
    result["context_value"] = np.nan if context is None else context.astype(float)
    return result


def compute_signal_feature_frame(frame: pd.DataFrame, registry: Mapping[str, Any], *,
                                 training_only_parameters: Mapping[str, Mapping[str, Any]] | None = None,
                                 context_frame: pd.DataFrame | None = None) -> SignalFeatureFrame:
    specs, data = validate_registry(registry), _input(frame)
    supplied, (context, context_columns) = training_only_parameters or {}, _context(context_frame, data)
    values, statuses = _base(data, specs, supplied)
    records = []
    for spec in specs:
        if spec.regime_interaction_policy == "NONE":
            records.append(_record(data, spec, values[spec.signal_id], statuses[spec.signal_id])); continue
        base = values[spec.base_signal_id or ""]
        if context is None or spec.context_feature not in context.columns:
            ctx = pd.Series(np.nan, index=data.index, dtype=float); value = base * ctx
            status = pd.Series("INELIGIBLE_CONTEXT_UNAVAILABLE", index=data.index, dtype="string")
        else:
            ctx = pd.to_numeric(context[spec.context_feature], errors="coerce").astype(float)
            value = base * ctx
            status = pd.Series(np.where(base.notna() & ctx.notna(), "ELIGIBLE", "INSUFFICIENT_BASE_OR_CONTEXT"),
                               index=data.index, dtype="string")
        values[spec.signal_id], statuses[spec.signal_id] = value, status
        records.append(_record(data, spec, value, status, base, ctx))
    output = pd.concat(records, ignore_index=True).sort_values(
        ["timestamp", "asset", "venue", "signal_id"], kind="mergesort").reset_index(drop=True)
    reports = build_reports(data, output, registry, specs, statuses, context_columns, len(supplied))
    return SignalFeatureFrame(output, *reports)
