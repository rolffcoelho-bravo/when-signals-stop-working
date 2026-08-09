# Gate V3-4 — Unified RSI and Bollinger Interpretation Engine

## Status

```text
IMPLEMENTATION_COMPLETE
AUTHORITATIVE_WINDOWS_VALIDATION_COMPLETE
REAL_DATA_EXECUTION_COMPLETE
IMPLEMENTATION_VALIDATED_AND_LOCKED
GATE_COMPLETE
```

The exact hardened implementation passed the authoritative Windows research-environment run and is frozen at commit `ff2e7ecba3fa69f22e0b109437d23b52d30fba2b`. Compact evidence was materialized at commit `705511de9e8ee22a9f8aff34506aebb6c26223e7`, and the final lock is `V3_G4_SIGNAL_ENGINE_LOCK.json` with status `IMPLEMENTATION_VALIDATED_AND_LOCKED`.

## the practitioner-question link

This gate advances the practitioner's question by defining exactly which RSI and Bollinger information Gate V3-5 may test against matched non-signal benchmarks.

It does not determine whether any interpretation predicts returns, creates economic value, deteriorates, or is likely to fail.

## Architecture

```text
compact bounded registry
    ↓
concise cryptographic signal identifiers
    ↓
causal RSI and Bollinger primitives
    ↓
registered interpretation features
    ↓
optional preserved-component regime interactions
    ↓
deterministic long-format evidence and manifests
```

Implementation files:

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
RUN_V3_G4_SIGNAL_ENGINE.ps1
RUN_V3_G4_SIGNAL_ENGINE.sh
```

## Registry composition

The bounded registry expands deterministically to:

```text
registered specifications: 48
base specifications: 44
explicit regime interactions: 4
training-only adaptive templates: 2
bounded maximum: 128
automatic selection: false
```

Each concise identifier is:

```text
v3sig:<feature_key>:<sha256(canonical_specification)>
```

The complete canonical definition is stored once in `signal_registry_manifest.json`. This binds the identifier to family, lookback, parameters, orientation, interpretation, crossing, persistence, normalization, interaction policy, registry version, parameter policy, and any base/context identities without repeating a large encoded specification in every long-format row.

## RSI calculation

RSI uses Wilder's exact causal procedure:

1. the first average gain and loss are simple averages over the first 14 price changes;
2. later averages use Wilder's recursive update;
3. no centered window, future fill, full-sample normalization, or target access is permitted.

The registered fixed challenger uses:

```text
lookback: 14
lower threshold: 30
upper threshold: 70
range window: 6
divergence window: 14
```

The family includes:

- level and centered level;
- slope and acceleration;
- rolling range;
- bullish and bearish price-RSI divergence;
- oversold and overbought mean reversion;
- continuation interpretations;
- outward and inward crossings;
- time in extreme regions;
- signed persistence;
- time since crossing and exit from extremes;
- a training-only adaptive-threshold template.

## Bollinger calculation

The fixed challenger uses:

```text
window: 20
standard deviations: 2
fixed relative-bandwidth squeeze threshold: 0.08
rolling standard-deviation convention: population, ddof = 0
```

The family includes:

- percentage-B;
- normalized middle-band and outer-band distance;
- distance magnitude;
- upper and lower mean reversion;
- upper breakout and lower breakdown;
- outside-band continuation and re-entry;
- bandwidth, change, and acceleration;
- squeeze and post-squeeze expansion;
- expansion persistence;
- band crossings;
- time and signed persistence outside bands;
- re-entry timing and time since squeeze release;
- a training-only adaptive squeeze template.

## Adaptive-parameter boundary

The engine does not estimate adaptive thresholds.

Training-only parameters are supplied by readable `feature_key`. An adaptive specification remains visible as:

```text
INELIGIBLE_TRAINING_PARAMETER_REQUIRED
```

until an upstream training-only process supplies registered values. Unknown keys and invalid thresholds fail closed. Fixed challengers remain visible regardless of adaptive availability.

## Regime interactions

Four predeclared interactions are registered:

```text
RSI oversold mean reversion × p_range
RSI overbought continuation × p_trend
Bollinger lower breakdown × p_panic_consistent
Bollinger post-squeeze expansion × dominant_eigenvalue_share
```

Probability and share context values must lie in `[0,1]`. Missing context remains visible as `INELIGIBLE_CONTEXT_UNAVAILABLE`. Available interactions preserve:

```text
base_signal_value
context_value
feature_value = base_signal_value × context_value
```

## Input and fail-closed controls

The engine verifies:

- required canonical columns;
- valid UTC timestamps;
- unique timestamp-asset-venue keys;
- nonempty asset and venue identifiers;
- finite OHLCV values;
- positive prices and nonnegative volume;
- valid OHLC low/high relationships;
- finite context and bounded probability/share context;
- registered adaptive parameter keys;
- valid fixed and adaptive parameter contracts;
- every no-selection and no-claim registry flag.

## Long-format output

`signal_features.csv` contains:

```text
timestamp
asset
venue
signal_id
feature_key
signal_family
interpretation
orientation
parameter_policy
regime_interaction_policy
feature_value
eligibility_status
base_signal_value
context_value
```

Every registered specification is emitted for every canonical source row. The required identity is:

```text
feature rows = canonical source rows × 48
```

Insufficient history and unavailable optional inputs remain explicit; candidates are not deleted because they are sparse or unpromising.

## Evidence outputs

Runtime outputs:

```text
signal_features.csv
signal_registry_manifest.json
signal_feature_manifest.json
signal_coverage_report.json
signal_validation_report.json
canonical_validation_report.json
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

The manifests bind source input, registry, complete expanded definitions, output identity, row-count identity, available context columns, supplied training parameters, and every no-claim boundary. CSV evidence is LF-normalized.

## Authoritative validation evidence

```text
repository realignment tests: 7 passed
exact hardened signal-engine tests: 19 passed
canonical source rows: 12171
canonical data SHA-256: 3c49bfcab5fdf3aba9ada614873fa424e97c1f66e2690b790204fc29fdb5109c
registered signal specifications: 48
expected feature rows: 584208
observed feature rows: 584208
row-count identity verified: true
automatic selection performed: false
target accessed: false
chronology accessed: false
predictive claims produced: false
economic claims produced: false
deterioration claims produced: false
failure claims produced: false
tracked working-tree mutation: false
```

The large `signal_features.csv` remains an untracked regenerable artifact and is bound by SHA-256 in the lock. Seven compact manifests are committed for repository review.

## Scientific boundary

Gate V3-4 supports:

> A bounded, target-blind, causal, reproducible RSI and Bollinger information family has been authoritatively validated and locked for subsequent matched evaluation.

It does not support:

- signal establishment;
- predictive superiority;
- economic value;
- conditional validity;
- deterioration or suspension;
- failure probability;
- a claim that either signal stopped working.

## Next gate

The current core gate is:

> Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection

Gate V3-5 is approved and has started at its frozen-contract stage. Target access, development model fitting, establishment-segment access, and V3-9 final-framework-reserve access remain false.
