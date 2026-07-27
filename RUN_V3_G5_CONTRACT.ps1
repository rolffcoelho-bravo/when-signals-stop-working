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

    Write-Host "GATE V3-5 - MATCHED FORECAST CONTRACT"

    Write-Host "1. VERIFYING FINAL V3-4 PARENT LOCK"
    python scripts/verify_v3_g4_lock.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4 final parent lock verification failed."
    }

    Write-Host "2. RUNNING V3-5 CONTRACT TESTS"
    python -m pytest -q tests/test_v3_g5_contract.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 contract tests failed."
    }

    Write-Host "3. RUNNING STANDALONE V3-5 CONTRACT VERIFIER"
    python scripts/verify_v3_g5_contract.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 standalone contract verification failed."
    }

    Write-Host "4. VERIFYING PATCH INTEGRITY"
    git diff --check
    if ($LASTEXITCODE -ne 0) {
        throw "Whitespace or patch-integrity defects were detected."
    }

    Write-Host "Gate V3-5 contract evidence passed."
    Write-Host "Target access remains disabled."
    Write-Host "Development model fitting remains disabled."
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
