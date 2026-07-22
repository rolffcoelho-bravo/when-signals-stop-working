$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Write-Host ""
Write-Host "TECHNICAL SIGNAL VALIDITY FRAMEWORK"
Write-Host "Version 2 Development Implementation Scaffold"
Write-Host "================================================="

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Repository virtual environment not found: $Python"
}

Set-Location $PSScriptRoot

Write-Host ""
Write-Host "1. Verifying the frozen Version 2 protocol"
& $Python "scripts\verify_v2_protocol_lock.py"
if ($LASTEXITCODE -ne 0) { throw "Protocol-lock verification failed." }

Write-Host ""
Write-Host "2. Building development-only assets"
& $Python "scripts\build_v2_development_assets.py"
if ($LASTEXITCODE -ne 0) { throw "Development-asset generation failed." }

Write-Host ""
Write-Host "3. Verifying the development scaffold"
& $Python "scripts\verify_v2_development_scaffold.py"
if ($LASTEXITCODE -ne 0) { throw "Development-scaffold verification failed." }

Write-Host ""
Write-Host "4. Running implementation tests"
& $Python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Implementation tests failed." }

Write-Host ""
Write-Host "VERSION 2 DEVELOPMENT SCAFFOLD COMPLETED."
Write-Host "Model fitting performed: False"
Write-Host "Holdout performance accessed: False"
