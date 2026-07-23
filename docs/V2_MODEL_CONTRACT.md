# Version 2 Model Contract

## 1. Contract purpose

This contract defines the admissible Version 2 model space. Implementation must conform to this document and `configs/v2_experiment_registry.json` before the locked evaluation segment is accessed.

## 2. Information sets

At forecast origin `t`, all inputs must be measurable at or before `t`. The following are prohibited:

- centred rolling windows;
- full-sample scaling or winsorisation;
- smoothed latent states using future observations;
- target-derived thresholds estimated outside training data;
- calibration on outer-test or holdout observations;
- parameter selection using locked-evaluation metrics.

## 3. Common benchmark

The benchmark retains the Version 1 non-indicator information set:

- lagged SOL returns;
- lagged BTC returns;
- causal trend measures;
- causal realised-volatility measures;
- price-range measures;
- volume and volume-change measures;
- transparent lagged market-state descriptors.

Any benchmark expansion must be applied identically to benchmark and candidate models and documented before holdout access.

## 4. Matched comparisons

For every model comparison:

```text
candidate = benchmark information + registered signal information
```

The benchmark and candidate must share:

- model class;
- training sample;
- preprocessing;
- hyperparameter-selection procedure;
- probability calibration;
- prediction horizon;
- target definition;
- decision threshold and transaction-cost treatment.

This matched-pair structure isolates incremental signal contribution.

## 5. Preprocessing

- imputation is not permitted for missing OHLCV observations;
- standardisation is fitted on training data only;
- clipping or winsorisation thresholds are training-only;
- spline knots are training-only;
- categorical or state encodings are fixed before test application;
- feature columns and transformations are recorded in a fold-level manifest.

## 6. Model families

### Regularized linear family

- classifier: logistic regression with L2 penalty;
- regressor: ridge regression;
- bounded regularisation grid specified in the registry.

### Spline-augmented family

- degree-three spline transformations;
- four or six knots;
- regularized linear estimator after transformation;
- spline transformation fitted only on training observations.

### Shallow gradient-boosting family

- histogram gradient boosting;
- shallow leaf structure;
- bounded iteration and regularisation grid;
- no unconstrained depth or automated external optimiser.

## 7. Regime conditioning

Soft state-probability interactions are the primary regime formulation. The regime filter is trained within each training partition and applied forward to validation, outer-test, and holdout observations.

A candidate cannot use the realised best historical regime to route predictions.

## 8. Window schemes

- expanding;
- trailing 2,190 four-hour observations, approximately one year;
- trailing 4,380 four-hour observations, approximately two years.

A window is eligible only when its minimum training requirement is met. Ineligible early-fold combinations are reported as structurally unavailable, not as failed models.

## 9. Candidate selection rule

Within each signal family:

1. rank candidates by mean inner-fold benchmark-relative primary loss;
2. exclude candidates with materially deficient calibration or coverage;
3. prefer lower complexity when differences are within one standard error;
4. record selection frequency across outer folds;
5. choose one final pipeline using development data only;
6. serialize the frozen pipeline definition before holdout access.

## 10. Model outputs

Every out-of-sample prediction record must include:

- timestamp;
- asset and venue;
- target and horizon;
- signal family;
- model family;
- benchmark probability or forecast;
- candidate probability or forecast;
- filtered state probabilities;
- decision threshold;
- position or risk gate where applicable;
- realised target;
- predictive loss differential;
- gross and net economic contribution where applicable;
- fold, window, and pipeline identifiers.

## 11. Model boundaries

Version 2 remains a research-validation framework. It is not a live trading engine, execution simulator, capacity model, or investment recommendation. Funding, open interest, liquidations, order-book depth, taxation, venue-specific fee tiers, and production latency remain outside Version 2 unless introduced through a documented amendment.
