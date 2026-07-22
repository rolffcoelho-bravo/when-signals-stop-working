#!/usr/bin/env bash
set -euo pipefail

export SHOCKBRIDGE_V2_HOLDOUT_AUTHORIZED=YES
python scripts/verify_v2_protocol_lock.py
python scripts/verify_v2_d0_lock.py
python scripts/verify_v2_d1_lock.py
python scripts/verify_v2_d2a_lock.py
python scripts/verify_v2_d2b_lock.py
python scripts/verify_v2_d2c_lock.py
python scripts/verify_v2_d3_lock.py
python scripts/build_v2_d3_assets.py
python scripts/verify_v2_d3_assets.py
python -m pytest -q
