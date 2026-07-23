# Version 2 D1 Causal Feature and Filtered-State Engine

## Checkpoint purpose

D1 establishes the information layer required by later nested model selection. It does not fit a benchmark or candidate forecasting model and does not access locked-evaluation performance.

## Governed outputs

The checkpoint produces:

- the frozen Version 1 benchmark feature set using trailing information only;
- a documented feature dictionary;
- a prefix-invariance audit for all 84 unique registered RSI and Bollinger signal specifications;
- training-scoped three-state Gaussian Markov filters for every outer and inner development fold;
- forward-filtered outer-test state probabilities;
- fold-level parameter, chronology, covariance, transition, and normalization evidence;
- a development-only manifest and status record.

## Causal boundary

At any forecast origin, every market and signal feature is a function only of observations available at or before that origin. State-filter parameters are estimated from the corresponding fold training partition. Evaluation probabilities are then generated sequentially without smoothing, relabelling, or access to later observations.

## Scope statement

The state engine is a conditioning and interaction layer. Its estimation is not treated as predictive candidate fitting. Predictive benchmark and signal models remain disabled until the D2 nested-selection checkpoint.

## Governance status

- Version 1 evidence: unchanged;
- Version 2 protocol: unchanged;
- D0 implementation lock: unchanged;
- predictive model fitting: not performed;
- holdout performance: not accessed.
