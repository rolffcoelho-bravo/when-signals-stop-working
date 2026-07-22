$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Write-Host ""
Write-Host "TECHNICAL SIGNAL VALIDITY FRAMEWORK"
Write-Host "Version 2 D2A Nested Linear Signal Screening"
Write-Host "=================================================="

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Repository Python environment not found: $python"
}

Set-Location $PSScriptRoot

Write-Host "`n1. Verifying prior governance locks"
& $python scripts\verify_v2_protocol_lock.py
& $python scripts\verify_v2_d0_lock.py
& $python scripts\verify_v2_d1_lock.py
& $python scripts\verify_v2_d2a_lock.py

Write-Host "`n2. Running development-only nested signal screening"
& $python scripts\build_v2_d2a_assets.py

Write-Host "`n3. Verifying D2A assets"
& $python scripts\verify_v2_d2a_assets.py

Write-Host "`n4. Running the complete implementation test suite"
& $python -m pytest -q

Write-Host "`nVERSION 2 D2A SCREENING COMPLETED."
Write-Host "Predictive model fitting performed: True"
Write-Host "Final pipeline selection performed: False"
Write-Host "Holdout performance accessed: False"
