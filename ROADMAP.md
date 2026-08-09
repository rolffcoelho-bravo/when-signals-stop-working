# Methodological Development Programme

## Research anchor

The programme exists to answer:

> Did RSI or Bollinger Bands establish incremental predictive and economic value, under which conditions, and—only after establishment—when is that contribution deteriorating or likely to fail?

The governing order is:

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

Complexity is admitted only when it improves evidence for this sequence. Spectral, network, panic-consistent, chronology, software, and governance layers are supporting components and cannot substitute for signal establishment.

## Version 1 — Parsimonious signal-validity framework

**Status:** complete and published.

Version 1 tested fixed RSI and Bollinger specifications against a common non-signal benchmark using five expanding chronological folds, cost-adjusted economic evidence, dependence-aware intervals, filtered market-state assessment, and sequential deterioration monitoring.

### Frozen determination

```text
RSI:                NOT_ESTABLISHED
Bollinger Bands:    NOT_ESTABLISHED
Combined model:     NOT_ESTABLISHED
```

A deterioration or suspension claim was therefore inadmissible.

## Version 2 — Conditional validity and inference hardening

**Status:** complete, locked, and merged as institutional `v2.0.0`.

Version 2 tested broader horizons, alternative signal interpretations, restrained nonlinear candidates, estimation windows, filtered-state interactions, calibration, abstention, nested chronological selection, multiplicity control, and one methodology-locked evaluation.

### Frozen determination

```text
RSI:                NO_PIPELINE_ADMITTED
Bollinger Bands:    NO_INCREMENTAL_EVIDENCE
Primary case:       NOT ESTABLISHED
```

The frozen Bollinger pipeline produced favourable means but failed the complete multiplicity-adjusted, dependence-aware predictive and economic confidence standard.

# Version 3 — Adaptive signal validity and failure-risk framework

## V3-0 — Design and product freeze

**Status:** complete.

The decision problem, reusable product requirement, canonical data contract, validation architecture, non-rescue rule, failure-event principle, and final output schema are frozen.

## V3-1 — Canonical data and adapter layer

**Status:** complete and locked.

Implemented:

- canonical OHLCV schema;
- source adapters;
- optional governed fields;
- deterministic manifests;
- data-quality and conformance controls.

## V3-2 — Multi-asset causal feature and spectral engine

**Status:** complete and locked.

Implemented:

- causal returns, downside, volatility, and volume features;
- fixed-panel rolling dependence matrices;
- dominant eigenvalue and dominant-eigenvalue share;
- eigenvalue gap;
- participation ratio and effective dimension;
- spectral entropy;
- first-eigenvector concentration and stability;
- complete eigenvalue spectrum;
- panel eligibility and sensitivity controls.

## V3-2B — Market-structure extension

**Status:** complete and locked.

Implemented:

- threshold networks;
- deterministic communities;
- minimum spanning trees;
- centrality concentration;
- path and topology descriptors;
- causal velocity, acceleration, and rolling-volatility dynamics.

## V3-3 — Panic-consistent probabilistic regime engine

**Status:** complete and locked.

Implemented:

- transparent V2 challenger;
- monotone mechanism-consistency probability;
- causal Gaussian HMM probability;
- transition risk;
- duration and occupancy evidence;
- uncertainty intervals and publication boundaries;
- mechanism contribution diagnostics;
- disagreement and coverage maps;
- no automatic model selection, ensemble, or consensus probability.

# Repository realignment

**Status:** complete and validated.

A full repository review found that implementation diverged after V3-3. The frozen plan defined V3-4 as the unified RSI and Bollinger signal engine, but chronology work occupied the historical V3-4A/B labels.

The realignment:

- restored the practitioner's question at repository root;
- restored the direct-answer logic;
- preserved all historical chronology artifacts and locks;
- reclassified chronology as a separate regime-validation extension;
- paused event alignment;
- restored and completed the true V3-4 signal engine;
- restored the establishment-before-failure sequence;
- prevented supporting regime validation from displacing the core signal-establishment programme.

Authoritative documents:

```text
PRACTITIONER_QUESTION.md
DIRECT_ANSWER_LOGIC.md
V3_REALIGNMENT_DECISION.md
docs/V3_REALIGNED_GATE_MAP.md
configs/v3_realignment_contract.json
```

# Regime-validation extension

## V3-RV1 — Independent regime-validation contract

**Historical identifier:** V3-4A  
**Status:** complete and historically locked.

The contract prevents model-derived events, chronology-driven model or threshold selection, retrospective event deletion, and retrospective event-boundary tuning.

## V3-RV2 — Independent chronology and provenance

**Historical identifier:** V3-4B  
**Status:** complete and historically locked; Windows checkout-portability revision remains open until revalidated.

