#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Repository Python environment not found: $PYTHON" >&2
  exit 1
fi

echo
echo "TECHNICAL SIGNAL VALIDITY FRAMEWORK"
echo "Version 2 D5 Robustness and Publication Evidence"
echo "===================================================="

echo
echo "1. Verifying prior governance locks"

for script in \
  verify_v2_protocol_lock.py \
  verify_v2_d0_lock.py \
  verify_v2_d1_lock.py \
  verify_v2_d2a_lock.py \
  verify_v2_d2b_lock.py \
  verify_v2_d2c_lock.py \
  verify_v2_d3_lock.py \
  verify_v2_d3_assets.py \
  verify_v2_d4_lock.py \
  verify_v2_d4_assets.py \
  verify_v2_d5_lock.py
do
  "$PYTHON" "scripts/$script"
done

echo
echo "2. Building D5 robustness and publication evidence"
"$PYTHON" scripts/build_v2_d5_assets.py

echo
echo "3. Verifying D5 assets"
"$PYTHON" scripts/verify_v2_d5_assets.py

echo
echo "4. Running the complete implementation test suite"
"$PYTHON" -m pytest -q

echo
echo "VERSION 2 D5 ROBUSTNESS AND PUBLICATION COMPLETED."
echo "Final evidence grade:        NO_INCREMENTAL_EVIDENCE"
echo "Primary case established:    False"
echo "Pipeline retuning performed: False"
echo "RSI re-entry performed:      False"
echo "V2.1 panic extension used:   False"
