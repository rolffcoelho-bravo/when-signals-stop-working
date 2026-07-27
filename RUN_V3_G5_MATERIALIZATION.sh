#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/src"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
unset PYTHONNOUSERSITE || true

echo "GATE V3-5 - REAL DEVELOPMENT FOUNDATION MATERIALIZATION"

echo "1. VERIFYING FINAL V3-4 PARENT LOCK"
python scripts/verify_v3_g4_lock.py

echo "2. VERIFYING AUTHORITATIVE V3-5 CONTRACT"
python scripts/verify_v3_g5_contract.py

echo "3. REVALIDATING V3-5 FOUNDATION"
bash RUN_V3_G5_FOUNDATION.sh

echo "4. RUNNING MATERIALIZATION TESTS"
python -m pytest -q tests/test_v3_g5_materialization.py

if [[ ! -f outputs/v3/signal_engine/signal_features.csv ]]; then
  echo "5. REGENERATING LOCKED V3-4 RUNTIME SIGNAL EVIDENCE"
  bash RUN_V3_G4_SIGNAL_ENGINE.sh
else
  echo "5. USING EXISTING LOCKED V3-4 RUNTIME SIGNAL EVIDENCE"
fi

echo "6. MATERIALIZING REAL DEVELOPMENT-ONLY FOUNDATION"
python scripts/run_v3_g5_materialization.py

echo "7. VERIFYING COMPLETE MATERIALIZATION EVIDENCE"
python scripts/verify_v3_g5_materialization.py

echo "8. VERIFYING PATCH AND TRACKED-WORKTREE INTEGRITY"
git diff --check
git diff --quiet
git diff --cached --quiet

echo "Gate V3-5 real development foundation evidence passed."
echo "Development target primitives are materialized."
echo "Fold-specific large-move labels remain deferred."
echo "Model fitting remains disabled."
echo "Signal-establishment segment remains inaccessible."
echo "V3-9 final-framework reserve remains inaccessible."
