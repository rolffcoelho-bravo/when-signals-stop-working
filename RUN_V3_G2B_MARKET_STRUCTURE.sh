#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:-configs/v3_market_structure_example.json}"
OUTPUT_DIRECTORY="${2:-outputs/v3/market_structure}"
export PYTHONNOUSERSITE=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

echo "1. VERIFYING LOCKED GATE V3-2 PARENT"
python scripts/verify_v3_g2_spectral.py

echo "2. RUNNING VERSION 3 MARKET-STRUCTURE EXTENSION"
python scripts/run_v3_market_structure.py \
  --config "$CONFIG" \
  --output-directory "$OUTPUT_DIRECTORY"

echo "3. RUNNING GATE V3-2B TESTS"
python -m pytest -q \
  tests/test_v3_market_structure.py \
  tests/test_v3_market_structure_runner.py

echo "4. VERIFYING GATE V3-2B LOCK"
python scripts/verify_v3_g2b_market_structure.py

echo "Gate V3-2B market-structure extension validation passed."
