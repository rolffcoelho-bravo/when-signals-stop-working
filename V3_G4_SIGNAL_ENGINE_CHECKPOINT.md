# Gate V3-4 — Unified RSI and Bollinger Interpretation Engine Checkpoint

## Status

```text
IMPLEMENTATION_COMPLETE_VALIDATION_PENDING
PRIOR_DEVELOPMENT_SUITE_19_PASSED
CURRENT_HARDENED_SUITE_EXECUTION_PENDING
LOCK_NOT_CREATED
```

Gate V3-4 has been implemented on `research/v3-adaptive-signal-validity`. It is not validated or locked until the authoritative Windows research environment executes the updated realignment verifier, the exact hardened 19-test suite, and the real-data signal runner successfully.

## Research-question link

Gate V3-4 advances Richard's question by defining the complete bounded RSI and Bollinger information family that Gate V3-5 will compare with matched non-signal benchmarks.

It does not answer whether any signal is established and cannot authorize deterioration or failure modelling.

## Corrected parent boundary

```text
Frozen Version 2 baseline:
5a07299367b80c3940e652e7bbdd208ce86ba5ef

Repository realignment checkpoint:
V3_REALIGNMENT_CHECKPOINT.md

Required standalone verifier:
scripts/verify_v3_realignment.py
```

The chronology extension remains scientifically reclassified as `V3-RV1` and `V3-RV2`; `V3-RV3` event alignment remains paused.

## Implementation inventory

```text
configs/v3_signal_interpretation_registry.json
configs/v3_signal_engine_example.json
src/shockbridge_signal_validity/v3/signal_registry.py
src/shockbridge_signal_validity/v3/signal_math.py
src/shockbridge_signal_validity/v3/signal_rsi.py
src/shockbridge_signal_validity/v3/signal_bollinger.py
src/shockbridge_signal_validity/v3/signal_reporting.py
src/shockbridge_signal_validity/v3/signal_engine.py
src/shockbridge_signal_validity/v3/signal_runner.py
scripts/run_v3_signal_engine.py
tests/test_v3_signal_registry.py
tests/test_v3_signal_engine.py
tests/test_v3_signal_runner.py
RUN_V3_G4_SIGNAL_ENGINE.ps1
RUN_V3_G4_SIGNAL_ENGINE.sh
docs/V3_G4_SIGNAL_ENGINE.md
V3_G4_SIGNAL_ENGINE_CHECKPOINT.md
```

## Registry evidence

```text
registered specifications: 48
base specifications: 44
regime interactions: 4
training-only adaptive templates: 2
bounded maximum: 128
identifier scheme: v3sig:<feature_key>:<sha256(canonical_specification)>
```

Complete canonical definitions are stored once in `signal_registry_manifest.json`. No candidate is automatically selected, ranked, promoted, or deleted.

## Output contract

```text
outputs/v3/signal_engine/signal_features.csv
outputs/v3/signal_engine/signal_registry_manifest.json
outputs/v3/signal_engine/signal_feature_manifest.json
outputs/v3/signal_engine/signal_coverage_report.json
outputs/v3/signal_engine/signal_validation_report.json
outputs/v3/signal_engine/canonical_validation_report.json
```

The required real-data identity is:

```text
feature rows = canonical source rows × 48
```

## Prior development evidence and current boundary

A controlled earlier form of the isolated suite completed with:

```text
19 passed
```

Final hardening was then applied to exact Wilder initialization, fixed/adaptive registry validation, malformed OHLC rejection, context-range validation, readable training-parameter keys, row-count transparency, and concise cryptographic identifiers. The existing 19 tests were updated to bind those controls.

Therefore, the prior run is useful development evidence, but the **exact hardened current branch head has not yet been executed**. It is not authoritative repository-environment acceptance evidence.

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

## Required authoritative execution

```powershell
.\RUN_V3_REALIGNMENT.ps1
.\RUN_V3_G4_SIGNAL_ENGINE.ps1
```

Expected high-level evidence:

```text
7 passed
Version 3 repository realignment verification passed.
Current hardened V3-4 suite execution pending: True
19 passed
Gate V3-4 unified RSI and Bollinger signal engine passed.
Registered signals: 48
Automatic selection performed: False
Target accessed: False
Chronology accessed: False
Predictive/economic/failure claims produced: False
Next core gate: V3-5
```

## Acceptance conditions before lock

1. The updated standalone realignment verifier passes.
2. All 19 exact hardened V3-4 tests pass.
3. Real canonical data generates the complete output package.
4. `signal_feature_manifest.json` records 48 signals and verifies `rows = source_rows × 48`.
5. The registry manifest contains all 48 complete signal definitions bound to concise IDs.
6. Adaptive templates and unavailable context remain explicit rather than dropped.
7. No target or chronology column is accessed.
8. No tracked file changes are caused by the runner.
9. Output hashes and final committed object identities are reviewed.
10. The checkpoint is revised with authoritative evidence before any lock is created.

## Next gate boundary

After validation and lock:

> Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection

Gate V3-5 has not started and requires separate approval. It, not V3-4, determines whether any Version 3 RSI or Bollinger pipeline earns establishment.
