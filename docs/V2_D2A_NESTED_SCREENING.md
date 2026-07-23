# Version 2 D2A Nested Signal-Specification Screening

## Purpose

D2A is the first predictive-model checkpoint in Version 2. It screens every registered standalone RSI and Bollinger specification on development data only, using nested chronological validation and matched non-indicator benchmarks.

D2A is not the final candidate-selection stage. It deliberately fixes the estimator, estimation window, and calibration rule so that registered signal definitions can be evaluated before model-family flexibility is introduced.

## Frozen D2A estimator

- target: directional return;
- benchmark classifier: L2-regularized logistic regression;
- candidate screen: one-step ridge score augmentation with the benchmark logit held as an offset;
- regularization: fixed at the D2A implementation value;
- training window: expanding;
- calibration: none;
- preprocessing: training-only standardization;
- regime formulation: forward-filtered state probabilities plus soft signal-state interactions.

## Nested selection

For each signal family, horizon, and outer fold:

1. every registered signal specification is evaluated on the three inner chronological folds;
2. benchmark and candidate share the same observations, preprocessing, state probabilities, estimator, and target;
3. the common benchmark is fitted once per fold and each signal block is assessed as an incremental offset augmentation;
4. specifications are ranked by mean inner-fold incremental log-loss contribution;
5. materially calibration-dominated specifications are excluded where alternatives remain;
6. one specification is selected without observing the outer fold;
7. the selected specification is refitted on the outer training partition and evaluated once on the outer test partition.

## Interpretation boundary

D2A may identify signal definitions worthy of full D2B model-family and window selection. It cannot establish a final Version 2 pipeline, economic value, holdout superiority, or operational status.

Any reported gate result is labelled `PRELIMINARY_SCREENING_ONLY_NOT_FINAL_GATE_2`.

## Prohibited actions

- locked-evaluation access;
- model-family or window selection;
- sigmoid or isotonic calibration selection;
- combined-signal construction;
- economic promotion;
- alteration of the Version 1 evidence, Version 2 protocol, D0 scaffold, or D1 engine.
