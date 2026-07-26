param(
    [string]$Report = "outputs/v3/g3_final_acceptance/final_acceptance_report.json"
)

$ErrorActionPreference = "Stop"
$env:PYTHONNOUSERSITE = "1"
$env:PYTHONPATH = "$PSScriptRoot\src"
$env:OMP_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

Write-Host "GATE V3-3D — FINAL ACCEPTANCE AND LOCK AUTHORIZATION"
python scripts/run_v3_g3_final_acceptance.py --report $Report
if ($LASTEXITCODE -ne 0) {
    throw "Gate V3-3D final acceptance failed. The final V3-3 lock is not authorized."
}

Write-Host "Gate V3-3D acceptance evidence passed."
Write-Host "The final lock must be created only from the generated report."
