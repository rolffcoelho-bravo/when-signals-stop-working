#!/usr/bin/env bash
set -euo pipefail
unset PYTHONNOUSERSITE || true
export PYTHONPATH="$(pwd)/src"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

echo "GATE V3-4B - CHRONOLOGY COMPILATION AND PROVENANCE"
python -m pytest -q tests/test_v3_external_chronology_registry.py tests/test_v3_cross_gate_lineage.py
python scripts/verify_v3_cross_gate_lineage.py
python scripts/run_v3_g4b_chronology.py
python scripts/verify_v3_g4b_chronology_lock.py
echo "Gate V3-4B chronology evidence and final lock passed."
