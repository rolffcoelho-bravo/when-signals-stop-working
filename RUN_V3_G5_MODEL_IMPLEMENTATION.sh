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

echo "GATE V3-5 - FOLD-SCOPED PREPROCESSING AND MATCHED ESTIMATOR IMPLEMENTATION"

echo "1. VERIFYING FINAL V3-4 PARENT LOCK"
python scripts/verify_v3_g4_lock.py

echo "2. VERIFYING VALIDATED V3-5 CONTRACT AND FOUNDATION OBJECTS"
python scripts/verify_v3_g5_validated_boundaries.py

echo "3. VERIFYING VALIDATED V3-5 MATERIALIZATION BOUNDARY"
python scripts/verify_v3_g5_materialization_boundary.py

if [[ ! -f outputs/v3/forecast_foundation/materialization_manifest.json ]]; then
  echo "4. REGENERATING VALIDATED REAL DEVELOPMENT FOUNDATION"
  bash RUN_V3_G5_MATERIALIZATION.sh
else
  echo "4. VERIFYING EXISTING REAL DEVELOPMENT FOUNDATION"
  python scripts/verify_v3_g5_materialization.py
fi

echo "5. RUNNING WARNING-FREE MODEL IMPLEMENTATION TESTS"
python -W error::FutureWarning -m pytest -q \
  tests/test_v3_g5_preprocessing.py \
  tests/test_v3_g5_model_registry.py \
  tests/test_v3_g5_estimators.py

echo "6. RUNNING WARNING-FREE STANDALONE MODEL IMPLEMENTATION VERIFIER"
python -W error::FutureWarning scripts/verify_v3_g5_model_implementation.py

echo "7. VERIFYING PATCH AND TRACKED-WORKTREE INTEGRITY"
git diff --check
git diff --quiet
git diff --cached --quiet

echo "Gate V3-5 model implementation evidence passed."
echo "Fold-scoped preprocessing is implemented."
echo "Matched estimator families are implemented."
echo "Logistic L2 compatibility warnings observed: 0"
echo "Only synthetic estimator fits were executed."
echo "Real development model fitting remains disabled."
echo "Development pipeline selection remains disabled."
echo "Signal-establishment segment remains inaccessible."
echo "V3-9 final-framework reserve remains inaccessible."
