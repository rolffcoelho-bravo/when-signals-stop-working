# Version 3 Realigned Gate Map

## Purpose

This map reconciles the frozen Version 3 implementation plan with the governed work on `research/v3-adaptive-signal-validity`.

Historical design and lock objects remain point-in-time evidence. This map controls current sequencing after the repository realignment decision.

## Research chain

```text
the practitioner's question
    ↓
Signal interpretation
    ↓
Matched benchmark comparison
    ↓
Predictive and economic establishment
    ↓
Conditional validity
    ↓
Prospective failure definition
    ↓
Failure probability
    ↓
Operational state and permitted action
```

Spectral, network, panic-consistent, and external-event evidence enter as supporting market-state information. They do not replace the signal-establishment chain.

## Core gate map

| Gate | Purpose | Current status | Advances the practitioner's question by |
|---|---|---|---|
| V3-0 | Design and product freeze | Complete | Defines the complete answer and product boundary |
| V3-1 | Canonical data and adapters | Complete and locked | Makes the answer reusable across conforming data |
| V3-2 | Causal features and spectral structure | Complete and locked | Supplies leakage-controlled market-structure context |
| V3-2B | Network and market-structure extension | Complete and locked | Adds topology, communities, MST, and dynamic descriptors |
| V3-3 | Panic-consistent probabilistic regime engine | Complete and locked | Supplies independent regime probabilities and uncertainty |
| **V3-4** | **Unified RSI and Bollinger Interpretation Engine** | **Authoritatively validated and locked** | **Defines the signal information to be tested** |
| **V3-5** | **Matched Benchmark-versus-Signal Forecast Selection** | **Approved; implementation started; contract frozen; target access not started** | **Determines whether signal information adds value** |
| V3-6 | Prospective failure-event definition | Not started | Defines what “stops working” means before modelling it |
| V3-7 | Failure-probability model | Not started | Estimates future breach risk for an established signal |
| V3-8 | Economic and operational decision engine | Not started | Converts evidence into governed permitted use |
| V3-9 | Methodology-locked final-framework evaluation | Not started; 2026 reserve protected | Produces untouched full-pipeline V3 evidence |
| V3-10 | External replication and transportability | Not started | Tests asset, venue, panel, and regime transportability |
| V3-11 | Reusable package and scoring workflow | Not started | Produces the model another user can operate |
| V3-12 | Final audit and institutional release | Not started | Makes the complete framework reproducible and citable |

Machine-readable core sequence identifiers:

```text
V3-4_SIGNAL_INTERPRETATION
V3-5_MATCHED_FORECAST_ESTABLISHMENT
V3-6_PROSPECTIVE_FAILURE_DEFINITION
V3-7_FAILURE_PROBABILITY
V3-8_DECISION_GOVERNANCE
V3-9_LOCKED_EVALUATION
V3-10_EXTERNAL_REPLICATION
V3-11_REUSABLE_SCORING_PACKAGE
V3-12_FINAL_RELEASE
```

## Final V3-4 boundary

The bounded Gate V3-4 registry expands deterministically to:

```text
48 registered specifications
44 base specifications
4 explicit regime interactions
2 training-only adaptive templates
```

Authoritative evidence:

```text
realignment tests: 7 passed
signal-engine tests: 19 passed
canonical source rows: 12171
feature rows: 584208
row-count identity: verified
validated implementation commit: ff2e7ecba3fa69f22e0b109437d23b52d30fba2b
evidence materialization commit: 705511de9e8ee22a9f8aff34506aebb6c26223e7
lock status: IMPLEMENTATION_VALIDATED_AND_LOCKED
```

V3-4 produced signal information only. It produced no predictive, economic, conditional-validity, deterioration, or failure-probability finding.

## Active Gate V3-5 boundary

Gate V3-5 is active under the fail-closed status:

```text
APPROVED_IMPLEMENTATION_STARTED_CONTRACT_FROZEN
target_accessed: false
development_model_fitting_started: false
signal_establishment_segment_accessed: false
final_framework_reserve_accessed: false
```

The contract is frozen in `configs/v3_g5_forecast_contract.json` before target access.

### Frozen data partition

