from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v3.panic_regime import (
    PANIC_REGIME_SCHEMA_VERSION,
    PanicRegimeConfig,
    PanicRegimeError,
    compute_panic_regime_probabilities,
)
from shockbridge_signal_validity.v3.panic_regime_runner import (
    run_panic_regime_engine,
)


def _fixture(rows: int = 120, seed: int = 11) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    timestamps = pd.date_range(
        "2024-01-01",
        periods=rows,
        freq="4h",
        tz="UTC",
    )
    stress = np.r_[np.zeros(rows // 2), np.ones(rows - rows // 2)]
    market = pd.DataFrame(
        {
            "timestamp": timestamps,
            "window": 30,
            "eligibility_status": "ELIGIBLE",
            "dominant_eigenvalue_share": 0.25 + 0.45 * stress + rng.normal(0, 0.01, rows),
            "eigenvalue_gap": 0.05 + 0.35 * stress + rng.normal(0, 0.01, rows),
            "participation_ratio": 4.5 - 2.5 * stress + rng.normal(0, 0.05, rows),
            "spectral_entropy": 0.9 - 0.45 * stress + rng.normal(0, 0.01, rows),
            "first_eigenvector_concentration": 0.2 + 0.4 * stress + rng.normal(0, 0.01, rows),
            "eigenvector_instability": 0.1 + 0.5 * stress + rng.normal(0, 0.01, rows),
            "network_density": 0.2 + 0.6 * stress + rng.normal(0, 0.01, rows),
            "network_average_clustering": 0.2 + 0.6 * stress + rng.normal(0, 0.01, rows),
            "network_modularity": 0.7 - 0.5 * stress + rng.normal(0, 0.01, rows),
            "network_connectivity_share": 0.3 + 0.65 * stress + rng.normal(0, 0.01, rows),
            "betweenness_centrality_concentration": 0.2 + 0.4 * stress + rng.normal(0, 0.01, rows),
            "eigenvector_centrality_concentration": 0.2 + 0.4 * stress + rng.normal(0, 0.01, rows),
            "mst_total_distance": 8.0 - 5.0 * stress + rng.normal(0, 0.05, rows),
        }
    )
    records: list[dict[str, object]] = []
    for index, timestamp in enumerate(timestamps):
        state = stress[index]
        for member in ("SOL@binance", "BTC@binance", "ETH@binance"):
            records.append(
                {
                    "timestamp": timestamp,
                    "series_id": member,
                    "log_return_1": rng.normal(-0.01 * state, 0.01 + 0.02 * state),
                    "bid_ask_spread_z": rng.normal(3.0 * state, 0.10),
                    "order_book_depth_log_change": rng.normal(-0.10 * state, 0.01),
                    "order_book_imbalance": rng.normal(0.0, 0.10 + 1.20 * state),
                    "cross_venue_price_dispersion": abs(rng.normal(0.001 + 0.02 * state, 0.001)),
                    "funding_stress_z": rng.normal(3.0 * state, 0.10),
                    "open_interest_log_change": rng.normal(0.0, 0.01 + 0.07 * state),
                    "liquidation_intensity": abs(rng.normal(0.001 + 0.05 * state, 0.001)),
                    "net_liquidation_pressure": rng.normal(0.0, 0.01 + 0.07 * state),
                    "downside_semivariance": abs(rng.normal(0.0001 + 0.005 * state, 0.00005)),
                    "abnormal_volume_z": rng.normal(2.0 * state, 0.10),
                    "drawdown": rng.normal(-0.01 - 0.40 * state, 0.01),
                    "drawdown_velocity": rng.normal(-0.05 * state, 0.005),
                    "downside_return_acceleration": rng.normal(-0.03 * state, 0.005),
                    "realised_volatility_18": abs(rng.normal(0.01 + 0.08 * state, 0.003)),
                    "realised_volatility_42": abs(rng.normal(0.01 + 0.08 * state, 0.003)),
                }
            )
    return market, pd.DataFrame(records)


def _config() -> PanicRegimeConfig:
    return PanicRegimeConfig(
        dependence_window=30,
        reference_series_id="SOL@binance",
        minimum_prior_observations=20,
        scaling_refit_interval=5,
        challenger_minimum_history=30,
        hmm_minimum_history=40,
        hmm_refit_interval=10,
        hmm_max_iter=8,
        minimum_state_occupancy_count=5,
    )


def test_config_requires_stable_reference_identifier() -> None:
    with pytest.raises(PanicRegimeError):
        PanicRegimeConfig(dependence_window=30, reference_series_id="SOL")


def test_engine_reports_every_registered_model_without_selection() -> None:
    market, series = _fixture()
    result = compute_panic_regime_probabilities(market, series, _config())
    assert result.manifest.schema_version == PANIC_REGIME_SCHEMA_VERSION
    assert set(result.probabilities["model_id"]) == set(result.manifest.model_ids)
    assert result.manifest.automatic_model_selection_performed is False
    assert result.manifest.automatic_ensemble_performed is False
    assert result.diagnostics["consensus_probability_produced"] is False


def test_monotone_probability_is_bounded_and_increases_under_concurrence() -> None:
    market, series = _fixture()
    result = compute_panic_regime_probabilities(market, series, _config())
    probability = result.probabilities.loc[
        result.probabilities["model_id"] == "MONOTONE_MECHANISM_SCORE_V1"
    ].reset_index(drop=True)
    valid = probability["filtered_probability"].dropna()
    assert valid.between(0.0, 1.0).all()
    midpoint = len(probability) // 2
    assert (
        probability.loc[midpoint:, "filtered_probability"].mean()
        > probability.loc[: midpoint - 1, "filtered_probability"].mean()
    )


def test_missing_market_plumbing_evidence_fails_closed() -> None:
    market, series = _fixture()
    series = series.drop(
        columns=[
            "bid_ask_spread_z",
            "order_book_depth_log_change",
            "order_book_imbalance",
            "cross_venue_price_dispersion",
            "funding_stress_z",
            "open_interest_log_change",
            "liquidation_intensity",
            "net_liquidation_pressure",
        ]
    )
    result = compute_panic_regime_probabilities(market, series, _config())
    monotone = result.probabilities.loc[
        result.probabilities["model_id"] == "MONOTONE_MECHANISM_SCORE_V1"
    ]
    assert monotone["filtered_probability"].isna().all()
    assert set(monotone["operational_state"]) == {
        "INSUFFICIENT_MECHANISM_EVIDENCE"
    }


def test_future_append_cannot_change_earlier_probabilities() -> None:
    market, series = _fixture()
    base = compute_panic_regime_probabilities(market, series, _config())
    extra_market, extra_series = _fixture(rows=20, seed=99)
    offset = market["timestamp"].max() + pd.Timedelta(hours=4)
    new_timestamps = pd.date_range(offset, periods=20, freq="4h", tz="UTC")
    extra_market["timestamp"] = new_timestamps
    mapping = dict(zip(sorted(extra_series["timestamp"].unique()), new_timestamps))
    extra_series["timestamp"] = extra_series["timestamp"].map(mapping)
    extended = compute_panic_regime_probabilities(
        pd.concat([market, extra_market], ignore_index=True),
        pd.concat([series, extra_series], ignore_index=True),
        _config(),
    )
    earlier = extended.probabilities.loc[
        extended.probabilities["timestamp"] <= market["timestamp"].max()
    ].reset_index(drop=True)
    pd.testing.assert_frame_equal(
        base.probabilities.reset_index(drop=True),
        earlier,
        check_exact=False,
        rtol=1e-12,
        atol=1e-12,
    )


def test_shuffled_input_produces_identical_manifest_identity() -> None:
    market, series = _fixture()
    first = compute_panic_regime_probabilities(market, series, _config())
    second = compute_panic_regime_probabilities(
        market.sample(frac=1.0, random_state=4),
        series.sample(frac=1.0, random_state=8),
        _config(),
    )
    assert first.manifest.manifest_sha256 == second.manifest.manifest_sha256
    pd.testing.assert_frame_equal(first.probabilities, second.probabilities)


def test_transparent_challenger_never_claims_panic_probability() -> None:
    market, series = _fixture()
    result = compute_panic_regime_probabilities(market, series, _config())
    challenger = result.probabilities.loc[
        result.probabilities["model_id"]
        == "V2_TRANSPARENT_STATE_CHALLENGER_V1"
    ]
    assert challenger["panic_probability_authorized"].eq(False).all()
    assert challenger["filtered_probability"].isna().all()
    assert set(challenger["operational_state"]) == {"NOT_AUTHORIZED_FOR_PANIC"}
    valid = challenger.loc[
        challenger["model_validity"] == "VALID_TRANSPARENT_CHALLENGER"
    ]
    assert np.allclose(
        valid[["p_range", "p_trend", "p_stress"]].sum(axis=1),
        1.0,
    )


def test_hmm_is_forward_filtered_bounded_and_anchored() -> None:
    market, series = _fixture()
    result = compute_panic_regime_probabilities(market, series, _config())
    hmm = result.probabilities.loc[
        result.probabilities["model_id"] == "CAUSAL_GAUSSIAN_HMM_V1"
    ]
    valid = hmm.loc[
        hmm["model_validity"]
        == "VALID_IMPLEMENTATION_PROBABILITY_UNCERTAINTY_PENDING",
        "filtered_probability",
    ]
    assert not valid.empty
    assert valid.between(0.0, 1.0).all()
    valid_refits = [
        record for record in result.diagnostics["hmm_refits"] if record["valid"]
    ]
    assert valid_refits
    assert all(record["directional_family_count"] >= 4 for record in valid_refits)


def test_ineligible_market_row_cannot_supply_structural_evidence() -> None:
    market, series = _fixture()
    market.loc[50, "eligibility_status"] = "INSUFFICIENT_PANEL_COVERAGE"
    result = compute_panic_regime_probabilities(market, series, _config())
    row = result.mechanism_scores.iloc[50]
    assert pd.isna(row["spectral_score"])
    assert pd.isna(row["network_score"])
    assert row["evidence_sufficiency"] == "INSUFFICIENT_MECHANISM_EVIDENCE"


def test_ambiguous_contagion_radius_is_excluded() -> None:
    market, series = _fixture()
    market["contagion_radius"] = np.linspace(0.1, 1.0, len(market))
    result = compute_panic_regime_probabilities(market, series, _config())
    assert "network__contagion_radius__score" not in result.mechanism_scores
    assert "contagion_radius" in result.diagnostics["excluded_ambiguous_features"]


def test_runner_writes_governed_preliminary_evidence(tmp_path: Path) -> None:
    market, series = _fixture()
    market_path = tmp_path / "market.csv"
    series_path = tmp_path / "series.csv"
    market.to_csv(market_path, index=False)
    series.to_csv(series_path, index=False)
    output = tmp_path / "output"
    run_panic_regime_engine(
        {
            "market_structure_path": str(market_path),
            "causal_series_path": str(series_path),
            "engine": _config().to_dict(),
        },
        output,
    )
    expected = {
        "panic_regime_probability.csv",
        "mechanism_family_scores.csv",
        "regime_manifest.json",
        "regime_validation_report.json",
        "probability_engine_diagnostics.json",
    }
    assert expected == {path.name for path in output.iterdir()}
    validation = json.loads(
        (output / "regime_validation_report.json").read_text(encoding="utf-8")
    )
    assert validation["final_v3_3_lock_permitted"] is False
    assert validation["next_subgate"] == "V3-3C — Governance and Diagnostics"
    assert validation["uncertainty_intervals_complete"] is False
