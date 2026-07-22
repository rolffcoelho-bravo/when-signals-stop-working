#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON=".venv/bin/python"
"$PYTHON" scripts/verify_v2_protocol_lock.py
"$PYTHON" scripts/verify_v2_d0_lock.py
"$PYTHON" scripts/verify_v2_d1_lock.py
"$PYTHON" scripts/verify_v2_d2a_lock.py
"$PYTHON" scripts/build_v2_d2a_assets.py
"$PYTHON" scripts/verify_v2_d2a_assets.py
"$PYTHON" -m pytest -q
