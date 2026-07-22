#!/usr/bin/env bash
set -euo pipefail

echo
echo "WHEN SIGNALS STOP WORKING"
echo "ShockBridge Pulse Technical Signal Validity Challenge"
echo "====================================================="
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found. Install Python 3.11 or later."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "1. Creating virtual environment..."
  python3 -m venv .venv
fi

PYTHON=".venv/bin/python"

echo "2. Installing the project..."
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -e ".[dev]"

echo "3. Downloading free public SOL and BTC data..."
"$PYTHON" scripts/download_free_data.py

echo "4. Validating the market data..."
"$PYTHON" scripts/validate_market_data.py

echo "5. Running implementation tests..."
"$PYTHON" -m pytest -q

echo "6. Running the three-stage challenge..."
"$PYTHON" -m shockbridge_signal_validity \
  --sol-csv data/raw/sol_usdt_4h.csv \
  --btc-csv data/raw/btc_usdt_4h.csv \
  --signals rsi bollinger combined \
  --primary-signal bollinger \
  --horizon 1 \
  --cost-bps 10 \
  --output-directory outputs

echo "7. Printing the direct conclusion..."
"$PYTHON" scripts/summarize_results.py

echo
echo "Challenge complete."
echo "Open outputs/research_report.md for the complete result."
