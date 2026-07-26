from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "v3_panic_regime_identification.json"
REGISTRY = ROOT / "configs" / "v3_panic_regime_model_registry.json"

REQUIRED_OUTPUTS = {
    "panic_regime_probability.csv",
    "transition_matrix.json",
    "state_duration.csv",
    "occupancy_statistics.json",
    "mechanism_contributions.csv",
    "probability_diagnostics.json",
    "regime_manifest.json",
    "regime_validation_report.json",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_latent_claim_boundary_is_explicit() -> None:
    contract = load(CONTRACT)
    target = contract["scientific_target"]
    assert target["latent_state"] is True
    assert "not a direct observation" in target["claim_boundary"].lower()
    assert "volatility-only panic classification" in target["prohibited_claims"]


def test_causal_scaling_is_prefix_invariant() -> None:
    contract = load(CONTRACT)
    scaling = contract["causal_scaling"]
    assert scaling["reference_information"] == "strictly_prior_observations_only"
    assert scaling["future_revisions_prohibited"] is True
    assert scaling["prefix_invariance_required"] is True
    assert scaling["minimum_prior_observations"] >= 250


def test_evidence_sufficiency_fails_closed() -> None:
    contract = load(CONTRACT)
    rule = contract["evidence_sufficiency"]
    assert rule["minimum_available_mechanism_families"] >= 4
    assert len(rule["required_blocks"]) == 3
    assert rule["failure_state"] == "INSUFFICIENT_MECHANISM_EVIDENCE"
    assert rule["single_family_dominance_prohibited"] is True


def test_all_six_mechanism_families_are_registered() -> None:
    contract = load(CONTRACT)
    observed = {family["id"] for family in contract["mechanism_families"]}
    assert observed == {
        "spectral",
        "network",
        "liquidity",
        "funding",
        "volatility",
        "downside",
    }


def test_model_selection_and_consensus_are_prohibited() -> None:
    contract = load(CONTRACT)
    registry = load(REGISTRY)
    reporting = contract["probability_and_reporting"]
    assert reporting["automatic_model_selection"] is False
    assert reporting["automatic_ensemble"] is False
    assert reporting["consensus_probability_prohibited"] is True
    assert registry["automatic_model_selection"] is False
    assert registry["automatic_ensemble"] is False
    assert registry["reporting_policy"]["consensus_probability_prohibited"] is True


def test_registered_models_are_mandatory_and_non_ranked() -> None:
    registry = load(REGISTRY)
    enabled = [model for model in registry["registered_models"] if model["enabled"]]
    assert len(enabled) == 3
    assert all(model["mandatory"] for model in enabled)
    assert all(model["selection_eligible"] is False for model in enabled)
    assert all(model["rankable"] is False for model in enabled)
    challenger = next(
        model
        for model in enabled
        if model["model_id"] == "V2_TRANSPARENT_STATE_CHALLENGER_V1"
    )
    assert challenger["panic_probability_authorized"] is False


def test_supervised_logistic_requires_external_labels() -> None:
    registry = load(REGISTRY)
    enabled_ids = {
        model["model_id"]
        for model in registry["registered_models"]
        if model["enabled"]
    }
    prohibited = {
        model["model_id"]
        for model in registry["prohibited_without_external_label_registry"]
    }
    assert "SUPERVISED_LOGISTIC_PANIC_V1" not in enabled_ids
    assert "SUPERVISED_LOGISTIC_PANIC_V1" in prohibited


def test_uncertainty_occupancy_label_control_and_outputs_are_frozen() -> None:
    contract = load(CONTRACT)
    assert contract["uncertainty"]["coverage"] == 0.95
    assert (
        contract["uncertainty"]["minimum_valid_replications"]
        <= contract["uncertainty"]["replications"]
    )
    assert contract["label_switching_control"]["required"] is True
    assert (
        contract["occupancy_and_duration"][
            "minimum_operational_episode_observations"
        ]
        >= 2
    )
    assert (
        contract["occupancy_and_duration"]["retroactive_backfill_prohibited"]
        is True
    )
    assert set(contract["required_final_gate_outputs"]) == REQUIRED_OUTPUTS
