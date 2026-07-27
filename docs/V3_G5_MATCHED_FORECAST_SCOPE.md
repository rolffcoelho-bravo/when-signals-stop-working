# Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection

## Gate status

```text
APPROVED
PARENT_V3_4_VALIDATED_AND_LOCKED
IMPLEMENTATION_STARTED
CONTRACT_FROZEN
TARGET_ACCESS_NOT_STARTED
MODEL_FITTING_NOT_STARTED
```

## Research-question link

Gate V3-5 is the first Version 3 gate permitted to test whether the 48 registered RSI and Bollinger specifications add incremental forecast and economic value beyond a matched non-signal benchmark.

It answers the establishment part of Richard's question. It does not define deterioration or estimate failure probability.

The controlling order remains:

```text
ESTABLISHMENT
    before
CONDITIONAL VALIDITY
    before
DETERIORATION
    before
FAILURE PROBABILITY
    before
OPERATIONAL ACTION
```

## Parent lock

Gate V3-5 may start only because Gate V3-4 is now locked as:

```text
V3_G4_SIGNAL_ENGINE_LOCK.json
status: IMPLEMENTATION_VALIDATED_AND_LOCKED
validated implementation commit: ff2e7ecba3fa69f22e0b109437d23b52d30fba2b
evidence materialization commit: 705511de9e8ee22a9f8aff34506aebb6c26223e7
```

The V3-4 signal definitions, identifiers, implementation objects, curated manifests, and runtime hashes may not be altered by V3-5.

## Objective

Determine whether registered RSI or Bollinger information improves a matched non-signal forecast pipeline under nested chronological development and one frozen signal-establishment segment.

For every admissible comparison:

```text
candidate = benchmark information + registered signal information
```

The candidate and benchmark must otherwise be identical.

## Data partition

The frozen SOL/USDT four-hour snapshot is partitioned as follows:

```text
Development selection:
2021-01-01 00:00 UTC through 2025-06-30 20:00 UTC

Signal-establishment segment:
2025-07-01 00:00 UTC through 2025-12-31 20:00 UTC

Final framework reserve for V3-9:
2026-01-01 00:00 UTC through 2026-07-22 08:00 UTC
```

The partition is methodology-locked for Version 3. It is not described as historically unseen because Version 1 and Version 2 used the same frozen snapshot in earlier governed studies.

Gate V3-5 may not access the 2026 final-framework reserve.

## Forecast targets and horizons

### Confirmatory target

```text
direction = 1[future cumulative log return > 0]
```

### Secondary targets

```text
expected return = future cumulative log return
large move = 1[absolute future cumulative log return > training-only horizon q90]
```

### Horizons

```text
4 hours   = 1 candle
8 hours   = 2 candles
12 hours  = 3 candles
24 hours  = 6 candles
48 hours  = 12 candles
72 hours  = 18 candles
```

The 4, 8, 12, and 24-hour horizons preserve Version 2 continuity. The 48 and 72-hour horizons implement the additional Version 3 protocol horizon set. A horizon may be excluded only through a documented pre-result feasibility rule.

## Signal candidate architecture

The locked V3-4 registry contains:

```text
48 registered specifications
44 base specifications
4 explicit market-state interactions
2 training-only adaptive templates
```

Primary candidate construction includes each eligible registered signal as a single matched augmentation.

Eight predeclared family blocks are also permitted:

```text
RSI_LEVEL_DYNAMICS
RSI_MEAN_REVERSION
RSI_CONTINUATION
RSI_DIVERGENCE
BOLLINGER_POSITION
BOLLINGER_MEAN_REVERSION
BOLLINGER_BREAKOUT
BOLLINGER_VOLATILITY_STRUCTURE
```

A combined RSI–Bollinger block is secondary only. Full Cartesian signal combinations are prohibited.

Adaptive and context-dependent candidates remain visible when ineligible. They may not be silently deleted because training-only parameters or context are unavailable.

## Benchmark information set

The benchmark preserves the Version 2 non-indicator continuity set:

- lagged SOL returns;
- lagged BTC returns;
- causal trend measures;
- causal realised-volatility measures;
- price-range measures;
- volume and volume-change measures;
- transparent lagged market-state descriptors.

Version 3 may add causal spectral, network, and forward-applied regime features only when the same additions enter the benchmark and candidate identically.

Regime information cannot rescue a signal by entering only the candidate benchmark comparison.

## Matched comparison contract

Every benchmark–candidate pair must use identical:

- model class;
- training observations;
- outer-test or establishment observations;
- preprocessing;
- hyperparameter-selection procedure;
- calibration procedure;
- target and horizon;
- transaction-cost policy;
- decision and abstention policy.

