# Gate V3-3D - Final Acceptance, Protected-Object Audit, and Lock

## Purpose

Gate V3-3D is the final authorization boundary for the complete panic-consistent regime engine. It must not create the final V3-3 lock until the integrated acceptance report has passed on the committed branch.

## Lock-lineage remediation

Earlier gate verifiers compare every historical protected path with the current working tree. That rule is invalid when a later gate deliberately becomes the new owner of a shared additive file. The package initializer is the concrete case: V3-1 protected the data-adapter export surface and V3-2 later protected an extended initializer containing spectral exports.

A second distinction is required between lock creation and lock finalization. A lock can be created as a draft evidence object and then finalized before the next gate freezes its exact blob. The first commit containing a lock file is therefore not automatically the authoritative immutability boundary.

V3-3D applies four separate controls:

1. each parent lock is anchored to the exact `parent_lock_blob_sha` recorded by its child gate when that reference exists;
2. a lock without a child blob reference is anchored to its creation blob;
3. every historical protected object must match the lock at the governed finalization commit where the authoritative lock blob first appears;
4. every current protected path must match the latest lock in the declared gate sequence that owns that path.

Any lock modification after the governed finalization commit is rejected, including a later change followed by a reversion. This does not weaken historical locks. It distinguishes pre-freeze finalization from post-freeze tampering.

## External chronology contract

V3-3C records external chronology through two frozen fields:

```text
external_chronology_validation_complete = false
external_chronology_deferred_to_later_robustness = true
```

The absence of an `external_chronology_used` field is not evidence of use. V3-3D therefore requires the two frozen fields above and additionally rejects any explicit `external_chronology_used = true` value. Missing completion or deferral fields fail closed.

This preserves the scientific distinction between:

- chronology validation not yet executed;
- chronology validation deliberately deferred;
- external chronology actually used in estimation, selection, or interpretation.

## Active Python environment contract

The acceptance wrappers must use the active Python interpreter together with the packages installed for that interpreter. They must not set `PYTHONNOUSERSITE=1`, because doing so can hide an explicitly installed user-scope `pytest` package while still invoking the system interpreter.

The Windows wrapper temporarily removes `PYTHONNOUSERSITE` for the governed child process and restores the caller's prior process value afterward. The POSIX wrapper unsets the variable within its own process. Both wrappers continue to pin `PYTHONPATH` to the repository `src` directory and restrict numerical-library thread counts.

This is an execution-environment correction only. It does not change model code, data, parameters, tests, or scientific determinations.

## Integrated acceptance suite

The runner executes:

```text
tests/test_v3_panic_regime_contract.py
tests/test_v3_panic_regime.py
tests/test_v3_panic_regime_diagnostics.py
tests/test_v3_lock_lineage.py
tests/test_v3_g3_final_acceptance.py
```

Expected total:

```text
46 passed
```

The lineage and final-acceptance suites verify:

- intentional latest-owner supersession;
- draft lock finalization before child freeze;
- rejection of modification after a child freezes the parent blob;
- rejection of current protected-object mismatch;
- rejection of modification to the latest unreferenced lock;
- ASCII-safe Windows PowerShell execution;
- preservation of the active Python environment in both launchers;
- successful audit of the actual repository V3-1 through V3-3C lock chain;
- acceptance of the exact frozen deferred-chronology contract;
- rejection of completed, non-deferred, missing, or explicitly used chronology states.

It then executes the V3-3A, V3-3B, and V3-3C portable lock verifiers and confirms:

- no automatic model selection;
- no automatic ensemble;
- no consensus probability;
- external chronology validation remains incomplete;
- external chronology remains explicitly deferred;
- external chronology was not used;
- the eight required V3-3 outputs remain frozen;
- Version 1 and Version 2 determinations remain unchanged.

## Final-lock rule

The runner writes:

```text
outputs/v3/g3_final_acceptance/final_acceptance_report.json
```

The report records creation commits, governed finalization commits, authoritative lock blobs, the source of each finalization anchor, and the three chronology-governance fields.

The final files:

```text
V3_G3_PANIC_REGIME_LOCK.json
V3_G3_PANIC_REGIME_CHECKPOINT.md
```

may be created only after that report states:

```text
FINAL_LOCK_AUTHORIZATION_EVIDENCE_COMPLETE
```

The acceptance runner does not self-create or self-approve the lock.
