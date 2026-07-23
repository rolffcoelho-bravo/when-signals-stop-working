# Version 3 Gated Implementation Plan

## Governing rule

Version 3 is not complete when an indicator model, panic classifier, or backtest produces favourable results. Completion requires a reusable, validated, externally tested, failure-aware decision-support framework that can score conforming new data without source-specific model changes.

No later gate may compensate for a failed earlier gate by weakening the protocol.

## Gate V3-0 — Design and product freeze

**Status:** completed.

Required evidence:

- Version 3 decision problem frozen;
- forecast, validity, and decision layers separated;
- canonical data contract frozen;
- panic-consistent terminology boundary frozen;
- signal interpretations enumerated;
- validation and non-rescue rules frozen;
- final reusable product requirement defined.

Artifacts:

- `V3_DESIGN_FREEZE.md`;
- `docs/V3_RESEARCH_PROTOCOL.md`;
- `docs/V3_MODEL_CONTRACT.md`;
- this implementation plan.

## Gate V3-1 — Canonical data and adapter layer

Objective: permit datasets to change without modifying research logic.

Deliverables:

- Version 3 canonical schema package;
- adapter interface;
- CSV or Parquet reference adapter;
- exchange OHLCV adapter;
- governed optional-field adapters for funding, open interest, liquidations, order book, and cross-venue data;
- deterministic source and data manifests;
- data-quality report;
- synthetic fixture and adapter-conformance tests.

Acceptance:

- two independently formatted datasets map to the same canonical schema;
- critical schema failures stop execution;
- model modules contain no source-specific field names or paths;
- deterministic hashes and manifests pass.

## Gate V3-2 — Multi-asset causal feature and spectral engine

Objective: estimate contemporaneous market structure without future leakage.

Deliverables:

- causal return, volatility, downside, volume, liquidity, leverage, and liquidation features;
- rolling dependence matrices;
- dominant eigenvalue share, eigenvalue gap, participation ratio, spectral entropy, eigenvector concentration, and correlation statistics;
- panel eligibility and coverage controls;
- panel-composition and window-sensitivity diagnostics;
- analytical and synthetic-matrix tests.

Acceptance:

- all rolling features use information available through the forecast origin;
- spectral outputs match analytical fixtures within tolerance;
- insufficient panel coverage fails closed;
- no retrospective panel selection is possible.

## Gate V3-3 — Panic-consistent probabilistic regime engine

Objective: estimate regime probabilities from multiple independent stress dimensions.

Deliverables:

- transparent Version 2 state challenger;
- spectral regime candidates;
- panic-consistent composite candidates;
- filtered probabilities and transition risks;
- duration, occupancy, stability, concentration, and sensitivity evidence;
- terminology and causal-attribution controls.

Acceptance:

- panic probability is not determined by a single feature;
- all state estimation is training-only and forward-applied;
- conditional claims require minimum occupancy and event counts;
- the engine distinguishes insufficient evidence from absence of panic-consistent conditions.

## Gate V3-4 — Unified RSI and Bollinger interpretation engine

Objective: represent indicators as parameterized information families rather than fixed trading rules.

Deliverables:

- RSI mean-reversion, continuation, crossing, persistence, slope, acceleration, divergence, and adaptive-threshold candidates;
- Bollinger mean-reversion, breakout, breakdown, percentage-B, distance, bandwidth, squeeze, expansion, and persistence candidates;
- stable feature and interpretation identifiers;
- signal-regime interaction builder;
- causal and numerical tests.

Acceptance:

- every signal feature is reproducible from its identifier;
- target information is inaccessible;
- candidate generation is bounded by a registry;
- the same engine is used in development, evaluation, replication, and scoring.

## Gate V3-5 — Matched forecast selection

Objective: determine whether signal information adds incremental predictive value.

Deliverables:

- matched benchmark and candidate pipelines;
- direction, expected-return, and large-move targets;
- nested chronological selection;
- regularized, spline, shallow boosting, dynamic-coefficient, and eligible state-space candidates;
- calibration and abstention controls;
- multiplicity, coverage, concentration, and complexity controls;
- frozen forecast pipeline registry.

Acceptance:

- candidates differ from benchmarks only through registered signal information;
- no random shuffle or full-sample preprocessing;
- selected pipelines satisfy development admission rules;
- non-admitted signal families remain rejected without rescue tuning.

## Gate V3-6 — Prospective failure-event and monitoring layer

Objective: define what “stops working” means before fitting a failure model.

Deliverables:

- registered monitoring windows;
- predictive, economic, calibration, coverage, structural-break, regime-transport, and data-quality boundaries;
- persistence and recovery rules;
- failure-time and competing-reason label generator;
- monitoring feature history built from strictly prior information;
- synthetic boundary-transition tests.

Acceptance:

