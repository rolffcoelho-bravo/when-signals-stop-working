#!/usr/bin/env bash
set -euo pipefail

REPORT="${1:-outputs/v3/g3_final_acceptance/final_acceptance_report.json}"
unset PYTHONNOUSERSITE
export PYTHONPATH="$(pwd)/src"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

echo "GATE V3-3D - FINAL ACCEPTANCE AND LOCK AUTHORIZATION"
python scripts/run_v3_g3_final_acceptance.py --report "$REPORT"
echo "Gate V3-3D acceptance evidence passed."
echo "The final lock must be created only from the generated report."
