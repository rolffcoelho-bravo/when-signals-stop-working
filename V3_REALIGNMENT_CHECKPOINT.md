# Version 3 Repository Realignment Checkpoint

## Status

```text
CORRECTION_IMPLEMENTED
WINDOWS_REVALIDATION_PENDING
V3_4_IMPLEMENTATION_COMPLETE_VALIDATION_PENDING
```

The repository realignment package is committed. Its first authoritative Windows execution exposed one exact-token mismatch in the standalone verifier. That defect has been corrected, and the approved true V3-4 signal engine has subsequently been implemented. The realignment and V3-4 remain unlocked until the updated suites pass in the Windows research environment.

## Baseline and branch

```text
Branch: research/v3-adaptive-signal-validity
Frozen Version 2 baseline: 5a07299367b80c3940e652e7bbdd208ce86ba5ef
Original realignment checkpoint commit: d2a65ab60199dbfcb6a79daebd412b535acb572d
Exact-token remediation commit: 44c2b61c8ca2ad2fb3bce330ca0640fc3ae92d36
```

## What was corrected

1. Richard's original question is restored at repository root.
2. The direct-answer hierarchy is explicit: establishment precedes conditional validity, deterioration, failure probability, and operational action.
3. Frozen Version 1 and Version 2 determinations remain unchanged.
4. Historical chronology work is preserved but reclassified as `V3-RV1` and `V3-RV2` regime-validation evidence.
5. Proposed event alignment is reclassified as `V3-RV3`, paused, and not started.
6. The true Gate V3-4 is restored as the Unified RSI and Bollinger Interpretation Engine.
7. The roadmap and README distinguish supporting regime infrastructure from the signal-validity and signal-failure chain.
8. A machine-readable contract, verifier, tests, and portable runners prevent silent gate drift.

## First Windows execution evidence

The initial authoritative run produced:

```text
6 passed
1 failed
```

The failing assertion was:

```text
Required phrase missing from DIRECT_ANSWER_LOGIC.md: ESTABLISHMENT
```

The scientific logic was already present, but the standalone verifier required the exact uppercase governance token. `DIRECT_ANSWER_LOGIC.md` was corrected to include the explicit machine-readable hierarchy:

```text
ESTABLISHMENT
CONDITIONAL_VALIDITY
DETERIORATION
FAILURE_PROBABILITY
OPERATIONAL_ACTION
```

The verifier was not weakened. The exact-token contract remains enforced.

## V3-4 advancement after approval

The true Gate V3-4 has now advanced to:

```text
IMPLEMENTATION_COMPLETE_VALIDATION_PENDING
```

Its implemented boundary is:

```text
registered specifications: 48
base specifications: 44
explicit regime interactions: 4
training-only adaptive templates: 2
development tests passed: 19
automatic selection performed: false
target accessed: false
chronology accessed: false
predictive/economic/deterioration/failure claims: false
lock created: false
```

The realignment contract and verifier now correctly require V3-4 implementation to be present while still rejecting any premature validation, lock, or empirical claim.

## Historical objects deliberately unchanged

The realignment does not rename or rewrite historical chronology locks, checkpoints, registries, evidence outputs, or frozen Version 1 and Version 2 determinations.

```text
V3-4A → scientifically reclassified as V3-RV1
V3-4B → scientifically reclassified as V3-RV2
V3-4C → proposed work reclassified as V3-RV3 and paused
```

## Updated realignment validation suite

The seven tests now cover:

1. restoration of Richard's question and the frozen answer;
2. implemented V3-4 status without predictive or failure claims;
3. chronology reclassification without rewriting history;
4. core sequence ordering from signal interpretation to failure probability;
5. required realignment and V3-4 implementation files;
6. fail-closed governance controls;
7. execution of the updated standalone realignment verifier.

## Required authoritative execution

```powershell
.\RUN_V3_REALIGNMENT.ps1
.\RUN_V3_G4_SIGNAL_ENGINE.ps1
```

Expected realignment evidence:

```text
7 passed
Version 3 repository realignment verification passed.
Richard question restored: True
Frozen V1/V2 determinations modified: False
Historical chronology work reclassified: V3-RV1/V3-RV2
Event alignment: V3-RV3 PAUSED_NOT_STARTED
Current core gate: V3-4 — Unified RSI and Bollinger Interpretation Engine
True V3-4 implementation started: True
True V3-4 status: IMPLEMENTATION_COMPLETE_VALIDATION_PENDING
Registered signal specifications: 48
```

Expected Gate V3-4 evidence:

```text
19 passed
Gate V3-4 unified RSI and Bollinger signal engine passed.
Registered signals: 48
Automatic selection performed: False
Target accessed: False
Chronology accessed: False
Predictive/economic/failure claims produced: False
Next core gate: V3-5
```

## Lock boundary

No realignment or Gate V3-4 lock may be created until:

- the updated seven-test realignment suite passes;
- the standalone realignment verifier passes;
- all 19 isolated V3-4 tests pass;
- the real canonical data generates the complete Gate V3-4 output package;
- feature rows equal canonical source rows multiplied by 48;
- `git status` contains no tracked modification caused by either runner;
- output hashes and final committed file identities are reviewed;
- the realignment and V3-4 checkpoints are revised with authoritative validation evidence.

## Next core gate

After authoritative V3-4 validation and lock:

> Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection

Gate V3-5 has not started and requires separate approval. It is the first gate permitted to determine whether any new Version 3 RSI or Bollinger pipeline earns establishment.
