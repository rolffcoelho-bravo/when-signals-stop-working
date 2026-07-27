# Version 3 Repository Realignment Checkpoint

## Status

```text
IMPLEMENTATION_COMPLETE_VALIDATION_PENDING
```

The repository realignment package is committed. It has not yet received authoritative local execution evidence from the Windows research environment and is therefore not locked.

## Implementation boundary

```text
Branch: research/v3-adaptive-signal-validity
Implementation boundary before checkpoint: 6c0ee34c33d5f101d99c1e3ec2b9b0f9bcb19d24
Frozen Version 2 baseline: 5a07299367b80c3940e652e7bbdd208ce86ba5ef
```

## What was corrected

1. Richard's original question is restored at repository root.
2. The direct-answer hierarchy is explicit: establishment precedes conditional validity, deterioration, failure probability, and operational action.
3. Frozen Version 1 and Version 2 determinations remain unchanged.
4. Historical chronology work is preserved but reclassified as `V3-RV1` and `V3-RV2` regime-validation evidence.
5. Proposed event alignment is reclassified as `V3-RV3`, paused, and not started.
6. The true Gate V3-4 is restored as the Unified RSI and Bollinger Interpretation Engine.
7. The roadmap and README now distinguish supporting regime infrastructure from the signal-validity and signal-failure chain.
8. A machine-readable contract, verifier, tests, and portable runners prevent silent gate drift.

## Files introduced

```text
RICHARD_QUESTION.md
DIRECT_ANSWER_LOGIC.md
V3_REALIGNMENT_DECISION.md
V3_REALIGNMENT_CHECKPOINT.md
RUN_V3_REALIGNMENT.ps1
RUN_V3_REALIGNMENT.sh
configs/v3_realignment_contract.json
docs/V3_REALIGNED_GATE_MAP.md
docs/V3_G4_SIGNAL_ENGINE_SCOPE.md
scripts/verify_v3_realignment.py
tests/test_v3_realignment_contract.py
```

## Files realigned

```text
README.md
ROADMAP.md
```

## Historical objects deliberately unchanged

The realignment does not rename or rewrite historical chronology locks, checkpoints, registries, evidence outputs, or frozen Version 1 and Version 2 determinations.

The historical identifiers remain auditable:

```text
V3-4A → scientifically reclassified as V3-RV1
V3-4B → scientifically reclassified as V3-RV2
V3-4C → proposed work reclassified as V3-RV3 and paused
```

## Validation suite

The isolated suite contains seven tests covering:

1. restoration of Richard's question and the frozen answer;
2. reopening of the true V3-4 without predictive or failure claims;
3. chronology reclassification without rewriting history;
4. core sequence ordering from signal interpretation to failure probability;
5. required-document existence and cross-references;
6. fail-closed governance controls;
7. execution of the standalone realignment verifier.

## Required local execution

```powershell
.\RUN_V3_REALIGNMENT.ps1
```

The runner temporarily clears process-level `PYTHONNOUSERSITE`, executes the seven tests, runs the standalone verifier, and restores the previous environment value.

## Expected result

```text
7 passed
Version 3 repository realignment verification passed.
Richard question restored: True
Frozen V1/V2 determinations modified: False
Historical chronology work reclassified: V3-RV1/V3-RV2
Event alignment: V3-RV3 PAUSED_NOT_STARTED
True next core gate: V3-4 — Unified RSI and Bollinger Interpretation Engine
True V3-4 implementation started: False
```

## Lock boundary

No realignment lock may be created until:

- the seven tests pass in the research environment;
- the standalone verifier passes;
- `git status` contains no tracked modification caused by the runner;
- the final committed file identities are reviewed;
- the checkpoint is revised with the authoritative validation evidence.

## Next core gate

After realignment validation and lock:

> Gate V3-4 — Unified RSI and Bollinger Interpretation Engine

Its approved scope is frozen in `docs/V3_G4_SIGNAL_ENGINE_SCOPE.md`. Implementation has not started at this checkpoint.
