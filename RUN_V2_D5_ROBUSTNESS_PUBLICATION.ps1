$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Repository Python environment not found: $python"
}

Write-Host ""
Write-Host "TECHNICAL SIGNAL VALIDITY FRAMEWORK"
Write-Host "Version 2 D5 Robustness and Publication Evidence"
Write-Host "===================================================="

Write-Host ""
Write-Host "1. Verifying prior governance locks"

$verificationScripts = @(
    "verify_v2_protocol_lock.py",
    "verify_v2_d0_lock.py",
    "verify_v2_d1_lock.py",
    "verify_v2_d2a_lock.py",
    "verify_v2_d2b_lock.py",
    "verify_v2_d2c_lock.py",
    "verify_v2_d3_lock.py",
    "verify_v2_d3_assets.py",
    "verify_v2_d4_lock.py",
    "verify_v2_d4_assets.py",
    "verify_v2_d5_lock.py"
)

foreach ($script in $verificationScripts) {
    & $python (Join-Path "scripts" $script)
    if ($LASTEXITCODE -ne 0) {
        throw "Governance verification failed: $script"
    }
}

Write-Host ""
Write-Host "2. Building D5 robustness and publication evidence"

& $python "scripts\build_v2_d5_assets.py"
if ($LASTEXITCODE -ne 0) {
    throw "D5 evidence generation failed."
}

Write-Host ""
Write-Host "3. Verifying D5 assets"

& $python "scripts\verify_v2_d5_assets.py"
if ($LASTEXITCODE -ne 0) {
    throw "D5 asset verification failed."
}

Write-Host ""
Write-Host "4. Running the complete implementation test suite"

& $python -m pytest -q
if ($LASTEXITCODE -ne 0) {
    throw "The complete repository test suite failed."
}

Write-Host ""
Write-Host "VERSION 2 D5 ROBUSTNESS AND PUBLICATION COMPLETED."
Write-Host "Final evidence grade:        NO_INCREMENTAL_EVIDENCE"
Write-Host "Primary case established:    False"
Write-Host "Pipeline retuning performed: False"
Write-Host "RSI re-entry performed:      False"
Write-Host "V2.1 panic extension used:   False"
