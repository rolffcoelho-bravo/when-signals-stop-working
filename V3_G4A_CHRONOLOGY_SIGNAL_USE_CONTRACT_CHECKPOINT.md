# Gate V3-4A — Independent Chronology and Signal-Use Eligibility Checkpoint

## Gate status

> `INDEPENDENT_CHRONOLOGY_AND_SIGNAL_USE_CONTRACT_COMPLETE_AND_LOCKED`

Gate V3-4A is implemented, validated, and locked. It freezes the scientific, chronological, statistical, and model-risk rules that must govern all later external-event validation and conditional signal-use analysis.

No external chronology was compiled, no Gate V3-3 probability was inspected, and no conditional RSI or Bollinger analysis was executed during this subgate.

## Repository position

- frozen baseline release: `v2.0.0`;
- frozen baseline commit: `5a07299367b80c3940e652e7bbdd208ce86ba5ef`;
- branch: `research/v3-adaptive-signal-validity`;
- parent gate: `V3-3`;
- parent lock: `V3_G3_PANIC_REGIME_LOCK.json`;
- parent lock blob: `0e35908c03e36d8caeb832a078ff0566ef4e2ea4`;
- validated core commit: `b4f9f03a09b268eb6359265dd133df3eddeb5e0e`;
- lock preparation commit: `e8e3833b0e6a8524a4c03e912d2c9ebd36e98b87`;
- V3-4A lock commit: `c340f626a105b986584d561eb58f5f5d21d5510d`;
- V3-4A lock: `V3_G4A_CHRONOLOGY_SIGNAL_USE_CONTRACT_LOCK.json`;
- V3-4A lock blob: `736991b5425d603fc43a5f19c217307fa0f11b41`.

## Status distinctions

| Dimension | Status | Evidence |
|---|---|---|
| Gate V3-3 parent | Locked | Blob `0e35908c03e36d8caeb832a078ff0566ef4e2ea4` |
| Gate V3-4A approval | Approved | User authorization for Gate V3-4 |
| Contract design | Implemented | JSON contract and Python validator |
| Isolated contract validation | Validated | 14 tests passed |
| Tested object identity | Validated | Three tested blobs equal repository blobs |
| Chronology compilation | Not started | Model-output access remains prohibited |
| Event alignment | Not started | Requires locked V3-4B chronology |
| RSI/Bollinger conditional diagnostics | Not started | Descriptive-only eligibility remains frozen |
| Gate V3-4A lock | Locked | Blob `736991b5425d603fc43a5f19c217307fa0f11b41` |
| Next subgate | V3-4B | Chronology compilation and provenance lock |

## Implementation inventory

Gate V3-4A adds:

```text
configs/v3_external_chronology_signal_use_contract.json
src/shockbridge_signal_validity/v3/chronology_signal_use_contract.py
tests/test_v3_external_chronology_signal_use_contract.py
scripts/validate_v3_g4a_contract.py
scripts/verify_v3_g4a_contract_lock.py
RUN_V3_G4A_CONTRACT.ps1
RUN_V3_G4A_CONTRACT.sh
docs/V3_EXTERNAL_CHRONOLOGY_SIGNAL_USE_CONTRACT.md
V3_G4A_CHRONOLOGY_SIGNAL_USE_CONTRACT_LOCK.json
V3_G4A_CHRONOLOGY_SIGNAL_USE_CONTRACT_CHECKPOINT.md
```

`Findings.md` was updated with only the implemented and validated V3-4A methodological contributions.

## Execution and test evidence

The isolated test suite executed against exact tested blobs:

```text
contract blob: 2d96c0d193343d2e7cb0cb4523cf8e3056b166fe
validator blob: 4e91e8a8dc289bffd651ae68d5dce46eb3ae5d19
test blob: f60a18a10383a7056f771e006db33f78ce8b7ce3
```

Result:

```text
14 passed in 0.04s
```

The tests establish:

1. exact parent V3-3 lock binding;
2. immutability of Version 1 and Version 2 determinations;
3. immutability of Gate V3-3 models, thresholds, and protected objects;
4. chronology compilation before model-output overlay;
5. prohibition on model-derived event inclusion;
6. prohibition on retrospective event deletion or boundary tuning;
7. explicit recognition that chronology is incomplete validation evidence, not complete ground truth;
8. fixed registered models and 1, 3, 6, and 12 observation horizons;
9. prohibition on chronology-driven threshold or model selection;
10. RSI status preserved as `NO_PIPELINE_ADMITTED`;
11. Bollinger status preserved as `NO_INCREMENTAL_EVIDENCE`;
12. both signals remain ineligible for conditional degradation claims;
13. Holm multiplicity control and negative-result retention;
14. fail-closed mutation handling for core governance violations.

## Scientific contract

### Primary question

Do pre-existing Gate V3-3 probabilities and causal state transitions align with independently documented market dislocations when the chronology is compiled without access to model outputs?

### Secondary question

Does independently inferred market state change the admissible interpretation or permitted use of a technical signal without revising its frozen unconditional verdict?

## Chronology independence boundary

The chronology must be compiled and locked before any model-output overlay.

The following are prohibited during V3-4A and V3-4B:

```text
model-output inspection
model-derived event inclusion
chronology-driven threshold selection
chronology-driven model selection
retrospective event deletion
retrospective event-boundary tuning
```

This prevents the chronology from becoming a post hoc reconstruction around probability peaks or preferred transitions.

## Chronology claim boundary

The chronology is not treated as a complete supervised panic label.

It may contain:

- undocumented missing events;
- uncertain event boundaries;
- conflicting sources;
- heterogeneous timestamp precision;
- differences in event severity definitions.

