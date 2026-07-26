from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v3.panic_regime_diagnostics import (
    DIAGNOSTICS_SCHEMA_VERSION,
    FAMILY_ORDER,
    PanicRegimeDiagnosticsConfig,
    PanicRegimeDiagnosticsError,
    causal_confirm_states,
    compute_panic_regime_governance,
)
from shockbridge_signal_validity.v3.panic_regime_diagnostics_runner import (
    run_panic_regime_diagnostics,
)


def _fixture(rows: int = 140, seed: int = 17):
    rng = np.random.default_rng(seed)
    timestamps = pd.date_range("2024-01-01", periods=rows, freq="4h", tz="UTC")
    phase = np.linspace(0.0, 1.0, rows)
    family_scores = {
        family: np.clip(
            0.15 + 0.75 * phase + rng.normal(0.0, 0.025, rows),
            0.01,
            0.99,
        )
        for family in FAMILY_ORDER
    }
    mechanism = pd.DataFrame({"timestamp": timestamps})
    for family, values in family_scores.items():
        mechanism[f"{family}_score"] = values
        mechanism[f"{family}_valid_feature_count"] = 3
        mechanism[f"{family}_registered_feature_count"] = 3
    mechanism["available_mechanism_count"] = 6
    mechanism["structural_evidence_available"] = True
    mechanism["plumbing_evidence_available"] = True
    mechanism["price_risk_evidence_available"] = True
    mechanism["evidence_sufficiency"] = "SUFFICIENT"
    mechanism["composite_mechanism_score"] = mechanism[
        [f"{family}_score" for family in FAMILY_ORDER]
    ].mean(axis=1)

    raw_monotone = 1.0 / (
        1.0
        + np.exp(
            -6.0 * (mechanism["composite_mechanism_score"].to_numpy() - 0.5)
        )
    )
    filtered = np.empty(rows)
    previous = None
    for index, value in enumerate(raw_monotone):
        previous = value if previous is None else 0.35 * value + 0.65 * previous
        filtered[index] = previous
    hmm_probability = np.clip(
        1.0 / (1.0 + np.exp(-16.0 * (phase - 0.72)))
        + rng.normal(0, 0.012, rows),
        0.001,
        0.999,
    )

    def state(probability: float) -> str:
        if probability < 0.25:
            return "LOW_PANIC_CONSISTENCY"
        if probability < 0.50:
            return "STRESS_BUILDING"
        if probability < 0.75:
            return "TRANSMISSION_ESCALATION"
        return "PANIC_CONSISTENT_REGIME"

    probability_rows = []
    for index, timestamp in enumerate(timestamps):
        challenger_values = np.asarray(
            [
                max(0.01, 0.75 - phase[index]),
                0.20,
                min(0.79, 0.05 + phase[index]),
            ]
        )
        challenger_values /= challenger_values.sum()
        probability_rows.append(
            {
                "timestamp": timestamp,
                "model_id": "V2_TRANSPARENT_STATE_CHALLENGER_V1",
                "raw_probability": np.nan,
                "filtered_probability": np.nan,
                "lower_95": np.nan,
                "upper_95": np.nan,
                "p_range": challenger_values[0],
                "p_trend": challenger_values[1],
                "p_stress": challenger_values[2],
                "operational_state": "NOT_AUTHORIZED_FOR_PANIC",
                "available_mechanism_count": 6,
                "evidence_sufficiency": "SUFFICIENT",
                "model_validity": "VALID_TRANSPARENT_CHALLENGER",
                "panic_probability_authorized": False,
                "uncertainty_status": "NOT_APPLICABLE",
            }
        )
        for model_id, raw, point in (
            ("MONOTONE_MECHANISM_SCORE_V1", raw_monotone[index], filtered[index]),
            ("CAUSAL_GAUSSIAN_HMM_V1", hmm_probability[index], hmm_probability[index]),
        ):
            probability_rows.append(
                {
                    "timestamp": timestamp,
                    "model_id": model_id,
                    "raw_probability": raw,
                    "filtered_probability": point,
                    "lower_95": np.nan,
                    "upper_95": np.nan,
                    "p_range": np.nan,
                    "p_trend": np.nan,
                    "p_stress": np.nan,
                    "operational_state": state(point),
                    "available_mechanism_count": 6,
                    "evidence_sufficiency": "SUFFICIENT",
                    "model_validity": (
                        "VALID_IMPLEMENTATION_PROBABILITY_UNCERTAINTY_PENDING"
                    ),
                    "panic_probability_authorized": True,
                    "uncertainty_status": "PENDING_V3_3C",
                }
            )
    probabilities = pd.DataFrame(probability_rows)

    market = pd.DataFrame(
        {
            "timestamp": timestamps,
            "window": 30,
            "eligibility_status": "ELIGIBLE",
            "dominant_eigenvalue_share": family_scores["spectral"],
            "network_density": family_scores["network"],
            "contagion_radius": np.linspace(0.2, 0.8, rows),
        }
    )
    series_rows = []
    for timestamp_index, timestamp in enumerate(timestamps):
        for series_id in ("SOL@binance", "BTC@binance", "ETH@binance"):
            series_rows.append(
                {
                    "timestamp": timestamp,
                    "series_id": series_id,
                    "bid_ask_spread_z": family_scores["liquidity"][timestamp_index],
                    "funding_stress_z": family_scores["funding"][timestamp_index],
                    "realised_volatility_18": family_scores["volatility"][
                        timestamp_index
                    ],
                    "drawdown": -family_scores["downside"][timestamp_index],
                }
            )
    series = pd.DataFrame(series_rows)
    refit_specs = [(50, True), (80, True), (110, False)]
    engine_diagnostics = {
        "feature_registry": {
            "spectral__dominant_eigenvalue_share": {
                "family": "spectral",
                "source": "market",
                "source_column": "dominant_eigenvalue_share",
            },
            "network__network_density": {
                "family": "network",
                "source": "market",
                "source_column": "network_density",
            },
            "liquidity__bid_ask_spread_stress": {
                "family": "liquidity",
                "source": "series",
                "source_column": "bid_ask_spread_z",
            },
            "funding__funding_rate_stress": {
                "family": "funding",
                "source": "series",
                "source_column": "funding_stress_z",
            },
            "volatility__realised_volatility_18": {
                "family": "volatility",
                "source": "series",
                "source_column": "realised_volatility_18",
            },
            "downside__drawdown_magnitude": {
                "family": "downside",
                "source": "series",
                "source_column": "drawdown",
            },
        },
        "hmm_refits": [
            {
                "forecast_origin_index": index,
                "forecast_origin_timestamp": timestamps[index].isoformat(),
                "valid": valid,
            }
            for index, valid in refit_specs
            if index < rows
        ],
    }
    parent_manifest = {
        "manifest_sha256": "parent-manifest-sha",
        "dependence_window": 30,
        "reference_series_id": "SOL@binance",
    }
    return (
        probabilities,
        mechanism,
        market,
        series,
        engine_diagnostics,
        parent_manifest,
    )


