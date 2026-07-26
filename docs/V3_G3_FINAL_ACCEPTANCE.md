# Gate V3-3D - Final Acceptance, Protected-Object Audit, and Lock

## Purpose

Gate V3-3D is the final authorization boundary for the complete panic-consistent regime engine. It must not create the final V3-3 lock until the integrated acceptance report has passed on the committed branch.

## Lock-lineage remediation

Earlier gate verifiers compare every historical protected path with the current working tree. That rule is invalid when a later gate deliberately becomes the new owner of a shared additive file. The package initializer is the concrete case: V3-1 protected the data-adapter export surface and V3-2 later protected an extended initializer containing spectral exports.

V3-3D therefore applies two separate tests:

1. every historical protected object must match its recorded Git blob at the commit that created its lock;
2. every current protected path must match the latest lock in the declared gate sequence that owns that path.

This does not weaken historical locks. It prevents a valid later supersession from being misclassified as corruption while still rejecting lock-file tampering and ungoverned current changes.

## Integrated acceptance suite

The runner executes:

```text
tests/test_v3_panic_regime_contract.py
tests/test_v3_panic_regime.py
tests/test_v3_panic_regime_diagnostics.py
tests/test_v3_lock_lineage.py
```

Expected total:

```text
38 passed
```

The additional regression assertion verifies that the Windows PowerShell wrapper is ASCII-only, contains the exact governed runner command, and has balanced double-quote delimiters. This prevents Windows PowerShell 5.1 from misreading UTF-8 smart punctuation as string delimiters.

It then executes the V3-3A, V3-3B, and V3-3C portable lock verifiers and confirms:

- no automatic model selection;
- no automatic ensemble;
- no consensus probability;
- no external chronology use;
- the eight required V3-3 outputs remain frozen;
- Version 1 and Version 2 determinations remain unchanged.

## Final-lock rule

The runner writes:

```text
outputs/v3/g3_final_acceptance/final_acceptance_report.json
```

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