```text
Development:
2021-01-01T00:00:00Z to 2025-06-30T20:00:00Z

Signal establishment:
2025-07-01T00:00:00Z to 2025-12-31T20:00:00Z

V3-9 final-framework reserve:
2026-01-01T00:00:00Z to 2026-07-22T08:00:00Z
```

V3-5 may not access the V3-9 reserve. Access before V3-9 is the fail-closed state:

```text
PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED
```

### Frozen analytical contract

```text
confirmatory target: direction
secondary targets: expected return and large-move probability
horizons: 4h, 8h, 12h, 24h, 48h, 72h
outer development folds: 5
inner selection folds: 3
primary one-way cost: 10 bps
cost sensitivity: 5 bps and 20 bps
confirmatory multiplicity: Holm 5%
secondary multiplicity: Benjamini-Hochberg q=0.10
```

For every admissible pair:

```text
candidate = benchmark information + registered signal information
```

Benchmark and candidate must otherwise share model class, rows, preprocessing, hyperparameter selection, calibration, target, horizon, cost treatment, and decision policy.

## Regime-validation extension

The chronology work remains a distinct extension because its primary object is validation of regime outputs against independent documentary evidence.

| Realigned identifier | Historical files | Purpose | Status |
|---|---|---|---|
| V3-RV1 | Historical `V3-4A` files | Freeze chronology independence and signal-use boundaries | Complete and historically locked |
| V3-RV2 | Historical `V3-4B` files | Compile documentary events, provenance, and uncertainty | Complete and historically locked; Windows checkout-portability revision open |
| V3-RV3 | Proposed historical `V3-4C` | Evaluate regime-event timing and false-alert burden | Paused; not started |

Historical names remain unchanged so old commits, checkpoints, hashes, and references remain auditable.

## Dependency rules

### V3-5 depends on

- the final V3-4 lock and 48-specification registry;
- matched benchmark and candidate identity;
- nested chronological development selection;
- predeclared targets, horizons, costs, and multiplicity rules;
- strict protection of the V3-9 final-framework reserve.

### V3-6 and V3-7 depend on

- at least one signal pipeline established by V3-5;
- a prospective deterministic failure definition;
- sufficient monitoring history and event support.

### V3-RV3 depends on

- a finalized V3-RV2 chronology package;
- a clear statement of which regime object is being validated;
- no threshold, model, panel, event, or boundary tuning after overlay.

V3-RV3 is not a prerequisite for V3-5 matched forecast selection.

## Stop rules

### Signal-family stop rule

When no pipeline for a signal family passes establishment:

```text
NO_PIPELINE_ADMITTED
or
NO_INCREMENTAL_EVIDENCE

then

FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED
DO_NOT_CLAIM_SIGNAL_DETERIORATION
```

### Final-reserve stop rule

Any Gate V3-5 access to the V3-9 reserve produces:

```text
PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED
```

### Failure-model stop rule

When prospective failure labels lack sufficient support, calibration, or discrimination:

```text
FAILURE_PROBABILITY_NOT_ESTABLISHED
REVALIDATION_REQUIRED
```

### Transportability stop rule

A SOL-only result cannot support a general crypto-market claim. General claims require predeclared cross-asset or cross-venue evidence.

## Documentation authority

The following hierarchy applies:

1. frozen Version 1 and Version 2 evidence and locks;
2. `V3_DESIGN_FREEZE.md` for Version 3 scientific identity;
3. `docs/V3_IMPLEMENTATION_PLAN.md` for the original core sequence;
4. `V3_REALIGNMENT_DECISION.md` for the correction of post-V3-3 gate use;
5. this map for current gate naming and dependencies;
6. `configs/v3_realignment_contract.json` for machine-readable current status;
7. gate-specific contracts, tests, checkpoints, and locks.

No lower-level checkpoint may redefine a higher-level research question.

## Immediate next action

```text
VALIDATE_V3_5_FROZEN_CONTRACT
THEN_IMPLEMENT_TARGET_FOLD_BENCHMARK_AND_MATCHED_SELECTION_ENGINES
```

Target generation, model fitting, and establishment access remain prohibited until the contract verifier and tests pass in the authoritative research environment.
