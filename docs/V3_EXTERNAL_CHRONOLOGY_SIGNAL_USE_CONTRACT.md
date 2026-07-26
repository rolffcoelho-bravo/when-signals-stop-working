# Gate V3-4A - Independent Chronology and Signal-Use Eligibility Contract

## Purpose

Gate V3-4A freezes the scientific and governance boundary for validating the locked Gate V3-3 panic-consistent regime engine against independently documented market dislocations and for evaluating whether an already-established technical signal should change interpretation or permitted use across regimes.

The gate does not compile the chronology, inspect model outputs, execute event alignment, or condition signal performance. Those actions belong to later V3-4 subgates.

## Parent boundary

The contract is anchored to:

```text
V3_G3_PANIC_REGIME_LOCK.json
0e35908c03e36d8caeb832a078ff0566ef4e2ea4
```

The following remain immutable:

- Version 1 and Version 2 determinations;
- the three registered Gate V3-3 models;
- the Gate V3-3 probability and state thresholds;
- all Gate V3-3 protected objects;
- the prohibition on automatic model selection, automatic ensembles, and consensus probability.

## Scientific questions

### Independent event alignment

Do the pre-existing panic-consistent probabilities and causal state transitions align with independently documented market dislocations when the event chronology is compiled without access to model outputs?

### Signal-use eligibility

Does an independently inferred regime change the admissible interpretation, reliability assessment, or permitted use of a technical signal without revising its frozen unconditional verdict?

## Chronology independence

The chronology registry must be compiled and locked before model-output overlay.

During V3-4A and V3-4B:

```text
model-output access = prohibited
model-derived event inclusion = prohibited
chronology-driven threshold selection = prohibited
chronology-driven model selection = prohibited
retrospective event deletion = prohibited
retrospective event-boundary tuning = prohibited
```

Every event requires an auditable identity, event type, start and end timestamp, source identity and type, source locator, publication timestamp, documentation status, severity class, timestamp precision, boundary uncertainty, and notes.

## Chronology is not complete ground truth

An external chronology is necessarily incomplete. It can omit undocumented stress, contain uncertain boundaries, and reflect heterogeneous source standards.

Therefore:

- the chronology is validation evidence, not a complete supervised panic label;
- classification metrics are prohibited unless a later gate establishes a sufficiently complete event registry;
- temporal overlap alone cannot establish causal event attribution;
- non-event observations cannot automatically be interpreted as true negatives;
- chronology completeness and source conflict must remain visible.

## Event taxonomy

The frozen taxonomy contains:

```text
LIQUIDITY_DISLOCATION
FUNDING_STRESS
LIQUIDATION_CASCADE
VOLATILITY_SHOCK
DOWNSIDE_DISLOCATION
MARKET_STRUCTURE_BREAK
EXCHANGE_OR_VENUE_DISRUPTION
CROSS_MARKET_CONTAGION
```

The categories map to the economic mechanisms registered in Gate V3-3 without using Gate V3-3 probabilities to decide which events qualify.

## Registered event-alignment design

The primary probability models are:

```text
MONOTONE_MECHANISM_SCORE_V1
CAUSAL_GAUSSIAN_HMM_V1
```

The transparent challenger remains separately reported and cannot be converted into a panic probability.

The fixed lead and decay horizons are:

```text
1, 3, 6, and 12 observations
```

The primary metrics are:

```text
transition_capture_rate
event_overlap_fraction
lead_time_distribution
false_alert_burden
post_event_decay
event_probability_rank_shift
cross_model_disagreement_during_events
```

These metrics describe alignment, timing, alert burden, decay, and model disagreement. They cannot rank models or select a champion.

## Matched non-event controls

Later event evaluation uses calendar-blocked non-event windows with the same asset, venue, and frequency. Event buffers are fixed at 12 observations.

Control selection cannot use:

- model probability;
- model disagreement;
- event-alignment outcomes;
- favourable signal performance.

## Signal-use eligibility principle

Conditional degradation testing is admissible only when unconditional incremental value was established before regime access under a frozen contract.

This requirement separates two questions:

1. Was the signal useful before conditioning?
2. Did that established usefulness deteriorate or change across independently inferred regimes?

Without the first result, the second cannot be described as signal failure.

## Frozen RSI and Bollinger boundaries

The current statuses remain:

```text
RSI: NO_PIPELINE_ADMITTED
BOLLINGER: NO_INCREMENTAL_EVIDENCE
```

Both are assigned:

```text
INELIGIBLE_BASELINE_NOT_ESTABLISHED
DESCRIPTIVE_REGIME_SENSITIVITY_ONLY
```

Consequently, Gate V3-4 cannot:

- rescue RSI;
- rescue Bollinger;
- promote either signal based on a favourable regime subgroup;
- claim that either signal stopped working;
- revise either frozen unconditional verdict.

Later descriptive diagnostics may show how signal outputs behave across regimes, but those results cannot become predictive-admission evidence.

## Permitted-use states

The registered use states are:

```text
UNASSESSED
RESEARCH_DIAGNOSTIC_ONLY
NO_CHANGE_SUPPORTED
RESTRICTED_USE
SUSPEND_USE
```

`RESTRICTED_USE` and `SUSPEND_USE` require an established baseline and a predeclared, statistically supported loss of reliability. The current RSI and Bollinger specifications cannot enter those states because their unconditional value was not established.

## Conditional diagnostic design

Signal parameters, signal pipelines, regime thresholds, and model definitions remain frozen.

The registered estimands are:

- benchmark-relative loss difference by predeclared regime;
- calibration change by predeclared regime;
- economic-value change by predeclared regime;
- signal-concentration change by predeclared regime.

The minimum evidence boundaries are:

```text
minimum regime observations = 50
minimum regime episodes = 5
```

Insufficient evidence produces:

```text
INSUFFICIENT_CONDITIONAL_EVIDENCE
```

## Multiplicity and reporting

Primary hypotheses must be registered before model overlay. Holm family-wise adjustment is mandatory. Raw and adjusted results, dependence-aware confidence intervals, every registered model, every registered horizon, negative findings, and insufficient-evidence outcomes must remain visible.

Favourable subgroup suppression is prohibited.

## Required outputs

The complete V3-4 programme requires:

```text
external_chronology.csv
chronology_manifest.json
chronology_provenance.json
chronology_merge_log.csv
event_alignment.csv
lead_lag_diagnostics.json
false_alert_burden.json
chronology_validation_report.json
signal_use_eligibility.json
conditional_signal_diagnostics.csv
v3_g4_decision_report.json
```

## Subgate sequence

### V3-4A

Independent chronology and signal-use eligibility contract. Model-output access is prohibited.

### V3-4B

Chronology compilation and provenance lock. Model-output access remains prohibited.

### V3-4C

Independent event-alignment evaluation using the already locked chronology and already locked Gate V3-3 outputs.

### V3-4D

Conditional signal-use diagnostics and final decision lock. Current RSI and Bollinger results remain descriptive-only.

## Publication value

The design prevents two common methodological failures:

1. building an event chronology after observing model peaks;
2. searching regime subgroups to recover a rejected or unestablished signal.

The resulting contribution is not another event-labelled classifier. It is a protected evaluation architecture that separates regime construction, independent chronology, event alignment, baseline signal eligibility, conditional diagnostics, and permitted-use policy.
