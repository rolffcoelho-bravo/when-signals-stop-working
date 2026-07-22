import json
import subprocess
from pathlib import Path


def test_d3_lock_metadata_and_verifier() -> None:
    payload = json.loads(Path("V2_D3_EVALUATION_LOCK.json").read_text(encoding="utf-8"))
    assert payload["expected_parent_commit"] == "5153f2e"
    assert payload["expected_pipeline_hash"] == "2f85b54f8f178ec59c2bfb8a06cd8dedb3e053e2bec4da40cb446d380def2851"
    assert payload["single_access"] is True
    result = subprocess.run(
        ["python", "scripts/verify_v2_d3_lock.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
