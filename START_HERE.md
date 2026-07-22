# Start Here

## Exact public V1 replication

The repository includes the frozen market-data snapshot. No API key or exchange account is required.

### Windows

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\RUN_CHALLENGE.ps1
```

### macOS or Linux

```bash
chmod +x RUN_CHALLENGE.sh
./RUN_CHALLENGE.sh
```

After execution, inspect:

1. `RESULTS.md` — concise public conclusion;
2. `outputs/research_report.md` — complete generated evidence;
3. `outputs/figures/` — publication-grade SVG figures;
4. `REPLICATION_MANIFEST.json` — snapshot and evidence map;
5. `REPLICATION_CHECKSUMS.sha256` — integrity record;
6. `PUBLIC_RELEASE_AUDIT.json` — sensitive-information audit.

## Creating a new data vintage

```powershell
.\RUN_CHALLENGE.ps1 -RefreshData
```

`-RefreshData` re-downloads the frozen V1 window. To extend the sample, run the downloader with explicit dates and publish the result as a new versioned experiment.