- a single adverse observation cannot create a failure event;
- labels are deterministic under the frozen definition;
- failure labels do not use future information at scoring time;
- thresholds are not selected to favour a candidate validity model.

## Gate V3-7 — Signal-validity and failure-probability model

Objective: estimate the probability that a validated signal will breach its operational standard.

Deliverables:

- discrete-time hazard baseline;
- regularized survival candidate;
- online change-point feature candidate;
- hidden semi-Markov or duration-aware state candidate where identified;
- calibrated boosting challenger;
- failure probabilities for 24 hours, 72 hours, 7 days, and 30 days;
- competing failure-reason probabilities where sample size permits;
- discrimination, calibration, lead-time, false-alarm, and decision-utility evidence.

Acceptance:

- failure probabilities are calibrated chronologically;
- the model improves over unconditional and persistence benchmarks;
- warning lead time is reported with false-alarm cost;
- failure predictions remain distinct from market-direction predictions.

## Gate V3-8 — Governed economic and operational decision engine

Objective: convert validated forecasts and failure risk into transparent permitted-use states.

Deliverables:

- frozen transaction-cost and slippage policies;
- decision coverage and turnover rules;
- `VALID`, `CONDITIONALLY_VALID`, `DEGRADING`, `SUSPENDED`, `REVALIDATION_REQUIRED`, and `INVALID` state machine;
- permitted-action mapping;
- boundary explanations;
- fail-closed behaviour for missing critical evidence;
- policy and state-transition tests.

Acceptance:

- positive forecasts cannot override suspended or invalid status;
- regime-limited approval is explicit;
- each decision exposes the evidence and boundary reasons;
- economic lower-bound, coverage, and liquidity requirements are enforced.

## Gate V3-9 — Methodology-locked evaluation

Objective: test the frozen Version 3 pipeline without post-result adaptation.

Prerequisites:

- data, panels, targets, horizons, candidate registries, costs, gates, failure events, and decision thresholds frozen;
- implementation and protocol locks passed;
- forecast and validity pipelines serialized;
- one-time access authorization recorded.

Deliverables:

- prediction-level forecast evidence;
- regime probabilities;
- failure probabilities;
- sequential validity states;
- predictive, economic, calibration, failure-risk, concentration, and decision-utility inference;
- complete negative and positive findings.

Acceptance:

- no retuning after evaluation access;
- multiplicity-adjusted and dependence-aware gates applied;
- all registered hypotheses receive explicit determinations;
- failure-model and forecast-model evidence are reported separately and jointly.

## Gate V3-10 — External replication and transportability

Objective: establish whether the process travels beyond the primary case.

Minimum cases:

- SOL continuity case;
- BTC cross-asset case;
- ETH cross-asset case;
- at least one independent venue where comparable data permit;
- broad liquid-asset panel for spectral estimation.

Deliverables:

- untouched replication configurations;
- asset- and venue-specific evidence;
- pooled and heterogeneous-effect analysis;
- transportability classification;
- failure-mode comparison across assets and venues.

Acceptance:

- no replication asset is selected because it is favourable;
- primary parameters are frozen or adaptation is explicitly classified and nested;
- general claims require cross-asset or cross-venue support;
- failures are reported without replacement by better-performing assets.

## Gate V3-11 — Reusable package, CLI, and scoring workflow

Objective: deliver a framework that another user can operate with a conforming dataset.

Deliverables:

- installable `shockbridge_signal_validity.v3` package;
- configuration schema and templates;
- adapter registry;
- serializable model bundle;
- programmatic API;
- commands:

```text
validate-data
build-features
fit-regime
select-forecast-models
fit-validity-model
run-locked-evaluation
run-external-replication
run-monitoring-simulation
score-new-data
build-evidence-report
run-v3-framework
```

- one-command reference workflow;
- machine-readable scoring output;
- model cards and decision report;
- end-to-end synthetic and real-data tests.

Acceptance:

- a fresh environment can install and execute the package;
- a user can change data through configuration and an adapter without modifying model code;
- the same model bundle can score later conforming observations;
- every output is linked to run, data, configuration, code, and pipeline identifiers;
- invalid inputs and failed gates stop safely.

## Gate V3-12 — Final audit and institutional release

Deliverables:

- complete repository validation;
- public release and sensitive-information audit;
- protocol, implementation, model, and evidence locks;
- reproducibility manifest;
- final evidence report;
- framework user guide;
- release notes and citation metadata;
- Python 3.11–3.13 CI matrix;
- immutable release tag.

Acceptance:

- all tests and required status checks pass;
- prior releases remain unchanged;
- claims match the evidence grade;
- the release contains the reusable scoring framework, not only historical outputs.

## Final completion statement

Only Gate V3-11 produces the model Richard can actually use. Gates V3-1 through V3-10 establish that the model and its decision states have a defensible evidential basis. Gate V3-12 makes the complete framework reproducible, citable, and immutable.