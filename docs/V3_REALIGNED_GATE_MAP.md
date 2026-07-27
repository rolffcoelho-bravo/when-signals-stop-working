# Version 3 Realigned Gate Map

## Purpose

This map reconciles the frozen Version 3 implementation plan with the work currently present on `research/v3-adaptive-signal-validity`.

The historical design and lock objects remain available as point-in-time evidence. This map controls current sequencing after the repository realignment decision.

## Research chain

```text
Richard's question
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

| Gate | Purpose | Current status | Advances Richard's question by |
|---|---|---|---|
| V3-0 | Design and product freeze | Complete | Defines the complete answer and product boundary |
| V3-1 | Canonical data and adapters | Complete | Makes the answer reusable across conforming data |
| V3-2 | Causal features and spectral structure | Complete | Supplies leakage-controlled market-structure context |
| V3-2B | Network and market-structure extension | Complete | Adds topology, communities, MST, and dynamic descriptors |
| V3-3 | Panic-consistent probabilistic regime engine | Complete | Supplies independent regime probabilities and uncertainty |
| **V3-4** | **Unified RSI and Bollinger interpretation engine** | **Reopened; next core gate** | **Defines the signal information to be tested** |
| V3-5 | Matched forecast selection | Not started | Determines whether signal information adds value |
| V3-6 | Prospective failure-event definition | Not started | Defines what “stops working” means before modelling it |
| V3-7 | Failure-probability model | Not started | Estimates future breach risk for an established signal |
| V3-8 | Economic and operational decision engine | Not started | Converts evidence into governed permitted use |
| V3-9 | Methodology-locked evaluation | Not started | Produces untouched confirmatory V3 evidence |
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

## Regime-validation extension

The chronology work is retained under a distinct extension because its primary object is validation of regime outputs against independent documentary evidence.

| Realigned identifier | Historical files | Purpose | Status |
|---|---|---|---|
| V3-RV1 | Historical `V3-4A` files | Freeze chronology independence and signal-use boundaries | Complete and historically locked |
| V3-RV2 | Historical `V3-4B` files | Compile documentary events, provenance, and uncertainty | Complete and historically locked; Windows checkout-portability revision open |
| V3-RV3 | Proposed historical `V3-4C` | Evaluate regime-event timing and false-alert burden | Paused; not started |

The historical names remain unchanged so old commits, checkpoints, hashes, and references remain auditable.

## Dependency rules

### V3-4 depends on

- V3-1 canonical data contract;
- causal OHLCV features;
- optional V3-2/V3-3 market-state features only through registered interfaces;
- target-blind signal construction;
- a bounded signal registry.

V3-4 does not depend on external chronology.

### V3-5 depends on

- the completed and locked V3-4 signal registry and implementation;
- matched benchmark and candidate identity;
- nested chronological development selection;
- predeclared targets, horizons, costs, and multiplicity rules.

### V3-6 and V3-7 depend on

- at least one signal pipeline established by V3-5 and later confirmed in the appropriate locked evaluation;
- a prospective, deterministic failure definition;
- sufficient monitoring history and event support.

### V3-RV3 depends on

- a finalized V3-RV2 chronology package;
- a clear statement of which regime object is being validated;
- no threshold, model, panel, event, or boundary tuning after overlay.

V3-RV3 is not a prerequisite for constructing the V3-4 signal engine.

## Stop rules

### Signal-family stop rule

When no pipeline for a signal family passes establishment:

```text
NO_ESTABLISHED_SIGNAL
FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED
DO_NOT_CLAIM_SIGNAL_DETERIORATION
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

The following hierarchy applies to current development:

1. frozen Version 1 and Version 2 evidence and locks;
2. `V3_DESIGN_FREEZE.md` for Version 3 scientific identity;
3. `docs/V3_IMPLEMENTATION_PLAN.md` for the original core sequence;
4. `V3_REALIGNMENT_DECISION.md` for the correction of post-V3-3 gate use;
5. this map for current gate naming and dependencies;
6. gate-specific contracts, tests, checkpoints, and locks.

No lower-level checkpoint may redefine a higher-level research question.
