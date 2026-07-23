# Version 2 Data and Replication Plan

## 1. Primary dataset

The primary case remains:

- SOL/USDT spot;
- Binance;
- four-hour UTC observations;
- BTC/USDT as the common market-context series;
- frozen snapshot ending `2026-07-22T08:00:00Z`.

The Version 1 snapshot is preserved. Version 2 creates new processed datasets and output namespaces rather than modifying Version 1 evidence.

## 2. Versioned output namespaces

Version 2 implementation must use:

```text
data/processed/v2/
outputs/v2/development/
outputs/v2/holdout/
outputs/v2/external_replication/
```

Version 1 files under `data/processed/` and `outputs/` remain unchanged.

## 3. Development and holdout partitions

The partition boundary is fixed at `2025-07-01T00:00:00Z`.

A machine-readable partition manifest must include:

- first and last timestamp;
- row count;
- target-specific usable row count;
- SHA-256 data hashes;
- horizon-specific purge boundaries;
- the implementation commit;
- the protocol-lock identifier.

## 4. External venue order

For same-asset external replication, the eligibility order is:

1. Coinbase SOL/USD;
2. Kraken SOL/USD or SOL/EUR;
3. another regulated or widely used spot venue documented before retrieval.

The first eligible venue by the declared data-quality rules is used as the primary external venue. Venue choice cannot depend on model performance.

## 5. External venue eligibility

A venue is eligible when:

- at least two years of comparable spot history are available;
- UTC candle construction is reproducible;
- missing or nonstandard intervals are quantified;
- symbol and quote-currency differences are documented;
- no authenticated account data are required;
- redistribution or retrieval instructions are documented.

If no venue is eligible, the limitation is reported and cross-asset replication proceeds without substituting an undisclosed venue.

## 6. Cross-asset cases

Secondary assets are:

- BTC/USDT;
- ETH/USDT.

SOL remains the primary research asset. Cross-asset results test transportability and do not replace the primary determination.

## 7. Data lineage

Each dataset must record:

- venue and symbol;
- retrieval route and timestamp;
- raw frequency and any resampling rule;
- timezone and candle-boundary convention;
- duplicates, missing values, and gap statistics;
- source and processed hashes;
- licensing or terms notice;
- code and configuration version.

## 8. Reproduction levels

### Level A - Exact snapshot replication

Uses tracked frozen data and must reproduce published Version 2 tables within declared numerical tolerances.

### Level B - Fresh-download replication

Retrieves the same instruments through public endpoints. Differences caused by venue revisions or late data are documented through a data-vintage comparison.

### Level C - External replication

Applies the frozen pipeline to eligible external venues or assets without changing the confirmatory primary-case model.

## 9. Public release boundaries

The Version 2 public package excludes:

- credentials and authenticated-account data;
- absolute local paths;
- virtual environments and caches;
- private correspondence;
- proprietary datasets without redistribution permission.

Where raw external data cannot be redistributed, the repository must provide acquisition code, source records, hashes where lawful, and a complete processed-data construction contract.
