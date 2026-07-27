# Gate V3-5 — Real Development Foundation Materialization Checkpoint

## Status

```text
APPROVED
PARENT_V3_4_IMPLEMENTATION_VALIDATED_AND_LOCKED
V3_5_CONTRACT_AUTHORITATIVELY_VALIDATED
V3_5_FOUNDATION_AUTHORITATIVELY_VALIDATED
VALIDATED_CONTRACT_AND_FOUNDATION_OBJECTS_PROTECTED
REAL_DEVELOPMENT_MATERIALIZATION_IMPLEMENTED
AUTHORITATIVE_EXECUTION_PENDING
MODEL_FITTING_NOT_STARTED
ESTABLISHMENT_SEGMENT_NOT_ACCESSED
FINAL_FRAMEWORK_RESERVE_NOT_ACCESSED
```

## Scientific purpose

This slice converts the validated Gate V3-5 foundation into deterministic real-data evidence without fitting, ranking, calibrating, admitting, or evaluating a forecast model.

It answers only whether the frozen development partition, target primitives, nested folds, continuity benchmark, locked signal registry, bounded candidate inventory, and matched-row coverage can be materialized consistently from the real repository data.

It does not answer whether RSI or Bollinger adds predictive or economic value.

## Parent evidence

```text
Gate V3-4 lock: IMPLEMENTATION_VALIDATED_AND_LOCKED
Validated V3-4 implementation: ff2e7ecba3fa69f22e0b109437d23b52d30fba2b
V3-5 contract validation commit: 013d91abc0c3c74a28784aed486edb4c95efc6d7
V3-5 foundation validation commit: dd8a8ec5f34f0b8587c8f0cdaaf4f3c0891e944a
V3-5 foundation tests: 16 passed
```

Machine-readable validation records:

```text
V3_G5_CONTRACT_VALIDATION.json
V3_G5_FOUNDATION_VALIDATION.json
```

The materialization runner verifies the exact frozen contract blob and every validated foundation implementation/test object against those commits. Local and staged mutations to protected paths fail before execution.

## Real source boundary

```text
SOL source: data/raw/sol_usdt_4h.csv
BTC source: data/raw/btc_usdt_4h.csv
Signal features: outputs/v3/signal_engine/signal_features.csv
Signal registry: evidence/v3/g4_signal_lock/signal_registry_manifest.json
Primary asset: SOL/USDT
Market context: BTC/USDT
Venue: binance_spot
Frequency: 4 hours
```

The SOL and BTC timestamps must align exactly. OHLCV imputation is prohibited.

The generated source manifest binds SHA-256 hashes for:

```text
configs/v3_g5_forecast_contract.json
data/raw/sol_usdt_4h.csv
data/raw/btc_usdt_4h.csv
outputs/v3/signal_engine/signal_features.csv
evidence/v3/g4_signal_lock/signal_registry_manifest.json
```

The signal-table and registry hashes must equal their V3-4 lock records.

## Frozen development boundary

```text
Development start: 2021-01-01T00:00:00Z
Development end: 2025-06-30T20:00:00Z
Expected development rows: 9852
```

Rows from the signal-establishment segment or the V3-9 final-framework reserve are inadmissible.

## Materialized target primitives

The runner produces direction and future-log-return target primitives for:

```text
1 candle  = 4 hours
2 candles = 8 hours
3 candles = 12 hours
6 candles = 24 hours
12 candles = 48 hours
18 candles = 72 hours
```

Expected rows by horizon:

```text
1: 9851
2: 9850
3: 9849
6: 9846
12: 9840
18: 9834
Total: 59070
```

Every horizon tail whose target timestamp would leave development is removed.

Large-move labels are not materialized here. Their q90 thresholds must be fitted separately inside each training fold.

## Nested fold identity

```text
6 horizons
5 outer expanding folds per horizon
3 inner folds per outer fold
30 outer records
90 inner records
120 total fold records
purge gap = forecast horizon
shuffle = false
```

Every training target timestamp must precede the corresponding test origin.

## Continuity benchmark

The real benchmark contains 9852 development timestamps and the frozen Version 2 continuity features:

```text
sol_ret_1
sol_ret_3
btc_ret_1
btc_ret_3
trend_12
vol_20
range_12
volume_z
```

Warm-up missingness remains explicit. No full-sample scaling, clipping, calibration, or imputation is performed.

## Candidate and matched-row identity

The locked signal registry produces:

```text
48 single-signal candidates
8 predeclared within-family blocks
1 combined secondary block
57 bounded candidates
```

Across six horizons the expected coverage identity is:

```text
57 × 6 = 342 candidate-horizon records
```

For each candidate-horizon record, the materializer reports one of:

```text
MATCHED_ROWS_AVAILABLE
INELIGIBLE_NO_COMPLETE_MATCHED_ROWS
INELIGIBLE_SIGNAL_COLUMNS_MISSING
```

Unavailable adaptive or context-dependent candidates remain visible. They are not deleted, replaced, rescued, or ranked.

## Runtime outputs

```text
outputs/v3/forecast_foundation/development_targets.csv
outputs/v3/forecast_foundation/nested_fold_plan.csv
outputs/v3/forecast_foundation/continuity_benchmark.csv
outputs/v3/forecast_foundation/candidate_inventory.csv
outputs/v3/forecast_foundation/matched_row_coverage.csv
outputs/v3/forecast_foundation/target_manifest.json
outputs/v3/forecast_foundation/fold_manifest.json
outputs/v3/forecast_foundation/benchmark_manifest.json
outputs/v3/forecast_foundation/candidate_inventory_manifest.json
outputs/v3/forecast_foundation/matched_coverage_manifest.json
outputs/v3/forecast_foundation/source_manifest.json
outputs/v3/forecast_foundation/materialization_manifest.json
```

The directory is ignored because it is regenerable. Every compact generated output is bound by SHA-256 in `materialization_manifest.json`.

## Implementation files

```text
src/shockbridge_signal_validity/v3/forecast_materialization.py
scripts/run_v3_g5_materialization.py
scripts/verify_v3_g5_materialization.py
scripts/verify_v3_g5_validated_boundaries.py
tests/test_v3_g5_materialization.py
RUN_V3_G5_MATERIALIZATION.ps1
RUN_V3_G5_MATERIALIZATION.sh
```

## Acceptance criteria

1. the five materialization tests pass;
2. the final V3-4 lock and validated V3-5 contract remain valid;
3. all protected V3-5 foundation objects equal the validated commit;
4. protected local and staged mutations are absent;
5. the sixteen-test V3-5 foundation remains valid;
6. SOL and BTC histories align exactly;
7. all five input objects are hash-bound;
8. development rows equal 9852;
9. target rows equal 59070;
10. nested fold rows equal 120;
11. candidates equal 57;
12. candidate-horizon coverage rows equal 342;
13. target timestamps never cross 2025-06-30T20:00:00Z;
14. large-move labels remain deferred to fold-scoped training;
15. model fitting and pipeline selection remain false;
16. establishment and final-reserve access remain false;
17. no tracked working-tree or staged-index mutation occurs.

## Required authoritative execution

```powershell
.\RUN_V3_G5_MATERIALIZATION.ps1
```

## Claims boundary

No predictive, economic, conditional-validity, deterioration, failure-probability, or operational-use claim is authorized at this checkpoint.

## Next implementation after acceptance

After authoritative materialization validation, the next slice may implement fold-scoped preprocessing and matched estimator families. Model fitting must remain blocked until that implementation passes its own tests and verifier.