def _config() -> PanicRegimeDiagnosticsConfig:
    return PanicRegimeDiagnosticsConfig(
        bootstrap_replications=80,
        minimum_valid_bootstrap_replications=60,
        minimum_interval_history=15,
        bootstrap_history_window=60,
        contribution_minimum_history=25,
        contribution_refit_interval=10,
        minimum_state_occupancy_count=5,
        scaling_minimum_prior_observations=20,
        scaling_refit_interval=5,
    )


def _run(rows: int = 140):
    fixture = _fixture(rows=rows)
    return compute_panic_regime_governance(*fixture, _config())


def test_config_rejects_invalid_threshold_sets() -> None:
    with pytest.raises(PanicRegimeDiagnosticsError):
        PanicRegimeDiagnosticsConfig(threshold_sensitivity=((0.5, 0.4, 0.7),))


def test_intervals_are_bounded_contain_point_and_gate_publication() -> None:
    result = _run()
    valid = result.probabilities.loc[result.probabilities["probability_publishable"]]
    assert not valid.empty
    assert valid["lower_95"].between(0.0, 1.0).all()
    assert valid["upper_95"].between(0.0, 1.0).all()
    assert (valid["lower_95"] <= valid["filtered_probability"]).all()
    assert (valid["filtered_probability"] <= valid["upper_95"]).all()
    early = result.probabilities.loc[
        result.probabilities["panic_probability_authorized"]
        & ~result.probabilities["probability_publishable"]
        & result.probabilities["filtered_probability"].notna()
    ]
    assert not early.empty
    assert set(early["uncertainty_status"]) == {
        "INSUFFICIENT_INTERVAL_HISTORY"
    }


