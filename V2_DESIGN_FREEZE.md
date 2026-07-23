# Version 2 Methodological Design Freeze

## Institutional status

**Status:** frozen before Version 2 implementation and before access to the Version 2 locked evaluation segment.

**Parent release:** `v1.2.0`

**Parent commit:** `748d1720da9131ebd6eb7b0606913fd43fc6e5e8`

**Development branch:** `research/v2-conditional-signal-validity`

Version 2 begins from the published Version 1 replication baseline. It does not revise, overwrite, or reinterpret the Version 1 determination.

## Research decision

Version 1 found that fixed RSI, Bollinger Band, and combined specifications did not establish stable incremental contribution over the common benchmark. Version 2 therefore tests a narrower and more defensible question:

> Is technical-signal contribution conditional on forecast horizon, market state, signal interpretation, nonlinear response, estimation window, or calibrated decision selectivity?

The design is not intended to manufacture a positive result. Every declared candidate, including negative candidates, remains reportable.

## Confirmatory scope

The confirmatory target is future-return direction. RSI and Bollinger Bands are assessed as separate signal families against the same non-indicator benchmark.

- `H1`: a development-selected, conditionally specified RSI pipeline improves locked-holdout directional probability forecasts over the benchmark.
- `H2`: a development-selected, conditionally specified Bollinger pipeline improves locked-holdout directional probability forecasts over the benchmark.

The two confirmatory hypotheses are controlled with the Holm family-wise procedure at five percent.

The combined signal family, expected-return target, large-move target, alternate economic thresholds, and external replication analyses are secondary. They cannot replace a failed confirmatory determination.

## Frozen analytical dimensions

### Horizons

- 4 hours;
- 8 hours;
- 12 hours;
- 24 hours.

### Targets

- future-return direction;
- cumulative future log return;
- training-defined large absolute move.

### Signal interpretations

- continuous indicator information;
- contrarian or mean-reversion orientation;
- continuation or breakout orientation;
- soft interactions with filtered range, trend, and stress probabilities.

### Estimation windows

- expanding history;
- trailing one year;
- trailing two years.

### Model classes

- regularized linear or logistic benchmark and candidate pairs;
- restrained spline-augmented benchmark and candidate pairs;
- shallow gradient-boosting benchmark and candidate pairs.

Candidate and benchmark models must use the same model class within each comparison.

## Validation architecture

```text
Frozen Version 1 reference
        ↓
Version 2 development sample
        ↓
Five outer chronological folds
        ↓
Three inner chronological folds
        ↓
Training-only selection and calibration
        ↓
One frozen pipeline per confirmatory signal family
        ↓
Single locked-holdout evaluation
        ↓
External venue and cross-asset replication
        ↓
Evidence grade and operational-status assessment
```

The final evaluation segment begins at `2025-07-01T00:00:00Z` and ends at the frozen snapshot boundary `2026-07-22T08:00:00Z`. This segment was included in the aggregate Version 1 study; it is therefore described as **Version 2 methodology-locked**, not as a historically unseen market period. It remains inaccessible for Version 2 selection, calibration, threshold choice, or feature design.

## Decision gates

A positive Version 2 determination requires all mandatory gates:

1. protocol and data-integrity verification;
2. positive development contribution in at least three of five outer folds;
3. locked-holdout predictive superiority after confirmatory multiplicity control;
4. positive cost-adjusted economic contribution at the primary ten-basis-point assumption;
5. minimum decision coverage and absence of single-period concentration;
6. robustness to declared parameter, cost, and window sensitivities.

External replication determines the strength and transportability grade of any primary-case result. It does not retroactively alter the locked primary-case evidence.

## Tamper-evident freeze

The following files are covered by `V2_PROTOCOL_LOCK.json`:

- `V2_DESIGN_FREEZE.md`;
- `configs/v2_experiment_registry.json`;
- `docs/V2_RESEARCH_PROTOCOL.md`;
- `docs/V2_MODEL_CONTRACT.md`;
- `docs/V2_VALIDATION_GATES.md`;
- `docs/V2_MULTIPLE_TESTING_CONTROL.md`;
- `docs/V2_DATA_AND_REPLICATION_PLAN.md`;
- `docs/V2_HOLDOUT_GOVERNANCE.md`.

Any substantive modification after the freeze must be recorded as a protocol amendment with a new lock file, a new commit, and explicit disclosure before the locked evaluation segment is accessed.
