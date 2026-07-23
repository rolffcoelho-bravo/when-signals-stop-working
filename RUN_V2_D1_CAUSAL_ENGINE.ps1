$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Write-Host "`nTECHNICAL SIGNAL VALIDITY FRAMEWORK"
Write-Host "Version 2 D1 Causal Feature and Filtered-State Engine"
Write-Host "======================================================="

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Repository Python environment not found: $Python"
}

Set-Location $PSScriptRoot

Write-Host "`n1. Verifying the frozen Version 2 protocol"
& $Python "scripts\verify_v2_protocol_lock.py"
if ($LASTEXITCODE -ne 0) { throw "Protocol lock verification failed." }

Write-Host "`n2. Verifying the D0 implementation lock"
& $Python "scripts\verify_v2_d0_lock.py"
if ($LASTEXITCODE -ne 0) { throw "D0 implementation lock verification failed." }

Write-Host "`n3. Verifying the D1 engine lock"
& $Python "scripts\verify_v2_d1_lock.py"
if ($LASTEXITCODE -ne 0) { throw "D1 engine lock verification failed." }

Write-Host "`n4. Building development-only D1 assets"
& $Python "scripts\build_v2_d1_assets.py"
if ($LASTEXITCODE -ne 0) { throw "D1 asset generation failed." }

Write-Host "`n5. Verifying D1 assets"
& $Python "scripts\verify_v2_d1_assets.py"
if ($LASTEXITCODE -ne 0) { throw "D1 asset verification failed." }

Write-Host "`n6. Running the complete implementation test suite"
& $Python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Repository tests failed." }

Write-Host "`nVERSION 2 D1 CAUSAL ENGINE COMPLETED."
Write-Host "Predictive model fitting performed: False"
Write-Host "State-filter fitting performed: True"
Write-Host "Holdout performance accessed: False"
