# Replication Package

## Purpose

The public release contains the minimum complete chain required to audit and reproduce the V1 conclusion:

1. frozen raw market data;
2. provenance and data-quality records;
3. deterministic feature and fold definitions;
4. complete out-of-sample predictions;
5. summary evidence and verdicts;
6. publication-grade figures;
7. runtime versions and file checksums.

## Exact replication

Run the repository without refreshing data:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\RUN_CHALLENGE.ps1
```

The runner uses the tracked frozen data snapshot, validates it, executes the tests, regenerates the model evidence, creates processed replication assets, verifies checksums, and audits the public release for sensitive paths or credentials.

## New data vintage

`RUN_CHALLENGE.ps1 -RefreshData` re-downloads the same frozen V1 window. Extending the end date requires explicit downloader arguments and must be published as a new versioned experiment.

## Public-surface rule

Tracked evidence includes data and outputs necessary for replication. Excluded content is limited to virtual environments, caches, build metadata, local logs, credentials, private keys, and optional raster exports.
