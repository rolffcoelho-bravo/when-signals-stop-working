#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="$(pwd)/src"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

echo "GATE V3-4A - INDEPENDENT CHRONOLOGY AND SIGNAL-USE CONTRACT"
python -m pytest -q tests/test_v3_external_chronology_signal_use_contract.py
python scripts/validate_v3_g4a_contract.py
echo "Gate V3-4A contract evidence passed."