The package contains 17 canonical events supported by 27 documentary sources, including 12 confirmed timing-eligible events and five boundary-uncertain events excluded from primary timing.

## V3-RV3 — Regime-event alignment

**Historical proposed identifier:** V3-4C  
**Status:** paused and not started.

This extension may resume only at an appropriate external-validation point. It is not allowed to displace the signal-establishment sequence.

# V3-4 — Unified RSI and Bollinger Interpretation Engine

**Status:** authoritatively validated and locked.

## the practitioner-question link

V3-4 defines the exact RSI and Bollinger information that V3-5 tests against matched non-signal benchmarks. It does not establish signal value and does not answer whether a signal stopped working.

## Locked implementation and evidence

```text
registered specifications: 48
base specifications: 44
explicit regime interactions: 4
training-only adaptive templates: 2
bounded maximum: 128
automatic selection: false
repository realignment tests: 7 passed
signal-engine tests: 19 passed
canonical source rows: 12171
feature rows: 584208
row-count identity: verified
validated implementation commit: ff2e7ecba3fa69f22e0b109437d23b52d30fba2b
evidence materialization commit: 705511de9e8ee22a9f8aff34506aebb6c26223e7
lock status: IMPLEMENTATION_VALIDATED_AND_LOCKED
```

## RSI families

- level and centered level;
- slope and acceleration;
- rolling range;
- causal bullish and bearish divergence;
- mean reversion;
- continuation;
- threshold crossings;
- persistence and duration;
- time since crossing and exit from extremes;
- training-only adaptive thresholds where registered.

## Bollinger families

- percentage-B and normalized distances;
- distance magnitude;
- upper and lower mean reversion;
- breakout and breakdown;
- outside-band continuation and re-entry;
- bandwidth level, change, and acceleration;
- squeeze and post-squeeze transition;
- expansion persistence;
- outside-band persistence and timing;
- training-only adaptive squeeze thresholds where registered.

## Registered market-state interactions

```text
RSI oversold mean reversion × p_range
RSI overbought continuation × p_trend
Bollinger lower breakdown × p_panic_consistent
Bollinger post-squeeze expansion × dominant_eigenvalue_share
```

Every interaction preserves the base signal and context component separately. Missing context and missing adaptive training parameters remain explicit ineligibility states rather than causing candidate deletion.

## Locked claims boundary

V3-4 produced no predictive, economic, conditional-validity, deterioration, or failure claim. Its large feature table remains regenerable and hash-bound; compact evidence is committed under `evidence/v3/g4_signal_lock/`.

# V3-5 — Matched Benchmark-versus-Signal Forecast Selection

**Status:** approved; implementation started; contract frozen; target access and model fitting not started.

## Objective

Determine whether registered signal information adds incremental predictive and economic value beyond a matched benchmark.

For every comparison:

```text
candidate = benchmark information + registered signal information
```

Benchmark and candidate must otherwise use identical model class, training rows, test rows, preprocessing, hyperparameter selection, calibration, target, horizon, cost treatment, and decision policy.

## Frozen partition

```text
Development selection:
2021-01-01T00:00:00Z to 2025-06-30T20:00:00Z

Signal-establishment segment:
2025-07-01T00:00:00Z to 2025-12-31T20:00:00Z

V3-9 final-framework reserve:
2026-01-01T00:00:00Z to 2026-07-22T08:00:00Z
```

The reserve is methodology-locked rather than historically unseen. Gate V3-5 may not access it.

## Frozen targets and horizons

```text
Confirmatory target: direction
Secondary targets: expected return and large-move probability
Horizons: 4h, 8h, 12h, 24h, 48h, 72h
```

The 4/8/12/24-hour set preserves Version 2 continuity. The 48/72-hour set implements the additional Version 3 protocol horizon family.

## Candidate architecture

Gate V3-5 receives all 48 locked V3-4 specifications and may evaluate:

- eligible single-feature augmentations;
- eight predeclared family blocks;
- a secondary combined RSI–Bollinger block.

Full Cartesian signal combinations, post-result candidate insertion, automatic deletion of unfavourable candidates, and rescue tuning are prohibited.

## Model families

- regularized logistic and ridge continuity models;
- degree-three spline-regularized challengers;
- shallow histogram gradient boosting;
- time-varying regularized generalized linear challenger;
- state-space or Markov-switching response models only when identifiability and occupancy gates pass.

Deep neural networks and unbounded automated search are prohibited before the first complete Version 3 evaluation.

## Chronological validation

```text
5 outer development folds
3 inner selection folds
no random shuffle
purge equal to target horizon
embargo when overlapping panel information requires it
training-only preprocessing
training-only regime estimation
training-only target thresholds
training-only calibration
```

Window schemes:

```text
expanding
rolling 2,190 observations
rolling 4,380 observations
```

