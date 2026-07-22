# Version 1 Model Contract

## Objective

Assess whether RSI or Bollinger Band information contributes benchmark-relative, out-of-sample predictive and economic value for the next SOL/USDT return and, where establishment is achieved, whether that contribution remains operationally credible.

## Data contract

- SOL/USDT and BTC/USDT spot OHLCV;
- common four-hour UTC timestamps;
- no duplicate timestamps;
- no missing OHLCV fields;
- venue, instrument, sample, and retrieval timestamp recorded in the data manifest;
- source and processed files covered by SHA-256 checksums.

## Target definition

For forecast horizon `h`:

```text
future_return[t] = log(close[t+h] / close[t])
target_up[t] = 1{future_return[t] > 0}
```

## Common benchmark

The non-indicator model contains recent SOL and BTC returns, trend, realized volatility, price range, volume, and transparent lagged market-state descriptors.

## Candidate models

- benchmark plus RSI level, slope, extremes, and interactions;
- benchmark plus Bollinger `%B`, BandWidth, distances, extremes, and interactions;
- benchmark plus both variable families and concordance features as a secondary specification.

## Validation contract

- no random shuffle;
- expanding chronological folds;
- gap equal to the forecast horizon;
- fold-local scaling and estimation;
- out-of-sample probability predictions only;
- log loss as the primary probability score;
- cost-adjusted incremental net edge;
- moving-block bootstrap uncertainty intervals.

## Filtered market states

Version 1 uses a transparent three-state Gaussian Markov forward filter initialized from training-only clusters of return, realized volatility, and trend. Test observations are processed sequentially. Full-sample smoothed states are not used for historical decisions.

## Structural-deterioration monitor

A robust one-sided CUSUM evaluates deterioration in benchmark-relative log-loss contribution and incremental net economic edge. Scale floors and bounded standardized inputs are used to prevent numerical instability.

## Operational status rules

- `NOT_ESTABLISHED` - historical establishment requirement not met;
- `ACTIVE` - established candidate with positive current evidence and no active deterioration condition;
- `REDUCED` - established candidate with uncertain, regime-dependent, or deteriorating current evidence;
- `SUSPENDED` - established candidate with active deterioration and non-positive recent predictive and economic evidence.

## Model boundaries

Version 1 is not a parameter-optimization engine, production execution simulator, or universal claim regarding SOL or technical indicators. Advanced inference, richer market data, cross-venue replication, and probabilistic failure hazards are governed through the methodological development programme.
