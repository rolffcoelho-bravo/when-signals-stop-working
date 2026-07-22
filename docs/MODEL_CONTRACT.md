# V1 Model Contract

## Objective

Test whether RSI or Bollinger Band information adds benchmark-relative, out-of-sample predictive and economic value for the next SOL return, and whether any established contribution remains operationally credible.

## Data contract

- SOL/USDT and BTC/USDT spot OHLCV;
- equal four-hour timestamps;
- UTC index;
- no duplicate timestamps or missing OHLCV fields;
- venue, symbol, sample, and retrieval timestamp recorded in the data manifest.

## Target

For horizon `h`:

```text
future_return[t] = log(close[t+h] / close[t])
target_up[t] = 1{future_return[t] > 0}
```

## Baseline

The non-indicator model contains recent SOL and BTC returns, trend, realized volatility, price range, volume, and transparent lagged market-state descriptors.

## Candidate models

- baseline + RSI level, slope, extremes, and interactions;
- baseline + Bollinger %B, BandWidth, distances, extremes, and interactions;
- baseline + both families and concordance features as a secondary model.

## Validation

- no random shuffle;
- expanding chronological folds;
- gap equal to the forecast horizon;
- fold-local scaling and estimation;
- out-of-sample probability predictions only;
- log loss as the primary probability score;
- cost-adjusted incremental net edge;
- moving-block bootstrap confidence intervals.

## Filtered regimes

V1 uses a transparent three-state Gaussian Markov forward filter initialized from training-only clusters of return, realized volatility, and trend. The test period is processed sequentially. No smoothed full-sample state is used for a historical decision.

## Structural monitor

A one-sided CUSUM monitors robustly standardized deterioration in incremental log-loss improvement and incremental net edge.

## Status rules

- `NOT_ESTABLISHED`: historical incremental evidence fails the establishment gate;
- `ACTIVE`: established signal, positive current evidence, no deterioration alarm;
- `REDUCED`: established signal with uncertain, regime-dependent, or deteriorating current evidence;
- `SUSPENDED`: established signal, active deterioration alarm, non-positive current predictive and economic gates.

## Model boundaries

V1 is not a parameter-optimization engine, execution simulator, or universal claim about SOL. Advanced inference, richer market data, and probabilistic failure hazards are reserved for later roadmap versions.