def test_future_append_cannot_change_earlier_diagnostics() -> None:
    extended_fixture = _fixture(rows=140)
    probabilities, mechanism, market, series, engine_diagnostics, parent_manifest = (
        extended_fixture
    )
    cutoff = sorted(mechanism["timestamp"].unique())[109]
    base_probabilities = probabilities.loc[probabilities["timestamp"] <= cutoff].copy()
    base_mechanism = mechanism.loc[mechanism["timestamp"] <= cutoff].copy()
    base_market = market.loc[market["timestamp"] <= cutoff].copy()
    base_series = series.loc[series["timestamp"] <= cutoff].copy()
    base_engine_diagnostics = {
        **engine_diagnostics,
        "hmm_refits": [
            record
            for record in engine_diagnostics["hmm_refits"]
            if record["forecast_origin_index"] < 110
        ],
    }
    base = compute_panic_regime_governance(
        base_probabilities,
        base_mechanism,
        base_market,
        base_series,
        base_engine_diagnostics,
        parent_manifest,
        _config(),
    )
    extended = compute_panic_regime_governance(*extended_fixture, _config())
    earlier = extended.probabilities.loc[
        extended.probabilities["timestamp"] <= cutoff
    ].reset_index(drop=True)
    pd.testing.assert_frame_equal(base.probabilities.reset_index(drop=True), earlier)
    base_disagreement = base.disagreement.reset_index(drop=True)
    earlier_disagreement = extended.disagreement.loc[
        extended.disagreement["timestamp"] <= cutoff
    ].reset_index(drop=True)
    pd.testing.assert_frame_equal(base_disagreement, earlier_disagreement)


def test_causal_confirmation_does_not_backfill_transition() -> None:
    raw = [
        "LOW_PANIC_CONSISTENCY",
        "LOW_PANIC_CONSISTENCY",
        "PANIC_CONSISTENT_REGIME",
        "PANIC_CONSISTENT_REGIME",
    ]
    confirmed = causal_confirm_states(raw, confirmation_observations=2)
    assert confirmed == [
        "UNCONFIRMED_STATE",
        "LOW_PANIC_CONSISTENCY",
        "LOW_PANIC_CONSISTENCY",
        "PANIC_CONSISTENT_REGIME",
    ]


def test_transition_rows_sum_to_one_and_risks_are_bounded() -> None:
    result = _run()
    assert result.diagnostics["transition_rows_sum_to_one"] is True
    for payload in result.transition_matrix["operational_state_models"].values():
        assert payload["rows_sum_to_one"] is True
    risks = result.probabilities[
        "one_step_panic_transition_probability"
    ].dropna()
    latent = result.probabilities["one_step_latent_panic_probability"].dropna()
    assert risks.between(0.0, 1.0).all()
    assert latent.between(0.0, 1.0).all()


def test_duration_output_enforces_minimum_and_no_backfill() -> None:
    result = _run()
    assert not result.state_duration.empty
    assert result.state_duration["retroactive_backfill_performed"].eq(False).all()
    uncensored = result.state_duration.loc[~result.state_duration["right_censored"]]
    assert uncensored["duration_observations"].ge(2).all()


def test_hmm_occupancy_reports_model_boundary() -> None:
    result = _run()
    payload = result.occupancy_statistics["hmm_binary_latent_state"]
    assert payload["observations"] > 0
    assert payload["model_validity"] in {
        "VALID_OCCUPANCY",
        "MODEL_INVALID_COLLAPSED_STATE",
    }
    assert payload["minimum_required_count"] >= 5


def test_monotone_contributions_sum_to_raw_logit() -> None:
    result = _run()
    frame = result.mechanism_contributions.loc[
        result.mechanism_contributions["model_id"].eq(
            "MONOTONE_MECHANISM_SCORE_V1"
        )
    ]
    assert not frame.empty
    timestamp = frame["timestamp"].iloc[-1]
    row = frame.loc[frame["timestamp"].eq(timestamp)]
    observed = float(row["logit_contribution"].sum())
    probability = float(row["full_probability"].iloc[0])
    expected = float(np.log(probability / (1.0 - probability)))
    assert observed == pytest.approx(expected, abs=1e-10)


def test_hmm_contributions_are_causal_surrogate_not_exact_claim() -> None:
    result = _run()
    frame = result.mechanism_contributions.loc[
        result.mechanism_contributions["model_id"].eq(
            "CAUSAL_GAUSSIAN_HMM_V1"
        )
    ]
    assert not frame.empty
    assert set(frame["status"]) == {
        "VALID_DIAGNOSTIC_SURROGATE_NOT_EXACT_HMM_DECOMPOSITION"
    }
    assert result.diagnostics["contribution_diagnostics"][
        "hmm_surrogate_refits"
    ]


def test_disagreement_index_is_diagnostic_only() -> None:
    result = _run()
    valid = result.disagreement["disagreement_index"].dropna()
    assert not valid.empty
    assert valid.between(0.0, 1.0).all()
    assert result.disagreement["diagnostic_only"].eq(True).all()
    assert result.disagreement["model_selection_performed"].eq(False).all()
    assert "HIGH_MODEL_RISK_ESCALATION" in set(
        result.disagreement["disagreement_class"]
    )


