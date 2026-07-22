# Start Here

## Windows

Run from the repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\RUN_CHALLENGE.ps1
```

The runner will:

1. create or reuse `.venv`;
2. install the project in editable mode;
3. reuse valid local OHLCV files or download public SOL/USDT and BTC/USDT candles;
4. validate timestamps, overlap, missing values, and four-hour spacing;
5. run the implementation tests;
6. clear stale generated evidence;
7. execute RSI, Bollinger, and combined models;
8. generate vector SVG figures and the referenced research report;
9. print separate direct conclusions.

Use `./RUN_CHALLENGE.ps1 -RefreshData` to force a fresh public-data download.

## macOS or Linux

```bash
chmod +x RUN_CHALLENGE.sh
./RUN_CHALLENGE.sh
```

## Principal outputs

Open these first:

```text
outputs/research_report.md
outputs/final_verdicts.json
outputs/figures/figure_02_validation_evidence.svg
outputs/figures/monitoring_bollinger.svg
```

## Reproducibility note

The public data route uses CCXT exchange OHLCV endpoints. No trading credentials are required for the default download. Results are venue-, symbol-, frequency-, sample-, and cost-specific.
