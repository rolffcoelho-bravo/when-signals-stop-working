$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "WHEN SIGNALS STOP WORKING"
Write-Host "ShockBridge Pulse Technical Signal Validity Challenge"
Write-Host "====================================================="
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found. Install Python 3.11 or later and try again."
}

if (-not (Test-Path ".venv")) {
    Write-Host "1. Creating virtual environment..."
    python -m venv .venv
}

$Python = Join-Path $PWD ".venv\Scripts\python.exe"

Write-Host "2. Installing the project..."
& $Python -m pip install --upgrade pip
& $Python -m pip install -e ".[dev]"

Write-Host "3. Downloading free public SOL and BTC data..."
& $Python scripts\download_free_data.py

Write-Host "4. Validating the market data..."
& $Python scripts\validate_market_data.py

Write-Host "5. Running implementation tests..."
& $Python -m pytest -q

Write-Host "6. Running the three-stage challenge..."
& $Python -m shockbridge_signal_validity `
    --sol-csv data/raw/sol_usdt_4h.csv `
    --btc-csv data/raw/btc_usdt_4h.csv `
    --signals rsi bollinger combined `
    --primary-signal bollinger `
    --horizon 1 `
    --cost-bps 10 `
    --output-directory outputs

Write-Host "7. Printing the direct conclusion..."
& $Python scripts\summarize_results.py

Write-Host ""
Write-Host "Challenge complete."
Write-Host "Open outputs\research_report.md for the complete result."
