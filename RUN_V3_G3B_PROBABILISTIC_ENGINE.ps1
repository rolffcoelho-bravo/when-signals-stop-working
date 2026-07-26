param(
    [string]$Config = "configs/v3_panic_regime_example.json",
    [string]$OutputDirectory = "outputs/v3/panic_regime"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$srcPath = Join-Path $repoRoot "src"
if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$srcPath;$env:PYTHONPATH"
} else {
    $env:PYTHONPATH = $srcPath
}
$env:PYTHONNOUSERSITE = "1"
$env:OMP_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

Write-Host "1. VERIFYING LOCKED GATE V3-3A IDENTIFICATION CONTRACT"
python scripts/verify_v3_g3a_identification.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-3A identification verification failed."
}

Write-Host "2. RUNNING GATE V3-3A AND V3-3B ISOLATED TESTS"
python -m pytest -q `
    tests/test_v3_panic_regime_contract.py `
    tests/test_v3_panic_regime.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-3B tests failed."
}

Write-Host "3. RUNNING VERSION 3 PROBABILISTIC REGIME ENGINE"
python scripts/run_v3_panic_regime.py `
    --config $Config `
    --output-directory $OutputDirectory
if ($LASTEXITCODE -ne 0) {
    throw "Version 3 probabilistic regime engine failed."
}

Write-Host "4. VERIFYING GATE V3-3B IMPLEMENTATION LOCK"
python scripts/verify_v3_g3b_probabilistic_engine.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-3B implementation lock verification failed."
}

Write-Host "Gate V3-3B probabilistic engine validation passed."
Write-Host "Uncertainty, transitions, duration, contributions and final V3-3 lock remain pending V3-3C and V3-3D."
