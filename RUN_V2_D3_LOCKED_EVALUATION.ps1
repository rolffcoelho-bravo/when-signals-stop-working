$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Repository Python environment not found: $python" }

$env:SHOCKBRIDGE_V2_HOLDOUT_AUTHORIZED = "YES"

& $python "scripts\verify_v2_protocol_lock.py"
if ($LASTEXITCODE -ne 0) { throw "Protocol lock verification failed." }
& $python "scripts\verify_v2_d0_lock.py"
if ($LASTEXITCODE -ne 0) { throw "D0 lock verification failed." }
& $python "scripts\verify_v2_d1_lock.py"
if ($LASTEXITCODE -ne 0) { throw "D1 lock verification failed." }
& $python "scripts\verify_v2_d2a_lock.py"
if ($LASTEXITCODE -ne 0) { throw "D2A lock verification failed." }
& $python "scripts\verify_v2_d2b_lock.py"
if ($LASTEXITCODE -ne 0) { throw "D2B lock verification failed." }
& $python "scripts\verify_v2_d2c_lock.py"
if ($LASTEXITCODE -ne 0) { throw "D2C lock verification failed." }
& $python "scripts\verify_v2_d3_lock.py"
if ($LASTEXITCODE -ne 0) { throw "D3 lock verification failed." }
& $python "scripts\build_v2_d3_assets.py"
if ($LASTEXITCODE -ne 0) { throw "D3 methodology-locked evaluation failed." }
& $python "scripts\verify_v2_d3_assets.py"
if ($LASTEXITCODE -ne 0) { throw "D3 asset verification failed." }
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Repository tests failed after D3." }

Write-Host "VERSION 2 D3 METHODOLOGY-LOCKED EVALUATION COMPLETED."
