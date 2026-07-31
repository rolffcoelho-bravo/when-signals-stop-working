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
FUNCTIONAL_VALIDATION_PASSED
COMPATIBILITY_REMEDIATION_IMPLEMENTED
WARNING_FREE_AUTHORITATIVE_RERUN_PENDING
REAL_DEVELOPMENT_MODEL_FITTING_NOT_STARTED
DEVELOPMENT_PIPELINE_SELECTION_NOT_STARTED
ESTABLISHMENT_SEGMENT_NOT_ACCESSED
FINAL_FRAMEWORK_RESERVE_NOT_ACCESSED
```

## Parent materialization evidence

The real development foundation passed in the Windows research environment at commit:

```text
91606edf50a2c0aee9bcb94a93350936ee53f81a
```

Authoritative identities:

```text
foundation tests: 16 passed
materialization tests: 5 passed
development rows: 9852
target primitive rows: 59070
nested fold records: 120
bounded candidates: 57
candidate-horizon records: 342
matched rows available records: 276
explicitly ineligible candidate-horizon records: 66
input hashes bound: true
tracked worktree clean: true
```

The machine-readable record is `V3_G5_MATERIALIZATION_VALIDATION.json`.

## Functional implementation validation

The first authoritative Windows execution completed at commit:

```text
5d31f1583bcf66f0231d8ef6b4f1e980d98def9b
```

Observed results:

```text
model-implementation tests: 26 passed
standalone verifier: passed
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
```

The run emitted six scikit-learn 1.8 `FutureWarning` messages because `LogisticRegression` was supplied with the explicit deprecated argument `penalty="l2"`. The warnings did not change fit results or the mathematical estimator, but they block final implementation lock because the argument is scheduled for removal in scikit-learn 1.10.

Machine-readable records:

```text
V3_G5_MODEL_IMPLEMENTATION_VALIDATION.json
V3_G5_MODEL_IMPLEMENTATION_REMEDIATION.json
```

## Compatibility remediation

The frozen mathematical policy remains L2-regularized logistic regression.

The API spelling is now version-aware:

```text
scikit-learn before 1.8:
penalty = "l2"

scikit-learn 1.8 or later:
l1_ratio = 0.0
deprecated penalty argument omitted
```

The classification `C` grid, solver, iteration limit, random seed, target registry, model-family registry, window registry, matched comparison rule, and candidate inventory are unchanged.

Both the pytest runner and standalone verifier now treat every `FutureWarning` as an execution failure.

## Scientific purpose

This slice implements the preprocessing and estimator objects required for later chronological development evaluation. It does not fit, rank, select, admit, calibrate, or evaluate any pipeline on real development data.

Synthetic estimator fitting is permitted only to verify implementation correctness.

## Frozen preprocessing policy

```text
missing-value policy: no imputation
row policy: matched complete rows only
clip lower quantile: 0.005
clip upper quantile: 0.995
clip fit scope: training fold only
standardization: training-fold mean and population standard deviation
zero-variance scale: 1.0
column-order drift: prohibited
future/test influence on fit: prohibited
```

Benchmark preprocessing is fitted once per training fold. Candidate preprocessing reuses the exact transformed benchmark columns and appends separately fitted registered-signal columns.

## Bounded estimator registry

The three targets are:

```text
direction: classification
expected_return: regression
large_move_probability: classification
```

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
status: INELIGIBLE_IMPLEMENTATION_NOT_AUTHORIZED
```

Window schemes:

```text
EXPANDING
ROLLING_ONE_YEAR: 2190 observations
ROLLING_TWO_YEARS: 4380 observations
```

Registry identity:

```text
executable configurations per target before windows: 17
executable pipeline specs per target: 51
gated pipeline specs per target: 3
total pipeline specs per target: 54
executable pipeline specs across targets: 153
gated pipeline specs across targets: 9
total pipeline specs across targets: 162
```

No specification is selected automatically.

## Matched estimator rule

For every pipeline specification:

```text
benchmark estimator class = candidate estimator class
benchmark hyperparameters = candidate hyperparameters
benchmark window = candidate window
benchmark training rows = candidate training rows
benchmark test rows = candidate test rows
candidate information = exact benchmark information + registered signal information
```

## Dynamic challenger

The time-varying regularized GLM is implemented as a deterministic exponentially weighted regularized GLM.

```text
forgetting factors: 0.97, 0.99
minimum training observations: 2190
classification regularization: fixed C = 1.0 with L2 semantics
regression regularization: fixed alpha = 1.0
```

Observations receive weights according to their age inside the training fold. Test and future rows cannot enter the weight calculation.

## Implementation files

```text
configs/v3_g5_model_implementation_contract.json
src/shockbridge_signal_validity/v3/forecast_preprocessing.py
src/shockbridge_signal_validity/v3/forecast_model_registry.py
src/shockbridge_signal_validity/v3/forecast_estimators.py
scripts/verify_v3_g5_materialization_boundary.py
scripts/verify_v3_g5_model_implementation.py
tests/test_v3_g5_preprocessing.py
tests/test_v3_g5_model_registry.py
tests/test_v3_g5_estimators.py
RUN_V3_G5_MODEL_IMPLEMENTATION.ps1
RUN_V3_G5_MODEL_IMPLEMENTATION.sh
```

## Required warning-free validation identity

```text
preprocessing tests: 8
model-registry tests: 7
estimator tests: 11
total model-implementation tests: 26
FutureWarnings: 0
pipeline specifications: 162
executable specifications: 153
gated specifications: 9
executable model families: 4
window schemes: 3
real development model fitting: false
```

## Required authoritative rerun

```powershell
.\RUN_V3_G5_MODEL_IMPLEMENTATION.ps1
```

## Current truth state

```text
development target primitives materialized: true
fold-scoped large-move labels materialized: false
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

The legacy frozen-contract token `TARGET_ACCESS_NOT_STARTED` remains defined as target consumption by model-selection or model-fitting execution. Target primitives may exist without advancing that boundary.

## Claims boundary

No predictive, economic, conditional-validity, deterioration, failure-probability, or operational-use claim is authorized at this checkpoint.

## Next implementation after validation

The chronological development execution engine remains blocked until the warning-free model implementation rerun passes and this layer is finally locked.
