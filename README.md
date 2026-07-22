# When Signals Stop Working

**A benchmark-relative framework for testing whether technical signals contain incremental information, where that information survives, and when deterioration becomes operationally meaningful.**

The repository evaluates two widely used signal families on four-hour SOL data:

- **RSI** - recent gain-loss momentum;
- **Bollinger Bands** - price location relative to a volatility-adjusted range.

The central question is not whether either indicator occasionally predicts the correct direction. It is whether the indicator improves a non-indicator benchmark on unseen chronological data, remains economically relevant after assumed costs, and retains that contribution across changing market regimes.

## Research logic

```text
Conventional signal event
        |
        v
Non-indicator benchmark comparison
        |
        v
Chronological out-of-sample evidence
        |
        v
Filtered range / trend / stress state
        |
        v
Sequential deterioration monitoring
        |
        v
NOT_ESTABLISHED / ACTIVE / REDUCED / SUSPENDED
```

A signal cannot be said to have “stopped working” unless it first demonstrated incremental value. If it never improves the benchmark, the correct conclusion is `NOT_ESTABLISHED`, not `SUSPENDED`.

## Current methodology - V1

V1 is deliberately simple, transparent, and reproducible:

1. threshold-event evidence for RSI, Bollinger Bands, and their secondary concordance test;
2. regularized logistic models compared with the same market-information benchmark;
3. expanding-window validation with a forecast-horizon gap;
4. transaction-cost-adjusted incremental edge and dependence-aware confidence intervals;
5. a training-only three-state Gaussian Markov forward filter;
6. a one-sided CUSUM deterioration monitor;
7. separate public verdicts for RSI and Bollinger Bands.

The advanced methodology roadmap is documented in [`ROADMAP.md`](ROADMAP.md).

## Default public specification

| Component | Frozen V1 setting |
|---|---|
| Asset | SOL/USDT spot |
| Market context | BTC/USDT spot |
| Frequency | Four-hour candles |
| Forecast horizon | Next four-hour candle |
| RSI | 14 periods; 30/70 events |
| Bollinger Bands | 20 periods; 2 standard deviations |
| Validation | 5 expanding chronological folds |
| Cost assumption | 10 basis points per one-way position change |
| Regimes | Range, trend, stress |
| Monitoring | One-sided online CUSUM |

These are predeclared research assumptions, not claimed optimal parameters.

## One-command Windows run

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\RUN_CHALLENGE.ps1
```

The runner reuses valid downloaded data, creates an isolated Matplotlib environment, executes implementation tests, stops on any native-command failure, and generates the evidence report and SVG figure suite.

Manual instructions are in [`START_HERE.md`](START_HERE.md).

## Evidence outputs

```text
outputs/
├── research_report.md
├── final_verdicts.json
├── run_manifest.json
├── stage_1_event_study.csv
├── stage_2_fold_results.csv
├── stage_2_oos_predictions.csv
├── stage_3_regime_summary.csv
└── figures/
    ├── figure_01_market_signal_anatomy.svg
    ├── figure_02_validation_evidence.svg
    ├── figure_03_probability_calibration.svg
    ├── figure_04_regime_evidence_matrix.svg
    ├── monitoring_rsi.svg
    ├── monitoring_bollinger.svg
    └── monitoring_combined.svg
```

The figures are vector-first, publication-oriented, and memory-safe. Raster export is optional rather than the default.

## Interpretation

The framework separates four different claims that are often conflated:

- **descriptive event effect** - what usually followed a conventional threshold event;
- **incremental predictive value** - whether the signal improves the benchmark probability forecast;
- **incremental economic value** - whether that improvement survives the declared cost assumption;
- **structural persistence** - whether the contribution remains credible under the current filtered regime and sequential monitor.

A negative result is informative. It can indicate that the indicator’s apparent effect was already encoded by trend, volatility, recent returns, or broader crypto-market movement.

## Public research boundaries

The V1 framework does not use order-book depth, funding, open interest, liquidation data, venue-specific slippage, tax treatment, or live execution. It is a research-validation repository, not an investment recommendation or a claim of universal market efficiency.

## Reproducibility and references

- Model contract: [`docs/MODEL_CONTRACT.md`](docs/MODEL_CONTRACT.md)
- Research protocol: [`docs/RESEARCH_PROTOCOL.md`](docs/RESEARCH_PROTOCOL.md)
- Figure catalog: [`docs/FIGURE_CATALOG.md`](docs/FIGURE_CATALOG.md)
- References: [`docs/REFERENCES.md`](docs/REFERENCES.md)
- Citation metadata: [`CITATION.cff`](CITATION.cff)

## License

MIT. Data remain subject to the terms and availability of their source venue and API provider.
