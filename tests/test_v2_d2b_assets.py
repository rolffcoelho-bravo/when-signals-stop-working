from pathlib import Path


def test_d2b_asset_verifier_is_present() -> None:
    assert Path("scripts/verify_v2_d2b_assets.py").exists()
