# Gate V3-4 — Unified RSI and Bollinger Interpretation Engine Checkpoint

## Status

```text
IMPLEMENTATION_COMPLETE_VALIDATION_PENDING
```

Gate V3-4 has been implemented on `research/v3-adaptive-signal-validity`. It is not validated or locked until the authoritative Windows research environment executes the realignment verifier, the isolated 19-test V3-4 suite, and the real-data signal runner successfully.

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
```

No candidate is automatically selected, ranked, promoted, or deleted.

## Output contract

```text
outputs/v3/signal_engine/signal_features.csv
outputs/v3/signal_engine/signal_registry_manifest.json
outputs/v3/signal_engine/signal_feature_manifest.json
outputs/v3/signal_engine/signal_coverage_report.json
outputs/v3/signal_engine/signal_validation_report.json
outputs/v3/signal_engine/canonical_validation_report.json
```

## Development validation

A controlled isolated development run completed:

```text
19 passed
```

This evidence covers the exact signal modules, compact registry expansion, synthetic canonical fixtures, deterministic long-format output, context interactions, and runner behavior. It is useful implementation evidence but is not the authoritative repository-environment acceptance run.

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
.\RUN_V3_G4_SIGNAL_ENGINE.ps1
```

Expected high-level evidence:

```text
Version 3 repository realignment verification passed.
19 passed
Gate V3-4 unified RSI and Bollinger signal engine passed.
Registered signals: 48
Automatic selection performed: False
Target accessed: False
Chronology accessed: False
Predictive/economic/failure claims produced: False
Next core gate: V3-5
```

The exact source-row and feature-row counts depend on the canonical V3-1 data available in the research environment. The expected identity is:

```text
feature rows = canonical source rows × 48
```

## Acceptance conditions before lock

1. The standalone realignment verifier passes after the exact-token remediation.
2. All 19 isolated V3-4 tests pass.
3. Real canonical data generates the complete output package.
4. `signal_feature_manifest.json` records 48 signals and no automatic selection.
5. Adaptive templates and unavailable context remain explicit rather than dropped.
6. No tracked file changes are caused by the runner.
7. Output hashes and final committed object identities are reviewed.
8. The checkpoint is revised with authoritative evidence before any lock is created.

## Next gate boundary

After validation and lock:

> Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection

Gate V3-5, not V3-4, determines whether any Version 3 RSI or Bollinger pipeline earns establishment.
