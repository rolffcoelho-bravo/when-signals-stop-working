# Gate V3-4 — Unified RSI and Bollinger Interpretation Engine Checkpoint

## Status

```text
IMPLEMENTATION_COMPLETE
AUTHORITATIVE_VALIDATION_COMPLETE_LOCK_PENDING
WINDOWS_REALIGNMENT_7_PASSED
WINDOWS_SIGNAL_SUITE_19_PASSED
REAL_DATA_EXECUTION_PASSED
OUTPUT_IDENTITY_VERIFIED
NO_TRACKED_MUTATION
VALIDATED_IMPLEMENTATION_COMMIT_FROZEN
LOCK_NOT_YET_PROMOTED
```

Gate V3-4 has passed its authoritative Windows research-environment acceptance boundary. The validated implementation is frozen at:

```text
ff2e7ecba3fa69f22e0b109437d23b52d30fba2b
```

Later lock tooling may be added, but every protected V3-4 implementation object must remain identical to that validated commit.

## Research-question link

Gate V3-4 advances Richard's question by defining the complete bounded RSI and Bollinger information family that Gate V3-5 will compare with matched non-signal benchmarks.

It does not establish predictive or economic value and cannot authorize deterioration or failure modelling.

## Frozen parent and implementation boundaries

```text
Frozen Version 2 baseline:
5a07299367b80c3940e652e7bbdd208ce86ba5ef

Historical V3-1 implementation boundary:
7a7a5c55184aadfb436774ff1e497ce873a96b6e

Authoritatively validated V3-4 implementation boundary:
ff2e7ecba3fa69f22e0b109437d23b52d30fba2b
```

The V3-1 lock remains unchanged. Its historical objects are verified at the original V3-1 boundary. Current direct V3-1 objects remain protected, and the shared `v3/__init__.py` is governed through backward-compatible V3-1 exports rather than an obsolete package-level blob comparison.

## Authoritative Windows acceptance evidence

```text
Repository realignment tests: 7 passed
Exact hardened V3-4 tests: 19 passed
Canonical source rows: 12171
Canonical data SHA-256: 3c49bfcab5fdf3aba9ada614873fa424e97c1f66e2690b790204fc29fdb5109c
Registered signal specifications: 48
Expected feature rows: 584208
Observed feature rows: 584208
Row-count identity verified: true
Automatic signal selection performed: false
Target accessed: false
Chronology accessed: false
Predictive claims produced: false
Economic claims produced: false
Deterioration claims produced: false
Failure claims produced: false
Tracked working-tree mutation: false
Next gate reported: V3-5
```

The complete runner finished successfully after verifying repository realignment, historical and current-compatible V3-1 ownership, the exact nineteen-test V3-4 suite, frozen SOL canonical-data materialization, real-data signal generation, output identities, and tracked-file cleanliness.

## Canonical input contract

```text
source: data/raw/sol_usdt_4h.csv
adapter: configs/v3_adapter_frozen_sol.json
canonical output: outputs/v3/data_adapter/canonical_market_data.csv
asset: SOL/USDT
venue: binance_spot
rows: 12171
```

BTC remains benchmark and market-context information for Gate V3-5. It is not silently converted into a second V3-4 target-signal family.

## Registry evidence

```text
registered specifications: 48
base specifications: 44
regime interactions: 4
training-only adaptive templates: 2
bounded maximum: 128
identifier scheme: v3sig:<feature_key>:<sha256(canonical_specification)>
```

No candidate was selected, ranked, promoted, or deleted by Gate V3-4.

## Runtime output contract

```text
outputs/v3/signal_engine/signal_features.csv
outputs/v3/signal_engine/signal_registry_manifest.json
outputs/v3/signal_engine/signal_feature_manifest.json
outputs/v3/signal_engine/signal_coverage_report.json
outputs/v3/signal_engine/signal_validation_report.json
outputs/v3/signal_engine/canonical_validation_report.json
```

The large `signal_features.csv` contains 584,208 rows. It remains a regenerable runtime artifact and will not be committed. The final lock binds it by SHA-256. Compact manifests are copied into `evidence/v3/g4_signal_lock/` for repository review.

## Lock materialization package

```text
scripts/finalize_v3_g4_lock.py
scripts/verify_v3_g4_lock.py
RUN_V3_G4_LOCK.ps1
RUN_V3_G4_LOCK.sh
V3_G4_SIGNAL_ENGINE_LOCK.json        generated locally
evidence/v3/g4_signal_lock/*.json    generated locally
```

The lock candidate generator:

1. requires a clean tracked working tree;
2. verifies that the validated V3-4 commit is an ancestor of the current branch;
3. confirms that every protected implementation object still equals the validated commit;
4. revalidates all runtime evidence;
5. hashes the raw source, canonical input, long-format feature table, and all manifests;
6. curates compact JSON evidence;
7. emits a reviewable lock candidate.

The final lock status remains pending until the generated candidate and curated manifests are committed, reviewed, and promoted from:

```text
LOCK_CANDIDATE_AWAITING_REPOSITORY_REVIEW
```

to:

```text
IMPLEMENTATION_VALIDATED_AND_LOCKED
```

## Claims prohibited at this checkpoint

```text
predictive claim: prohibited
economic claim: prohibited
conditional-validity claim: prohibited
deterioration claim: prohibited
failure-probability claim: prohibited
RSI/Bollinger rescue: prohibited
frozen V1/V2 modification: prohibited
```

## Next action

```powershell
.\RUN_V3_G4_LOCK.ps1
```

After the lock candidate is generated and verified, commit only the compact lock and curated evidence. The ignored runtime directories remain local and reproducible.

## Next gate boundary

Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection — is approved but has not started.

Its parent validation requirement is complete. It may begin immediately after final V3-4 lock promotion, without another approval request. Gate V3-5, not V3-4, determines whether any Version 3 RSI or Bollinger pipeline earns establishment.
