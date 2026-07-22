from pathlib import Path


def test_d2c_asset_verifier_is_present() -> None:
    assert Path("scripts/verify_v2_d2c_assets.py").exists()