## Development admission

A pipeline may receive establishment access only when it satisfies:

1. positive mean benchmark-relative primary metric;
2. positive contribution in at least three of five outer folds;
3. no single fold provides more than 60 percent of positive gain;
4. calibration is not materially worse than the benchmark;
5. coverage and nonzero-decision requirements pass;
6. mean economic contribution at ten basis points is positive;
7. the one-standard-error rule prefers the least complex competitive model.

Development admission is not final establishment.

## Signal-establishment gate

One frozen pipeline per confirmatory family may access the 2025 second-half establishment segment after the admission registry and access authorization are committed.

Primary establishment requires all applicable predictive, economic, chronological, calibration, coverage, concentration, and Holm-adjusted multiplicity gates to pass.

Economic assumptions:

```text
primary one-way cost: 10 bps
sensitivity: 5 bps and 20 bps
uncertainty: moving-block bootstrap
```

## Current implementation truth state

```text
contract frozen: true
targets generated: false
folds generated: false
benchmark features assembled: false
candidate registry assembled: false
development models fitted: false
development pipelines admitted: false
establishment authorization created: false
establishment segment accessed: false
final-framework reserve accessed: false
signal established: false
failure modelling admissible: false
```

## Immediate implementation sequence

1. validate the frozen V3-5 contract;
2. implement target and partition engine;
3. implement five outer and three inner chronological folds;
4. assemble benchmark and matched candidate row contracts;
5. implement restrained model pipelines;
6. execute nested development selection;
7. apply admission, calibration, coverage, concentration, and economic gates;
8. freeze admitted pipelines;
9. create establishment authorization before segment access;
10. execute establishment inference and final determination.

## Establishment stop rule

When no RSI or Bollinger pipeline passes the complete standard:

```text
NO_PIPELINE_ADMITTED
or
NO_INCREMENTAL_EVIDENCE

then

FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED
```

The core failure programme stops for that family.

# V3-6 — Prospective failure-event and monitoring layer

**Status:** not started.

This gate is admissible only for an established signal pipeline.

It must freeze:

- monitoring windows;
- predictive and economic tolerances;
- calibration and coverage boundaries;
- structural-break and parameter-instability thresholds;
- persistence, recovery, and revalidation rules;
- deterministic competing failure reasons.

# V3-7 — Signal-validity and failure-probability model

**Status:** not started.

The model must estimate chronologically calibrated probabilities for:

```text
24 hours
72 hours
7 days
30 days
```

It must report discrimination, calibration, warning lead time, false-alert burden, and decision utility against unconditional and persistence benchmarks.

# V3-8 — Governed economic and operational decision engine

**Status:** not started.

Required validity states:

```text
VALID
CONDITIONALLY_VALID
DEGRADING
SUSPENDED
REVALIDATION_REQUIRED
INVALID
```

Required actions:

```text
USE_WITHIN_REGISTERED_BOUNDARIES
USE_ONLY_IN_APPROVED_REGIMES
REDUCE_RELIANCE
SUSPEND_NEW_DECISIONS
REVALIDATE_BEFORE_REUSE
DO_NOT_USE
```

# V3-9 — Methodology-locked final-framework evaluation

**Status:** not started; 2026 reserve protected.

The complete frozen V3 forecast, validity, and decision pipeline receives one-time evaluation access to the 2026 reserve. No post-result retuning is permitted.

# V3-10 — External replication and transportability

**Status:** not started.

Minimum cases:

- SOL continuity case;
- BTC cross-asset case;
- ETH cross-asset case;
- at least one independent venue where comparable data permit;
- a broad liquid-asset panel for spectral estimation.

The V3-RV chronology may support regime validation here without becoming a supervised ground-truth label by assumption.

# V3-11 — Reusable package and scoring workflow

**Status:** not started.

This gate produces the model another user can operate:

```text
validate-data
build-features
fit-regime
build-signal-features
select-forecast-models
fit-validity-model
run-locked-evaluation
run-external-replication
run-monitoring-simulation
score-new-data
build-evidence-report
run-v3-framework
```

# V3-12 — Final audit and institutional release

**Status:** not started.

Completion requires:

- full repository validation;
- Python 3.11–3.13 CI;
- protocol, implementation, model, and evidence locks;
- reproducibility manifest;
- final evidence report;
- model cards and user guide;
- immutable release tag;
- claims matching the evidence grade.

# Programme controls

Every gate must preserve:

- the the practitioner research anchor;
- predeclared hypotheses and parameter ranges;
- chronological validation;
- locked evaluation boundaries;
- complete reporting of negative and positive results;
- the non-rescue rule;
- explicit separation between supporting regime evidence and signal establishment;
- strict protection of the V3-9 final-framework reserve;
- governance proportional to the scientific claim protected.
