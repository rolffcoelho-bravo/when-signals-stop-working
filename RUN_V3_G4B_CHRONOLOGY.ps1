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
    Write-Host "GATE V3-4B - CHRONOLOGY COMPILATION AND PROVENANCE"
    python -m pytest -q tests/test_v3_external_chronology_registry.py tests/test_v3_cross_gate_lineage.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4B chronology tests failed."
    }
    python scripts/verify_v3_cross_gate_lineage.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3 cross-gate lineage verification failed."
    }
    python scripts/run_v3_g4b_chronology.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4B chronology compilation failed."
    }
    Write-Host "Gate V3-4B chronology evidence passed."
}
finally {
    [Environment]::SetEnvironmentVariable(
        "PYTHONNOUSERSITE",
        $PreviousPythonNoUserSite,
        "Process"
    )
}
