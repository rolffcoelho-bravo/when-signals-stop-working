$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $repo ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Repository Python environment not found: $python"
}

Set-Location $repo

Write-Host ""
Write-Host "TECHNICAL SIGNAL VALIDITY FRAMEWORK"
Write-Host "Version 2 D2C Development Admission and Pipeline Freeze"
Write-Host "=========================================================="

Write-Host "`n1. Verifying prior governance locks"
& $python scripts\verify_v2_protocol_lock.py
if ($LASTEXITCODE -ne 0) { throw "Protocol lock failed." }
& $python scripts\verify_v2_d0_lock.py
if ($LASTEXITCODE -ne 0) { throw "D0 lock failed." }
& $python scripts\verify_v2_d1_lock.py
if ($LASTEXITCODE -ne 0) { throw "D1 lock failed." }
& $python scripts\verify_v2_d2a_lock.py
if ($LASTEXITCODE -ne 0) { throw "D2A lock failed." }
& $python scripts\verify_v2_d2b_lock.py
if ($LASTEXITCODE -ne 0) { throw "D2B lock failed." }
& $python scripts\verify_v2_d2c_lock.py
if ($LASTEXITCODE -ne 0) { throw "D2C lock failed." }

Write-Host "`n2. Building development-only D2C admission assets"
& $python scripts\build_v2_d2c_assets.py
if ($LASTEXITCODE -ne 0) { throw "D2C admission build failed." }

Write-Host "`n3. Verifying D2C assets"
& $python scripts\verify_v2_d2c_assets.py
if ($LASTEXITCODE -ne 0) { throw "D2C asset verification failed." }

Write-Host "`n4. Running the complete implementation test suite"
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Repository tests failed." }

Write-Host "`nVERSION 2 D2C ADMISSION COMPLETED."
Write-Host "Economic gate evaluated: False"
Write-Host "Holdout authorization enabled: False"
Write-Host "Holdout performance accessed: False"
