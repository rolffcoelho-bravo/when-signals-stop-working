
import json
from pathlib import Path


def test_d4_config_preserves_frozen_pipeline_and_family() -> None:
    payload = json.loads(Path("configs/v2_d4_confirmatory_inference.json").read_text(encoding="utf-8"))
    assert payload["expected_signal_family"] == "bollinger"
    assert payload["confirmatory_family"][0]["confirmatory_p_value"] == 1.0
    assert payload["governance"]["pipeline_retuning_permitted"] is False
    assert payload["governance"]["rsi_reentry_permitted"] is False
    assert payload["governance"]["panic_state_extension_in_confirmatory_verdict"] is False


def test_block_length_exception_is_explicit() -> None:
    text = Path("docs/V2_D4_EXECUTION_EXCEPTION.md").read_text(encoding="utf-8")
    assert "did not materialize" in text
    assert "late materialization" in text
    assert "No D3 probability" in text
