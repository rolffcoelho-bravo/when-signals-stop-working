from pathlib import Path


def test_d4_verifier_does_not_hardcode_validation_run_outcomes() -> None:
    verifier = Path("scripts/verify_v2_d4_assets.py").read_text(encoding="utf-8")
    assert 'positive_subperiods != 1' not in verifier
    assert 'mean_incremental_net_return"]) < 0.0' not in verifier
    assert "positive_subperiods != int(predictive_gate" in verifier
    assert "economic_checks != economic_gate" in verifier


def test_d4_interpretation_is_generated_from_observed_evidence() -> None:
    builder = Path("scripts/build_v2_d4_assets.py").read_text(encoding="utf-8")
    assert "primary_economic_interval.mean > 0.0" in builder
    assert "predictive_gate_pass else 'did not pass'" in builder
    assert "Its matched economic contribution at the primary cost was also negative." not in builder


def test_d4_erratum_declares_no_methodological_change() -> None:
    text = Path("docs/V2_D4_VERIFIER_ERRATUM.md").read_text(encoding="utf-8")
    assert "empirical outcomes" in text
    assert "does not change" in text
    assert "D3 predictions" in text