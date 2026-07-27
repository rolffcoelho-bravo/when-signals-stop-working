$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "$PSScriptRoot\src"
$env:OMP_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

$PreviousPythonNoUserSite = [Environment]::GetEnvironmentVariable(
    "PYTHONNOUSERSITE",
    "Process"
)
$PreviousLocation = Get-Location

try {
    Set-Location $PSScriptRoot
    [Environment]::SetEnvironmentVariable("PYTHONNOUSERSITE", $null, "Process")

    Write-Host "GATE V3-4 - UNIFIED RSI AND BOLLINGER INTERPRETATION ENGINE"

    Write-Host "1. VERIFYING REPOSITORY REALIGNMENT"
    python scripts/verify_v3_realignment.py
    if ($LASTEXITCODE -ne 0) {
        throw "Repository realignment verification failed."
    }

    Write-Host "2. VERIFYING LOCKED V3-1 CANONICAL DATA ADAPTER"
    python scripts/verify_v3_g1_data_adapter.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-1 canonical-data parent verification failed."
    }

    Write-Host "3. RUNNING EXACT HARDENED V3-4 TEST SUITE"
    python -m pytest -q `
        tests/test_v3_signal_registry.py `
        tests/test_v3_signal_engine.py `
        tests/test_v3_signal_runner.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4 signal-engine tests failed."
    }

    Write-Host "4. MATERIALIZING FROZEN SOL CANONICAL INPUT"
    if (-not (Test-Path "data/raw/sol_usdt_4h.csv")) {
        throw "Frozen SOL source snapshot is missing: data/raw/sol_usdt_4h.csv"
    }
    python scripts/run_v3_data_adapter.py `
        --config "configs/v3_adapter_frozen_sol.json" `
        --output-directory "outputs/v3/data_adapter"
    if ($LASTEXITCODE -ne 0) {
        throw "Frozen SOL canonical-data materialization failed."
    }
    if (-not (Test-Path "outputs/v3/data_adapter/canonical_market_data.csv")) {
        throw "Canonical input was not created by the V3-1 adapter."
    }

    Write-Host "5. EXECUTING V3-4 ON FROZEN REAL DATA"
    if (Test-Path "outputs/v3/signal_engine") {
        Remove-Item "outputs/v3/signal_engine" -Recurse -Force
    }
    python scripts/run_v3_signal_engine.py `
        --config "configs/v3_signal_engine_example.json" `
        --output-directory "outputs/v3/signal_engine"
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4 signal-engine execution failed."
    }

    Write-Host "6. VERIFYING COMPLETE V3-4 EVIDENCE PACKAGE"
    python scripts/verify_v3_g4_signal_outputs.py `
        --output-directory "outputs/v3/signal_engine"
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4 output evidence verification failed."
    }

    Write-Host "7. VERIFYING NO TRACKED WORKING-TREE MUTATION"
    git diff --check
    if ($LASTEXITCODE -ne 0) {
        throw "Whitespace or patch-integrity defects were detected."
    }
    git diff --exit-code -- .
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4 execution modified tracked repository files."
    }

    Write-Host "Gate V3-4 authoritative implementation evidence passed."
    Write-Host "Gate V3-5 remains approved and blocked only until the V3-4 lock is created."
}
finally {
    Set-Location $PreviousLocation
    [Environment]::SetEnvironmentVariable(
        "PYTHONNOUSERSITE",
        $PreviousPythonNoUserSite,
        "Process"
    )
}
