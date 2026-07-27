#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$ROOT/src"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
unset PYTHONNOUSERSITE

printf '%s\n' 'GATE V3-REALIGNMENT - RICHARD QUESTION AND CORE SEQUENCE'
python -m pytest -q tests/test_v3_realignment_contract.py
python scripts/verify_v3_realignment.py
printf '%s\n' 'Version 3 repository realignment evidence passed.'
