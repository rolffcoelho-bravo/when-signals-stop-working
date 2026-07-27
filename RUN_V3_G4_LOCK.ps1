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

    Write-Host "GATE V3-4 - AUTHORITATIVE LOCK MATERIALIZATION"

    Write-Host "1. GENERATING LOCK CANDIDATE FROM VALIDATED EVIDENCE"
    python scripts/finalize_v3_g4_lock.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4 lock candidate generation failed."
    }

    Write-Host "2. VERIFYING LOCK CANDIDATE AND CURATED EVIDENCE"
    python scripts/verify_v3_g4_lock.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4 lock candidate verification failed."
    }

    Write-Host "3. VERIFYING PATCH INTEGRITY"
    git diff --check
    if ($LASTEXITCODE -ne 0) {
        throw "Whitespace or patch-integrity defects were detected."
    }

    Write-Host "Gate V3-4 lock candidate is ready for repository review."
    Write-Host "Generated tracked candidates:"
    Write-Host "  V3_G4_SIGNAL_ENGINE_LOCK.json"
    Write-Host "  evidence/v3/g4_signal_lock/*.json"
    Write-Host "The large runtime signal_features.csv remains untracked and hash-bound."
    Write-Host "Gate V3-5 remains approved but must wait for final lock promotion."
}
finally {
    Set-Location $PreviousLocation
    [Environment]::SetEnvironmentVariable(
        "PYTHONNOUSERSITE",
        $PreviousPythonNoUserSite,
        "Process"
    )
}