Consequently, classification metrics are prohibited unless a later gate establishes sufficient registry completeness. Event overlap cannot by itself establish causal attribution.

## Frozen event taxonomy

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

Each event must carry auditable source, timestamp, severity, documentation, precision, boundary-uncertainty, and merge information.

## Registered event-alignment design

The two probability models remain separately reported:

```text
MONOTONE_MECHANISM_SCORE_V1
CAUSAL_GAUSSIAN_HMM_V1
```

The transparent challenger remains separately visible but is not converted into a panic probability.

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

The metrics cannot select a model, create a champion, or authorize a consensus probability.

## Signal-use eligibility result

Gate V3-4A formalizes a strict prerequisite:

> Conditional degradation can be tested only when unconditional incremental value was established before regime access under a frozen contract.

The current signals therefore remain:

| Signal | Frozen Version 2 status | Conditional eligibility | Permitted scope |
|---|---|---|---|
| RSI | `NO_PIPELINE_ADMITTED` | `INELIGIBLE_BASELINE_NOT_ESTABLISHED` | `DESCRIPTIVE_REGIME_SENSITIVITY_ONLY` |
| Bollinger | `NO_INCREMENTAL_EVIDENCE` | `INELIGIBLE_BASELINE_NOT_ESTABLISHED` | `DESCRIPTIVE_REGIME_SENSITIVITY_ONLY` |

This prevents favourable regime subgroups from being used to rescue either signal.

## Permitted-use states

The contract registers:

```text
UNASSESSED
RESEARCH_DIAGNOSTIC_ONLY
NO_CHANGE_SUPPORTED
RESTRICTED_USE
SUSPEND_USE
```

`RESTRICTED_USE` and `SUSPEND_USE` require an established unconditional baseline and a predeclared, statistically supported loss of reliability. The current RSI and Bollinger specifications cannot enter those states.

## Conditional diagnostic boundaries

Later diagnostics must preserve:

- frozen signal parameters;
- no signal retraining or retuning;
- frozen Gate V3-3 thresholds;
- chronological evaluation;
- dependence-aware inference;
- minimum 50 observations per regime;
- minimum five regime episodes;
- `INSUFFICIENT_CONDITIONAL_EVIDENCE` when boundaries are not met.

For current RSI and Bollinger specifications, all results remain descriptive.

## Multiplicity and reporting

The contract requires:

- predeclared primary hypotheses;
- Holm family-wise adjustment;
- raw and adjusted results;
- dependence-aware confidence intervals;
- all registered models and horizons;
- retention of negative and insufficient results;
- prohibition on favourable subgroup suppression.

## Required V3-4 outputs

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

These are programme-level outputs. Gate V3-4A creates only the governing contract and does not claim that these empirical outputs exist yet.

## Methodological results

### Result 1 — Chronology independence becomes enforceable

The external event list can no longer be assembled after observing model peaks without violating a protected contract.

### Result 2 — Event alignment is separated from supervised classification

Incomplete chronology can support timing and burden diagnostics without being misrepresented as a complete binary target.

### Result 3 — Baseline eligibility prevents regime-conditioned rescue

A signal cannot be declared degraded, restricted, or suspended when unconditional usefulness was never established. The same rule prevents a favourable regime subset from promoting an unestablished signal.

### Result 4 — Decision-use policy becomes a separate scientific layer

Signal prediction, regime inference, event validation, and permitted use are distinct objects. This separation is central to the publication and institutional value of the framework.

## Scientific assessment

V3-4A substantially strengthens the research design because it closes the largest remaining pathway for retrospective bias: constructing external events and conditional signal claims after seeing the regime results.

The design is more rigorous than a conventional crisis-event study because it combines:

1. an independently compiled chronology;
2. frozen regime models and thresholds;
3. explicit chronology incompleteness;
4. fixed event-alignment metrics;
5. baseline signal eligibility;
6. multiplicity control;
7. a governed signal-use policy.

## Model-risk assessment

### Chronology incompleteness

Documented events are not a full inventory of stress. False-alert burden must therefore be reported cautiously because some apparent non-event alerts may correspond to undocumented dislocations.

### Source conflict

Conflicting boundaries remain visible and are excluded from primary timing metrics until adjudicated without model access.

### Model disagreement

The monotone and HMM probabilities remain distinct. Event alignment cannot be used to select one model or average them.

### Subgroup risk

Conditional signal results are particularly vulnerable to small samples, overlapping episodes, dependence, and favourable subgroup selection. The frozen sample and episode boundaries are therefore mandatory.

### Interpretation risk

Descriptive regime sensitivity for RSI or Bollinger is not evidence of predictive value, degradation, or recovery.

## Perceived-value and problem-solving opportunities

### Independent model validation

The chronology layer creates a credible validation product for model-risk, treasury, trading-risk, exchange, and market-surveillance settings because event evidence is structurally separated from model construction.

### Signal permissioning

The eligibility and use-state architecture can later support governed policies describing when a validated signal may be used normally, restricted, or suspended.

### Audit-ready event provenance

The required provenance and merge logs create a reusable event registry suitable for replication, external review, and later expansion across assets and venues.

### Publication value

The principal novelty is not merely conditioning indicators on regimes. It is the protected separation of unconditional signal establishment, independent regime inference, chronology validation, conditional diagnostics, and permitted-use decisions.

## Final judgment

Gate V3-4A is approved, implemented, validated, and locked.

No empirical event-alignment result is claimed. No chronology was compiled. No model output was accessed. No RSI or Bollinger verdict changed.

## Next subgate

Proceed to Gate V3-4B only from the lock blob:

```text
736991b5425d603fc43a5f19c217307fa0f11b41
```

Gate V3-4B must compile and lock the external chronology and provenance package while model-output access remains prohibited.
