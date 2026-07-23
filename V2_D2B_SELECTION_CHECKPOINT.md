# Version 2 Checkpoint D2B

## Institutional designation

**Full nested model, window, calibration, state-conditioning, and abstention selection on development data only**

## Admission criteria

D2B is complete only when:

- the structural inventory contains all 90 frozen configurations;
- all 40 D2A family-horizon-outer contexts are represented;
- structural selection uses only three inner chronological folds;
- calibration is fitted only on chronological training subsets;
- isotonic calibration remains diagnostic-only;
- abstention selection uses only inner-fold predictions;
- each selected pipeline is evaluated once on its untouched outer fold;
- no methodology-locked evaluation or holdout file is accessed;
- all prior locks, the D2B lock, asset verification, and the complete test suite pass.

## Expected production evidence

- 90-row structural pipeline inventory;
- 10,800 inner structural result rows;
- 40 selected structural pipelines;
- 360 inner calibration result rows;
- 40 selected calibration methods;
- 480 inner decision-policy result rows;
- 40 selected decision policies;
- 40 outer-fold pipeline results;
- observation-level outer predictions;
- eight family-horizon development-stability rows;
- implementation manifest and execution status.

## Boundary

D2B performs nested development selection. It does not freeze a family-level holdout pipeline or evaluate confirmatory, economic, or transportability gates. Those actions require later governed checkpoints.
