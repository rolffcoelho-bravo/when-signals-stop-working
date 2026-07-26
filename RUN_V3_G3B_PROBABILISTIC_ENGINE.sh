#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:-configs/v3_panic_regime_example.json}"
OUTPUT_DIRECTORY="${2:-outputs/v3/panic_regime}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHONNOUSERSITE=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

printf '%s\n' "1. VERIFYING LOCKED GATE V3-3A IDENTIFICATION CONTRACT"
python scripts/verify_v3_g3a_identification.py

printf '%s\n' "2. RUNNING GATE V3-3A AND V3-3B ISOLATED TESTS"
python -m pytest -q \
  tests/test_v3_panic_regime_contract.py \
  tests/test_v3_panic_regime.py

printf '%s\n' "3. RUNNING VERSION 3 PROBABILISTIC REGIME ENGINE"
python scripts/run_v3_panic_regime.py \
  --config "${CONFIG}" \
  --output-directory "${OUTPUT_DIRECTORY}"

printf '%s\n' "4. VERIFYING GATE V3-3B IMPLEMENTATION LOCK"
python scripts/verify_v3_g3b_probabilistic_engine.py

printf '%s\n' "Gate V3-3B probabilistic engine validation passed."
printf '%s\n' "Uncertainty, transitions, duration, contributions and final V3-3 lock remain pending V3-3C and V3-3D."
