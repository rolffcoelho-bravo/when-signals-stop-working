param(
    [string]$Config = "configs/v3_panic_regime_diagnostics_example.json",
    [string]$OutputDirectory = "outputs/v3/panic_regime_governance"
)

$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "$PSScriptRoot\src"
$env:PYTHONNOUSERSITE = "1"
$env:OMP_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

Write-Host "1. VERIFYING LOCKED GATE V3-3B PARENT"
python scripts/verify_v3_g3b_probabilistic_engine.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-3B parent verification failed."
}

Write-Host "2. RUNNING GATE V3-3C GOVERNANCE AND DIAGNOSTICS"
python scripts/run_v3_panic_regime_diagnostics.py `
    --config $Config `
    --output-directory $OutputDirectory
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-3C diagnostics execution failed."
}

Write-Host "3. RUNNING GATE V3-3C ISOLATED TESTS"
python -m pytest -q tests/test_v3_panic_regime_diagnostics.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-3C tests failed."
}

Write-Host "4. VERIFYING GATE V3-3C LOCK"
python scripts/verify_v3_g3c_governance.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-3C lock verification failed."
}

Write-Host "Gate V3-3C governance and diagnostics validation passed."
