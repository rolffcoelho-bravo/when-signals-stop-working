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

    Write-Host "GATE V3-5 - FOLD-SCOPED PREPROCESSING AND MATCHED ESTIMATOR IMPLEMENTATION"

    Write-Host "1. VERIFYING FINAL V3-4 PARENT LOCK"
    python scripts/verify_v3_g4_lock.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4 final parent lock verification failed."
    }

    Write-Host "2. VERIFYING VALIDATED V3-5 CONTRACT AND FOUNDATION OBJECTS"
    python scripts/verify_v3_g5_validated_boundaries.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 validated foundation boundary verification failed."
    }

    Write-Host "3. VERIFYING VALIDATED V3-5 MATERIALIZATION BOUNDARY"
    python scripts/verify_v3_g5_materialization_boundary.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 materialization boundary verification failed."
    }

    $MaterializationManifest = "outputs\v3\forecast_foundation\materialization_manifest.json"
    if (-not (Test-Path $MaterializationManifest)) {
        Write-Host "4. REGENERATING VALIDATED REAL DEVELOPMENT FOUNDATION"
        .\RUN_V3_G5_MATERIALIZATION.ps1
        if ($LASTEXITCODE -ne 0) {
            throw "Gate V3-5 materialization regeneration failed."
        }
    }
    else {
        Write-Host "4. VERIFYING EXISTING REAL DEVELOPMENT FOUNDATION"
        python scripts/verify_v3_g5_materialization.py
        if ($LASTEXITCODE -ne 0) {
            throw "Gate V3-5 existing materialization verification failed."
        }
    }

    Write-Host "5. RUNNING MODEL IMPLEMENTATION TESTS"
    python -m pytest -q `
        tests/test_v3_g5_preprocessing.py `
        tests/test_v3_g5_model_registry.py `
        tests/test_v3_g5_estimators.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 model implementation tests failed."
    }

    Write-Host "6. RUNNING STANDALONE MODEL IMPLEMENTATION VERIFIER"
    python scripts/verify_v3_g5_model_implementation.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 model implementation verification failed."
    }

    Write-Host "7. VERIFYING PATCH AND TRACKED-WORKTREE INTEGRITY"
    git diff --check
    if ($LASTEXITCODE -ne 0) {
        throw "Whitespace or patch-integrity defects were detected."
    }
    git diff --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 model implementation modified tracked working-tree files."
    }
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-5 model implementation modified the staged index."
    }

    Write-Host "Gate V3-5 model implementation evidence passed."
    Write-Host "Fold-scoped preprocessing is implemented."
    Write-Host "Matched estimator families are implemented."
    Write-Host "Only synthetic estimator fits were executed."
    Write-Host "Real development model fitting remains disabled."
    Write-Host "Development pipeline selection remains disabled."
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
