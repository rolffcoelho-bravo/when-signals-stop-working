# Version 3 Canonical Data and Adapter Layer

## Purpose

Gate V3-1 separates source-specific ingestion from research and model logic. A new dataset is admitted only after an adapter maps it into the Version 3 canonical schema and the validator produces a passing evidence report.

Model, feature, regime, forecast, validity, and decision modules may consume canonical fields only. They may not refer directly to exchange-specific column names, local file layouts, or provider-specific response structures.

## Canonical key and required fields

Each row is uniquely identified by:

```text
timestamp
asset
venue
```

The required market fields are:

```text
open
high
low
close
volume
```

Timestamps are converted to UTC. Prices must be strictly positive, volume must be non-negative, and OHLC values must satisfy the registered low/high boundaries. Duplicate canonical keys stop execution.

The machine-readable contract is stored in `configs/v3_canonical_data_contract.json`.

## Supported adapters

### File adapter

`FileMarketDataAdapter` supports CSV and Parquet sources. Parquet use requires a pandas-compatible Parquet engine in the execution environment.

Source columns are mapped through configuration:

```json
{
  "adapter_type": "file",
  "adapter": {
    "path": "data/input/market_data.csv",
    "format": "csv",
    "timezone": "UTC",
    "column_map": {
      "timestamp": "time",
      "open": "open_price",
      "high": "high_price",
      "low": "low_price",
      "close": "close_price",
      "volume": "base_volume"
    },
    "constants": {
      "asset": "SOL/USDT",
      "venue": "example_venue"
    }
  }
}
```

A complete template is provided in `configs/v3_adapter_example.json`.

### Exchange OHLCV adapter

`CcxtOHLCVAdapter` maps the repository's governed CCXT ingestion into the same canonical contract. Its configuration declares the exchange, symbol, timeframe, and date boundary. The downstream framework receives no CCXT-specific fields.

### Optional-field adapter

`OptionalFieldFileAdapter` admits registered supplemental variables such as funding rates, open interest, liquidations, spreads, order-book depth, exchange flows, and cross-venue dispersion.

Supplemental data must contain the same canonical key. Duplicate keys, unregistered fields, and hidden forward filling are prohibited. Missing supplemental observations remain missing unless a later protocol explicitly registers a field-specific treatment.

## Validation evidence

The validator reports:

- required-field and numeric failures;
- UTC timestamp conversion;
- duplicate canonical keys;
- non-positive prices and negative volume;
- OHLC boundary violations;
- interval gaps;
- panel-alignment gaps;
- field-level missingness;
- source normalization warnings.

Critical findings produce a failed report and stop the runner. Warnings remain visible and are preserved downstream.

## Deterministic identity

Every admitted source produces:

- source-file or source-content SHA-256;
- adapter-configuration SHA-256;
- canonical-data SHA-256;
- deterministic manifest SHA-256;
- schema version and loaded row count.

The canonical data hash is calculated only after UTC conversion, registered-column selection, numeric conversion, and deterministic sorting. Equivalent source layouts therefore produce the same canonical data identity.

## Execution

PowerShell:

```powershell
./RUN_V3_G1_DATA_ADAPTER.ps1 -Config configs/v3_adapter_example.json
```

Direct Python runner:

```text
python scripts/run_v3_data_adapter.py --config configs/v3_adapter_example.json --output-directory outputs/v3/data_adapter
```

The runner writes:

```text
canonical_market_data.csv
source_manifest.json
validation_report.json
```

## Gate boundary

Gate V3-1 validates data portability and source governance. It does not estimate regimes, technical signals, forecasts, failure probabilities, or trading decisions. Those functions remain unavailable until their corresponding Version 3 gates are implemented and approved.
