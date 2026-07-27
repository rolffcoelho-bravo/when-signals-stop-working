# Gate V3-4 — Unified RSI and Bollinger Interpretation Engine Checkpoint

## Status

```text
IMPLEMENTATION_COMPLETE_VALIDATION_PENDING
WINDOWS_REALIGNMENT_7_PASSED
WINDOWS_SIGNAL_SUITE_19_PASSED
REAL_DATA_INPUT_MATERIALIZATION_REMEDIATED
CURRENT_EXACT_ACCEPTANCE_RERUN_PENDING
LOCK_NOT_CREATED
```

Gate V3-4 has been implemented on `research/v3-adaptive-signal-validity`. The Windows research environment has now passed the corrected seven-test repository-realignment suite and the exact hardened nineteen-test signal-engine suite. The first real-data execution then stopped because `outputs/v3/data_adapter/canonical_market_data.csv` had not been materialized locally.

This was an execution-orchestration defect, not an RSI, Bollinger, registry, leakage, or forecasting failure. The runner now verifies the locked V3-1 adapter, regenerates the canonical SOL input from the frozen public raw snapshot, executes V3-4, verifies all output identities, and fails before downstream manifest access when any prerequisite fails.

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

Locked canonical adapter verifier:
scripts/verify_v3_g1_data_adapter.py
```

The chronology extension remains scientifically reclassified as `V3-RV1` and `V3-RV2`; `V3-RV3` event alignment remains paused.

## Implementation inventory

```text
configs/v3_adapter_frozen_sol.json
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
scripts/verify_v3_g4_signal_outputs.py
tests/test_v3_signal_registry.py
tests/test_v3_signal_engine.py
tests/test_v3_signal_runner.py
RUN_V3_G4_SIGNAL_ENGINE.ps1
RUN_V3_G4_SIGNAL_ENGINE.sh
docs/V3_G4_SIGNAL_ENGINE.md
V3_G4_SIGNAL_ENGINE_CHECKPOINT.md
```

## Canonical input contract

The authoritative V3-4 input is materialized deterministically from:

```text
source: data/raw/sol_usdt_4h.csv
adapter: configs/v3_adapter_frozen_sol.json
output: outputs/v3/data_adapter/canonical_market_data.csv
asset: SOL/USDT
venue: binance_spot
```

The source is the frozen public Version 1/2 SOL snapshot. BTC remains benchmark and market-context information for Gate V3-5; it is not silently converted into a second V3-4 target-signal family.

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

The new output verifier also confirms that the physical CSV row count equals the manifest row count, the registry contains all 48 definitions, canonical validation passed, no prohibited action occurred, and the next gate is V3-5.

## Authoritative Windows evidence received

```text
Repository realignment: 7 passed
Exact hardened V3-4 tests: 19 passed
Real-data execution: stopped before feature generation
Immediate cause: canonical input path did not exist locally
```

No V3-4 output manifest existed after the stop. All later blank-manifest and false-condition messages were downstream cascade errors caused by manually continuing after the fail-fast runner had already terminated. They are not scientific or implementation findings.

## Remediation

The platform runners now perform the complete dependency chain in one command:

```text
verify realignment
    ↓
verify locked V3-1 adapter
    ↓
run exact 19-test V3-4 suite
    ↓
materialize frozen SOL canonical input
    ↓
execute V3-4 real-data engine
    ↓
verify complete output package and row identities
    ↓
verify no tracked working-tree mutation
```

The runner deletes any stale V3-4 output directory before execution, so old manifests cannot be mistaken for current evidence.

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

## Required final authoritative execution

```powershell
.\RUN_V3_G4_SIGNAL_ENGINE.ps1
```

The runner itself now performs every acceptance check. Do not execute separate manifest commands unless this command completes successfully.

## Acceptance conditions before lock

1. The updated standalone realignment verifier passes.
2. The locked V3-1 adapter verifier passes.
3. All 19 current V3-4 tests pass.
4. The frozen SOL snapshot is converted into valid canonical data.
5. Real canonical data generates the complete V3-4 output package.
6. `signal_feature_manifest.json` records 48 signals and verifies `rows = source_rows × 48`.
7. The physical long-format CSV row count matches the manifest.
8. The registry manifest contains all 48 complete signal definitions.
9. Adaptive templates and unavailable context remain explicit rather than dropped.
10. No target, chronology, predictive, economic, deterioration, or failure claim is produced.
11. No tracked file changes are caused by the runner.
12. Output hashes and final committed object identities are reviewed.
13. The checkpoint and contract are revised with authoritative real-data evidence before the lock is created.

## Next gate boundary

Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection — is approved but has not started.

It may begin immediately after the V3-4 authoritative evidence and lock are complete, without another approval request. Gate V3-5, not V3-4, determines whether any Version 3 RSI or Bollinger pipeline earns establishment.
