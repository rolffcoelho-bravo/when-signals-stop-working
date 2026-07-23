# Version 2 Checkpoint D2A

## Institutional designation

**Nested benchmark-relative signal-specification screening on development data only**

## Admission criteria

D2A is complete only when:

- all 84 registered standalone signal specifications are represented;
- each of four horizons and five outer folds is evaluated;
- inner selection uses only the corresponding outer-training partition;
- benchmark and candidate comparisons are matched;
- outer predictions are generated only after inner selection;
- no holdout file exists;
- all earlier governance locks verify;
- the D2A lock and asset verifier pass.

## Expected evidence

- inner screening results;
- selected specification by family, horizon, and outer fold;
- outer-fold matched predictions;
- outer-fold predictive metrics;
- family-horizon preliminary screening summary;
- implementation manifest and execution status.

## Boundary

D2A is a screening checkpoint. D2B performs bounded model-family, window, calibration, and hyperparameter selection using only specifications admitted by D2A.
