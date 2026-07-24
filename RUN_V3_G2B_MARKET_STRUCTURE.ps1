param(
    [string]$Config = "configs/v3_market_structure_example.json",
    [string]$OutputDirectory = "outputs/v3/market_structure"
)

$ErrorActionPreference = "Stop"
$env:PYTHONNOUSERSITE = "1"
$env:OMP_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

Write-Host "1. VERIFYING LOCKED GATE V3-2 PARENT"
python scripts/verify_v3_g2_spectral.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-2 parent verification failed."
}

Write-Host "2. RUNNING VERSION 3 MARKET-STRUCTURE EXTENSION"
python scripts/run_v3_market_structure.py `
    --config $Config `
    --output-directory $OutputDirectory
if ($LASTEXITCODE -ne 0) {
    throw "Version 3 market-structure extension failed."
}

Write-Host "3. RUNNING GATE V3-2B TESTS"
python -m pytest -q `
    tests/test_v3_market_structure.py `
    tests/test_v3_market_structure_runner.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-2B tests failed."
}

Write-Host "4. VERIFYING GATE V3-2B LOCK"
python scripts/verify_v3_g2b_market_structure.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-2B lock verification failed."
}

Write-Host "Gate V3-2B market-structure extension validation passed."
