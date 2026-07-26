#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:-configs/v3_panic_regime_diagnostics_example.json}"
OUTPUT_DIRECTORY="${2:-outputs/v3/panic_regime_governance}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PYTHONPATH="$ROOT/src"
export PYTHONNOUSERSITE=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

printf '%s\n' '1. VERIFYING LOCKED GATE V3-3B PARENT'
python scripts/verify_v3_g3b_probabilistic_engine.py

printf '%s\n' '2. RUNNING GATE V3-3C GOVERNANCE AND DIAGNOSTICS'
python scripts/run_v3_panic_regime_diagnostics.py \
  --config "$CONFIG" \
  --output-directory "$OUTPUT_DIRECTORY"

printf '%s\n' '3. RUNNING GATE V3-3C ISOLATED TESTS'
python -m pytest -q tests/test_v3_panic_regime_diagnostics.py

printf '%s\n' '4. VERIFYING GATE V3-3C LOCK'
python scripts/verify_v3_g3c_governance.py

printf '%s\n' 'Gate V3-3C governance and diagnostics validation passed.'
