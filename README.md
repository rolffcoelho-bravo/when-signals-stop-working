# When Signals Stop Working

**A fully reproducible, benchmark-relative framework for testing whether technical indicators contain incremental information, where that information survives, and when deterioration becomes operationally meaningful.**

[![CI](https://github.com/rolffcoelho-bravo/when-signals-stop-working/actions/workflows/ci.yml/badge.svg)](https://github.com/rolffcoelho-bravo/when-signals-stop-working/actions/workflows/ci.yml)

## Research question

The repository evaluates RSI and Bollinger Bands on four-hour SOL data. It does not ask whether an indicator occasionally appears correct. It asks whether indicator information:

1. improves a non-indicator benchmark on unseen chronological data;
2. remains economically relevant after the declared cost assumption;
3. survives market-regime changes;
4. can be governed with explicit establishment and suspension rules.

A signal cannot be said to have **stopped working** unless it first established stable incremental value. If it never clears that gate, the correct status is `NOT_ESTABLISHED`.

## Published V1 finding

The frozen V1 experiment uses 12,171 aligned Binance spot candles from **2021-01-01 00:00 UTC** through **2026-07-22 08:00 UTC**. RSI and Bollinger Bands each improved predictive log loss in only 1 of 5 chronological folds; the combined model improved 2 of 5. All three models received `NOT_ESTABLISHED`.

See [`RESULTS.md`](RESULTS.md) and the complete generated [`outputs/research_report.md`](outputs/research_report.md).

## Frozen V1 specification

| Component | Setting |
|---|---|
| Research asset | SOL/USDT spot |
| Market context | BTC/USDT spot |
| Venue | Binance |
| Frequency | Four-hour candles |
| Forecast horizon | Next four-hour candle |
| RSI | 14 periods; 30/70 events |
| Bollinger Bands | 20 periods; 2 standard deviations |
| Validation | 5 expanding chronological folds with a gap |
| Cost assumption | 10 bps per one-way position change |
| Regimes | Filtered range, trend, stress |
| Monitoring | Robust one-sided CUSUM |

These settings are predeclared research assumptions, not claimed optimal parameters.

## Complete replication package

The public repository tracks the evidence necessary to reproduce V1 exactly:

```text
data/raw/                 frozen SOL and BTC OHLCV, provenance, validation
data/processed/           aligned data, model features, exact fold assignments
outputs/                  report, verdicts, all folds, OOS predictions, SVG figures
environment/              sanitized package versions
REPLICATION_MANIFEST.json snapshot definition and public-evidence map
REPLICATION_CHECKSUMS.sha256 file-integrity record
PUBLIC_RELEASE_AUDIT.json sensitive-information audit
```

No private account data or API credentials are used. The public snapshot was retrieved through public market-data interfaces.

## Run and verify

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

For a governed run plus Git commit and push, use `PUBLISH_PUBLIC_REPLICATION.ps1`.

The runner:

1. reuses the frozen snapshot by default;
2. validates timestamps and OHLCV integrity;
3. executes the implementation tests;
4. regenerates all model outputs and SVG figures;
5. builds processed replication datasets and fold assignments;
6. records sanitized runtime versions and SHA-256 checksums;
7. audits the public tree for credentials and local absolute paths;
8. verifies the generated replication package.

`-RefreshData` re-downloads the same frozen V1 date range. A genuinely new vintage requires explicit downloader dates and a new versioned experiment.

## Evidence architecture

```text
Conventional event evidence
        ↓
Common non-indicator benchmark
        ↓
Chronological out-of-sample comparison
        ↓
Filtered range / trend / stress state
        ↓
Sequential deterioration monitoring
        ↓
NOT_ESTABLISHED / ACTIVE / REDUCED / SUSPENDED
```

## Why the negative result is valuable

The V1 result shows that descriptive indicator events should not automatically be interpreted as stable forecasting edge. A rigorous negative finding narrows the next research question: whether information is conditional on horizon, target, regime, nonlinear response, or reversal-versus-continuation interpretation.

The predeclared V2 design is documented in [`ROADMAP.md`](ROADMAP.md). It uses nested walk-forward selection, multiple reported horizons and targets, a locked holdout, cross-venue replication, and formal predictive-comparison controls rather than post-hoc tuning.

## Documentation

- Results: [`RESULTS.md`](RESULTS.md)
- Start guide: [`START_HERE.md`](START_HERE.md)
- Replication package: [`docs/REPLICATION_PACKAGE.md`](docs/REPLICATION_PACKAGE.md)
- Public release policy: [`docs/PUBLIC_RELEASE_POLICY.md`](docs/PUBLIC_RELEASE_POLICY.md)
- Model contract: [`docs/MODEL_CONTRACT.md`](docs/MODEL_CONTRACT.md)
- Research protocol: [`docs/RESEARCH_PROTOCOL.md`](docs/RESEARCH_PROTOCOL.md)
- Figure catalog: [`docs/FIGURE_CATALOG.md`](docs/FIGURE_CATALOG.md)
- References: [`docs/REFERENCES.md`](docs/REFERENCES.md)
- Citation metadata: [`CITATION.cff`](CITATION.cff)

## Research boundaries

The results are venue-, pair-, timeframe-, sample-, target-, and cost-specific. V1 excludes funding, open interest, liquidations, order-book depth, venue-specific slippage, capacity, taxation, and live execution. This repository provides research evidence, not investment advice.

## License and data notice

ShockBridge-authored code and documentation are licensed under MIT. Third-party market data are included solely to support transparent replication and remain subject to the source venue's applicable terms and availability.
