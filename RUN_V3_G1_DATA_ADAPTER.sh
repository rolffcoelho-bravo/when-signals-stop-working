#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:-configs/v3_adapter_example.json}"
OUTPUT_DIRECTORY="${2:-outputs/v3/data_adapter}"
export PYTHONNOUSERSITE=1

echo "1. VERIFYING GATE V3-1 IMPLEMENTATION LOCK"
python scripts/verify_v3_g1_data_adapter.py

echo "2. RUNNING VERSION 3 CANONICAL DATA ADAPTER"
python scripts/run_v3_data_adapter.py \
  --config "$CONFIG" \
  --output-directory "$OUTPUT_DIRECTORY"

echo "3. RUNNING GATE V3-1 CONFORMANCE TESTS"
python -m pytest -q \
  tests/test_v3_data_contract.py \
  tests/test_v3_adapters.py \
  tests/test_v3_exchange_and_parquet_adapters.py \
  tests/test_v3_data_runner.py

echo "Gate V3-1 canonical data and adapter validation passed."
