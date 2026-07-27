# Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection Checkpoint

## Status

```text
APPROVED
PARENT_V3_4_IMPLEMENTATION_VALIDATED_AND_LOCKED
IMPLEMENTATION_STARTED
CONTRACT_FROZEN
CONTRACT_AUTHORITATIVELY_VALIDATED
FOUNDATION_IMPLEMENTED_VALIDATION_PENDING
DEVELOPMENT_TARGET_ENGINE_IMPLEMENTED
PARTITION_GUARD_IMPLEMENTED
NESTED_FOLD_ENGINE_IMPLEMENTED
CONTINUITY_BENCHMARK_IMPLEMENTED
BOUNDED_CANDIDATE_INVENTORY_IMPLEMENTED
MATCHED_ROW_CONTRACT_IMPLEMENTED
MODEL_FITTING_NOT_STARTED
ESTABLISHMENT_SEGMENT_NOT_ACCESSED
FINAL_FRAMEWORK_RESERVE_NOT_ACCESSED
```

## Parent evidence

Gate V3-4 is finalized as:

```text
lock: V3_G4_SIGNAL_ENGINE_LOCK.json
status: IMPLEMENTATION_VALIDATED_AND_LOCKED
validated implementation commit: ff2e7ecba3fa69f22e0b109437d23b52d30fba2b
evidence materialization commit: 705511de9e8ee22a9f8aff34506aebb6c26223e7
lock promotion commit: 4150d73ff1e12d5b022e591f0a6ee700c29b5ce1
source rows: 12171
registered signal specifications: 48
feature rows: 584208
```

No V3-4 protected object may be modified by Gate V3-5.

## Contract validation evidence

The frozen Gate V3-5 contract was authoritatively validated on the Windows research environment at commit:

```text
013d91abc0c3c74a28784aed486edb4c95efc6d7
```

Evidence:

```text
V3-4 final lock verifier: passed
repository realignment tests: 7 passed
V3-5 contract tests: 7 passed
standalone V3-5 contract verifier: passed
patch integrity: passed
tracked worktree: clean
branch synchronized with origin: true
target access: false
model fitting: false
signal-establishment access: false
V3-9 reserve access: false
```

The machine-readable record is `V3_G5_CONTRACT_VALIDATION.json`.

## Research-question link

Gate V3-5 tests whether any registered RSI or Bollinger interpretation earns new Version 3 benchmark-relative predictive and economic establishment.

It does not inherit a positive result from Version 1, Version 2, the spectral engine, the panic-consistent regime engine, or chronology work.

Frozen earlier determinations remain:

```text
Version 1 RSI: NOT_ESTABLISHED
Version 1 Bollinger: NOT_ESTABLISHED
Version 2 RSI: NO_PIPELINE_ADMITTED
Version 2 Bollinger: NO_INCREMENTAL_EVIDENCE
```

## Frozen partition

```text
Development:
2021-01-01T00:00:00Z to 2025-06-30T20:00:00Z

Signal-establishment segment:
2025-07-01T00:00:00Z to 2025-12-31T20:00:00Z

V3-9 final-framework reserve:
2026-01-01T00:00:00Z to 2026-07-22T08:00:00Z
```

The establishment segment requires a later committed authorization object. The final-framework reserve is inaccessible to Gate V3-5 and fails closed as `PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED`.

## Frozen analytical boundary

```text
confirmatory target: direction
secondary targets: expected return, large-move probability
horizons: 4h, 8h, 12h, 24h, 48h, 72h
outer development folds: 5
inner selection folds: 3
primary one-way cost: 10 bps
cost sensitivity: 5 bps, 20 bps
confirmatory multiplicity: Holm 5%
secondary multiplicity: Benjamini-Hochberg q=0.10
```

## Matched comparison rule

```text
candidate = benchmark information + registered signal information
```

Benchmark and candidate must share model class, rows, preprocessing, hyperparameter selection, calibration, target, horizon, decision policy, and costs.

Candidate-specific missingness is handled through one complete matched-row intersection. Cross-candidate raw metric ranking on unequal rows is prohibited.

## Implemented foundation

```text
src/shockbridge_signal_validity/v3/forecast_contract.py
src/shockbridge_signal_validity/v3/forecast_targets.py
src/shockbridge_signal_validity/v3/forecast_splits.py
src/shockbridge_signal_validity/v3/forecast_benchmark.py
src/shockbridge_signal_validity/v3/forecast_inventory.py
src/shockbridge_signal_validity/v3/forecast_matching.py
scripts/verify_v3_g5_foundation.py
tests/test_v3_g5_targets_partitions.py
tests/test_v3_g5_splits_matching.py
tests/test_v3_g5_inventory_benchmark.py
RUN_V3_G5_FOUNDATION.ps1
RUN_V3_G5_FOUNDATION.sh
```

### Target engine

- builds direction and expected-return targets for all six registered horizons;
- removes horizon tails whose target timestamp would leave development;
- separates training-only large-move threshold fitting from label application;
- preserves future-append invariance before the append boundary.

### Chronological folds

- creates five outer expanding folds and three inner folds per outer fold;
- applies purge gaps equal to each forecast horizon;
- verifies training target timestamps precede test origins;
- prohibits shuffling.

### Continuity benchmark

- preserves the Version 2 non-indicator base features;
- requires exact SOL/BTC timestamp alignment;
- prohibits OHLCV imputation;
- permits declared V3 context extensions only as shared benchmark information.

### Candidate inventory

The locked 48 signal specifications produce:

```text
48 single-signal candidates
8 predeclared within-family blocks
1 combined RSI/Bollinger secondary block
57 bounded feature candidates
```

No Cartesian signal search, candidate deletion, or automatic selection is performed.

### Matched row contract

For each candidate and target horizon:

- benchmark and candidate use the same complete rows;
- the candidate contains the complete benchmark plus registered signal columns;
- row identity is hashed;
- establishment and reserve timestamps fail closed.

## Current truth state

```text
contract validated: true
foundation implementation complete: true
foundation authoritative execution: pending
real development targets generated: false
real fold manifests generated: false
real benchmark features assembled: false
real candidate registry materialized: false
development models fitted: false
development pipelines admitted: false
establishment authorization created: false
establishment segment accessed: false
signal established: false
failure modelling admissible: false
```

## Required authoritative validation

```powershell
.\RUN_V3_G5_FOUNDATION.ps1
```

Expected evidence includes sixteen passing foundation tests, 120 synthetic nested-fold records, preservation of all 48 locked signals, a bounded 57-candidate inventory, identical matched rows, no model fitting, and no establishment or final-reserve access.

## Next implementation after validation

1. materialize real development-only target and fold manifests;
2. materialize the real continuity benchmark and bounded candidate inventory;
3. implement fold-scoped preprocessing and matched model families;
4. implement calibration, abstention, economic, and multiplicity controls;
5. execute development selection only after the model implementation passes its own acceptance boundary;
6. freeze admitted pipelines before any establishment-segment authorization.

## Claims boundary

No predictive, economic, conditional-validity, deterioration, failure, or operational-use claim is authorized at this checkpoint.
