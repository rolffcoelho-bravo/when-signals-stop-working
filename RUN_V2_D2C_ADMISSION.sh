#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python}"

printf '\nTECHNICAL SIGNAL VALIDITY FRAMEWORK\n'
printf 'Version 2 D2C Development Admission and Pipeline Freeze\n'
printf '==========================================================\n'

"$PYTHON" scripts/verify_v2_protocol_lock.py
"$PYTHON" scripts/verify_v2_d0_lock.py
"$PYTHON" scripts/verify_v2_d1_lock.py
"$PYTHON" scripts/verify_v2_d2a_lock.py
"$PYTHON" scripts/verify_v2_d2b_lock.py
"$PYTHON" scripts/verify_v2_d2c_lock.py
"$PYTHON" scripts/build_v2_d2c_assets.py
"$PYTHON" scripts/verify_v2_d2c_assets.py
"$PYTHON" -m pytest -q

printf '\nVERSION 2 D2C ADMISSION COMPLETED.\n'
printf 'Economic gate evaluated: False\n'
printf 'Holdout authorization enabled: False\n'
printf 'Holdout performance accessed: False\n'
