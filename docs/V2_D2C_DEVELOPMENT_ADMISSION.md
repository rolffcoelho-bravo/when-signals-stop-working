# Version 2 D2C Development Admission and Pipeline Freeze

## Purpose

D2C converts the completed D2B nested development evidence into a final family-level decision for each confirmatory signal family. It does not inspect the methodology-locked evaluation period and does not evaluate the final economic evidence gate.

## Admission unit

The admission unit is a signal-family and forecast-horizon pair. The confirmatory families are RSI and Bollinger Bands, and the registered horizons are 1, 2, 3, and 6 four-hour candles.

A family-horizon pair advances only when all of the following development controls pass:

1. five outer development folds are present;
2. mean benchmark-relative incremental log loss is strictly positive;
3. at least three of five outer folds are positive;
4. no single fold contributes more than 60% of total positive loss reduction;
5. candidate Brier score is not materially worse than the benchmark;
6. candidate expected calibration error is not materially worse than the benchmark;
7. selected policy coverage is at least 10%;
8. the selected policies produce at least 100 development decisions in aggregate.

Net trading edge is recorded as a diagnostic but is not a D2C admission gate. Economic admission belongs to the locked-evaluation stage.

## Family decision

When multiple horizons pass, D2C selects one horizon using mean incremental log-loss contribution as the primary criterion, followed by positive-fold count, concentration, Brier score, and shorter horizon as deterministic tie breakers.

When no horizon passes, the family receives `NO_PIPELINE_ADMITTED`. This is a valid research outcome and prevents holdout execution for that family.

## Frozen component selection

For an admitted family, D2C freezes one complete pipeline from pooled inner-development evidence:

- one registered RSI or Bollinger specification;
- one structural model, estimation window, and state-conditioning choice;
- one confirmatory calibration method (`none` or `sigmoid`);
- one decision threshold satisfying the development coverage and decision-count controls.

The frozen pipeline receives a canonical SHA-256 identifier. Isotonic calibration remains diagnostic-only.

## Governance boundary

D2C creates the pipeline registry but does not authorize use of the methodology-locked evaluation segment. A separate D3 authorization checkpoint is required. No holdout file, prediction, metric, or verdict may be created by D2C.
