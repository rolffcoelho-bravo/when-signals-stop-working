# Gate V3-1 — Canonical Data and Adapter Checkpoint

## Status

> `IMPLEMENTATION_COMPLETE_AND_LOCKED`

Gate V3-1 establishes the source-independent data boundary required by the Version 3 Adaptive Signal Validity, Regime, and Failure Framework.

## Baseline preservation

- frozen baseline: `v2.0.0`;
- baseline commit: `5a07299367b80c3940e652e7bbdd208ce86ba5ef`;
- Version 3 branch: `research/v3-adaptive-signal-validity`;
- locked implementation boundary: `7a7a5c55184aadfb436774ff1e497ce873a96b6e`;
- Version 2 files modified: none;
- Version 3 changes relative to the baseline: additive only.

## Delivered components

- canonical market-data schema and validation report types;
- deterministic canonical-frame, source, configuration, and manifest identity;
- CSV and Parquet reference ingestion;
- governed CCXT OHLCV ingestion;
- registered optional-field ingestion and one-to-one joining;
- UTC conversion and deterministic row ordering;
- duplicate-key, OHLC-boundary, price, volume, missingness, interval-gap, and panel-alignment controls;
- fail-closed critical validation;
- reusable JSON configuration template;
- programmatic runner and PowerShell/shell execution runners;
- repository-object implementation lock and portable verifier;
- synthetic adapter-conformance tests.

## Acceptance evidence

The isolated Gate V3-1 conformance suite completed with:

```text
12 passed
```

The suite establishes that:

1. independently formatted source datasets map to an identical canonical frame and canonical-data hash;
2. UTC conversion and canonical ordering are deterministic;
3. invalid OHLC values, missing required fields, duplicate keys, and unregistered mappings fail closed;
4. CSV, Parquet, and governed exchange ingestion share the same downstream contract;
5. optional fields are joined without hidden forward filling;
6. the runner emits canonical data, a source manifest, and a validation report;
7. the lock verifier protects the registered implementation objects.

## Gate boundary

Gate V3-1 does not estimate spectral structure, panic-consistent regimes, RSI or Bollinger information, market forecasts, failure probabilities, or permitted-use decisions.

Those functions remain unavailable until the corresponding Version 3 gates are implemented and approved.

## Next gate

> `V3-2 — MULTI-ASSET CAUSAL FEATURE AND SPECTRAL ENGINE`

Gate V3-2 will construct leakage-controlled panel returns, volatility, downside, volume, liquidity, leverage, and liquidation features together with dominant-eigenvalue share, eigenvalue gap, participation ratio, spectral entropy, eigenvector concentration, and correlation-structure diagnostics.
