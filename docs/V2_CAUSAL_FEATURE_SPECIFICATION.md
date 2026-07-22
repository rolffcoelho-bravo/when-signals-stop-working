# Version 2 Causal Feature Specification

## Institutional objective

This specification converts the frozen Version 2 information contract into deterministic, prefix-invariant feature transformations.

## Common benchmark information

The D1 benchmark layer retains the Version 1 information set: lagged SOL and BTC returns, a trailing SOL trend measure, trailing realised volatility, a trailing high-low range, and a trailing log-volume standard score. Candidate comparisons in later checkpoints must use the identical benchmark feature matrix.

## Signal information

RSI and Bollinger features are generated on demand from the registered parameter space. D1 records levels, slopes or changes, distances, events, extremes, and a fixed six-candle causal event-persistence decay. The persistence rule is an implementation constant rather than a selected hyperparameter.

## Prefix invariance

For every unique registered signal specification, D1 compares features computed on a historical prefix with the same rows computed after later observations are appended. Any difference above `1e-12`, including a missing-value mismatch, fails the checkpoint.

## Prohibited transformations

D1 prohibits centred windows, backward filling, full-sample scaling, target-derived features, future state smoothing, and any transformation that changes an earlier feature after later observations are appended.
