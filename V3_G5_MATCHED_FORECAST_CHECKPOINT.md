# Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection Checkpoint

## Status

```text
APPROVED
PARENT_V3_4_IMPLEMENTATION_VALIDATED_AND_LOCKED
CONTRACT_AUTHORITATIVELY_VALIDATED
FOUNDATION_AUTHORITATIVELY_VALIDATED
MATERIALIZATION_AUTHORITATIVELY_VALIDATED
MODEL_IMPLEMENTATION_AUTHORITATIVELY_VALIDATED_AND_PROTECTED
CHRONOLOGICAL_DEVELOPMENT_ENGINE_CONTRACT_FROZEN
CHRONOLOGICAL_DEVELOPMENT_ENGINE_IMPLEMENTED
CHRONOLOGICAL_DEVELOPMENT_ENGINE_AUTHORITATIVE_VALIDATION_PENDING
TARGET_ACCESS_NOT_STARTED
REAL_DEVELOPMENT_MODEL_FITTING_NOT_STARTED
PIPELINE_ADMISSION_NOT_STARTED
ESTABLISHMENT_AUTHORIZATION_NOT_CREATED
ESTABLISHMENT_SEGMENT_NOT_ACCESSED
FINAL_FRAMEWORK_RESERVE_NOT_ACCESSED
```

## Research-question link

Gate V3-5 determines whether any registered RSI or Bollinger interpretation earns new Version 3 benchmark-relative predictive and economic establishment. No earlier gate or version supplies a positive result automatically.

Frozen earlier determinations remain:

```text
Version 1 RSI: NOT_ESTABLISHED
Version 1 Bollinger: NOT_ESTABLISHED
Version 2 RSI: NO_PIPELINE_ADMITTED
Version 2 Bollinger: NO_INCREMENTAL_EVIDENCE
```

## Validated boundaries

```text
V3-4 signal engine lock:
ff2e7ecba3fa69f22e0b109437d23b52d30fba2b

V3-5 contract validation:
013d91abc0c3c74a28784aed486edb4c95efc6d7

V3-5 foundation validation:
dd8a8ec5f34f0b8587c8f0cdaaf4f3c0891e944a

V3-5 materialization validation:
91606edf50a2c0aee9bcb94a93350936ee53f81a

V3-5 warning-free model implementation validation:
37c7360afde61a01ee9f9c5237dcf6bdf42985dd
```

Validated test evidence:

```text
contract tests: 7 passed
foundation tests: 16 passed
materialization tests: 5 passed
model implementation tests: 26 passed
model implementation FutureWarnings: 0
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

The establishment segment requires a later committed authorization object. The final-framework reserve is inaccessible to Gate V3-5.

## Matched comparison rule

```text
candidate = benchmark information + registered signal information
```

Benchmark and candidate must share rows, model class, preprocessing, hyperparameter selection, calibration method, target, horizon, decision policy, and cost assumptions.

## Authoritative real foundation

```text
development rows: 9852
target primitive rows: 59070
nested fold records: 120
bounded candidates: 57
candidate-horizon records: 342
matched candidate-horizon records: 276
explicitly ineligible candidate-horizon records: 66
input hashes bound: true
```

Large-move labels remain fold-scoped and training-only.

## Protected model implementation

```text
pipeline specifications: 162
executable specifications: 153
gated specifications: 9
executable model families: 4
window schemes: 3
protected implementation objects: 10
```

The preprocessing and estimator implementation is pinned to commit `37c7360afde61a01ee9f9c5237dcf6bdf42985dd`.

## Chronological development engine

The new engine implements:

```text
fold-only q90 large-move thresholds
training-only none/sigmoid calibration
isotonic diagnostic calibration
inner-only abstention selection
one-standard-error complexity preference
matched outer-fold prediction and metrics
10 bps primary cost with 5/20 bps sensitivities
horizon-spaced economic decisions
positive-fold and gain-concentration controls
Holm confirmatory multiplicity
Benjamini-Hochberg secondary multiplicity
```

Bounded workload identity:

```text
matched candidate-horizon records: 276
executable pipeline specifications: 153
candidate-pipeline-target combinations: 42,228
outer folds: 5
bounded outer-fold jobs: 211,140
```

The workload is computed but not executed in this implementation-validation slice.

## Current truth state

```text
contract validated: true
foundation validated: true
materialization validated: true
model implementation validated and protected: true
chronological engine implementation complete: true
chronological engine authoritative validation: pending
development target primitives generated: true
model-selection target consumption started: false
real development models fitted: false
real development predictions generated: false
development pipelines ranked: false
development pipelines admitted: false
establishment authorization created: false
establishment segment accessed: false
final-framework reserve accessed: false
signal established: false
failure modelling admissible: false
```

The frozen exact token `TARGET_ACCESS_NOT_STARTED` means no target primitive has been consumed by real model-selection or model-fitting execution.

## Required authoritative execution

```powershell
.\RUN_V3_G5_DEVELOPMENT_ENGINE.ps1
```

This runner uses synthetic matched fits only and treats every `FutureWarning` as an error.

## Next boundary

After the 31-test engine validation passes, the next step is a separate real-development execution authorization with compute limits, resumability, checkpointing, deterministic output manifests, and a staged schedule for the bounded 211,140 jobs.

## Claims boundary

No predictive, economic, conditional-validity, deterioration, failure-probability, or operational-use claim is authorized at this checkpoint.
