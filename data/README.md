# Data and Provenance

This directory contains the frozen public data snapshot and ShockBridge-authored transformations required to reproduce V1 exactly.

## Raw snapshot

- `raw/sol_usdt_4h.csv` — Binance spot SOL/USDT four-hour OHLCV.
- `raw/btc_usdt_4h.csv` — Binance spot BTC/USDT four-hour OHLCV.
- `raw/download_manifest.json` — source, symbols, requested dates, retrieval time, and row counts.
- `raw/data_validation.json` — timestamp continuity, duplicates, missing values, and sample overlap.

The frozen V1 snapshot runs from **2021-01-01 00:00 UTC** through the **2026-07-22 08:00 UTC** candle. The downloader remains available to create later vintages, but a refreshed dataset is a new experiment and may not reproduce the published V1 result.

## Processed replication data

- `processed/aligned_market_data.csv` — timestamp-aligned SOL and BTC OHLCV.
- `processed/model_features.csv` — complete feature and target matrix used by V1.
- `processed/fold_boundaries.csv` — chronological training and test boundaries.
- `processed/fold_assignments.csv` — exact observation-level fold membership.
- `processed/feature_manifest.json` — feature groups, target definitions, and configuration.

## Integrity

`../REPLICATION_CHECKSUMS.sha256` records SHA-256 hashes for the raw data, processed data, configuration, runtime record, and generated evidence.

## Rights and attribution

The MIT license applies to ShockBridge-authored code and documentation. It does not grant ownership of third-party market data. The snapshot is provided for transparent research replication and remains subject to the source venue's applicable terms and availability.
