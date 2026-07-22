# Replication Guide

## Purpose

This guide reproduces the published Version 1 assessment using the tracked and checksum-verified market-data snapshot. No exchange account, API key, or private trading interface is required.

## System requirement

Python 3.11 or later is recommended.

## Windows

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\RUN_REPLICATION.ps1
```

## macOS or Linux

```bash
chmod +x RUN_REPLICATION.sh
./RUN_REPLICATION.sh
```

## Verification sequence

The replication process performs the following controls:

1. validates the frozen SOL and BTC OHLCV snapshot;
2. executes the implementation and public-reporting tests;
3. regenerates the Version 1 model outputs;
4. recreates the vector evidence suite;
5. rebuilds processed data and exact fold assignments;
6. records sanitized runtime versions;
7. calculates SHA-256 integrity checksums;
8. audits the public tree for credentials and local machine paths;
9. verifies the completed replication package.

## Primary outputs

Review the following files after completion:

1. `RESULTS.md` - institutional empirical determination;
2. `outputs/research_report.md` - complete generated evidence report;
3. `outputs/figures/` - vector analytical figures;
4. `REPLICATION_MANIFEST.json` - snapshot and evidence map;
5. `REPLICATION_CHECKSUMS.sha256` - file-integrity record;
6. `PUBLIC_RELEASE_AUDIT.json` - sensitive-information audit.

## New data vintage

```powershell
.\RUN_REPLICATION.ps1 -RefreshData
```

`-RefreshData` retrieves the same frozen Version 1 date range. Extending the sample constitutes a new experiment and must be published under a new version with updated manifests, checksums, results, and interpretation.
