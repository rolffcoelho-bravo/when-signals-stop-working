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
python scripts/verify_v3_realignment.py
python -m pytest -q \
  tests/test_v3_signal_registry.py \
  tests/test_v3_signal_engine.py \
  tests/test_v3_signal_runner.py
python scripts/run_v3_signal_engine.py \
  --config configs/v3_signal_engine_example.json \
  --output-directory outputs/v3/signal_engine

echo "Gate V3-4 implementation evidence passed."
