# Gate V3-4 — Unified RSI and Bollinger Interpretation Engine

## Gate status

```text
APPROVED_AND_REOPENED
IMPLEMENTATION_COMPLETE
AUTHORITATIVE_VALIDATION_COMPLETE
IMPLEMENTATION_VALIDATED_AND_LOCKED
GATE_COMPLETE
```

## Objective

Create a bounded, reproducible, target-blind signal-information engine for RSI and Bollinger Bands. The engine represents each indicator as a family of explicit interpretations rather than as one fixed trading rule.

This gate does not estimate predictive value. It generates the signal information that Gate V3-5 tests against matched non-signal benchmarks.

## Parent boundary

Gate V3-4 consumes:

- the V3-1 canonical OHLCV contract;
- causal information measurable at or before timestamp `t`;
- optional regime and market-structure outputs through stable registered interfaces;
- no external chronology for parameter selection or feature construction.

The frozen Version 1 and Version 2 determinations remain unchanged.

## Required signal registry

Every signal specification has a stable identifier encoding at least:

```text
signal_family
lookback_or_window
threshold_or_band_parameter
orientation
interpretation
crossing_rule
persistence_rule
normalisation_rule
regime_interaction_policy
registry_version
parameter_policy
```

The same identifier must regenerate the same feature values in development, locked evaluation, external replication, and later scoring.

## RSI interpretations

The bounded registry includes predeclared candidates from the following groups.

### Mean reversion

- overbought mean reversion;
- oversold mean reversion;
- symmetric two-sided mean reversion.

### Continuation

- overbought continuation;
- oversold continuation;
- threshold-break continuation.

### Event and persistence structure

- upward and downward threshold crossings;
- time above or below threshold;
- consecutive-period persistence;
- time since crossing;
- exit from extreme region.

### Shape and dynamics

- RSI level;
- centered and scaled RSI level;
- slope;
- acceleration;
- rolling range;
- price-RSI divergence using causal trailing definitions only.

### Adaptive thresholds

Adaptive thresholds are permitted only when:

- the threshold family is registered before evaluation;
- estimation occurs inside training data only;
- no locked-evaluation or chronology outcome influences the threshold;
- fixed-threshold challengers remain visible.

The Gate V3-4 implementation does not estimate adaptive thresholds. Training-only values must be supplied through an upstream training contract; otherwise the candidate remains visible as `INELIGIBLE_TRAINING_PARAMETER_REQUIRED`.

## Bollinger interpretations

### Mean reversion

- upper-band mean reversion;
- lower-band mean reversion;
- re-entry after an outside-band observation.

### Continuation and breakout

- upper-band breakout;
- lower-band breakdown;
- continuation after outside-band persistence.

### Relative position

- percentage-B;
- signed normalized distance from the middle band;
- signed normalized distance from the nearest outer band;
- distance magnitude.

### Volatility structure

- bandwidth level;
- bandwidth change;
- bandwidth acceleration;
- squeeze indicator from training-only or fixed registered boundaries;
- post-squeeze expansion;
- expansion persistence.

### Event and persistence structure

- crossing of the upper or lower band;
- time outside the bands;
- consecutive outside-band observations;
- re-entry timing;
- time since squeeze release.

## Regime interactions

The engine generates four explicit signal-regime interaction candidates through registered interfaces while preserving both components separately:

```text
rsi_oversold_mean_reversion × p_range
rsi_overbought_continuation × p_trend
bollinger_lower_breakdown × p_panic_consistent
bollinger_squeeze_release × dominant_eigenvalue_share
```

Their existence does not establish conditional signal value. When context is unavailable, the interaction remains visible as `INELIGIBLE_CONTEXT_UNAVAILABLE`.

## Implemented modules

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
V3_G4_SIGNAL_ENGINE_LOCK.json
```

## Output contract

```text
signal_features.csv
signal_registry_manifest.json
signal_feature_manifest.json
signal_coverage_report.json
signal_validation_report.json
canonical_validation_report.json
```

The output preserves stable identifiers and makes missing or ineligible features explicit.

## Locked registry boundary

```text
registered specifications: 48
base specifications: 44
explicit regime interactions: 4
training-only adaptive templates: 2
bounded maximum: 128
automatic selection: false
```

## Acceptance evidence

All acceptance criteria passed:

1. every registered feature is reproducible from its identifier;
2. calculations are causal and target-blind;
3. future observations cannot change earlier emitted features;
4. input row order cannot change ordered output identity;
5. missing required OHLCV data fails closed;
6. no candidate is deleted because it appears unpromising;
7. no signal, threshold, interpretation, or interaction is selected automatically;
8. fixed and adaptive candidates remain distinguishable;
9. the registry is bounded and machine-readable;
10. later gates reuse the locked engine;
11. Version 1 and Version 2 verdicts remain unchanged;
12. no predictive, economic, deterioration, or failure claim was produced;
13. the exact nineteen-test suite passed in the authoritative research environment;
14. real canonical input generated the complete package without tracked-file mutation.

Authoritative totals:

```text
source rows: 12171
registered signals: 48
feature rows: 584208
row-count identity: verified
validated implementation commit: ff2e7ecba3fa69f22e0b109437d23b52d30fba2b
evidence materialization commit: 705511de9e8ee22a9f8aff34506aebb6c26223e7
lock status: IMPLEMENTATION_VALIDATED_AND_LOCKED
```

## Prohibited actions

The final V3-4 boundary did not:

- fit a target model;
- inspect future returns during feature generation;
- rank candidates by evaluation performance;
- use external chronology to tune signal definitions;
- promote RSI or Bollinger to `VALID` or `CONDITIONALLY_VALID`;
- declare that either signal stopped working;
- estimate signal-failure probability;
- remove negative or low-coverage candidates after seeing results.

## Next gate

The current core gate is:

> Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection

Gate V3-5 is approved and active at its contract-freeze stage. It, not V3-4, determines whether any new Version 3 signal pipeline earns establishment.
