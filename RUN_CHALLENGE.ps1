param(
    [switch]$RefreshData
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-NativeStep {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    Write-Host "`n$Label"
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

Write-Host ""
Write-Host "WHEN SIGNALS STOP WORKING"
Write-Host "ShockBridge Pulse - V1 Signal Validity Framework"
Write-Host "=================================================="

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found. Install Python 3.11 or later."
}

if (-not (Test-Path ".venv")) {
    Invoke-NativeStep -Label "1. Creating virtual environment" -Executable "python" -Arguments @("-m", "venv", ".venv")
} else {
    Write-Host "`n1. Reusing existing virtual environment"
}

$Python = Join-Path $PWD ".venv\Scripts\python.exe"
$env:MPLBACKEND = "Agg"
$env:MPLCONFIGDIR = Join-Path $PWD ".matplotlib"
$env:PYTHONUNBUFFERED = "1"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
New-Item -ItemType Directory -Force -Path $env:MPLCONFIGDIR | Out-Null

Invoke-NativeStep -Label "2. Installing or updating the project" -Executable $Python -Arguments @("-m", "pip", "install", "-e", ".[dev]")

$SolData = "data\raw\sol_usdt_4h.csv"
$BtcData = "data\raw\btc_usdt_4h.csv"
if ($RefreshData -or -not (Test-Path $SolData) -or -not (Test-Path $BtcData)) {
    Invoke-NativeStep -Label "3. Downloading public SOL and BTC OHLCV" -Executable $Python -Arguments @("scripts\download_free_data.py")
} else {
    Write-Host "`n3. Reusing validated local market data"
}

Invoke-NativeStep -Label "4. Validating market data" -Executable $Python -Arguments @("scripts\validate_market_data.py")
Invoke-NativeStep -Label "5. Running implementation tests" -Executable $Python -Arguments @("-m", "pytest", "-q")

Write-Host "`n6. Clearing stale generated evidence"
if (Test-Path "outputs") {
    Get-ChildItem "outputs" -Force | Where-Object { $_.Name -ne ".gitkeep" } | Remove-Item -Recurse -Force
}
New-Item -ItemType Directory -Force -Path "outputs" | Out-Null

Invoke-NativeStep -Label "7. Running the three-stage framework" -Executable $Python -Arguments @(
    "-m", "shockbridge_signal_validity",
    "--sol-csv", $SolData,
    "--btc-csv", $BtcData,
    "--signals", "rsi", "bollinger", "combined",
    "--primary-signal", "bollinger",
    "--horizon", "1",
    "--cost-bps", "10",
    "--output-directory", "outputs"
)

Invoke-NativeStep -Label "8. Printing the direct conclusions" -Executable $Python -Arguments @("scripts\summarize_results.py")

Write-Host "`nFramework completed successfully."
Write-Host "Report: outputs\research_report.md"
Write-Host "Figures: outputs\figures"
Write-Host "Manifest: outputs\run_manifest.json"
