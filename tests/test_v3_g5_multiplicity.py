from __future__ import annotations

import pytest

from shockbridge_signal_validity.v3.forecast_contract import ForecastProtocolViolation
from shockbridge_signal_validity.v3.forecast_multiplicity import (
    benjamini_hochberg_adjust,
    holm_adjust,
)


def test_holm_adjustment_is_monotone_in_sorted_order() -> None:
    results = holm_adjust(["a", "b", "c", "d"], [0.001, 0.01, 0.04, 0.2], alpha=0.05)
    by_raw = sorted(results, key=lambda value: value.raw_p_value)
    assert [value.adjusted_p_value for value in by_raw] == sorted(
        value.adjusted_p_value for value in by_raw
    )
    assert by_raw[0].rejected is True
    assert by_raw[-1].rejected is False


def test_holm_preserves_original_identifier_order() -> None:
    results = holm_adjust(["z", "x", "y"], [0.2, 0.001, 0.02])
    assert [value.hypothesis_id for value in results] == ["z", "x", "y"]
    assert all(value.method == "HOLM" for value in results)


def test_benjamini_hochberg_rejects_through_largest_eligible_rank() -> None:
    results = benjamini_hochberg_adjust(
        ["a", "b", "c", "d", "e"],
        [0.001, 0.01, 0.025, 0.2, 0.8],
        q=0.10,
    )
    rejected = {value.hypothesis_id for value in results if value.rejected}
    assert rejected == {"a", "b", "c"}
    assert all(value.method == "BENJAMINI_HOCHBERG" for value in results)


def test_adjusted_p_values_remain_bounded() -> None:
    results = benjamini_hochberg_adjust(["a", "b", "c"], [0.9, 0.95, 1.0])
    assert all(0.0 <= value.adjusted_p_value <= 1.0 for value in results)


def test_multiplicity_rejects_duplicate_ids_and_invalid_values() -> None:
    with pytest.raises(ForecastProtocolViolation, match="unique"):
        holm_adjust(["a", "a"], [0.1, 0.2])
    with pytest.raises(ForecastProtocolViolation, match="\[0,1\]"):
        benjamini_hochberg_adjust(["a", "b"], [0.1, 1.2])
