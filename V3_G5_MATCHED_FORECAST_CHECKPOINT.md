# Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection Checkpoint

## Status

```text
APPROVED
PARENT_V3_4_IMPLEMENTATION_VALIDATED_AND_LOCKED
IMPLEMENTATION_STARTED
CONTRACT_FROZEN
CONTRACT_AUTHORITATIVELY_VALIDATED
FOUNDATION_AUTHORITATIVELY_VALIDATED
REAL_DEVELOPMENT_MATERIALIZATION_IMPLEMENTED
MATERIALIZATION_AUTHORITATIVE_EXECUTION_PENDING
TARGET_ACCESS_NOT_STARTED
DEVELOPMENT_MODEL_FITTING_NOT_STARTED
PIPELINE_ADMISSION_NOT_STARTED
ESTABLISHMENT_AUTHORIZATION_NOT_CREATED
ESTABLISHMENT_SEGMENT_NOT_ACCESSED
FINAL_FRAMEWORK_RESERVE_NOT_ACCESSED
```

## Research-question link

Gate V3-5 determines whether any registered RSI or Bollinger interpretation earns new Version 3 benchmark-relative predictive and economic establishment.

It does not inherit a positive result from Version 1, Version 2, the spectral engine, the panic-consistent regime engine, or chronology work.

Frozen earlier determinations remain:

```text
Version 1 RSI: NOT_ESTABLISHED
Version 1 Bollinger: NOT_ESTABLISHED
Version 2 RSI: NO_PIPELINE_ADMITTED
Version 2 Bollinger: NO_INCREMENTAL_EVIDENCE
```

## Parent and validation evidence

```text
V3-4 lock: IMPLEMENTATION_VALIDATED_AND_LOCKED
V3-4 validated implementation: ff2e7ecba3fa69f22e0b109437d23b52d30fba2b
V3-4 evidence materialization: 705511de9e8ee22a9f8aff34506aebb6c26223e7
V3-5 contract validation commit: 013d91abc0c3c74a28784aed486edb4c95efc6d7
V3-5 foundation validation commit: dd8a8ec5f34f0b8587c8f0cdaaf4f3c0891e944a
V3-5 contract tests: 7 passed
V3-5 foundation tests: 16 passed
```

Machine-readable records:

```text
V3_G5_CONTRACT_VALIDATION.json
V3_G5_FOUNDATION_VALIDATION.json
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

## Validated implementation foundation

The foundation includes:

```text
forecast_contract.py
forecast_targets.py
forecast_splits.py
forecast_benchmark.py
forecast_inventory.py
forecast_matching.py
```

Validated identities:

```text
forecast horizons: 6
nested fold records: 120
single-signal candidates: 48
bounded candidates: 57
matched benchmark/candidate rows identical: true
model fitting performed: false
```

## Real development materialization implementation

The current implementation adds:

```text
forecast_materialization.py
run_v3_g5_materialization.py
verify_v3_g5_materialization.py
test_v3_g5_materialization.py
RUN_V3_G5_MATERIALIZATION.ps1
RUN_V3_G5_MATERIALIZATION.sh
V3_G5_MATERIALIZATION_CHECKPOINT.md
```

Expected real-data identities:

```text
development rows: 9852
target primitive rows: 59070
nested fold rows: 120
bounded candidates: 57
candidate-horizon coverage rows: 342
```

Large-move labels are not globally materialized. Their q90 thresholds remain training-fold-only.

Unavailable adaptive or context-dependent candidates remain explicit as ineligible coverage records rather than being deleted.

## Current truth state

```text
contract validated: true
foundation validated: true
materialization implementation complete: true
materialization authoritative execution: pending
real development target primitives generated: false
real fold manifest generated: false
real continuity benchmark generated: false
real candidate inventory generated: false
real matched-row coverage generated: false
development models fitted: false
development pipelines admitted: false
establishment authorization created: false
establishment segment accessed: false
signal established: false
failure modelling admissible: false
```

## Required authoritative execution

```powershell
.\RUN_V3_G5_MATERIALIZATION.ps1
```

Expected runner stages:

1. verify the final V3-4 lock;
2. verify the frozen V3-5 contract;
3. revalidate the sixteen-test foundation;
4. run five materialization tests;
5. regenerate V3-4 runtime evidence only when absent;
6. materialize real development-only evidence;
7. verify all row identities and hashes;
8. verify no tracked or staged mutation.

## Next implementation after validation

After the materialization passes, the next slice may implement fold-scoped preprocessing and matched estimator families. Actual model fitting remains a separate governed execution boundary.

## Claims boundary

No predictive, economic, conditional-validity, deterioration, failure-probability, or operational-use claim is authorized at this checkpoint.
