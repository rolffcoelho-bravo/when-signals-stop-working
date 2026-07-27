$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "$PSScriptRoot\src"
$env:OMP_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

$PreviousPythonNoUserSite = [Environment]::GetEnvironmentVariable(
    "PYTHONNOUSERSITE",
    "Process"
)

try {
    [Environment]::SetEnvironmentVariable("PYTHONNOUSERSITE", $null, "Process")

    Write-Host "GATE V3-4 - UNIFIED RSI AND BOLLINGER INTERPRETATION ENGINE"

    python scripts/verify_v3_realignment.py
    if ($LASTEXITCODE -ne 0) {
        throw "Repository realignment verification failed."
    }

    python -m pytest -q `
        tests/test_v3_signal_registry.py `
        tests/test_v3_signal_engine.py `
        tests/test_v3_signal_runner.py
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4 signal-engine tests failed."
    }

    python scripts/run_v3_signal_engine.py `
        --config "configs/v3_signal_engine_example.json" `
        --output-directory "outputs/v3/signal_engine"
    if ($LASTEXITCODE -ne 0) {
        throw "Gate V3-4 signal-engine execution failed."
    }

    Write-Host "Gate V3-4 implementation evidence passed."
}
finally {
    [Environment]::SetEnvironmentVariable(
        "PYTHONNOUSERSITE",
        $PreviousPythonNoUserSite,
        "Process"
    )
}
