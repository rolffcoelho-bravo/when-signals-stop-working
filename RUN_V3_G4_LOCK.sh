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
echo "GATE V3-4 - AUTHORITATIVE LOCK MATERIALIZATION"
echo "1. GENERATING LOCK CANDIDATE FROM VALIDATED EVIDENCE"
python scripts/finalize_v3_g4_lock.py

echo "2. VERIFYING LOCK CANDIDATE AND CURATED EVIDENCE"
python scripts/verify_v3_g4_lock.py

echo "3. VERIFYING PATCH INTEGRITY"
git diff --check

echo "Gate V3-4 lock candidate is ready for repository review."
echo "The large runtime signal_features.csv remains untracked and hash-bound."
echo "Gate V3-5 remains approved but must wait for final lock promotion."
