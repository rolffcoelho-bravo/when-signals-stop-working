#!/usr/bin/env bash
set -euo pipefail

export MPLBACKEND=Agg
export MPLCONFIGDIR="$(pwd)/.matplotlib"
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
mkdir -p "$MPLCONFIGDIR"

echo
printf '%s\n' "TECHNICAL SIGNAL VALIDITY FRAMEWORK" "ShockBridge Pulse - Institutional Version 1 Replication" "=================================================="

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
PYTHON=.venv/bin/python
"$PYTHON" -m pip install -e '.[dev]'

if [ ! -f data/raw/sol_usdt_4h.csv ] || [ ! -f data/raw/btc_usdt_4h.csv ]; then
  "$PYTHON" scripts/download_free_data.py
fi
"$PYTHON" scripts/validate_market_data.py
"$PYTHON" -m pytest -q
find outputs -mindepth 1 ! -name .gitkeep ! -name README.md -delete 2>/dev/null || true
"$PYTHON" -m shockbridge_signal_validity \
  --sol-csv data/raw/sol_usdt_4h.csv \
  --btc-csv data/raw/btc_usdt_4h.csv \
  --signals rsi bollinger combined \
  --primary-signal bollinger \
  --horizon 1 \
  --cost-bps 10 \
  --output-directory outputs
"$PYTHON" scripts/summarize_results.py
"$PYTHON" scripts/build_replication_assets.py
"$PYTHON" scripts/audit_public_release.py
"$PYTHON" scripts/verify_replication.py

echo "Report: outputs/research_report.md"
echo "Figures: outputs/figures"

echo "Institutional replication completed successfully."
