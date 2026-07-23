#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:-configs/v3_spectral_example.json}"
OUTPUT_DIRECTORY="${2:-outputs/v3/spectral}"
export PYTHONNOUSERSITE=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

echo "1. VERIFYING GATE V3-1 DATA-ADAPTER LOCK"
python scripts/verify_v3_g1_data_adapter.py

echo "2. RUNNING VERSION 3 CAUSAL SPECTRAL ENGINE"
python scripts/run_v3_spectral_features.py \
  --config "$CONFIG" \
  --output-directory "$OUTPUT_DIRECTORY"

echo "3. RUNNING GATE V3-2 TESTS"
python -m pytest -q \
  tests/test_v3_spectral.py \
  tests/test_v3_spectral_runner.py

echo "Gate V3-2 multi-asset causal feature and spectral validation passed."
