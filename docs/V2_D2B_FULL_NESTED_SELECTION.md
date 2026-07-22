# Version 2 D2B Full Nested Pipeline Selection

## Purpose

D2B is the first development checkpoint that compares the complete registered predictive architecture after D2A signal-specification screening. It remains fully inside the development partition.

## Candidate boundary

For each signal family, forecast horizon, and outer development fold, D2B uses only the signal specification selected by D2A for that context. It does not reopen the 84-specification signal grid.

The structural inventory contains 90 configurations:

- 15 registered model and hyperparameter specifications;
- three estimation-window schemes;
- unconditioned and soft-state-conditioned signal blocks.

## Nested sequence

Within each outer fold:

1. all 90 structural configurations are evaluated across the three inner chronological folds with no calibration;
2. one structural configuration is selected by benchmark-relative log loss, fold stability, calibration non-dominance, and deterministic complexity tie-breaks;
3. `none`, `sigmoid`, and diagnostic-only `isotonic` calibration are evaluated using chronological training-only calibration segments;
4. only `none` and `sigmoid` are eligible for confirmatory selection;
5. abstention thresholds are selected from the frozen set using inner-fold coverage and net directional edge at the predeclared 10-basis-point one-way cost;
6. the complete selected pipeline is evaluated once on the untouched outer fold.

## Matched comparison

Benchmark and candidate use the same model family, hyperparameters, estimation window, and calibration method. The candidate differs only by the admitted signal-information block and, where selected, its soft state-probability interactions.

## Governance boundary

D2B does not:

- access the methodology-locked evaluation segment;
- declare confirmatory statistical significance;
- apply the final economic gate;
- freeze the family-level holdout pipeline;
- alter Version 1 evidence or any earlier Version 2 checkpoint.

D2C will assess development admission across the five outer folds and freeze at most one pipeline per confirmatory signal family before any holdout authorization.
