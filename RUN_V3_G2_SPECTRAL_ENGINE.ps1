param(
    [string]$Config = "configs/v3_spectral_example.json",
    [string]$OutputDirectory = "outputs/v3/spectral"
)

$ErrorActionPreference = "Stop"
$env:PYTHONNOUSERSITE = "1"
$env:OMP_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

Write-Host "1. VERIFYING GATE V3-1 DATA-ADAPTER LOCK"
python scripts/verify_v3_g1_data_adapter.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-1 lock verification failed."
}

Write-Host "2. RUNNING VERSION 3 CAUSAL SPECTRAL ENGINE"
python scripts/run_v3_spectral_features.py `
    --config $Config `
    --output-directory $OutputDirectory
if ($LASTEXITCODE -ne 0) {
    throw "Version 3 causal spectral engine failed."
}

Write-Host "3. RUNNING GATE V3-2 TESTS"
python -m pytest -q `
    tests/test_v3_spectral.py `
    tests/test_v3_spectral_runner.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-2 tests failed."
}

Write-Host "4. VERIFYING GATE V3-2 IMPLEMENTATION LOCK"
python scripts/verify_v3_g2_spectral.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-2 lock verification failed."
}

Write-Host "Gate V3-2 multi-asset causal feature and spectral validation passed."
