# Data Provenance and Replication Assets

This directory contains the frozen public market-data snapshot and ShockBridge-authored transformations required to reproduce the Version 1 determination.

## Raw snapshot

- `raw/sol_usdt_4h.csv` - Binance spot SOL/USDT four-hour OHLCV;
- `raw/btc_usdt_4h.csv` - Binance spot BTC/USDT four-hour OHLCV;
- `raw/download_manifest.json` - source, instruments, requested dates, retrieval time, and row counts;
- `raw/data_validation.json` - timestamp continuity, duplicate checks, missing-value checks, and sample overlap.

The frozen Version 1 snapshot extends from **1 January 2021, 00:00 UTC** through the **22 July 2026, 08:00 UTC** candle. A refreshed or extended snapshot constitutes a new data vintage and may not reproduce the published Version 1 determination.

## Processed replication assets

- `processed/aligned_market_data.csv` - timestamp-aligned SOL and BTC OHLCV;
- `processed/model_features.csv` - complete feature and target matrix;
- `processed/fold_boundaries.csv` - chronological training and test boundaries;
- `processed/fold_assignments.csv` - exact observation-level fold membership;
- `processed/feature_manifest.json` - feature groups, targets, and frozen configuration.

## Integrity control

`../REPLICATION_CHECKSUMS.sha256` records SHA-256 hashes for the raw data, processed data, configuration, runtime record, and generated evidence.

## Data rights and attribution

The MIT License applies to ShockBridge-authored code and documentation. It does not grant ownership of third-party market data. The snapshot is included exclusively for transparent research replication and remains subject to the source venue's applicable terms and availability.
