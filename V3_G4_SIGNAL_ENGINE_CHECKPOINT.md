# Gate V3-4 — Unified RSI and Bollinger Interpretation Engine Checkpoint

## Status

```text
IMPLEMENTATION_COMPLETE_VALIDATION_PENDING
WINDOWS_REALIGNMENT_7_PASSED
WINDOWS_SIGNAL_SUITE_19_PASSED
REAL_DATA_INPUT_MATERIALIZATION_REMEDIATED
V3_1_HISTORICAL_OWNER_REMEDIATION_IMPLEMENTED
CURRENT_EXACT_ACCEPTANCE_RERUN_PENDING
LOCK_NOT_CREATED
```

Gate V3-4 has been implemented on `research/v3-adaptive-signal-validity`. The Windows research environment has passed the corrected seven-test repository-realignment suite and the exact hardened nineteen-test signal-engine suite.

The first real-data execution stopped because `outputs/v3/data_adapter/canonical_market_data.csv` had not been materialized locally. The self-contained runner remediation then exposed a second parent-verification problem: the historical V3-1 verifier compared the current shared package initializer `src/shockbridge_signal_validity/v3/__init__.py` with its V3-1-era blob even though later gates legitimately extended that initializer with spectral exports.

Neither stop was an RSI, Bollinger, registry, leakage, forecast, or empirical failure. The runner and parent verifier now distinguish historical lock integrity, current direct implementation integrity, and legitimate later ownership of a shared export surface.

## Research-question link

Gate V3-4 advances Richard's question by defining the complete bounded RSI and Bollinger information family that Gate V3-5 will compare with matched non-signal benchmarks.

It does not answer whether any signal is established and cannot authorize deterioration or failure modelling.

## Corrected parent boundary

```text
Frozen Version 2 baseline:
5a07299367b80c3940e652e7bbdd208ce86ba5ef

Historical V3-1 implementation boundary:
7a7a5c55184aadfb436774ff1e497ce873a96b6e

Repository realignment checkpoint:
V3_REALIGNMENT_CHECKPOINT.md

Required standalone verifier:
scripts/verify_v3_realignment.py

Locked canonical adapter verifier:
scripts/verify_v3_g1_data_adapter.py
```

The V3-1 lock file remains unchanged. Every protected object is verified at the historical V3-1 boundary. Current direct V3-1 implementation objects are separately checked as committed Git blobs, and uncommitted modifications to those direct paths fail closed. The shared `v3/__init__.py` may contain later-gate exports, but all required V3-1 public symbols must remain present.

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
scripts/verify_v3_g1_data_adapter.py
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

The output verifier confirms that the physical CSV row count equals the manifest row count, the registry contains all 48 definitions, canonical validation passed, no prohibited action occurred, and the next gate is V3-5.

## Authoritative Windows evidence received

```text
Repository realignment: 7 passed
Exact hardened V3-4 tests: 19 passed
First real-data execution: stopped before feature generation
First immediate cause: canonical input path did not exist locally
Second self-contained rerun: stopped during V3-1 parent verification
Second immediate cause: shared package initializer had legitimate later-gate exports
```

No V3-4 output manifest existed after either stop. Blank-manifest and false-condition messages produced by manually continuing after a runner failure are cascade errors, not scientific or implementation findings.

## Parent-verifier remediation

The V3-1 verifier now applies three distinct checks:

```text
historical integrity
    every protected V3-1 blob equals the lock at commit
    7a7a5c55184aadfb436774ff1e497ce873a96b6e

current direct implementation integrity
    direct V3-1 committed objects still equal the locked blobs
    uncommitted modifications to those paths fail closed

shared export compatibility
    the evolved v3/__init__.py may include later exports
    every required V3-1 public symbol must remain available
```

Committed-object comparisons use Git object identities rather than checkout bytes, making the verifier invariant to Windows line-ending conversion. The existing V3-4 runner test now binds the historical-lock and current-export compatibility outputs without increasing the nineteen-test inventory.

## Complete runner chain

The platform runners perform the dependency chain in one command:

```text
verify realignment
    ↓
verify historical and current-compatible V3-1 parent
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

The runner itself performs every acceptance check. Do not execute separate manifest commands unless this command completes successfully.

## Acceptance conditions before lock

1. The updated standalone realignment verifier passes.
2. The historical V3-1 lock verifies at commit `7a7a5c55184aadfb436774ff1e497ce873a96b6e`.
3. Current direct V3-1 implementation objects match their locked committed blobs and their working-tree paths are clean.
4. The current shared Version 3 export surface preserves all V3-1 public symbols.
5. All 19 current V3-4 tests pass.
6. The frozen SOL snapshot is converted into valid canonical data.
7. Real canonical data generates the complete V3-4 output package.
8. `signal_feature_manifest.json` records 48 signals and verifies `rows = source_rows × 48`.
9. The physical long-format CSV row count matches the manifest.
10. The registry manifest contains all 48 complete signal definitions.
11. Adaptive templates and unavailable context remain explicit rather than dropped.
12. No target, chronology, predictive, economic, deterioration, or failure claim is produced.
13. No tracked file changes are caused by the runner.
14. Output hashes and final committed object identities are reviewed.
15. The checkpoint and contract are revised with authoritative real-data evidence before the lock is created.

## Next gate boundary

Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection — is approved but has not started.

It may begin immediately after the V3-4 authoritative evidence and lock are complete, without another approval request. Gate V3-5, not V3-4, determines whether any Version 3 RSI or Bollinger pipeline earns establishment.
