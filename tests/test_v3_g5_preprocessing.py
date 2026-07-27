from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v3.forecast_contract import ForecastProtocolViolation
from shockbridge_signal_validity.v3.forecast_preprocessing import (
    assert_no_fit_timestamp_at_or_after,
    fit_fold_preprocessor,
    fit_matched_fold_preprocessors,
)


def _frames(rows: int = 400) -> tuple[pd.DataFrame, pd.DataFrame]:
    index = pd.date_range("2021-01-01T00:00:00Z", periods=rows, freq="4h")
    phase = np.linspace(0.0, 15.0, rows)
    benchmark = pd.DataFrame(
        {
            "ret": np.sin(phase),
            "vol": 1.0 + np.cos(phase) ** 2,
            "constant": 3.0,
        },
        index=index,
    )
    candidate = benchmark.copy()
    candidate["signal_a"] = np.cos(phase / 2.0)
    candidate["signal_b"] = np.sin(phase / 3.0)
    return benchmark, candidate


def test_fold_preprocessor_is_training_only_and_deterministic() -> None:
    benchmark, _ = _frames()
    training = benchmark.iloc[:300]
    first = fit_fold_preprocessor(training)
    second = fit_fold_preprocessor(training.copy())
    assert first == second
    assert first.fit_rows == 300
    assert first.manifest()["missing_value_imputation_performed"] is False
    transformed = first.transform(benchmark.iloc[300:])
    assert transformed.shape == (100, 3)
    assert np.isfinite(transformed.to_numpy()).all()


def test_future_mutation_does_not_change_fitted_preprocessor() -> None:
    benchmark, _ = _frames()
    training = benchmark.iloc[:300]
    original = fit_fold_preprocessor(training)
    mutated = benchmark.copy()
    mutated.iloc[300:, :] = mutated.iloc[300:, :] * 100000.0
    refitted = fit_fold_preprocessor(mutated.iloc[:300])
    assert original == refitted


def test_training_missingness_fails_closed_without_imputation() -> None:
    benchmark, _ = _frames()
    benchmark.iloc[10, 0] = np.nan
    with pytest.raises(ForecastProtocolViolation, match="imputation is prohibited"):
        fit_fold_preprocessor(benchmark.iloc[:300])


def test_zero_variance_feature_uses_unit_scale() -> None:
    benchmark, _ = _frames()
    preprocessor = fit_fold_preprocessor(benchmark.iloc[:300])
    scale = dict(zip(preprocessor.columns, preprocessor.scales, strict=True))
    assert scale["constant"] == 1.0
    transformed = preprocessor.transform(benchmark.iloc[300:])
    assert transformed["constant"].eq(0.0).all()


def test_matched_preprocessing_reuses_exact_benchmark_transformation() -> None:
    benchmark, candidate = _frames()
    matched = fit_matched_fold_preprocessors(
        benchmark.iloc[:300],
        candidate.iloc[:300],
    )
    benchmark_test, candidate_test = matched.transform_pair(
        benchmark.iloc[300:],
        candidate.iloc[300:],
    )
    pd.testing.assert_frame_equal(
        benchmark_test,
        candidate_test.loc[:, list(benchmark.columns)],
        check_exact=True,
    )
    assert matched.manifest()["same_benchmark_transformation_in_candidate"] is True
    assert matched.manifest()["missing_value_imputation_performed"] is False


def test_candidate_must_begin_with_exact_benchmark_columns() -> None:
    benchmark, candidate = _frames()
    reordered = candidate[["signal_a", "ret", "vol", "constant", "signal_b"]]
    with pytest.raises(ForecastProtocolViolation, match="begin with the exact benchmark"):
        fit_matched_fold_preprocessors(benchmark.iloc[:300], reordered.iloc[:300])


def test_transform_rejects_column_order_drift() -> None:
    benchmark, _ = _frames()
    fitted = fit_fold_preprocessor(benchmark.iloc[:300])
    with pytest.raises(ForecastProtocolViolation, match="column order differs"):
        fitted.transform(benchmark.iloc[300:][["vol", "ret", "constant"]])


def test_fit_timestamp_boundary_is_enforced() -> None:
    benchmark, _ = _frames()
    fitted = fit_fold_preprocessor(benchmark.iloc[:300])
    boundary = benchmark.index[300]
    assert_no_fit_timestamp_at_or_after([fitted], boundary)
    with pytest.raises(ForecastProtocolViolation, match="test or future"):
        assert_no_fit_timestamp_at_or_after([fitted], benchmark.index[299])
