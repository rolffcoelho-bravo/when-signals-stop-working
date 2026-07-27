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

The frozen plan defined Gate V3-4 as the unified RSI and Bollinger interpretation engine. The active branch instead used the V3-4A and V3-4B labels for external chronology governance and compilation, with a proposed V3-4C event-alignment evaluation.

The chronology work is valid supporting research, but it does not implement the signal engine, matched forecast engine, failure definition, failure-probability model, or operational decision layer required to answer Richard's question.

## Research anchor restored

The controlling practical question is:

> Did RSI or Bollinger Bands establish incremental predictive and economic value, under which conditions, and—only after establishment—when is that contribution deteriorating or likely to fail?

The current frozen answer remains:

```text
RSI Version 2: NO_PIPELINE_ADMITTED
Bollinger Version 2: NO_INCREMENTAL_EVIDENCE
Signal deterioration claim: INADMISSIBLE_BASELINE_NOT_ESTABLISHED
Failure-probability claim: INADMISSIBLE_BASELINE_NOT_ESTABLISHED
```

No Version 1 or Version 2 result is changed by this realignment.

## Historical chronology work preserved and reclassified

Historical file names, lock blobs, checkpoints, tests, source registries, and evidence outputs remain unchanged for auditability. Their scientific role is reclassified as a separate regime-validation extension:

| Historical identifier | Realigned scientific classification | Status |
|---|---|---|
| `V3-4A` chronology and signal-use contract | `V3-RV1` independent regime-validation contract | Complete and historically locked |
| `V3-4B` chronology compilation and provenance | `V3-RV2` independent chronology and provenance | Complete and historically locked, subject to the active Windows checkout-portability revision |
| Proposed `V3-4C` event alignment | `V3-RV3` regime-event alignment | Paused and not started |

`RV` means `REGIME_VALIDATION`. This reclassification does not rename historical files or rewrite historical lock objects.

## True core sequence restored

The controlling Version 3 sequence is:

```text
V3-0   Design and product freeze                         COMPLETE
V3-1   Canonical data and adapter layer                 COMPLETE
V3-2   Causal feature and spectral engine               COMPLETE
V3-2B  Market-structure extension                       COMPLETE
V3-3   Panic-consistent probabilistic regime engine     COMPLETE
V3-4   Unified RSI and Bollinger interpretation engine  IMPLEMENTED / VALIDATION PENDING
V3-5   Matched benchmark-versus-signal forecast engine  NOT STARTED
V3-6   Prospective failure-event and monitoring layer   NOT STARTED
V3-7   Signal-validity and failure-probability model     NOT STARTED
V3-8   Economic and operational decision engine         NOT STARTED
V3-9   Methodology-locked evaluation                    NOT STARTED
V3-10  External replication and transportability        NOT STARTED
V3-11  Reusable package and scoring workflow            NOT STARTED
V3-12  Final audit and institutional release            NOT STARTED
```

The regime-validation extension is supporting evidence and cannot displace the core sequence:

```text
V3-RV1 Independent regime-validation contract           COMPLETE
V3-RV2 Independent chronology and provenance             COMPLETE / PORTABILITY REVISION OPEN
V3-RV3 Regime-event alignment                            PAUSED
```

## True Gate V3-4 implementation

The true V3-4 implementation now exists as a bounded, reproducible, target-blind signal-information engine.

```text
registered specifications: 48
base specifications: 44
explicit regime interactions: 4
training-only adaptive templates: 2
bounded maximum: 128
controlled development tests: 19 passed
authoritative Windows validation: pending
lock: not created
```

### RSI family

- overbought and oversold mean reversion;
- overbought and oversold continuation;
- threshold crossings;
- threshold duration and persistence;
- level, slope, acceleration, and rolling range;
- causal price-RSI divergence;
- training-only adaptive thresholds where predeclared.

### Bollinger family

- upper- and lower-band mean reversion;
- upper breakout and lower breakdown;
- percentage-B and normalized band distance;
- bandwidth level, change, and acceleration;
- squeeze and post-squeeze transition;
- persistence outside the bands and re-entry timing;
- training-only adaptive squeeze thresholds where predeclared.

### Registered market-state interactions

```text
RSI oversold mean reversion × p_range
RSI overbought continuation × p_trend
Bollinger lower breakdown × p_panic_consistent
Bollinger post-squeeze expansion × dominant_eigenvalue_share
```

Every interaction preserves its base signal and context values separately. Missing context and missing training-only adaptive parameters remain explicit ineligibility states.

### Gate boundary

Gate V3-4 generates signal information only. It may not:

- select a winning signal using future or locked-evaluation outcomes;
- claim predictive or economic value;
- promote RSI or Bollinger to an operational status;
- use chronology to tune parameters;
- estimate signal-failure probability;
- rewrite Version 1 or Version 2 results.

## Establishment stop rule

After Gate V3-5, if no Version 3 RSI or Bollinger pipeline passes the complete establishment standard, the signal-failure programme must stop for that family.

```text
FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED
```

The spectral, network, panic-consistent, and chronology components may continue as a separate market-regime research contribution, but they cannot be presented as an answer to when a rejected signal stopped working.

## Governance proportionality rule

Future governance work must be proportional to the scientific gate it protects. No new lock-lineage, ownership, checkpoint, or portability layer may become a separate research gate unless its absence prevents execution or invalidates a core empirical claim.

## Authoritative supporting documents

```text
RICHARD_QUESTION.md
DIRECT_ANSWER_LOGIC.md
docs/V3_REALIGNED_GATE_MAP.md
docs/V3_G4_SIGNAL_ENGINE_SCOPE.md
docs/V3_G4_SIGNAL_ENGINE.md
V3_G4_SIGNAL_ENGINE_CHECKPOINT.md
configs/v3_realignment_contract.json
ROADMAP.md
```

## Current action

Authoritatively validate the corrected realignment and the implemented V3-4 signal engine on the Windows research environment, review the real canonical-data manifests and tracked working-tree state, and then create the V3-4 lock only if all evidence passes.

The paused `V3-RV3` event-alignment study may resume only after the core signal-establishment sequence reaches an appropriate external-validation boundary. Gate V3-5 remains not started and requires separate approval after V3-4 validation and lock.
