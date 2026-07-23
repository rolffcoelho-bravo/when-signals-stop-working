from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v3.spectral import (
    CausalFeatureConfig,
    PanelSpec,
    SpectralFeatureError,
    build_causal_series_features,
    build_close_panel,
    compare_registered_panels,
    compute_spectral_feature_frame,
    spectral_metrics_from_correlation,
)


def synthetic_panel(periods: int = 90) -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-01", periods=periods, freq="4h", tz="UTC")
    market = np.sin(np.linspace(0.0, 8.0, periods)) * 0.004
    rows = []
    for index, asset in enumerate(("SOL", "BTC", "ETH")):
        idiosyncratic = np.cos(
            np.linspace(0.0, 5.0 + index, periods)
        ) * (0.001 + index * 0.0002)
        returns = market + idiosyncratic
        closes = (100.0 + index * 20.0) * np.exp(np.cumsum(returns))
        for timestamp, close in zip(timestamps, closes):
            rows.append(
                {
                    "timestamp": timestamp,
                    "asset": asset,
                    "venue": "binance",
                    "open": close * 0.999,
                    "high": close * 1.002,
                    "low": close * 0.998,
                    "close": close,
                    "volume": 1000.0 + index * 100.0,
                    "funding_rate": 0.0001 * (index + 1),
                    "open_interest": 10000.0 + index * 500.0,
                    "long_liquidations": 5.0 + index,
                    "short_liquidations": 4.0 + index,
                    "bid_ask_spread": 0.01 + index * 0.001,
                    "order_book_depth": 50000.0 + index * 1000.0,
                }
            )
    return pd.DataFrame(rows)


def panel_spec(**kwargs) -> PanelSpec:
    return PanelSpec(
        members=("SOL@binance", "BTC@binance", "ETH@binance"),
        dependence_windows=kwargs.pop("dependence_windows", (20, 30)),
        minimum_complete_observations=kwargs.pop(
            "minimum_complete_observations", 15
        ),
        minimum_window_coverage=kwargs.pop("minimum_window_coverage", 0.80),
        **kwargs,
    )


def test_identity_and_common_mode_analytical_fixtures() -> None:
    identity = spectral_metrics_from_correlation(np.eye(4))
    assert identity["dominant_eigenvalue_share"] == pytest.approx(0.25)
    assert identity["participation_ratio"] == pytest.approx(4.0)
    assert identity["spectral_entropy"] == pytest.approx(1.0)
    assert identity["average_correlation"] == pytest.approx(0.0)

    common = spectral_metrics_from_correlation(np.ones((4, 4)))
    assert common["dominant_eigenvalue_share"] == pytest.approx(1.0)
    assert common["participation_ratio"] == pytest.approx(1.0)
    assert common["spectral_entropy"] == pytest.approx(0.0, abs=1e-12)
    assert common["network_density"] == pytest.approx(1.0)


def test_fixed_panel_order_and_explicit_membership() -> None:
    frame = synthetic_panel().sample(frac=1.0, random_state=7)
    close = build_close_panel(frame, panel_spec())
    assert list(close.columns) == [
        "SOL@binance",
        "BTC@binance",
        "ETH@binance",
    ]

    with pytest.raises(SpectralFeatureError, match="absent"):
        build_close_panel(
            frame,
            PanelSpec(
                members=("SOL@binance", "BTC@binance", "XRP@binance"),
                dependence_windows=(20,),
                minimum_complete_observations=15,
            ),
        )


def test_spectral_features_are_causal_under_future_mutation() -> None:
    frame = synthetic_panel()
    spec = panel_spec(dependence_windows=(20,))
    baseline = compute_spectral_feature_frame(frame, spec).frame
    cutoff = pd.Timestamp("2024-01-09 00:00:00", tz="UTC")

    mutated = frame.copy()
    future = mutated["timestamp"] > cutoff
    mutated.loc[future, "close"] *= np.linspace(1.0, 2.0, future.sum())
    changed = compute_spectral_feature_frame(mutated, spec).frame

    columns = [
        "timestamp",
        "window",
        "eligibility_status",
        "dominant_eigenvalue_share",
        "spectral_entropy",
        "average_correlation",
    ]
    left = baseline.loc[
        baseline["timestamp"] <= cutoff, columns
    ].reset_index(drop=True)
    right = changed.loc[
        changed["timestamp"] <= cutoff, columns
    ].reset_index(drop=True)
    pd.testing.assert_frame_equal(left, right)


def test_series_features_are_causal_under_future_mutation() -> None:
    frame = synthetic_panel()
    spec = panel_spec(dependence_windows=(20,))
    config = CausalFeatureConfig(
        volatility_windows=(6,), stress_window=12, volume_window=12
    )
    baseline = build_causal_series_features(frame, spec, config)
    cutoff = pd.Timestamp("2024-01-09 00:00:00", tz="UTC")

    mutated = frame.copy()
    mutated.loc[mutated["timestamp"] > cutoff, "volume"] *= 50.0
    changed = build_causal_series_features(mutated, spec, config)
    left = baseline.loc[baseline["timestamp"] <= cutoff].reset_index(drop=True)
    right = changed.loc[changed["timestamp"] <= cutoff].reset_index(drop=True)
    pd.testing.assert_frame_equal(left, right)


def test_insufficient_panel_coverage_fails_closed() -> None:
    frame = synthetic_panel(periods=45)
    ordered = frame["timestamp"].sort_values().unique()
    mask = (frame["asset"] == "ETH") & (frame["timestamp"] >= ordered[20])
    frame = frame.loc[~mask].copy()
    result = compute_spectral_feature_frame(
        frame,
        panel_spec(
            dependence_windows=(20,),
            minimum_window_coverage=0.95,
        ),
    )
    threshold = frame["timestamp"].min() + pd.Timedelta(hours=4 * 25)
    late = result.frame.loc[result.frame["timestamp"] >= threshold]
    assert not late.empty
    assert (
        late["eligibility_status"] == "INSUFFICIENT_PANEL_COVERAGE"
    ).all()
    assert late["dominant_eigenvalue_share"].isna().all()


@pytest.mark.parametrize("estimator", ["sample", "ewma", "shrinkage"])
def test_registered_estimators_produce_bounded_metrics(estimator: str) -> None:
    result = compute_spectral_feature_frame(
        synthetic_panel(),
        panel_spec(dependence_windows=(20,), estimator=estimator),
    )
    eligible = result.frame.loc[
        result.frame["eligibility_status"] == "ELIGIBLE"
    ]
    assert not eligible.empty
    assert eligible["dominant_eigenvalue_share"].between(1.0 / 3.0, 1.0).all()
    assert eligible["spectral_entropy"].between(0.0, 1.0).all()
    assert eligible["eigenvector_stability"].dropna().between(0.0, 1.0).all()


def test_registered_panel_comparison_never_selects_a_winner() -> None:
    frame = synthetic_panel()
    result = compare_registered_panels(
        frame,
        [
            panel_spec(dependence_windows=(20,)),
            PanelSpec(
                members=("SOL@binance", "BTC@binance"),
                dependence_windows=(20,),
                minimum_complete_observations=15,
            ),
        ],
    )
    assert len(result) == 2
    assert not result["selection_performed"].any()
    assert result["panel_id"].is_unique


def test_manifest_and_output_are_deterministic() -> None:
    frame = synthetic_panel().sample(frac=1.0, random_state=19)
    first = compute_spectral_feature_frame(frame, panel_spec())
    second = compute_spectral_feature_frame(frame, panel_spec())
    assert first.manifest == second.manifest
    pd.testing.assert_frame_equal(first.frame, second.frame)
