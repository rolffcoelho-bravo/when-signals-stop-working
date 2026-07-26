$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "$PSScriptRoot\src"
$env:OMP_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

Write-Host "GATE V3-4A - INDEPENDENT CHRONOLOGY AND SIGNAL-USE CONTRACT"
python -m pytest -q tests/test_v3_external_chronology_signal_use_contract.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-4A contract tests failed."
}

python scripts/validate_v3_g4a_contract.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-4A contract validation failed."
}

Write-Host "Gate V3-4A contract evidence passed."
