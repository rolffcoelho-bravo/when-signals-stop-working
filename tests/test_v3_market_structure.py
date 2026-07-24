from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v3.market_structure import (
    MarketStructureError,
    NetworkSpec,
    compute_market_structure_feature_frame,
    correlation_distance,
    minimum_spanning_tree,
    network_metrics_from_correlation,
)
from shockbridge_signal_validity.v3.spectral import PanelSpec


def synthetic_panel(periods: int = 60) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01", periods=periods, freq="4h", tz="UTC")
    rows: list[dict[str, object]] = []
    common = np.sin(np.linspace(0.0, 7.0, periods)) * 0.003
    for index, asset in enumerate(("SOL", "BTC", "ETH", "BNB")):
        returns = common + np.cos(
            np.linspace(0.0, 4.0 + index, periods)
        ) * (0.0005 + index * 0.0001)
        closes = (100.0 + index * 10.0) * np.exp(np.cumsum(returns))
        for timestamp, close in zip(timestamps, closes):
            rows.append(
                {
                    "timestamp": timestamp,
                    "asset": asset,
                    "venue": "fixture",
                    "open": close * 0.999,
                    "high": close * 1.002,
                    "low": close * 0.998,
                    "close": close,
                    "volume": 1000.0 + index,
                }
            )
    return pd.DataFrame(rows)


def panel_spec() -> PanelSpec:
    return PanelSpec(
        members=(
            "SOL@fixture",
            "BTC@fixture",
            "ETH@fixture",
            "BNB@fixture",
        ),
        dependence_windows=(20,),
        minimum_complete_observations=15,
        minimum_window_coverage=0.80,
        estimator="sample",
        network_threshold=0.50,
    )


def test_identity_network_is_sparse_and_mst_is_deterministic() -> None:
    metrics = network_metrics_from_correlation(
        np.eye(4),
        ("A", "B", "C", "D"),
        NetworkSpec(threshold=0.50),
    )
    assert metrics["network_density"] == 0.0
    assert metrics["network_component_count"] == 4
    assert metrics["network_community_count"] == 4
    assert metrics["mst_total_distance"] == pytest.approx(3.0 * np.sqrt(2.0))
    edges = json.loads(metrics["mst_edges"])
    assert edges == [
        ["A", "B", pytest.approx(np.sqrt(2.0))],
        ["A", "C", pytest.approx(np.sqrt(2.0))],
        ["A", "D", pytest.approx(np.sqrt(2.0))],
    ]


def test_common_mode_network_is_dense_and_single_community() -> None:
    metrics = network_metrics_from_correlation(
        np.ones((4, 4)),
        ("A", "B", "C", "D"),
        NetworkSpec(threshold=0.50),
    )
    assert metrics["network_density"] == 1.0
    assert metrics["network_average_clustering"] == 1.0
    assert metrics["network_component_count"] == 1
    assert metrics["network_community_count"] == 1
    assert metrics["mst_total_distance"] == 0.0
    assert metrics["network_radius"] < 1e-9


def test_block_structure_recovers_two_communities() -> None:
    correlation = np.array(
        [
            [1.0, 0.90, 0.10, 0.10],
            [0.90, 1.0, 0.10, 0.10],
            [0.10, 0.10, 1.0, 0.85],
            [0.10, 0.10, 0.85, 1.0],
        ]
    )
    metrics = network_metrics_from_correlation(
        correlation,
        ("A", "B", "C", "D"),
        NetworkSpec(threshold=0.50),
    )
    assert json.loads(metrics["network_communities"]) == [["A", "B"], ["C", "D"]]
    assert metrics["network_community_count"] == 2
    assert metrics["network_modularity"] > 0.0


def test_minimum_spanning_tree_has_n_minus_one_edges() -> None:
    correlation = np.array(
        [[1.0, 0.80, 0.30], [0.80, 1.0, 0.40], [0.30, 0.40, 1.0]]
    )
    tree, edges = minimum_spanning_tree(correlation_distance(correlation))
    assert len(edges) == 2
    assert np.count_nonzero(np.triu(tree, 1)) == 2


def test_members_must_match_matrix() -> None:
    with pytest.raises(MarketStructureError):
        network_metrics_from_correlation(np.eye(3), ("A", "B"))


def test_future_mutation_cannot_change_prior_outputs() -> None:
    frame = synthetic_panel()
    baseline = compute_market_structure_feature_frame(
        frame,
        panel_spec(),
        network_spec=NetworkSpec(dynamic_window=3),
    ).frame
    cutoff = pd.Timestamp("2026-01-07T00:00:00Z")
    changed = frame.copy()
    future = changed["timestamp"] > cutoff
    changed.loc[future, "close"] *= np.linspace(1.0, 2.0, int(future.sum()))
    altered = compute_market_structure_feature_frame(
        changed,
        panel_spec(),
        network_spec=NetworkSpec(dynamic_window=3),
    ).frame
    columns = [
        "timestamp",
        "window",
        "eligibility_status",
        "dominant_eigenvalue_share",
        "network_density",
        "network_modularity",
        "mst_total_distance",
    ]
    pd.testing.assert_frame_equal(
        baseline.loc[baseline["timestamp"] <= cutoff, columns].reset_index(drop=True),
        altered.loc[altered["timestamp"] <= cutoff, columns].reset_index(drop=True),
    )


def test_dynamic_market_structure_outputs_are_present() -> None:
    result = compute_market_structure_feature_frame(
        synthetic_panel(),
        panel_spec(),
        network_spec=NetworkSpec(dynamic_window=3),
    )
    eligible = result.frame.loc[result.frame["eligibility_status"] == "ELIGIBLE"]
    for column in (
        "dominant_eigenvalue_share_velocity",
        "dominant_eigenvalue_share_acceleration",
        "network_density_velocity",
        "network_modularity_velocity",
        "mst_total_distance_velocity",
        "eigenvector_instability",
        "market_mode_strength",
    ):
        assert column in result.frame
    assert eligible["dominant_eigenvalue_share_velocity"].notna().sum() > 0
    assert result.manifest.output_sha256


def test_insufficient_coverage_fails_closed() -> None:
    frame = synthetic_panel(periods=30)
    cutoff = frame["timestamp"].unique()[10]
    frame = frame.loc[~((frame["asset"] == "ETH") & (frame["timestamp"] >= cutoff))]
    result = compute_market_structure_feature_frame(frame, panel_spec())
    assert "INSUFFICIENT_PANEL_COVERAGE" in set(result.frame["eligibility_status"])


def test_output_is_deterministic() -> None:
    frame = synthetic_panel()
    left = compute_market_structure_feature_frame(
        frame,
        panel_spec(),
        network_spec=NetworkSpec(dynamic_window=3),
    )
    right = compute_market_structure_feature_frame(
        frame.sample(frac=1.0, random_state=4),
        panel_spec(),
        network_spec=NetworkSpec(dynamic_window=3),
    )
    pd.testing.assert_frame_equal(left.frame, right.frame)
    assert left.manifest.manifest_sha256 == right.manifest.manifest_sha256
