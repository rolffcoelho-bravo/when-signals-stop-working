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

echo "GATE V3-5 - REAL DEVELOPMENT EXECUTION AUTHORIZATION CANDIDATE"

echo "1. VERIFYING FINAL V3-4 PARENT LOCK"
python scripts/verify_v3_g4_lock.py

echo "2. VERIFYING VALIDATED V3-5 FOUNDATION BOUNDARIES"
python scripts/verify_v3_g5_validated_boundaries.py

echo "3. VERIFYING VALIDATED V3-5 MATERIALIZATION BOUNDARY"
python scripts/verify_v3_g5_materialization_boundary.py

echo "4. VERIFYING VALIDATED V3-5 MODEL IMPLEMENTATION BOUNDARY"
python scripts/verify_v3_g5_model_implementation_boundary.py

echo "5. VERIFYING VALIDATED V3-5 DEVELOPMENT ENGINE BOUNDARY"
python scripts/verify_v3_g5_development_engine_boundary.py

if [[ ! -f outputs/v3/forecast_foundation/materialization_manifest.json ]]; then
  echo "6. REGENERATING VALIDATED REAL DEVELOPMENT FOUNDATION"
  bash RUN_V3_G5_MATERIALIZATION.sh
else
  echo "6. VERIFYING EXISTING REAL DEVELOPMENT FOUNDATION"
  python scripts/verify_v3_g5_materialization.py
fi

echo "7. RUNNING WARNING-FREE AUTHORIZATION PLANNING TESTS"
python -W error::FutureWarning -m pytest -q \
  tests/test_v3_g5_real_execution_authorization.py

echo "8. MATERIALIZING DETERMINISTIC STAGE-ALIGNED AUTHORIZATION PLAN"
python -W error::FutureWarning scripts/materialize_v3_g5_real_execution_authorization.py

echo "9. VERIFYING COMPLETE AUTHORIZATION CANDIDATE EVIDENCE"
python -W error::FutureWarning scripts/verify_v3_g5_real_execution_authorization.py

echo "10. VERIFYING PATCH AND TRACKED-WORKTREE INTEGRITY"
git diff --check
git diff --quiet
git diff --cached --quiet

echo "Gate V3-5 real execution authorization candidate evidence passed."
echo "Development engine remains protected."
echo "The complete 211140-job plan is deterministic and hash-bound."
echo "All stage-aligned batches remain PLANNED_NOT_STARTED."
echo "No batch crosses a scientific stage boundary."
echo "Real development execution remains unauthorized."
echo "Real development model fitting remains disabled."
echo "Development pipeline selection remains disabled."
echo "Signal-establishment segment remains inaccessible."
echo "V3-9 final-framework reserve remains inaccessible."
