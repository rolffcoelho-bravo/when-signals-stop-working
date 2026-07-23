from pathlib import Path


def test_d2a_asset_verifier_is_present() -> None:
    assert Path("scripts/verify_v2_d2a_assets.py").exists()
