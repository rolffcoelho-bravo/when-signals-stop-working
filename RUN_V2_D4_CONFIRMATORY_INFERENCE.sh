
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON=".venv/bin/python"

printf '\nTECHNICAL SIGNAL VALIDITY FRAMEWORK\n'
printf 'Version 2 D4 Confirmatory Inference and Economic Gates\n'
printf '=========================================================\n'

"$PYTHON" scripts/verify_v2_protocol_lock.py
"$PYTHON" scripts/verify_v2_d0_lock.py
"$PYTHON" scripts/verify_v2_d1_lock.py
"$PYTHON" scripts/verify_v2_d2a_lock.py
"$PYTHON" scripts/verify_v2_d2b_lock.py
"$PYTHON" scripts/verify_v2_d2c_lock.py
"$PYTHON" scripts/verify_v2_d3_lock.py
"$PYTHON" scripts/verify_v2_d3_assets.py
"$PYTHON" scripts/verify_v2_d4_lock.py
"$PYTHON" scripts/build_v2_d4_assets.py
"$PYTHON" scripts/verify_v2_d4_assets.py
"$PYTHON" -m pytest -q
