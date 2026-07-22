import json
from pathlib import Path


def test_d3_config_freezes_single_bollinger_access() -> None:
    payload = json.loads(Path("configs/v2_d3_locked_evaluation.json").read_text(encoding="utf-8"))
    assert payload["expected_frozen_pipeline_count"] == 1
    assert payload["expected_signal_family"] == "bollinger"
    assert payload["authorization"]["forbidden_signal_families"] == ["rsi"]
    assert payload["governance"]["pipeline_retuning_permitted"] is False
    assert payload["governance"]["statistical_gate_evaluated"] is False
    assert payload["governance"]["economic_gate_evaluated"] is False


def test_v21_panic_scope_is_separate_from_confirmatory_v2() -> None:
    text = Path("docs/V2_1_PANIC_STATE_EXTENSION_SCOPE.md").read_text(encoding="utf-8")
    assert "secondary diagnostic" in text
    assert "must not modify" in text
    assert "PANIC_CONSISTENT_REGIME" in text
