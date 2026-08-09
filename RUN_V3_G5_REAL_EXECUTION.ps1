$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "$PSScriptRoot\src"

# We must constrain the math threads to 1 per worker so they don't fight
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

    Write-Host "GATE V3-5 - REAL DEVELOPMENT EXECUTION"
    
    $LockFile = "V3_G5_REAL_EXECUTION_AUTHORIZATION_LOCK.json"
    if (-not (Test-Path $LockFile)) {
        Write-Host "Authorization lock missing. Attempting to finalize candidate..."
        python scripts/finalize_v3_g5_real_execution_authorization.py
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to finalize execution authorization."
        }
    }
    
    Write-Host "Starting multi-processing local execution runner..."
    python -W error::FutureWarning scripts/run_v3_g5_execution_orchestrator.py
    if ($LASTEXITCODE -ne 0) {
        throw "Real development execution failed or encountered errors."
    }
    
    Write-Host "Real development execution completed."
}
finally {
    Set-Location $PreviousLocation
    [Environment]::SetEnvironmentVariable(
        "PYTHONNOUSERSITE",
        $PreviousPythonNoUserSite,
        "Process"
    )
}
