# Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection Checkpoint

## Status

```text
APPROVED
PARENT_V3_4_IMPLEMENTATION_VALIDATED_AND_LOCKED
IMPLEMENTATION_STARTED
CONTRACT_FROZEN
CONTRACT_AUTHORITATIVELY_VALIDATED
FOUNDATION_AUTHORITATIVELY_VALIDATED
MATERIALIZATION_AUTHORITATIVELY_VALIDATED
MODEL_IMPLEMENTATION_CONTRACT_FROZEN
FOLD_SCOPED_PREPROCESSING_IMPLEMENTED
MATCHED_ESTIMATOR_FAMILIES_IMPLEMENTED
MODEL_IMPLEMENTATION_FUNCTIONAL_VALIDATION_PASSED
MODEL_IMPLEMENTATION_COMPATIBILITY_REMEDIATION_IMPLEMENTED
MODEL_IMPLEMENTATION_WARNING_FREE_RERUN_PENDING
TARGET_ACCESS_NOT_STARTED
REAL_DEVELOPMENT_MODEL_FITTING_NOT_STARTED
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
V3-5 contract validation commit: 013d91abc0c3c74a28784aed486edb4c95efc6d7
V3-5 foundation validation commit: dd8a8ec5f34f0b8587c8f0cdaaf4f3c0891e944a
V3-5 materialization validation commit: 91606edf50a2c0aee9bcb94a93350936ee53f81a
V3-5 functional model validation commit: 5d31f1583bcf66f0231d8ef6b4f1e980d98def9b
V3-5 contract tests: 7 passed
V3-5 foundation tests: 16 passed
V3-5 materialization tests: 5 passed
V3-5 model implementation tests: 26 passed
```

Machine-readable records:

```text
V3_G5_CONTRACT_VALIDATION.json
V3_G5_FOUNDATION_VALIDATION.json
V3_G5_MATERIALIZATION_VALIDATION.json
V3_G5_MODEL_IMPLEMENTATION_VALIDATION.json
V3_G5_MODEL_IMPLEMENTATION_REMEDIATION.json
```

The model implementation run passed functionally but emitted six scikit-learn 1.8 `FutureWarning` messages for the deprecated explicit `penalty="l2"` argument. The mathematical estimator remained L2-regularized, but final implementation lock is blocked until a warning-free rerun passes.

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

## Validated foundation and real materialization

Validated foundation identities:

```text
forecast horizons: 6
nested fold records: 120
single-signal candidates: 48
bounded candidates: 57
matched benchmark/candidate rows identical: true
```

Authoritative real materialization identities:

```text
development rows: 9852
target primitive rows: 59070
nested fold records: 120
bounded candidates: 57
candidate-horizon records: 342
matched rows available records: 276
explicitly ineligible candidate-horizon records: 66
input hashes bound: true
```

Large-move labels are not globally materialized. Their q90 thresholds remain training-fold-only.

## Implemented preprocessing and estimator boundary

Frozen preprocessing policy:

```text
no imputation
matched complete rows only
training-fold clipping: 0.5% and 99.5% quantiles
training-fold standardization
population standard deviation
zero-variance scale: 1.0
future/test influence prohibited
exact benchmark transformation reused in candidate
```

Executable model families:

```text
regularized_linear
spline_regularized
shallow_hist_gradient_boosting
time_varying_regularized_glm
```

Eligibility-gated secondary family:

```text
state_space_or_markov_switching
INELIGIBLE_IMPLEMENTATION_NOT_AUTHORIZED
```

Window schemes:

```text
EXPANDING
ROLLING_ONE_YEAR: 2190 observations
ROLLING_TWO_YEARS: 4380 observations
```

Bounded model identity:

```text
pipeline specifications: 162
executable specifications: 153
gated specifications: 9
```

No model family, specification, or candidate is selected automatically.

## Logistic compatibility remediation

The frozen classification policy remains L2-regularized logistic regression.

```text
scikit-learn before 1.8: penalty = "l2"
scikit-learn 1.8 or later: l1_ratio = 0.0 and deprecated penalty omitted
```

The `C` grids, solver, targets, model families, windows, matched-row contracts, and candidate inventory are unchanged. Pytest and the standalone verifier now fail on every `FutureWarning`.

## Current truth state

```text
contract validated: true
foundation validated: true
materialization validated: true
development target primitives generated: true
real fold manifest generated: true
real continuity benchmark generated: true
real candidate inventory generated: true
real matched-row coverage generated: true
fold-scoped large-move labels generated: false
model implementation complete: true
model implementation functional validation: passed
model implementation warning-free validation: pending
model-selection target consumption started: false
real development models fitted: false
development pipelines ranked: false
development pipelines admitted: false
establishment authorization created: false
establishment segment accessed: false
signal established: false
failure modelling admissible: false
```

The frozen exact token `TARGET_ACCESS_NOT_STARTED` is retained and means that target primitives have not been consumed by model-selection or model-fitting execution.

## Required authoritative rerun

```powershell
.\RUN_V3_G5_MODEL_IMPLEMENTATION.ps1
```

Expected runner stages:

1. verify the final V3-4 lock;
2. verify validated V3-5 contract and foundation objects;
3. verify the authoritative materialization boundary;
4. verify or regenerate the real development foundation;
5. run 26 model-implementation tests with `FutureWarning` treated as error;
6. run the standalone implementation verifier with `FutureWarning` treated as error;
7. verify zero tracked or staged mutation.

## Next implementation after validation

The chronological development execution engine remains blocked until the warning-free implementation rerun passes and the estimator layer is finally locked. Real-data model fitting remains a separate governed execution boundary.

## Claims boundary

No predictive, economic, conditional-validity, deterioration, failure-probability, or operational-use claim is authorized at this checkpoint.
