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
echo "GATE V3-4 - UNIFIED RSI AND BOLLINGER INTERPRETATION ENGINE"

echo "1. VERIFYING REPOSITORY REALIGNMENT"
python scripts/verify_v3_realignment.py

echo "2. VERIFYING LOCKED V3-1 CANONICAL DATA ADAPTER"
python scripts/verify_v3_g1_data_adapter.py

echo "3. RUNNING EXACT HARDENED V3-4 TEST SUITE"
python -m pytest -q \
  tests/test_v3_signal_registry.py \
  tests/test_v3_signal_engine.py \
  tests/test_v3_signal_runner.py

echo "4. MATERIALIZING FROZEN SOL CANONICAL INPUT"
test -f data/raw/sol_usdt_4h.csv
python scripts/run_v3_data_adapter.py \
  --config configs/v3_adapter_frozen_sol.json \
  --output-directory outputs/v3/data_adapter
test -f outputs/v3/data_adapter/canonical_market_data.csv

echo "5. EXECUTING V3-4 ON FROZEN REAL DATA"
rm -rf outputs/v3/signal_engine
python scripts/run_v3_signal_engine.py \
  --config configs/v3_signal_engine_example.json \
  --output-directory outputs/v3/signal_engine

echo "6. VERIFYING COMPLETE V3-4 EVIDENCE PACKAGE"
python scripts/verify_v3_g4_signal_outputs.py \
  --output-directory outputs/v3/signal_engine

echo "7. VERIFYING NO TRACKED WORKING-TREE MUTATION"
git diff --check
git diff --exit-code -- .

echo "Gate V3-4 authoritative implementation evidence passed."
echo "Gate V3-5 remains approved and blocked only until the V3-4 lock is created."
