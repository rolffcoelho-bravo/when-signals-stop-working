# Gate V3-4 — Unified RSI and Bollinger Interpretation Engine

## Gate status

```text
APPROVED_AND_REOPENED
IMPLEMENTATION_NOT_STARTED
```

## Objective

Create a bounded, reproducible, target-blind signal-information engine for RSI and Bollinger Bands. The engine represents each indicator as a family of explicit interpretations rather than as one fixed trading rule.

This gate does not estimate predictive value. It generates the signal information that Gate V3-5 will test against matched non-signal benchmarks.

## Parent boundary

Gate V3-4 consumes:

- the V3-1 canonical OHLCV contract;
- causal information measurable at or before timestamp `t`;
- optional regime and market-structure outputs through stable registered interfaces;
- no external chronology for parameter selection or feature construction.

The frozen Version 1 and Version 2 determinations remain unchanged.

## Required signal registry

Every signal specification must have a stable identifier encoding at least:

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
```

The same identifier must regenerate the same feature values in development, locked evaluation, external replication, and later scoring.

## RSI interpretations

The bounded registry must include predeclared candidates from the following groups.

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

## Bollinger interpretations

The bounded registry must include predeclared candidates from the following groups.

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

The engine may generate explicit signal-regime interaction features using registered V3-3 outputs. Every interaction must preserve both components separately.

Examples:

```text
rsi_oversold_mean_reversion × p_range
rsi_overbought_continuation × p_trend
bollinger_lower_breakdown × p_panic_consistent
bollinger_squeeze_release × dominant_eigenvalue_share
```

These interactions are candidate information. Their existence does not establish conditional signal value.

## Required implementation modules

The gate should produce at minimum:

```text
configs/v3_signal_interpretation_registry.json
src/shockbridge_signal_validity/v3/signal_registry.py
src/shockbridge_signal_validity/v3/signal_engine.py
src/shockbridge_signal_validity/v3/signal_runner.py
scripts/run_v3_signal_engine.py
tests/test_v3_signal_registry.py
tests/test_v3_signal_engine.py
tests/test_v3_signal_runner.py
RUN_V3_G4_SIGNAL_ENGINE.ps1
RUN_V3_G4_SIGNAL_ENGINE.sh
docs/V3_G4_SIGNAL_ENGINE.md
```

## Required outputs

```text
signal_features.csv
signal_registry_manifest.json
signal_feature_manifest.json
signal_coverage_report.json
signal_validation_report.json
```

The output must preserve stable identifiers and make missing or ineligible features explicit.

## Acceptance criteria

1. Every registered feature is reproducible from its identifier.
2. All calculations are causal and target-blind.
3. Appending future observations cannot change earlier emitted features.
4. Input row order cannot change ordered output identity.
5. Missing required OHLCV data fails closed.
6. No candidate is deleted because it appears unpromising.
7. No signal, threshold, interpretation, or interaction is selected automatically.
8. Fixed and adaptive candidates remain distinguishable.
9. The registry is bounded and machine-readable.
10. The same engine is used by later development, locked evaluation, replication, and scoring.
11. Version 1 and Version 2 verdicts remain unchanged.
12. No predictive, economic, deterioration, or failure claim is produced by this gate.

## Prohibited actions

Gate V3-4 may not:

- fit a target model;
- inspect future returns during feature generation;
- rank candidates by locked-evaluation performance;
- use external chronology to tune signal definitions;
- promote RSI or Bollinger to `VALID` or `CONDITIONALLY_VALID`;
- declare that either signal stopped working;
- estimate signal-failure probability;
- remove negative or low-coverage candidates after seeing results.

## Next gate

After implementation, validation, and lock of this signal engine, the next core gate is:

> Gate V3-5 — Matched Benchmark-versus-Signal Forecast Selection

That gate, not V3-4, determines whether any new Version 3 signal pipeline earns establishment.
