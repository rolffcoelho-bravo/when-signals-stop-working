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

    Write-Host "GATE V3-5 - REAL DEVELOPMENT FOUNDATION MATERIALIZATION"

    Write-Host "1. VERIFYING FINAL V3-4 PARENT LOCK"
    python scripts/verify_v3_g4_lock.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4 final parent lock verification failed."
    }

    Write-Host "2. VERIFYING VALIDATED V3-5 CONTRACT AND FOUNDATION OBJECTS"
    python scripts/verify_v3_g5_validated_boundaries.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 validated-boundary verification failed."
    }

    Write-Host "3. VERIFYING AUTHORITATIVE V3-5 CONTRACT"
    python scripts/verify_v3_g5_contract.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 contract verification failed."
    }

    Write-Host "4. REVALIDATING V3-5 FOUNDATION"
    .\RUN_V3_G5_FOUNDATION.ps1
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 foundation revalidation failed."
    }

    Write-Host "5. RUNNING MATERIALIZATION TESTS"
    python -m pytest -q tests/test_v3_g5_materialization.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 materialization tests failed."
    }

    $SignalFeatures = "outputs\v3\signal_engine\signal_features.csv"
    if (-not (Test-Path $SignalFeatures)) {
        Write-Host "6. REGENERATING LOCKED V3-4 RUNTIME SIGNAL EVIDENCE"
        .\RUN_V3_G4_SIGNAL_ENGINE.ps1
        if ($LASTEXITCODE -ne 0) {
            throw "Gate V3-4 runtime evidence regeneration failed."
        }
    }
    else {
        Write-Host "6. USING EXISTING LOCKED V3-4 RUNTIME SIGNAL EVIDENCE"
    }

    Write-Host "7. MATERIALIZING REAL DEVELOPMENT-ONLY FOUNDATION"
    python scripts/run_v3_g5_materialization.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 real foundation materialization failed."
    }

    Write-Host "8. VERIFYING COMPLETE MATERIALIZATION EVIDENCE"
    python scripts/verify_v3_g5_materialization.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 materialization evidence verification failed."
    }

    Write-Host "9. VERIFYING PATCH AND TRACKED-WORKTREE INTEGRITY"
    git diff --check
    if ($LASTEXITCODE -ne 0) {
        throw "Whitespace or patch-integrity defects were detected."
    }
    git diff --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 materialization modified tracked working-tree files."
    }
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 materialization modified the staged index."
    }

    Write-Host "Gate V3-5 real development foundation evidence passed."
    Write-Host "Development target primitives are materialized."
    Write-Host "Fold-specific large-move labels remain deferred."
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
