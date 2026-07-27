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

    Write-Host "GATE V3-5 - FORECAST FOUNDATION"

    Write-Host "1. VERIFYING FINAL V3-4 PARENT LOCK"
    python scripts/verify_v3_g4_lock.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4 final parent lock verification failed."
    }

    Write-Host "2. VERIFYING AUTHORITATIVE V3-5 CONTRACT"
    python scripts/verify_v3_g5_contract.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 contract verification failed."
    }

    Write-Host "3. RUNNING V3-5 FOUNDATION TESTS"
    python -m pytest -q `
        tests/test_v3_g5_targets_partitions.py `
        tests/test_v3_g5_splits_matching.py `
        tests/test_v3_g5_inventory_benchmark.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 foundation tests failed."
    }

    Write-Host "4. RUNNING STANDALONE FOUNDATION VERIFIER"
    python scripts/verify_v3_g5_foundation.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 foundation verification failed."
    }

    Write-Host "5. VERIFYING PATCH INTEGRITY"
    git diff --check
    if ($LASTEXITCODE -ne 0) {
        throw "Whitespace or patch-integrity defects were detected."
    }

    Write-Host "Gate V3-5 forecast foundation evidence passed."
    Write-Host "Target construction remains development-only."
    Write-Host "Model fitting remains disabled."
    Write-Host "Signal-establishment segment remains inaccessible."
    Write-Host "V3-9 final-framework reserve remains inaccessible."
}
finally {
    Set-Location $PreviousLocation
    [Environment]::SetEnvironmentVariable(
        "PYTHONNOUSERSITE",
        $PreviousPythonNoUserSite,
        "Process"
    )
}
