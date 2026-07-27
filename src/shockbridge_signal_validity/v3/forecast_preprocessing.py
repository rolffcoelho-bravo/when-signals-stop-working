from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable

import numpy as np
import pandas as pd

from .forecast_contract import ForecastProtocolViolation, require_utc_index


DEFAULT_LOWER_QUANTILE = 0.005
DEFAULT_UPPER_QUANTILE = 0.995


def _validate_complete_numeric_frame(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ForecastProtocolViolation(f"{label} must be a nonempty DataFrame.")
    index = require_utc_index(frame.index, f"{label} timestamps")
    if frame.columns.duplicated().any():
        raise ForecastProtocolViolation(f"{label} columns must be unique.")
    columns = [str(value) for value in frame.columns]
    if any(not value for value in columns):
        raise ForecastProtocolViolation(f"{label} columns must be nonempty strings.")
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    numeric.index = index
    numeric.columns = columns
    if numeric.isna().any().any():
        raise ForecastProtocolViolation(
            f"{label} contains missing values; Gate V3-5 imputation is prohibited."
        )
    values = numeric.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ForecastProtocolViolation(f"{label} contains non-finite values.")
    return numeric.astype(float)


def _signature(payload: dict[str, object]) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FittedFoldPreprocessor:
    columns: tuple[str, ...]
    lower_bounds: tuple[float, ...]
    upper_bounds: tuple[float, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    fit_rows: int
    fit_start_utc: str
    fit_end_utc: str
    lower_quantile: float
    upper_quantile: float
    preprocessor_id: str

    def transform(self, frame: pd.DataFrame, label: str = "fold feature") -> pd.DataFrame:
        numeric = _validate_complete_numeric_frame(frame, label)
        if tuple(numeric.columns) != self.columns:
            raise ForecastProtocolViolation(
                f"{label} column order differs from the fitted fold preprocessor."
            )
        lower = pd.Series(self.lower_bounds, index=self.columns, dtype=float)
        upper = pd.Series(self.upper_bounds, index=self.columns, dtype=float)
        means = pd.Series(self.means, index=self.columns, dtype=float)
        scales = pd.Series(self.scales, index=self.columns, dtype=float)
        clipped = numeric.clip(lower=lower, upper=upper, axis="columns")
        transformed = (clipped - means) / scales
        if not np.isfinite(transformed.to_numpy(dtype=float)).all():
            raise ForecastProtocolViolation(
                f"{label} transformation produced non-finite values."
            )
        return transformed

    def manifest(self) -> dict[str, object]:
        return {
            "schema_version": "v3.g5-fold-preprocessor.v1",
            "preprocessor_id": self.preprocessor_id,
            "columns": list(self.columns),
            "fit_rows": self.fit_rows,
            "fit_start_utc": self.fit_start_utc,
            "fit_end_utc": self.fit_end_utc,
            "clip_lower_quantile": self.lower_quantile,
            "clip_upper_quantile": self.upper_quantile,
            "standardization": "TRAINING_FOLD_MEAN_AND_POPULATION_STD",
            "zero_variance_scale": 1.0,
            "missing_value_imputation_performed": False,
            "fit_scope": "TRAINING_FOLD_ONLY",
        }


def fit_fold_preprocessor(
    training_frame: pd.DataFrame,
    *,
    lower_quantile: float = DEFAULT_LOWER_QUANTILE,
    upper_quantile: float = DEFAULT_UPPER_QUANTILE,
) -> FittedFoldPreprocessor:
    if not 0.0 <= float(lower_quantile) < float(upper_quantile) <= 1.0:
        raise ForecastProtocolViolation("Training-only clipping quantiles are invalid.")
    numeric = _validate_complete_numeric_frame(training_frame, "training fold feature")
    lower = numeric.quantile(float(lower_quantile), interpolation="linear")
    upper = numeric.quantile(float(upper_quantile), interpolation="linear")
    if (lower > upper).any():
        raise ForecastProtocolViolation("Training-only clipping bounds are not ordered.")
    clipped = numeric.clip(lower=lower, upper=upper, axis="columns")
    means = clipped.mean(axis=0)
    scales = clipped.std(axis=0, ddof=0)
    scales = scales.mask(scales <= 0.0, 1.0)
    payload: dict[str, object] = {
        "columns": list(numeric.columns),
        "lower_bounds": [float(value) for value in lower],
        "upper_bounds": [float(value) for value in upper],
        "means": [float(value) for value in means],
        "scales": [float(value) for value in scales],
        "fit_rows": int(len(numeric)),
        "fit_start_utc": numeric.index.min().isoformat(),
        "fit_end_utc": numeric.index.max().isoformat(),
        "lower_quantile": float(lower_quantile),
        "upper_quantile": float(upper_quantile),
    }
    return FittedFoldPreprocessor(
        columns=tuple(str(value) for value in numeric.columns),
        lower_bounds=tuple(float(value) for value in lower),
        upper_bounds=tuple(float(value) for value in upper),
        means=tuple(float(value) for value in means),
        scales=tuple(float(value) for value in scales),
        fit_rows=int(len(numeric)),
        fit_start_utc=numeric.index.min().isoformat(),
        fit_end_utc=numeric.index.max().isoformat(),
        lower_quantile=float(lower_quantile),
        upper_quantile=float(upper_quantile),
        preprocessor_id=_signature(payload),
    )


@dataclass(frozen=True)
class MatchedFoldPreprocessors:
    benchmark: FittedFoldPreprocessor
    signal: FittedFoldPreprocessor
    benchmark_columns: tuple[str, ...]
    signal_columns: tuple[str, ...]
    matched_preprocessor_id: str

    def transform_pair(
        self,
        benchmark_frame: pd.DataFrame,
        candidate_frame: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        benchmark_numeric = _validate_complete_numeric_frame(
            benchmark_frame, "benchmark fold feature"
        )
        candidate_numeric = _validate_complete_numeric_frame(
            candidate_frame, "candidate fold feature"
        )
        if not benchmark_numeric.index.equals(candidate_numeric.index):
            raise ForecastProtocolViolation(
                "Benchmark and candidate preprocessing rows are not identical."
            )
        expected_candidate_columns = self.benchmark_columns + self.signal_columns
        if tuple(benchmark_numeric.columns) != self.benchmark_columns:
            raise ForecastProtocolViolation("Benchmark fold columns changed.")
        if tuple(candidate_numeric.columns) != expected_candidate_columns:
            raise ForecastProtocolViolation("Candidate fold columns changed.")
        benchmark_transformed = self.benchmark.transform(
            benchmark_numeric, "benchmark fold feature"
        )
        signal_transformed = self.signal.transform(
            candidate_numeric.loc[:, list(self.signal_columns)],
            "registered signal fold feature",
        )
        candidate_transformed = pd.concat(
            [benchmark_transformed, signal_transformed], axis=1
        )
        pd.testing.assert_frame_equal(
            benchmark_transformed,
            candidate_transformed.loc[:, list(self.benchmark_columns)],
            check_exact=True,
        )
        return benchmark_transformed, candidate_transformed

    def manifest(self) -> dict[str, object]:
        return {
            "schema_version": "v3.g5-matched-fold-preprocessor.v1",
            "matched_preprocessor_id": self.matched_preprocessor_id,
            "benchmark_preprocessor_id": self.benchmark.preprocessor_id,
            "signal_preprocessor_id": self.signal.preprocessor_id,
            "benchmark_columns": list(self.benchmark_columns),
            "signal_columns": list(self.signal_columns),
            "same_benchmark_transformation_in_candidate": True,
            "missing_value_imputation_performed": False,
            "fit_scope": "TRAINING_FOLD_ONLY",
        }


def fit_matched_fold_preprocessors(
    benchmark_training: pd.DataFrame,
    candidate_training: pd.DataFrame,
    *,
    lower_quantile: float = DEFAULT_LOWER_QUANTILE,
    upper_quantile: float = DEFAULT_UPPER_QUANTILE,
) -> MatchedFoldPreprocessors:
    benchmark = _validate_complete_numeric_frame(
        benchmark_training, "benchmark training fold"
    )
    candidate = _validate_complete_numeric_frame(
        candidate_training, "candidate training fold"
    )
    if not benchmark.index.equals(candidate.index):
        raise ForecastProtocolViolation(
            "Benchmark and candidate training rows must be identical."
        )
    benchmark_columns = tuple(str(value) for value in benchmark.columns)
    if tuple(candidate.columns[: len(benchmark_columns)]) != benchmark_columns:
        raise ForecastProtocolViolation(
            "Candidate training columns must begin with the exact benchmark columns."
        )
    signal_columns = tuple(str(value) for value in candidate.columns[len(benchmark_columns) :])
    if not signal_columns:
        raise ForecastProtocolViolation(
            "Candidate training frame contains no registered signal columns."
        )
    benchmark_preprocessor = fit_fold_preprocessor(
        benchmark,
        lower_quantile=lower_quantile,
        upper_quantile=upper_quantile,
    )
    signal_preprocessor = fit_fold_preprocessor(
        candidate.loc[:, list(signal_columns)],
        lower_quantile=lower_quantile,
        upper_quantile=upper_quantile,
    )
    payload = {
        "benchmark_preprocessor_id": benchmark_preprocessor.preprocessor_id,
        "signal_preprocessor_id": signal_preprocessor.preprocessor_id,
        "benchmark_columns": list(benchmark_columns),
        "signal_columns": list(signal_columns),
    }
    return MatchedFoldPreprocessors(
        benchmark=benchmark_preprocessor,
        signal=signal_preprocessor,
        benchmark_columns=benchmark_columns,
        signal_columns=signal_columns,
        matched_preprocessor_id=_signature(payload),
    )


def assert_no_fit_timestamp_at_or_after(
    preprocessors: Iterable[FittedFoldPreprocessor],
    boundary: object,
) -> None:
    timestamp = pd.Timestamp(boundary)
    if timestamp.tzinfo is None:
        raise ForecastProtocolViolation("Preprocessor boundary must be timezone-aware UTC.")
    timestamp = timestamp.tz_convert("UTC")
    for preprocessor in preprocessors:
        fit_end = pd.Timestamp(preprocessor.fit_end_utc).tz_convert("UTC")
        if fit_end >= timestamp:
            raise ForecastProtocolViolation(
                "A fold preprocessor used test or future observations."
            )
