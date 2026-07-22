# Replication Package Specification

## Purpose

The public release contains the minimum complete evidence chain required to audit and reproduce the Version 1 determination:

1. frozen raw market data;
2. provenance and data-quality records;
3. deterministic feature and target definitions;
4. exact chronological fold membership;
5. complete out-of-sample predictions;
6. summary evidence and operational determinations;
7. vector analytical figures;
8. sanitized runtime versions and integrity checksums.

## Exact replication

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\RUN_REPLICATION.ps1
```

The runner uses the tracked frozen snapshot, validates the data, executes the tests, regenerates the analytical evidence, creates processed replication assets, audits the public tree, and verifies the checksum record.

## New data vintage

`RUN_REPLICATION.ps1 -RefreshData` retrieves the same frozen Version 1 window. Extending the sample requires explicit downloader arguments and constitutes a new versioned experiment.

## Public-surface control

Tracked evidence includes only the data and outputs required for replication. Excluded content comprises virtual environments, caches, packaging metadata, local logs, credentials, private keys, machine-specific paths, and optional raster duplicates.
