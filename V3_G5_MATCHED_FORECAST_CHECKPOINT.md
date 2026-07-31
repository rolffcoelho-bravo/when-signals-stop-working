# Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection Checkpoint

## Status

```text
APPROVED
PARENT_V3_4_IMPLEMENTATION_VALIDATED_AND_LOCKED
CONTRACT_FROZEN
CONTRACT_AUTHORITATIVELY_VALIDATED
FOUNDATION_AUTHORITATIVELY_VALIDATED
MATERIALIZATION_AUTHORITATIVELY_VALIDATED
MODEL_IMPLEMENTATION_AUTHORITATIVELY_VALIDATED_AND_PROTECTED
DEVELOPMENT_ENGINE_AUTHORITATIVELY_VALIDATED_AND_PROTECTED
REAL_EXECUTION_AUTHORIZATION_CANDIDATE_IMPLEMENTED
REAL_EXECUTION_AUTHORIZATION_CANDIDATE_VALIDATION_PENDING
TARGET_ACCESS_NOT_STARTED
REAL_DEVELOPMENT_MODEL_FITTING_NOT_STARTED
PIPELINE_ADMISSION_NOT_STARTED
ESTABLISHMENT_AUTHORIZATION_NOT_CREATED
ESTABLISHMENT_SEGMENT_NOT_ACCESSED
FINAL_FRAMEWORK_RESERVE_NOT_ACCESSED
```

## Research question

Gate V3-5 tests whether any locked RSI or Bollinger interpretation earns new benchmark-relative predictive and economic establishment under Version 3. No earlier result is inherited as positive evidence.

Frozen earlier determinations remain:

```text
Version 1 RSI: NOT_ESTABLISHED
Version 1 Bollinger: NOT_ESTABLISHED
Version 2 RSI: NO_PIPELINE_ADMITTED
Version 2 Bollinger: NO_INCREMENTAL_EVIDENCE
```

## Validated chain

```text
V3-4 signal engine:
ff2e7ecba3fa69f22e0b109437d23b52d30fba2b

V3-5 contract:
013d91abc0c3c74a28784aed486edb4c95efc6d7

V3-5 forecast foundation:
dd8a8ec5f34f0b8587c8f0cdaaf4f3c0891e944a

V3-5 real foundation materialization:
91606edf50a2c0aee9bcb94a93350936ee53f81a

V3-5 preprocessing and estimator implementation:
37c7360afde61a01ee9f9c5237dcf6bdf42985dd

V3-5 chronological development engine:
9827d5320d45c4b54a7fe85a24403651f3e239c9
```

Validation tests:

```text
contract: 7 passed
foundation: 16 passed
materialization: 5 passed
model implementation: 26 passed, 0 FutureWarnings
development engine: 33 passed, 0 FutureWarnings
```

## Frozen partition

```text
Development:
2021-01-01T00:00:00Z to 2025-06-30T20:00:00Z

Signal establishment:
2025-07-01T00:00:00Z to 2025-12-31T20:00:00Z

V3-9 final-framework reserve:
2026-01-01T00:00:00Z to 2026-07-22T08:00:00Z
```

The establishment segment requires a later committed establishment authorization. The V3-9 reserve remains inaccessible.

## Matched comparison rule

```text
candidate = benchmark information + registered signal information
```

Benchmark and candidate share rows, model class, preprocessing, hyperparameter selection, calibration, target, horizon, decision policy, and costs.

## Authoritative data and model identities

```text
development rows: 9,852
target primitive rows: 59,070
nested fold records: 120
bounded candidates: 57
candidate-horizon records: 342
matched candidate-horizon records: 276
explicitly ineligible candidate-horizon records: 66
pipeline specifications: 162
executable specifications: 153
gated specifications: 9
```

Large-move labels remain training-fold-only.

## Protected development engine

```text
strict training/calibration/test chronology
fold-scoped q90 large-move thresholds
training-only calibration and abstention
one-standard-error complexity preference
matched outer-fold evaluation
predictive and economic metrics
positive-fold and concentration controls
Holm and Benjamini-Hochberg multiplicity
```

The protected bounded workload is:

```text
candidate-pipeline-target combinations: 42,228
outer-fold jobs: 211,140
```

No real job has been executed.

## Authorization candidate

The planning-only authorization candidate defines:

```text
complete job plan: 211,140 rows
jobs per full batch: 250
stage-aligned batch count: 847 to 848
final batch jobs: 130
execution stages: 6
mixed-stage batches: prohibited
parallel batches: 1
worker processes: 1
checkpoint after each batch: required
input/output hash binding: required
```

The exact batch count depends only on whether the combined secondary direction candidate is eligible. The workload remains fixed at 211,140 jobs.

The authorization candidate validates planning and resumability only. All batches remain `PLANNED_NOT_STARTED`; real execution remains unauthorized until a later final authorization object promotes a specific stage or batch range.

## Current truth state

```text
contract validated: true
foundation validated: true
materialization validated: true
model implementation validated and protected: true
development engine validated and protected: true
authorization candidate implementation complete: true
authorization candidate authoritative validation: pending
development target primitives generated: true
model-selection target consumption started: false
real development models fitted: false
real development predictions generated: false
development pipelines ranked: false
development pipelines admitted: false
final real-execution authorization created: false
establishment authorization created: false
establishment segment accessed: false
final-framework reserve accessed: false
signal established: false
failure modelling admissible: false
```

The frozen token `TARGET_ACCESS_NOT_STARTED` means no real model-selection or model-fitting process has consumed the target primitives.

## Required next execution

```powershell
.\RUN_V3_G5_REAL_EXECUTION_AUTHORIZATION.ps1
```

## Claims boundary

No predictive, economic, conditional-validity, deterioration, failure-probability, or operational-use claim is authorized.
