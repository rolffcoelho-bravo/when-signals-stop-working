#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$ROOT/src"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
unset PYTHONNOUSERSITE || true

cd "$ROOT"
echo "GATE V3-5 - MATCHED FORECAST CONTRACT"
echo "1. VERIFYING FINAL V3-4 PARENT LOCK"
python scripts/verify_v3_g4_lock.py

echo "2. RUNNING V3-5 CONTRACT TESTS"
python -m pytest -q tests/test_v3_g5_contract.py

echo "3. RUNNING STANDALONE V3-5 CONTRACT VERIFIER"
python scripts/verify_v3_g5_contract.py

echo "4. VERIFYING PATCH INTEGRITY"
git diff --check

echo "Gate V3-5 contract evidence passed."
echo "Target access and development model fitting remain disabled."
echo "V3-9 final-framework reserve remains inaccessible."
