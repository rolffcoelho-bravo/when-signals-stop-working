from __future__ import annotations

from pathlib import Path

from shockbridge_signal_validity.v3.forecast_model_registry import (
    build_pipeline_registry,
    load_contracts,
    pipeline_registry_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
FORECAST_CONTRACT = ROOT / "configs" / "v3_g5_forecast_contract.json"
IMPLEMENTATION_CONTRACT = ROOT / "configs" / "v3_g5_model_implementation_contract.json"


def _registry():
    forecast, implementation = load_contracts(
        FORECAST_CONTRACT,
        IMPLEMENTATION_CONTRACT,
    )
    return forecast, implementation, build_pipeline_registry(forecast, implementation)


def test_pipeline_registry_has_frozen_bounded_identity() -> None:
    _, _, registry = _registry()
    assert len(registry) == 162
    assert sum(spec.executable for spec in registry) == 153
    assert sum(not spec.executable for spec in registry) == 9
    assert len({spec.pipeline_spec_id for spec in registry}) == 162


def test_each_target_has_54_specs_and_51_executable_specs() -> None:
    _, _, registry = _registry()
    for target in ("direction", "expected_return", "large_move_probability"):
        target_specs = [spec for spec in registry if spec.target_name == target]
        assert len(target_specs) == 54
        assert sum(spec.executable for spec in target_specs) == 51
        assert sum(not spec.executable for spec in target_specs) == 3


def test_each_target_window_has_17_executable_and_one_gated_spec() -> None:
    _, _, registry = _registry()
    for target in ("direction", "expected_return", "large_move_probability"):
        for window in ("EXPANDING", "ROLLING_ONE_YEAR", "ROLLING_TWO_YEARS"):
            block = [
                spec
                for spec in registry
                if spec.target_name == target and spec.window_id == window
            ]
            assert len(block) == 18
            assert sum(spec.executable for spec in block) == 17
            assert sum(not spec.executable for spec in block) == 1


def test_model_families_and_windows_match_frozen_contract() -> None:
    _, _, registry = _registry()
    assert {spec.model_family for spec in registry} == {
        "regularized_linear",
        "spline_regularized",
        "shallow_hist_gradient_boosting",
        "time_varying_regularized_glm",
        "state_space_or_markov_switching",
    }
    assert {spec.window_id for spec in registry} == {
        "EXPANDING",
        "ROLLING_ONE_YEAR",
        "ROLLING_TWO_YEARS",
    }


def test_registry_is_deterministic() -> None:
    forecast, implementation, first = _registry()
    second = build_pipeline_registry(forecast, implementation)
    assert first == second


def test_state_space_family_remains_explicitly_gated() -> None:
    _, _, registry = _registry()
    gated = [spec for spec in registry if not spec.executable]
    assert len(gated) == 9
    assert {spec.model_family for spec in gated} == {"state_space_or_markov_switching"}
    assert {spec.ineligibility_status for spec in gated} == {
        "INELIGIBLE_IMPLEMENTATION_NOT_AUTHORIZED"
    }


def test_registry_manifest_reports_no_fitting_or_selection() -> None:
    _, _, registry = _registry()
    manifest = pipeline_registry_manifest(registry)
    assert manifest["pipeline_specifications"] == 162
    assert manifest["executable_pipeline_specifications"] == 153
    assert manifest["gated_pipeline_specifications"] == 9
    assert manifest["automatic_selection_performed"] is False
    assert manifest["real_development_model_fitting_performed"] is False
