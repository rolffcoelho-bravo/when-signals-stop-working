param(
    [string]$Config = "configs/v3_adapter_example.json",
    [string]$OutputDirectory = "outputs/v3/data_adapter"
)

$ErrorActionPreference = "Stop"
$env:PYTHONNOUSERSITE = "1"

Write-Host "1. VERIFYING GATE V3-1 IMPLEMENTATION LOCK"
python scripts/verify_v3_g1_data_adapter.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-1 implementation lock verification failed."
}

Write-Host "2. RUNNING VERSION 3 CANONICAL DATA ADAPTER"
python scripts/run_v3_data_adapter.py `
    --config $Config `
    --output-directory $OutputDirectory
if ($LASTEXITCODE -ne 0) {
    throw "Version 3 canonical data adapter failed."
}

Write-Host "3. RUNNING GATE V3-1 CONFORMANCE TESTS"
python -m pytest -q `
    tests/test_v3_data_contract.py `
    tests/test_v3_adapters.py `
    tests/test_v3_exchange_and_parquet_adapters.py `
    tests/test_v3_data_runner.py
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-1 conformance tests failed."
}

Write-Host "Gate V3-1 canonical data and adapter validation passed."
