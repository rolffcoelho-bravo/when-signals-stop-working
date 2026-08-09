# Version 3 Repository Realignment Checkpoint

## Status

```text
CORRECTION_IMPLEMENTED
WINDOWS_REVALIDATION_PASSED
V3_4_IMPLEMENTATION_VALIDATED_AND_LOCKED
V3_5_IMPLEMENTATION_STARTED_CONTRACT_FROZEN
REALIGNMENT_COMPLETE
```

The repository realignment is complete. the practitioner's question and the establishment-before-failure sequence are restored, historical chronology work remains preserved under the V3-RV extension, Gate V3-4 is authoritatively validated and locked, and Gate V3-5 is active at its frozen-contract boundary.

## Baseline and branch

```text
Branch: research/v3-adaptive-signal-validity
Frozen Version 2 baseline: 5a07299367b80c3940e652e7bbdd208ce86ba5ef
Original realignment checkpoint commit: d2a65ab60199dbfcb6a79daebd412b535acb572d
Validated V3-4 implementation commit: ff2e7ecba3fa69f22e0b109437d23b52d30fba2b
V3-4 evidence materialization commit: 705511de9e8ee22a9f8aff34506aebb6c26223e7
V3-4 lock promotion commit: 4150d73ff1e12d5b022e591f0a6ee700c29b5ce1
```

## What was corrected

1. the practitioner's original question is restored at repository root.
2. The direct-answer hierarchy is explicit: establishment precedes conditional validity, deterioration, failure probability, and operational action.
3. Frozen Version 1 and Version 2 determinations remain unchanged.
4. Historical chronology work is preserved but reclassified as `V3-RV1` and `V3-RV2` regime-validation evidence.
5. Proposed event alignment is reclassified as `V3-RV3`, paused, and not started.
6. The true Gate V3-4 was restored, implemented, validated, and locked as the Unified RSI and Bollinger Interpretation Engine.
7. Gate V3-5 now occupies the correct matched forecast-establishment position.
8. README, roadmap, gate map, findings, machine-readable contract, verifiers, tests, and runners enforce the corrected sequence.

## Historical exact-token remediation

The first Windows realignment execution produced:

```text
6 passed
1 failed
```

The failing assertion was:

```text
Required phrase missing from DIRECT_ANSWER_LOGIC.md: ESTABLISHMENT
```

The scientific logic was already present, but the standalone verifier required the exact uppercase governance token. The document was corrected without weakening the verifier.

The corrected suite subsequently passed:

```text
7 passed
```

## Final Gate V3-4 evidence

```text
status: IMPLEMENTATION_VALIDATED_AND_LOCKED
repository realignment tests: 7 passed
exact hardened V3-4 tests: 19 passed
canonical source rows: 12171
registered signal specifications: 48
feature rows: 584208
row-count identity: verified
automatic selection: false
target accessed: false
chronology accessed: false
predictive claims: false
economic claims: false
deterioration claims: false
failure claims: false
tracked mutation: false
```

The final lock is `V3_G4_SIGNAL_ENGINE_LOCK.json`. The large feature table remains an untracked regenerable artifact and is bound by SHA-256. Compact evidence is committed under `evidence/v3/g4_signal_lock/`.

## Historical objects deliberately unchanged

The realignment does not rename or rewrite historical chronology locks, checkpoints, registries, evidence outputs, or frozen Version 1 and Version 2 determinations.

```text
V3-4A → scientifically reclassified as V3-RV1
V3-4B → scientifically reclassified as V3-RV2
V3-4C → proposed work reclassified as V3-RV3 and paused
```

## Active Gate V3-5 contract

Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection — is approved and has started only at its contract-freeze stage.

```text
contract: configs/v3_g5_forecast_contract.json
status: APPROVED_IMPLEMENTATION_STARTED_CONTRACT_FROZEN
target access: false
development model fitting: false
signal-establishment segment access: false
V3-9 final-framework reserve access: false
```

Frozen partition:

```text
Development:
2021-01-01T00:00:00Z to 2025-06-30T20:00:00Z

Signal establishment:
2025-07-01T00:00:00Z to 2025-12-31T20:00:00Z

V3-9 final-framework reserve:
2026-01-01T00:00:00Z to 2026-07-22T08:00:00Z
```

The 2026 reserve is inaccessible to Gate V3-5. Early access is the protocol violation `PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED`.

## Current realignment validation suite

The seven tests now cover:

1. preservation of the practitioner's question and frozen Version 1/2 answers;
2. final V3-4 lock and authoritative evidence;
3. active V3-5 contract state without target or model access;
4. chronology reclassification without historical rewriting;
5. establishment-before-failure sequence and stop rules;
6. fail-closed drift and reserve-access governance;
7. execution of the standalone realignment verifier.

## Current authoritative execution

```powershell
.\RUN_V3_REALIGNMENT.ps1
.\RUN_V3_G5_CONTRACT.ps1
```

The V3-5 runner verifies the final V3-4 lock, runs seven V3-5 contract tests, executes the standalone contract verifier, and checks patch integrity.

## Current core gate

> Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection

The contract is frozen, but its authoritative Windows validation remains pending. Target generation, chronological fold creation, model fitting, candidate ranking, pipeline admission, and establishment access remain prohibited until that validation passes.
