
import json
from pathlib import Path
import subprocess


def test_d4_lock_metadata() -> None:
    payload = json.loads(Path("V2_D4_INFERENCE_LOCK.json").read_text(encoding="utf-8"))
    assert payload["checkpoint"] == "V2_D4_CONFIRMATORY_INFERENCE_AND_ECONOMIC_GATES"
    assert payload["expected_parent_commit"] == "d0872b9"
    assert payload["expected_pipeline_hash"] == "2f85b54f8f178ec59c2bfb8a06cd8dedb3e053e2bec4da40cb446d380def2851"
    assert payload["pipeline_retuning_permitted"] is False


def test_d4_lock_verifier() -> None:
    result = subprocess.run(["python", "scripts/verify_v2_d4_lock.py"], check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
