$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Write-Host ""
Write-Host "TECHNICAL SIGNAL VALIDITY FRAMEWORK"
Write-Host "Version 2 D2B Full Nested Pipeline Selection"
Write-Host "=================================================="

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Repository Python environment not found: $python"
}

Set-Location $PSScriptRoot

Write-Host "`n1. Verifying prior governance locks"
& $python scripts\verify_v2_protocol_lock.py
if ($LASTEXITCODE -ne 0) { throw "Protocol lock verification failed." }
& $python scripts\verify_v2_d0_lock.py
if ($LASTEXITCODE -ne 0) { throw "D0 lock verification failed." }
& $python scripts\verify_v2_d1_lock.py
if ($LASTEXITCODE -ne 0) { throw "D1 lock verification failed." }
& $python scripts\verify_v2_d2a_lock.py
if ($LASTEXITCODE -ne 0) { throw "D2A lock verification failed." }
& $python scripts\verify_v2_d2b_lock.py
if ($LASTEXITCODE -ne 0) { throw "D2B lock verification failed." }

Write-Host "`n2. Running development-only full nested pipeline selection"
& $python scripts\build_v2_d2b_assets.py
if ($LASTEXITCODE -ne 0) { throw "D2B selection execution failed." }

Write-Host "`n3. Verifying D2B assets"
& $python scripts\verify_v2_d2b_assets.py
if ($LASTEXITCODE -ne 0) { throw "D2B asset verification failed." }

Write-Host "`n4. Running the complete implementation test suite"
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Repository tests failed." }

Write-Host "`nVERSION 2 D2B SELECTION COMPLETED."
Write-Host "Nested pipeline selection performed: True"
Write-Host "Economic gate evaluated: False"
Write-Host "Holdout pipeline freeze performed: False"
Write-Host "Holdout performance accessed: False"
