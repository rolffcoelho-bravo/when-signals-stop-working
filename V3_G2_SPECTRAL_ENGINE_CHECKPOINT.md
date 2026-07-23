# Gate V3-2 — Multi-Asset Causal Feature and Spectral Engine Checkpoint

## Status

> `IMPLEMENTATION_COMPLETE_AND_LOCKED`

Gate V3-2 establishes the leakage-controlled market-structure layer required by the Version 3 Adaptive Signal Validity, Regime, and Failure Framework.

## Baseline preservation

- frozen baseline: `v2.0.0`;
- baseline commit: `5a07299367b80c3940e652e7bbdd208ce86ba5ef`;
- Version 3 branch: `research/v3-adaptive-signal-validity`;
- locked implementation boundary: `745dc751d88aa80d400e0fde7332e30a2de78728`;
- Version 2 files modified: none;
- Version 3 changes relative to the baseline: additive only.

## Delivered components

- explicit fixed-panel contract using stable `asset@venue` identifiers;
- deterministic close and log-return panel construction;
- causal return, drawdown, downside, volatility and volume features;
- governed liquidity, leverage, funding, liquidation, order-book, exchange-flow and cross-venue features where available;
- sample, EWMA and diagonal-shrinkage dependence estimators;
- dominant eigenvalue and dominant-eigenvalue share;
- normalized eigenvalue gap;
- participation ratio and effective dimension;
- normalized spectral entropy;
- first-eigenvector concentration and sign-invariant stability;
- average correlation and correlation dispersion;
- threshold-network density and degree concentration;
- explicit panel-coverage and dependence-window eligibility states;
- registered window and panel-composition sensitivity diagnostics without automatic selection;
- deterministic input, configuration, output and manifest identity;
- CSV and Parquet runner with machine-readable evidence outputs;
- PowerShell and shell validation workflows;
- repository-object lock and portable analytical/causal verifier.

## Acceptance evidence

The isolated Gate V3-2 suite completed with:

```text
11 passed
```

The suite and portable verifier establish that:

1. identity and common-mode correlation fixtures produce the analytically correct spectral limits;
2. future changes cannot alter earlier causal series or spectral outputs;
3. panel order and membership are explicit and deterministic;
4. absent registered members stop execution;
5. insufficient coverage produces a fail-closed ineligibility state rather than silent panel shrinkage;
6. sample, EWMA and shrinkage estimators produce bounded spectral outputs;
7. registered panel comparisons do not choose a favourable composition;
8. registered dependence windows remain visible and no preferred window is selected;
9. manifests and output hashes are deterministic;
10. the end-to-end runner emits the complete evidence package.

## Output contract

Gate V3-2 produces:

```text
causal_series_features.csv
spectral_market_structure.csv
spectral_manifest.json
spectral_diagnostics.json
canonical_validation_report.json
```

The primary downstream variables include:

```text
dominant_eigenvalue_share
eigenvalue_gap
participation_ratio
spectral_entropy
first_eigenvector_concentration
eigenvector_stability
average_correlation
correlation_dispersion
network_density
network_degree_concentration
window_coverage
eligibility_status
```

## Gate boundary

Gate V3-2 does not label investor panic and does not estimate `PANIC_CONSISTENT_REGIME`. It does not evaluate RSI or Bollinger predictive power, estimate signal-failure probability, or produce a trading decision.

The largest eigenvalue is treated as one dependence-concentration measure, not as sufficient evidence of panic.

## Validation boundary

The recorded `11 passed` result is the isolated Gate V3-2 suite. Full repository and multi-version CI validation remains a later audit obligation and is not represented here as completed.

## Next gate

> `V3-3 — PANIC-CONSISTENT PROBABILISTIC REGIME ENGINE`

Gate V3-3 will combine multiple independently motivated stress dimensions:

- spectral and correlation concentration;
- downside acceleration and drawdown velocity;
- volatility and downside-semivariance jumps;
- abnormal volume;
- liquidity and order-book deterioration;
- funding, leverage and liquidation stress;
- cross-venue dislocation;
- filtered transition and duration evidence.

The output will be a forward-filtered probability of `PANIC_CONSISTENT_REGIME`, with explicit insufficient-evidence states, minimum occupancy controls, transition uncertainty and no causal investor-panic claim unless the data support it.
