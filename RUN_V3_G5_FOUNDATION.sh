#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$ROOT"

export PYTHONPATH="$ROOT/src"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

printf '%s\n' "GATE V3-5 - FORECAST FOUNDATION"
printf '%s\n' "1. VERIFYING FINAL V3-4 PARENT LOCK"
python scripts/verify_v3_g4_lock.py

printf '%s\n' "2. VERIFYING AUTHORITATIVE V3-5 CONTRACT"
python scripts/verify_v3_g5_contract.py

printf '%s\n' "3. RUNNING V3-5 FOUNDATION TESTS"
python -m pytest -q \
  tests/test_v3_g5_targets_partitions.py \
  tests/test_v3_g5_splits_matching.py \
  tests/test_v3_g5_inventory_benchmark.py

printf '%s\n' "4. RUNNING STANDALONE FOUNDATION VERIFIER"
python scripts/verify_v3_g5_foundation.py

printf '%s\n' "5. VERIFYING PATCH INTEGRITY"
git diff --check

printf '%s\n' "Gate V3-5 forecast foundation evidence passed."
printf '%s\n' "Target construction remains development-only."
printf '%s\n' "Model fitting remains disabled."
printf '%s\n' "Signal-establishment segment remains inaccessible."
printf '%s\n' "V3-9 final-framework reserve remains inaccessible."
