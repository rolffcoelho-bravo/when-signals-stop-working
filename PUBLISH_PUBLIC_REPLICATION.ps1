param(
    [switch]$RefreshFrozenData
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-NativeStep {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    Write-Host "`n$Label"
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

if (-not (Test-Path ".git")) {
    throw "Run this script from the initialized repository root."
}

Write-Host "`nTECHNICAL SIGNAL VALIDITY FRAMEWORK"
Write-Host "Institutional Public Replication Release"
Write-Host "======================================="

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

if ($RefreshFrozenData) {
    & ".\RUN_REPLICATION.ps1" -RefreshData
} else {
    & ".\RUN_REPLICATION.ps1"
}
if (-not $?) {
    throw "The replication framework did not complete successfully."
}

$audit = Get-Content "PUBLIC_RELEASE_AUDIT.json" -Raw | ConvertFrom-Json
if ($audit.status -ne "PASS") {
    throw "The public release audit did not pass."
}

$forbiddenTrackedPatterns = @(
    "(^|/)\.venv/",
    "(^|/)__pycache__/",
    "(^|/)\.pytest_cache/",
    "(^|/)\.matplotlib/",
    "\.egg-info/",
    "(^|/)\.env($|\.)",
    "\.pem$",
    "\.key$",
    "credentials\.json$",
    "secrets\.json$"
)

$trackedCandidates = @(git ls-files --cached --others --exclude-standard)
$forbidden = @(
    $trackedCandidates | Where-Object {
        $path = $_
        $forbiddenTrackedPatterns | Where-Object { $path -match $_ }
    }
)
if ($forbidden.Count -gt 0) {
    throw "Forbidden files detected in the public tree: $($forbidden -join ', ')"
}

Write-Host "`nStaging the professional replication package"
git add -A
if ($LASTEXITCODE -ne 0) {
    throw "git add failed."
}

$staged = @(git diff --cached --name-only)
if ($staged.Count -eq 0) {
    Write-Host "No new changes require a commit."
} else {
    Write-Host "Files staged: $($staged.Count)"
    git commit -m "Publish complete V1 replication data and evidence"
    if ($LASTEXITCODE -ne 0) {
        throw "git commit failed."
    }

    Invoke-NativeStep `
        -Label "Pushing the public replication release" `
        -Executable "git" `
        -Arguments @("push", "origin", "main")
}

Write-Host "`nFinal verification"
git status
git log -2 --oneline

Write-Host "`nINSTITUTIONAL PUBLIC REPLICATION RELEASE COMPLETED SUCCESSFULLY."
Write-Host "Results: RESULTS.md"
Write-Host "Report: outputs\research_report.md"
Write-Host "Manifest: REPLICATION_MANIFEST.json"
Write-Host "Checksums: REPLICATION_CHECKSUMS.sha256"
Write-Host "Audit: PUBLIC_RELEASE_AUDIT.json"