Candidate-specific missingness is handled through a matched row intersection. The benchmark is re-estimated on those exact rows. Raw metrics from unmatched candidate samples may not be ranked against one another.

## Model families

### Primary continuity model

- L2 logistic regression for direction and large-move probability;
- ridge regression for expected return.

### Restrained nonlinear challengers

- degree-three spline expansion with four or six training-fitted knots followed by regularized linear estimation;
- shallow histogram gradient boosting with bounded leaf count, iterations, sample size, and L2 regularization.

### Version 3 dynamic challenger

- time-varying regularized generalized linear model with registered forgetting factors `0.97` and `0.99`.

### Eligibility-gated secondary model

A state-space or Markov-switching response model is permitted only when minimum regime occupancy and identifiability gates pass. Automatic state-count selection is prohibited.

Deep neural networks, unbounded automated search, and post-result model insertion are prohibited.

## Chronological validation

Development uses:

```text
5 outer chronological folds
3 inner chronological folds
no shuffle
purge gap equal to forecast horizon
embargo where overlapping panel information requires it
training-only preprocessing
training-only regime estimation
training-only target thresholds
training-only calibration
```

Window schemes are:

```text
expanding
rolling 2,190 observations
rolling 4,380 observations
```

Selection frequency, structural ineligibility, candidate coverage, and fold concentration must be reported.

## Development admission

A pipeline may be frozen for signal-establishment access only when development evidence satisfies all applicable controls:

1. positive mean benchmark-relative primary metric;
2. positive contribution in at least three of five outer folds;
3. no single fold supplies more than 60 percent of the positive gain;
4. calibration is not materially worse than the matched benchmark;
5. coverage and nonzero-decision requirements pass;
6. mean economic contribution at the primary cost is positive;
7. the one-standard-error rule selects the least complex statistically competitive pipeline.

Development admission is not final signal establishment.

## Signal-establishment segment

One pipeline per confirmatory family may receive single access to the frozen 2025 second-half establishment segment after:

- all development predictions exist;
- the admitted pipeline registry is serialized;
- an access authorization record is committed;
- the final-framework reserve remains inaccessible.

A confirmatory family earns `PRIMARY_CASE_ESTABLISHED` only when all required predictive, economic, chronological, calibration, coverage, concentration, and multiplicity gates pass.

The two confirmatory families are controlled by Holm family-wise adjustment at five percent.

Secondary targets and combined-family analyses use Benjamini–Hochberg control at `q = 0.10` and cannot replace a failed directional confirmatory result.

## Economic contract

The primary one-way cost is ten basis points, with five- and twenty-basis-point sensitivity.

Economic decisions are horizon-spaced to avoid treating overlapping target windows as independent executable decisions. The benchmark and candidate use the same position or abstention policy.

Positive mean net contribution is insufficient. Establishment requires a positive dependence-aware lower confidence bound at the primary cost.

## Required outputs

```text
target_manifest.json
fold_manifest.json
candidate_registry.json
outer_fold_predictions.csv
outer_fold_results.csv
development_selection_report.json
frozen_pipeline_registry.json
establishment_authorization.json
establishment_predictions.csv
establishment_inference.json
v3_g5_determination.json
```

Every prediction row must preserve timestamp, target, horizon, signal family, signal or block identifier, model family, benchmark forecast, candidate forecast, realised target, loss differential, decision policy, gross and net contribution, fold, window, calibration, and pipeline identifiers.

## Stop rules

When no family passes development admission:

```text
NO_PIPELINE_ADMITTED
FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED
```

When an admitted family fails establishment:

```text
NO_INCREMENTAL_EVIDENCE
FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED
```

When conditional occupancy is insufficient:

```text
CONDITIONAL_CLAIM_NOT_AUTHORIZED
```

Any V3-5 access to the 2026 reserve is:

```text
PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED
```

## Claims prohibited before completion

Gate V3-5 may not yet claim:

- signal establishment;
- conditional validity;
- deterioration;
- signal failure;
- failure probability;
- operational-use authorization.

## Current implementation boundary

```text
contract: configs/v3_g5_forecast_contract.json
contract status: frozen
implementation started: true
target access: false
development model fitting: false
signal-establishment access: false
final-framework reserve access: false
```

## Next implementation work

1. target and partition engine;
2. chronological fold engine;
3. benchmark feature assembly;
4. signal-feature eligibility and block registry;
5. matched model pipelines;
6. nested development runner;
7. admission and pipeline-freeze layer;
8. establishment authorization and single-access runner;
9. inference and final Gate V3-5 determination.
