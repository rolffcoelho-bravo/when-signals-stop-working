# Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection Checkpoint

## Status

```text
APPROVED
PARENT_V3_4_IMPLEMENTATION_VALIDATED_AND_LOCKED
IMPLEMENTATION_STARTED
CONTRACT_FROZEN
TARGET_ACCESS_NOT_STARTED
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

## Contract files

```text
configs/v3_g5_forecast_contract.json
docs/V3_G5_MATCHED_FORECAST_SCOPE.md
V3_G5_MATCHED_FORECAST_CHECKPOINT.md
scripts/verify_v3_g5_contract.py
tests/test_v3_g5_contract.py
RUN_V3_G5_CONTRACT.ps1
RUN_V3_G5_CONTRACT.sh
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

The final-framework reserve is inaccessible to Gate V3-5.

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

## Candidate boundary

Gate V3-5 receives the 48 locked V3-4 specifications. It may test eligible single-feature augmentations and eight predeclared family blocks. It may not create an unrestricted Cartesian indicator search.

Ineligible adaptive or context-dependent candidates remain reported rather than deleted.

## Current truth state

```text
targets generated: false
folds generated: false
benchmark features assembled: false
candidate registry assembled: false
development models fitted: false
development pipelines admitted: false
establishment authorization created: false
establishment segment accessed: false
signal established: false
failure modelling admissible: false
```

## Required next implementation

1. implement target generation with horizon-tail purging;
2. implement frozen data partition enforcement;
3. implement five outer and three inner chronological folds;
4. assemble benchmark and candidate row contracts;
5. implement matched regularized, spline, shallow-boosting, and dynamic challengers;
6. implement calibration, abstention, economic, and multiplicity controls;
7. freeze admitted pipelines before establishment access;
8. execute establishment only after an authorization object is committed;
9. stop the failure programme when no signal establishes.

## Claims boundary

No predictive, economic, conditional-validity, deterioration, failure, or operational-use claim is authorized at this checkpoint.