def test_coverage_maps_asset_venue_and_governed_exclusion() -> None:
    result = _run()
    assert {
        "SOL@binance",
        "BTC@binance",
        "ETH@binance",
        "__MARKET_PANEL__",
    }.issubset(set(result.coverage["series_id"]))
    excluded = result.coverage.loc[result.coverage["governed_exclusion"]]
    assert set(excluded["feature"]) == {"network__contagion_radius"}
    assert result.coverage_summary["coverage_used_for_model_selection"] is False


def test_sensitivity_evidence_is_complete_and_nonselective() -> None:
    result = _run()
    assert set(result.sensitivity) >= {
        "threshold_sensitivity",
        "ewma_alpha_sensitivity",
        "scaling_refit_boundary_sensitivity",
        "hmm_refit_and_saturation_sensitivity",
    }
    assert result.sensitivity["automatic_selection_performed"] is False
    assert result.sensitivity["hmm_refit_and_saturation_sensitivity"][
        "refit_origins"
    ] == 3


def test_shuffled_input_produces_identical_manifest_and_outputs() -> None:
    probabilities, mechanism, market, series, engine_diagnostics, parent_manifest = (
        _fixture()
    )
    first = compute_panic_regime_governance(
        probabilities,
        mechanism,
        market,
        series,
        engine_diagnostics,
        parent_manifest,
        _config(),
    )
    second = compute_panic_regime_governance(
        probabilities.sample(frac=1.0, random_state=1),
        mechanism.sample(frac=1.0, random_state=2),
        market.sample(frac=1.0, random_state=3),
        series.sample(frac=1.0, random_state=4),
        engine_diagnostics,
        parent_manifest,
        _config(),
    )
    assert first.manifest.manifest_sha256 == second.manifest.manifest_sha256
    pd.testing.assert_frame_equal(first.probabilities, second.probabilities)
    pd.testing.assert_frame_equal(first.disagreement, second.disagreement)


def test_missing_feature_registry_fails_closed() -> None:
    probabilities, mechanism, market, series, _, parent_manifest = _fixture()
    with pytest.raises(PanicRegimeDiagnosticsError):
        compute_panic_regime_governance(
            probabilities,
            mechanism,
            market,
            series,
            {},
            parent_manifest,
            _config(),
        )


def test_runner_writes_complete_governance_package(tmp_path: Path) -> None:
    probabilities, mechanism, market, series, engine_diagnostics, parent_manifest = (
        _fixture()
    )
    engine_output = tmp_path / "engine"
    engine_output.mkdir()
    probabilities.to_csv(engine_output / "panic_regime_probability.csv", index=False)
    mechanism.to_csv(engine_output / "mechanism_family_scores.csv", index=False)
    (engine_output / "regime_manifest.json").write_text(
        json.dumps(parent_manifest), encoding="utf-8"
    )
    (engine_output / "probability_engine_diagnostics.json").write_text(
        json.dumps(engine_diagnostics), encoding="utf-8"
    )
    market_path = tmp_path / "market.csv"
    series_path = tmp_path / "series.csv"
    market.to_csv(market_path, index=False)
    series.to_csv(series_path, index=False)
    output = tmp_path / "governance"
    run_panic_regime_diagnostics(
        {
            "engine_output_directory": str(engine_output),
            "market_structure_path": str(market_path),
            "causal_series_path": str(series_path),
            "diagnostics": _config().to_dict(),
        },
        output,
    )
    expected = {
        "panic_regime_probability.csv",
        "transition_matrix.json",
        "state_duration.csv",
        "occupancy_statistics.json",
        "mechanism_contributions.csv",
        "cross_model_disagreement.csv",
        "mechanism_coverage.csv",
        "mechanism_coverage_summary.json",
        "mechanism_coverage_heatmap.svg",
        "sensitivity_diagnostics.json",
        "probability_diagnostics.json",
        "regime_manifest.json",
        "regime_validation_report.json",
    }
    assert expected == {path.name for path in output.iterdir()}
    validation = json.loads(
        (output / "regime_validation_report.json").read_text(encoding="utf-8")
    )
    assert (
        validation["status"]
        == "GOVERNANCE_AND_DIAGNOSTICS_COMPLETE_FINAL_ACCEPTANCE_PENDING"
    )
    assert validation["final_v3_3_lock_permitted"] is False
    assert validation["next_subgate"].startswith("V3-3D")
    manifest = json.loads(
        (output / "regime_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["schema_version"] == DIAGNOSTICS_SCHEMA_VERSION
    assert manifest["automatic_model_selection_performed"] is False
