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

echo "GATE V3-5 - CHRONOLOGICAL DEVELOPMENT EXECUTION ENGINE"

echo "1. VERIFYING FINAL V3-4 PARENT LOCK"
python scripts/verify_v3_g4_lock.py

echo "2. VERIFYING VALIDATED V3-5 FOUNDATION BOUNDARIES"
python scripts/verify_v3_g5_validated_boundaries.py

echo "3. VERIFYING VALIDATED V3-5 MATERIALIZATION BOUNDARY"
python scripts/verify_v3_g5_materialization_boundary.py

echo "4. VERIFYING VALIDATED V3-5 MODEL IMPLEMENTATION BOUNDARY"
python scripts/verify_v3_g5_model_implementation_boundary.py

if [[ ! -f outputs/v3/forecast_foundation/materialization_manifest.json ]]; then
  echo "5. REGENERATING VALIDATED REAL DEVELOPMENT FOUNDATION"
  bash RUN_V3_G5_MATERIALIZATION.sh
else
  echo "5. VERIFYING EXISTING REAL DEVELOPMENT FOUNDATION"
  python scripts/verify_v3_g5_materialization.py
fi

echo "6. RUNNING WARNING-FREE DEVELOPMENT ENGINE TESTS"
python -W error::FutureWarning -m pytest -q \
  tests/test_v3_g5_development_metrics.py \
  tests/test_v3_g5_calibration_selection.py \
  tests/test_v3_g5_multiplicity.py \
  tests/test_v3_g5_development_execution.py

echo "7. RUNNING WARNING-FREE DEVELOPMENT ENGINE VERIFIER"
python -W error::FutureWarning scripts/verify_v3_g5_development_execution.py

echo "8. VERIFYING PATCH AND TRACKED-WORKTREE INTEGRITY"
git diff --check
git diff --quiet
git diff --cached --quiet

echo "Gate V3-5 chronological development engine evidence passed."
echo "Fold-scoped large-move thresholds are implemented."
echo "Training-only calibration and abstention are implemented."
echo "Predictive, economic, concentration, and multiplicity controls are implemented."
echo "Only synthetic matched outer-fold fits were executed."
echo "Real development model fitting remains disabled."
echo "Development pipeline selection remains disabled."
echo "Signal-establishment segment remains inaccessible."
echo "V3-9 final-framework reserve remains inaccessible."
