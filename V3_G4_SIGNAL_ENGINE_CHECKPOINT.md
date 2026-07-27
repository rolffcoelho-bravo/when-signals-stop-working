# Gate V3-4 — Unified RSI and Bollinger Interpretation Engine Checkpoint

## Status

```text
IMPLEMENTATION_COMPLETE
AUTHORITATIVE_VALIDATION_COMPLETE
WINDOWS_REALIGNMENT_7_PASSED
WINDOWS_SIGNAL_SUITE_19_PASSED
REAL_DATA_EXECUTION_PASSED
OUTPUT_IDENTITY_VERIFIED
NO_TRACKED_MUTATION
IMPLEMENTATION_VALIDATED_AND_LOCKED
GATE_COMPLETE
```

## Final boundaries

```text
Frozen Version 2 baseline:
5a07299367b80c3940e652e7bbdd208ce86ba5ef

Historical V3-1 implementation boundary:
7a7a5c55184aadfb436774ff1e497ce873a96b6e

Authoritatively validated V3-4 implementation boundary:
ff2e7ecba3fa69f22e0b109437d23b52d30fba2b

Evidence materialization commit:
705511de9e8ee22a9f8aff34506aebb6c26223e7

Lock promotion commit:
4150d73ff1e12d5b022e591f0a6ee700c29b5ce1
```

The final lock is:

```text
V3_G4_SIGNAL_ENGINE_LOCK.json
status: IMPLEMENTATION_VALIDATED_AND_LOCKED
```

Every protected V3-4 implementation object remains bound to the validated implementation commit. The compact curated evidence remains bound by SHA-256. The 584,208-row long-format table remains an untracked regenerable artifact and is bound by its recorded SHA-256.

## Research-question link

Gate V3-4 defines the complete bounded RSI and Bollinger information family that Gate V3-5 may compare with matched non-signal benchmarks.

It does not establish predictive or economic value and cannot by itself authorize conditional validity, deterioration, failure modelling, or operational use.

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

The complete runner verified repository realignment, historical and current-compatible V3-1 ownership, the exact nineteen-test V3-4 suite, frozen SOL canonical-data materialization, real-data signal generation, output identities, and tracked-file cleanliness.

## Canonical input contract

```text
source: data/raw/sol_usdt_4h.csv
adapter: configs/v3_adapter_frozen_sol.json
canonical output: outputs/v3/data_adapter/canonical_market_data.csv
asset: SOL/USDT
venue: binance_spot
rows: 12171
```

BTC remains benchmark and market-context information for Gate V3-5. It is not a second V3-4 target-signal family.

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

## Runtime and curated evidence

Runtime outputs:

```text
outputs/v3/signal_engine/signal_features.csv
outputs/v3/signal_engine/signal_registry_manifest.json
outputs/v3/signal_engine/signal_feature_manifest.json
outputs/v3/signal_engine/signal_coverage_report.json
outputs/v3/signal_engine/signal_validation_report.json
outputs/v3/signal_engine/canonical_validation_report.json
```

Committed evidence:

```text
V3_G4_SIGNAL_ENGINE_LOCK.json
evidence/v3/g4_signal_lock/canonical_source_manifest.json
evidence/v3/g4_signal_lock/canonical_validation_report.json
evidence/v3/g4_signal_lock/signal_canonical_validation_report.json
evidence/v3/g4_signal_lock/signal_coverage_report.json
evidence/v3/g4_signal_lock/signal_feature_manifest.json
evidence/v3/g4_signal_lock/signal_registry_manifest.json
evidence/v3/g4_signal_lock/signal_validation_report.json
```

## Locked claims boundary

```text
predictive claim: not produced by V3-4
economic claim: not produced by V3-4
conditional-validity claim: not produced by V3-4
deterioration claim: not produced by V3-4
failure-probability claim: not produced by V3-4
RSI/Bollinger rescue: prohibited
frozen V1/V2 modification: prohibited
```

## Next gate

Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection — is approved and has started at its frozen contract boundary.

Current V3-5 state:

```text
contract frozen: true
target access: false
development model fitting: false
signal-establishment segment access: false
V3-9 final-framework reserve access: false
```

Gate V3-5 must make the registered signals earn new evidence through matched chronological comparison. The V3-4 lock cannot be altered to improve a V3-5 result.
