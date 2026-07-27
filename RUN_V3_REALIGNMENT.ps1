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

try {
    [Environment]::SetEnvironmentVariable("PYTHONNOUSERSITE", $null, "Process")

    Write-Host "GATE V3-REALIGNMENT - RICHARD QUESTION AND CORE SEQUENCE"
    python -m pytest -q tests/test_v3_realignment_contract.py
    if ($LASTEXITCODE -ne 0) {
        throw "Version 3 repository realignment tests failed."
    }

    python scripts/verify_v3_realignment.py
    if ($LASTEXITCODE -ne 0) {
        throw "Version 3 repository realignment verification failed."
    }

    Write-Host "Version 3 repository realignment evidence passed."
}
finally {
    [Environment]::SetEnvironmentVariable(
        "PYTHONNOUSERSITE",
        $PreviousPythonNoUserSite,
        "Process"
    )
}
