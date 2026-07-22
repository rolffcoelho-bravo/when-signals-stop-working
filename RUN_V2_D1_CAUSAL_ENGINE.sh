#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON=".venv/bin/python"

printf '\nTECHNICAL SIGNAL VALIDITY FRAMEWORK\n'
printf 'Version 2 D1 Causal Feature and Filtered-State Engine\n'
printf '=======================================================\n'

"$PYTHON" scripts/verify_v2_protocol_lock.py
"$PYTHON" scripts/verify_v2_d0_lock.py
"$PYTHON" scripts/verify_v2_d1_lock.py
"$PYTHON" scripts/build_v2_d1_assets.py
"$PYTHON" scripts/verify_v2_d1_assets.py
"$PYTHON" -m pytest -q

printf '\nVERSION 2 D1 CAUSAL ENGINE COMPLETED.\n'
printf 'Predictive model fitting performed: False\n'
printf 'State-filter fitting performed: True\n'
printf 'Holdout performance accessed: False\n'
