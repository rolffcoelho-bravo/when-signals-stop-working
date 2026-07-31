# Gate V3-5 — Fold-Scoped Preprocessing and Matched Estimator Implementation

## Status

```text
APPROVED
PARENT_V3_4_IMPLEMENTATION_VALIDATED_AND_LOCKED
V3_5_CONTRACT_AUTHORITATIVELY_VALIDATED
V3_5_FOUNDATION_AUTHORITATIVELY_VALIDATED
V3_5_MATERIALIZATION_AUTHORITATIVELY_VALIDATED
MODEL_IMPLEMENTATION_CONTRACT_FROZEN
FOLD_SCOPED_PREPROCESSING_IMPLEMENTED
MATCHED_ESTIMATOR_FAMILIES_IMPLEMENTED
WARNING_FREE_AUTHORITATIVE_VALIDATION_PASSED
MODEL_IMPLEMENTATION_AUTHORITATIVELY_VALIDATED_AND_PROTECTED
REAL_DEVELOPMENT_MODEL_FITTING_NOT_STARTED
DEVELOPMENT_PIPELINE_SELECTION_NOT_STARTED
ESTABLISHMENT_SEGMENT_NOT_ACCESSED
FINAL_FRAMEWORK_RESERVE_NOT_ACCESSED
```

## Authoritative boundary

The warning-free Windows validation passed at:

```text
37c7360afde61a01ee9f9c5237dcf6bdf42985dd
```

Validated identity:

```text
model implementation tests: 26 passed
standalone verifier: passed
FutureWarnings: 0
scikit-learn: 1.9
logistic L2 semantics preserved: true
pipeline specifications: 162
executable specifications: 153
gated specifications: 9
executable model families: 4
window schemes: 3
synthetic classification and regression fits: passed
real development model fitting: false
development pipeline selection: false
establishment segment access: false
final reserve access: false
tracked worktree: clean
```

Machine-readable records:

```text
V3_G5_MODEL_IMPLEMENTATION_VALIDATION.json
V3_G5_MODEL_IMPLEMENTATION_REMEDIATION.json
```

The compatibility remediation is closed. Scikit-learn versions before 1.8 use `penalty="l2"`; versions 1.8 and later use the mathematically equivalent `l1_ratio=0.0` while omitting the deprecated argument.

## Protected implementation

The following ten objects are pinned to commit `37c7360afde61a01ee9f9c5237dcf6bdf42985dd`:

```text
configs/v3_g5_model_implementation_contract.json
src/shockbridge_signal_validity/v3/forecast_preprocessing.py
src/shockbridge_signal_validity/v3/forecast_model_registry.py
src/shockbridge_signal_validity/v3/forecast_estimators.py
scripts/verify_v3_g5_model_implementation.py
tests/test_v3_g5_preprocessing.py
tests/test_v3_g5_model_registry.py
tests/test_v3_g5_estimators.py
RUN_V3_G5_MODEL_IMPLEMENTATION.ps1
RUN_V3_G5_MODEL_IMPLEMENTATION.sh
```

`scripts/verify_v3_g5_model_implementation_boundary.py` rejects later Git-object drift and local or staged mutation of those paths.

## Frozen preprocessing policy

```text
no imputation
matched complete rows only
training-fold clipping at 0.5% and 99.5%
training-fold mean and population-standard-deviation scaling
zero-variance scale: 1.0
future/test influence prohibited
exact benchmark transformation reused in candidate
```

## Bounded estimator registry

Executable families:

```text
regularized_linear
spline_regularized
shallow_hist_gradient_boosting
time_varying_regularized_glm
```

Eligibility-gated family:

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

No specification is selected automatically.

## Current truth state

```text
development target primitives materialized: true
model implementation validated and protected: true
model-selection target consumption started: false
real development models fitted: false
development pipelines ranked: false
development pipelines admitted: false
establishment authorization created: false
establishment segment accessed: false
final-framework reserve accessed: false
signal established: false
failure modelling admissible: false
```

## Claims boundary

No predictive, economic, conditional-validity, deterioration, failure-probability, or operational-use claim is authorized by this layer.

## Next implementation

The chronological development execution engine is now the active implementation slice. Real development fitting remains separately blocked.
