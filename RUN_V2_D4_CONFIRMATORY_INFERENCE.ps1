
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Repository Python environment not found: $python"
}

Set-Location $PSScriptRoot

Write-Host ""
Write-Host "TECHNICAL SIGNAL VALIDITY FRAMEWORK"
Write-Host "Version 2 D4 Confirmatory Inference and Economic Gates"
Write-Host "========================================================="

Write-Host "`n1. Verifying prior governance locks"
& $python scripts\verify_v2_protocol_lock.py
& $python scripts\verify_v2_d0_lock.py
& $python scripts\verify_v2_d1_lock.py
& $python scripts\verify_v2_d2a_lock.py
& $python scripts\verify_v2_d2b_lock.py
& $python scripts\verify_v2_d2c_lock.py
& $python scripts\verify_v2_d3_lock.py
& $python scripts\verify_v2_d3_assets.py
& $python scripts\verify_v2_d4_lock.py
if ($LASTEXITCODE -ne 0) { throw "A governance lock or D3 evidence verification failed." }

Write-Host "`n2. Building D4 confirmatory evidence"
& $python scripts\build_v2_d4_assets.py
if ($LASTEXITCODE -ne 0) { throw "D4 inference execution failed." }

Write-Host "`n3. Verifying D4 assets"
& $python scripts\verify_v2_d4_assets.py
if ($LASTEXITCODE -ne 0) { throw "D4 asset verification failed." }

Write-Host "`n4. Running the complete implementation test suite"
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "The complete repository test suite failed." }

Write-Host "`nVERSION 2 D4 CONFIRMATORY INFERENCE COMPLETED."
Write-Host "Pipeline retuning performed: False"
Write-Host "RSI re-entry performed: False"
Write-Host "V2.1 panic-state extension used: False"
