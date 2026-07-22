# Version 2 Research Protocol

## 1. Objective

Version 2 evaluates whether RSI or Bollinger Band information contributes incremental value only under identifiable conditional structures that were not represented by the parsimonious Version 1 specification.

The study separates five questions:

1. Does the indicator improve directional probability forecasts?
2. Does it improve expected-return forecasts?
3. Does it improve large-move probability forecasts?
4. Is any contribution conditional on horizon, market state, signal interpretation, or estimation window?
5. Does development evidence survive a single methodology-locked evaluation and external replication?

## 2. Confirmatory hypotheses

### H1 - RSI directional contribution

A single RSI pipeline selected exclusively through nested chronological development validation improves directional log loss over a matched non-indicator benchmark on the locked evaluation segment.

### H2 - Bollinger directional contribution

A single Bollinger pipeline selected exclusively through nested chronological development validation improves directional log loss over a matched non-indicator benchmark on the locked evaluation segment.

The confirmatory family contains exactly these two hypotheses. Holm adjustment controls family-wise error at `alpha = 0.05`.

## 3. Secondary analyses

The following are secondary and cannot substitute for a failed confirmatory hypothesis:

- expected cumulative return;
- large absolute move probability;
- combined RSI and Bollinger information;
- individual horizon findings not selected by the frozen development procedure;
- alternate transaction-cost assumptions;
- hard regime routing;
- abstention-threshold comparisons;
- cross-asset and cross-venue transportability.

Secondary probability hypotheses use Benjamini-Hochberg false-discovery-rate control at `q = 0.10` within each declared family.

## 4. Data partition

### Development segment

- start: `2021-01-01T00:00:00Z`;
- end: `2025-06-30T20:00:00Z`.

### Locked evaluation segment

- start: `2025-07-01T00:00:00Z`;
- end: `2026-07-22T08:00:00Z`.

The locked segment is not available for feature choice, parameter selection, model-class choice, calibration, threshold selection, or debugging. It may be accessed only after the pre-holdout gate in `docs/V2_HOLDOUT_GOVERNANCE.md` passes.

The period formed part of the published Version 1 aggregate assessment. Version 2 therefore describes it as methodology-locked rather than historically unseen.

## 5. Horizons

The declared horizon set is:

```text
h = 1, 2, 3, 6 four-hour candles
```

Equivalent elapsed horizons are 4, 8, 12, and 24 hours. All horizons remain in the development evidence. The confirmatory holdout pipeline contains one development-selected horizon per signal family.

## 6. Targets

For horizon `h`:

```text
future_return_h[t] = log(close[t+h] / close[t])
direction_h[t] = 1{future_return_h[t] > 0}
large_move_h[t] = 1{|future_return_h[t]| > q90_training(|future_return_h|)}
```

The large-move threshold is estimated inside each training partition and applied unchanged to the corresponding validation or test partition.

## 7. Benchmark discipline

Every candidate is compared with a matched benchmark using:

- the same estimation observations;
- the same target and horizon;
- the same model class;
- the same preprocessing and calibration architecture;
- the same chronological folds;
- the same execution and cost assumptions.

The candidate differs only through the addition of the declared signal-information family and its predeclared conditional interactions.

## 8. Candidate signal families

### RSI

- periods: 7, 14, 21, 28;
- threshold pairs: 20/80, 25/75, 30/70, 35/65;
- level, slope, distance from 50, threshold distance, and event persistence;
- contrarian and continuation orientations;
- soft interactions with filtered market-state probabilities.

### Bollinger Bands

- periods: 10, 20, 30, 40;
- standard-deviation multipliers: 1.5, 2.0, 2.5;
- `%B`, BandWidth, band distance, band-crossing persistence, and BandWidth change;
- contrarian and continuation orientations;
- soft interactions with filtered market-state probabilities.

### Combined specification

The combined family is secondary. It uses the standalone RSI and Bollinger specifications selected within the same inner training process. A full Cartesian combination of all RSI and Bollinger parameters is prohibited.

## 9. Conditional market-state structure

The Version 1 forward-only three-state filter remains the transparent state layer. It is estimated on training observations only and applied sequentially.

The primary conditional formulation uses soft interactions:

```text
signal_feature × P(range)
signal_feature × P(trend)
signal_feature × P(stress)
```

Full-sample smoothing and retrospective regime relabelling are prohibited. Hard regime routing is secondary and must be selected within inner chronological validation.

## 10. Model classes

The restrained model set comprises:

1. regularized linear or logistic models;
2. spline-augmented regularized models;
3. shallow histogram gradient boosting.

Model hyperparameters are bounded by `configs/v2_experiment_registry.json`. Unregistered models or grids require a protocol amendment before holdout access.

## 11. Nested chronological selection

- five outer chronological development folds;
- three inner chronological folds within each outer training partition;
- horizon-specific purge gap equal to the forecast horizon;
- no random shuffle;
- all transformations fitted only on the relevant training partition;
- complete reporting of outer-fold evidence and inner selection frequency.

Candidate ranking uses mean benchmark-relative primary loss, subject to stability and complexity controls. Ties favour the lower-complexity candidate.

## 12. Calibration and abstention

Classification models may be uncalibrated or sigmoid-calibrated. Calibration is fitted only within temporal training partitions. Isotonic calibration is diagnostic and cannot define the confirmatory pipeline.

Directional abstention thresholds are:

```text
|p(up) - 0.5| > 0.02, 0.05, or 0.10
```

Performance and decision coverage are always reported together. Confirmatory economic evidence requires at least ten-percent holdout coverage and at least 100 non-zero decisions.

## 13. Economic assessment

The primary one-way cost is ten basis points. Five and twenty basis points are sensitivity cases.

Directional and expected-return models may produce cost-adjusted positions. The large-move target is a risk or exposure gate and is not presented as an independent directional strategy.

Economic evidence requires a positive moving-block-bootstrap lower confidence bound at the primary cost assumption.

## 14. Reporting obligation

The final Version 2 report must disclose:

- every registered candidate family;
- every development outer fold;
- inner selection frequencies;
- the exact frozen pipelines entering holdout;
- the holdout-access timestamp and commit;
- adjusted and unadjusted confirmatory p-values;
- probability, calibration, economic, coverage, and concentration evidence;
- all secondary analyses, including negative results;
- external replication eligibility, data quality, and findings;
- any protocol amendment or execution exception.
