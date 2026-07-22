# When Signals Stop Working

A governed Python research framework for answering a question that ordinary indicator backtests rarely answer:

> When does a technical signal stop adding useful information?

The repository implements both **RSI** and **Bollinger Bands** for SOL, then bridges them through one common validation contract.


## Small challenge

**ShockBridge Pulse Technical Signal Validity Challenge**

The challenge asks:

> When does RSI stop working, and does the same establishment-and-failure logic apply to Bollinger Bands once Richard's corrected indicator is tested?

Bollinger Bands are the corrected primary empirical signal. RSI remains a parallel first-class model because it answers Richard's original question directly. The combined model is secondary.

## Fastest Windows route

From PowerShell in the repository folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\RUN_CHALLENGE.ps1
```

The script creates a virtual environment, installs the project, downloads free public SOL/USDT and BTC/USDT candles, validates the data, runs the tests, executes the three-stage model, and prints the final verdict.

For manual instructions, open [`START_HERE.md`](START_HERE.md).

## Why both indicators are included

Richard originally referred to RSI and later corrected the indicator to Bollinger Bands. They are related because both can be used to describe price extremes, but they measure different structures:

- **RSI** measures recent gain-loss momentum.
- **Bollinger Bands** measure price location relative to a volatility-adjusted moving range.

They should not be treated as substitutes.

The framework therefore uses:

1. **Bollinger Bands as the corrected primary empirical candidate**, because that is the signal Richard actually used.
2. **RSI as a parallel first-class candidate**, because the original question - "When will RSI stop working?" - still requires a direct answer.
3. **A combined model as a secondary robustness test**, evaluating whether momentum and volatility-position information reinforce each other.

The combined model is not allowed to replace the primary result merely because it performs better after the data are observed.

## The three-stage architecture

### Stage 1 - Event validity

The framework tests conventional events:

- RSI crosses below 30 or above 70.
- SOL closes outside a 20-period, two-standard-deviation Bollinger Band.
- Both indicators become extreme in the same reversal direction.

It measures event count, net signed return, win rate, confidence interval, and an exploratory matched-random comparison.

### Stage 2 - Incremental benchmark comparison

Every signal model is compared with the same non-indicator baseline:

```text
Baseline:
SOL returns + BTC returns + trend + volatility + range + volume + market state
```

Candidate models add:

- RSI features,
- Bollinger features, or
- both indicator families and concordance features.

All results are generated through expanding chronological folds with a horizon-sized gap. No random train-test split is used.

### Stage 3 - Filtered regimes and structural-change monitoring

A compact three-state Gaussian Markov filter is fitted on each training fold and then updated sequentially through the test period. It produces filtered probabilities for range, trend, and stress without using future test observations.

A single one-sided CUSUM then monitors deterioration in benchmark-relative predictive loss and net edge.

A signal receives one of four operational conclusions:

- **ACTIVE** - incremental value remains positive in the current monitoring window.
- **REDUCED** - evidence is conditional, uncertain, or concentrated in particular regimes.
- **SUSPENDED** - a historically supported signal crosses the declared failure gate for consecutive monitoring windows.
- **NOT_ESTABLISHED** - reliable incremental value was never demonstrated.

This distinction is essential. A signal cannot be said to have "stopped working" when it was never established under a valid test.

## Default research specification

- Asset: SOL/USDT
- Market context: BTC/USDT
- Candle frequency: 4 hours
- Forecast horizon: next 4-hour candle
- RSI: 14 periods, 30/70
- Bollinger Bands: 20 periods, 2 standard deviations
- Primary signal: Bollinger Bands
- Costs: 10 basis points per one-way position change
- Validation: 5 expanding chronological folds
- Monitoring: one 180-observation calibration window and one online CUSUM

These are frozen demonstration assumptions, not universal optimal parameters.

## Installation

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS or Linux:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -e ".[dev]"
```

## Run with public exchange data

```bash
python -m shockbridge_signal_validity \
  --signals rsi bollinger combined \
  --primary-signal bollinger \
  --exchange binance \
  --sol-symbol SOL/USDT \
  --btc-symbol BTC/USDT \
  --timeframe 4h \
  --start 2021-01-01 \
  --horizon 1 \
  --cost-bps 10 \
  --output-directory outputs
```

Public data availability depends on the exchange and jurisdiction.

## Run with local CSV files

```bash
python -m shockbridge_signal_validity \
  --sol-csv data/sol_4h.csv \
  --btc-csv data/btc_4h.csv \
  --signals rsi bollinger combined \
  --primary-signal bollinger
```

Required columns:

```text
Date, Open, High, Low, Close, Volume
```

## Outputs

```text
stage_1_event_study.csv
stage_2_fold_results.csv
stage_2_oos_predictions.csv
stage_3_regime_summary.csv
final_verdicts.json
research_report.md
cumulative_net_return_<signal>.png
rolling_incremental_edge_<signal>.png
structural_change_<signal>.png
```

## Direct answers produced by the framework

The report produces one conclusion for RSI and another for Bollinger Bands. A valid statement for either signal takes one of these forms:

> Bollinger Band extremes never demonstrated incremental predictive value under the frozen specification. Their apparent success should not be described as an edge that later stopped working.

> Bollinger Band information added value only during range-bound conditions. The signal became non-actionable when the market moved into persistent trend or stress regimes and its recent incremental edge crossed the failure gate.

> Bollinger Bands retained positive benchmark-relative value after costs and chronological validation. The signal remains active under the current monitoring rule.

## Research boundaries

This repository is a reproducible research prototype. It does not include order-book depth, liquidation data, funding rates, exchange-specific slippage, tax treatment, or live execution. It does not provide investment advice.
