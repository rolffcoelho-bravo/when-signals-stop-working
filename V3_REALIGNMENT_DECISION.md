# Version 3 Repository Realignment Decision

## Gate identity

```text
Gate: V3-REALIGNMENT
Status: RESEARCH_QUESTION_AND_GATE_SEQUENCE_REALIGNED
Branch: research/v3-adaptive-signal-validity
Frozen baseline: v2.0.0
Baseline commit: 5a07299367b80c3940e652e7bbdd208ce86ba5ef
```

## Reason for the gate

A full repository review found that Version 3 correctly implemented its canonical data, spectral, network, and panic-consistent regime layers, but then diverged from the frozen implementation sequence.

The frozen plan defined Gate V3-4 as the **Unified RSI and Bollinger Interpretation Engine**. Historical development instead used the V3-4A and V3-4B labels for external chronology governance and compilation, with a proposed V3-4C event-alignment evaluation.

The chronology work remains valid supporting research, but it does not implement the signal engine, matched forecast engine, failure definition, failure-probability model, or operational decision layer required to answer the practitioner's question.

## Research anchor restored

The controlling practical question is:

> Did RSI or Bollinger Bands establish incremental predictive and economic value, under which conditions, and—only after establishment—when is that contribution deteriorating or likely to fail?

The frozen earlier answer remains:

```text
RSI Version 2: NO_PIPELINE_ADMITTED
Bollinger Version 2: NO_INCREMENTAL_EVIDENCE
Signal deterioration claim: INADMISSIBLE_BASELINE_NOT_ESTABLISHED
Failure-probability claim: INADMISSIBLE_BASELINE_NOT_ESTABLISHED
```

No Version 1 or Version 2 result is changed by the realignment.

## Historical chronology work preserved and reclassified

Historical file names, lock blobs, checkpoints, tests, source registries, and evidence outputs remain unchanged for auditability.

| Historical identifier | Realigned scientific classification | Status |
|---|---|---|
| `V3-4A` chronology and signal-use contract | `V3-RV1` independent regime-validation contract | Complete and historically locked |
| `V3-4B` chronology compilation and provenance | `V3-RV2` independent chronology and provenance | Complete and historically locked; portability revision open |
| Proposed `V3-4C` event alignment | `V3-RV3` regime-event alignment | Paused and not started |

`RV` means `REGIME_VALIDATION`. This reclassification does not rename historical files or rewrite historical lock objects.

## Current core sequence

```text
V3-0   Design and product freeze                         COMPLETE
V3-1   Canonical data and adapter layer                 COMPLETE AND LOCKED
V3-2   Causal feature and spectral engine               COMPLETE AND LOCKED
V3-2B  Market-structure extension                       COMPLETE AND LOCKED
V3-3   Panic-consistent probabilistic regime engine     COMPLETE AND LOCKED
V3-4   Unified RSI and Bollinger Interpretation Engine  VALIDATED AND LOCKED
V3-5   Matched benchmark-versus-signal forecast engine  APPROVED / CONTRACT FROZEN / IMPLEMENTATION STARTED
V3-6   Prospective failure-event and monitoring layer   NOT STARTED
V3-7   Signal-validity and failure-probability model     NOT STARTED
V3-8   Economic and operational decision engine         NOT STARTED
V3-9   Methodology-locked final-framework evaluation    NOT STARTED
V3-10  External replication and transportability        NOT STARTED
V3-11  Reusable package and scoring workflow            NOT STARTED
V3-12  Final audit and institutional release            NOT STARTED
```

The regime-validation extension remains supporting evidence:

```text
V3-RV1 Independent regime-validation contract           COMPLETE
V3-RV2 Independent chronology and provenance             COMPLETE / PORTABILITY REVISION OPEN
V3-RV3 Regime-event alignment                            PAUSED
```

## Gate V3-4 final determination

The Unified RSI and Bollinger Interpretation Engine is complete and locked.

```text
registered specifications: 48
base specifications: 44
explicit regime interactions: 4
training-only adaptive templates: 2
bounded maximum: 128
exact hardened Windows suite: 19 passed
canonical source rows: 12171
feature rows: 584208
row-count identity: verified
validated implementation commit: ff2e7ecba3fa69f22e0b109437d23b52d30fba2b
evidence materialization commit: 705511de9e8ee22a9f8aff34506aebb6c26223e7
lock status: IMPLEMENTATION_VALIDATED_AND_LOCKED
```

Gate V3-4 generated no predictive, economic, conditional-validity, deterioration, or failure claim. Its locked output is the bounded signal information set consumed by Gate V3-5.

## Gate V3-5 active boundary

Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection — is approved and has begun at its contract-freeze stage.

```text
contract: configs/v3_g5_forecast_contract.json
scope: docs/V3_G5_MATCHED_FORECAST_SCOPE.md
implementation started: true
target access: false
development model fitting: false
signal-establishment segment access: false
V3-9 final-framework reserve access: false
```

The Gate V3-5 partition is frozen as:

```text
Development selection:
2021-01-01T00:00:00Z to 2025-06-30T20:00:00Z

Signal-establishment segment:
2025-07-01T00:00:00Z to 2025-12-31T20:00:00Z

V3-9 final-framework reserve:
2026-01-01T00:00:00Z to 2026-07-22T08:00:00Z
```

The reserve is not historically unseen because prior governed versions used the same frozen snapshot. It is nevertheless inaccessible to V3-5 selection and signal establishment.

## Matched forecast rule

For every Gate V3-5 comparison:

```text
candidate = benchmark information + registered signal information
```

Benchmark and candidate must otherwise share model class, rows, preprocessing, hyperparameter selection, calibration, target, horizon, decision policy, and transaction costs.

Gate V3-5 includes the continuity horizons 4, 8, 12, and 24 hours plus the declared Version 3 horizons 48 and 72 hours. Direction is confirmatory; expected return and large-move probability are secondary.

## Establishment stop rule

When no Version 3 RSI or Bollinger family passes development admission or the frozen establishment segment:

```text
NO_PIPELINE_ADMITTED
or
NO_INCREMENTAL_EVIDENCE

then

FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED
```

Spectral, network, panic-consistent, and chronology components may continue as separate market-regime research, but they cannot be presented as an answer to when a rejected signal stopped working.

## Governance proportionality rule

Future governance work must be proportional to the scientific gate it protects. No lock-lineage, ownership, checkpoint, or portability layer may become a separate research gate unless its absence prevents execution or invalidates a core empirical claim.

## Authoritative supporting documents

```text
PRACTITIONER_QUESTION.md
DIRECT_ANSWER_LOGIC.md
docs/V3_REALIGNED_GATE_MAP.md
docs/V3_G4_SIGNAL_ENGINE_SCOPE.md
docs/V3_G4_SIGNAL_ENGINE.md
V3_G4_SIGNAL_ENGINE_CHECKPOINT.md
V3_G4_SIGNAL_ENGINE_LOCK.json
docs/V3_G5_MATCHED_FORECAST_SCOPE.md
V3_G5_MATCHED_FORECAST_CHECKPOINT.md
configs/v3_g5_forecast_contract.json
configs/v3_realignment_contract.json
ROADMAP.md
```

## Current action

Validate the frozen Gate V3-5 contract and then implement the target, partition, fold, benchmark, matched-candidate, development-selection, pipeline-freeze, establishment-authorization, inference, and determination layers.

The paused `V3-RV3` event-alignment study may resume only after the core signal-establishment and final-framework sequence reaches an appropriate external-validation boundary.
