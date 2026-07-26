# Gate V3-3B — Panic-Consistent Probabilistic Regime Engine

## Purpose

Gate V3-3B implements the first causal probability layer of Version 3. It transforms the locked V3-2 and V3-2B market-structure evidence into governed mechanism-family scores and reports every registered regime model without automatic selection.

This subgate is an implementation layer. Probability uncertainty, transition matrices, episode duration, final occupancy evidence, mechanism-contribution decomposition, the approved cross-model disagreement index, and the final V3-3 lock remain responsibilities of V3-3C and V3-3D.

## Inputs

The engine consumes the two protected Gate V3-2B outputs:

```text
market_structure_features.csv
causal_series_features.csv
```

The dependence window is supplied explicitly in configuration. The engine cannot choose a favourable window.

Asset-level liquidity, funding, volatility, and downside features are aggregated cross-sectionally through the median at each timestamp. The reference series used by the transparent challenger is also fixed in configuration.

## Mechanism transformation

Each registered feature is transformed so larger directed values indicate greater mechanism pressure. Scaling uses expanding robust historical location and scale estimates fitted only on prior observations.

For feature \(j\),

\[
z_{j,t}
=
d_j
\frac{x_{j,t}-\operatorname{median}(x_{j,<t})}
{1.4826\,\operatorname{MAD}(x_{j,<t})+\varepsilon}.
\]

The historical parameters are refreshed on a predeclared interval and held fixed between refresh points. This preserves exact prefix invariance while avoiding a retrospective full-sample transformation.

The directed score is

\[
m_{j,t}=\frac{1}{1+e^{-\operatorname{clip}(z_{j,t},-5,5)}}.
\]

Feature scores are combined by the within-family median. A mechanism family remains unavailable unless it contains the registered minimum number and fraction of valid features.

## Evidence sufficiency

A probability requires:

- at least four available mechanism families;
- spectral or network evidence;
- liquidity or funding evidence;
- volatility or downside evidence.

When these conditions fail, the engine publishes:

```text
INSUFFICIENT_MECHANISM_EVIDENCE
```

It does not interpret missing evidence as low panic consistency.

## Registered models

### V2 transparent state challenger

`V2_TRANSPARENT_STATE_CHALLENGER_V1` preserves the earlier range, trend, and stress filter as a non-panic challenger. It is trained on a fixed initial history of the configured reference series and forward-filtered afterward.

It reports:

```text
p_range
p_trend
p_stress
```

Its panic probability fields remain empty and `panic_probability_authorized` is always false.

### Monotone mechanism score

For sufficient family evidence,

\[
q_t=\frac{1}{|\mathcal{G}_t|}\sum_{g\in\mathcal{G}_t}M_g(t),
\]

and

\[
p_t=\frac{1}{1+\exp\{-6(q_t-0.5)\}}.
\]

The probability is filtered through the registered causal EWMA. Family weights are equal and no fitting against a panic label occurs.

### Causal Gaussian HMM

`CAUSAL_GAUSSIAN_HMM_V1` is a deterministic two-state diagonal-Gaussian hidden Markov model over the six family scores.

At forecast origin \(t\):

1. parameters are estimated only from the prefix ending at \(t-1\);
2. the current observation is processed through a one-step forward filter;
3. previously emitted probabilities are never revised;
4. the panic-consistent state is anchored by higher composite pressure and higher pressure in at least four families;
5. failed anchoring or minimum occupancy invalidates the model rather than triggering relabelling.

No retrospective smoothed state probability is emitted.

## Ambiguous topology control

The upstream `contagion_radius` variable is a radius measured in correlation-distance space. Greater market dependence can reduce this distance radius, while greater network fragmentation can increase it. It therefore lacks a universally monotone panic direction in its raw form.

Gate V3-3B excludes this variable from the default mechanism score and records the exclusion in diagnostics. A future transformation may be admitted only through an explicit protocol amendment or registered challenger. This is preferable to assigning a convenient sign silently.

## Output contract

Gate V3-3B writes:

```text
panic_regime_probability.csv
mechanism_family_scores.csv
regime_manifest.json
regime_validation_report.json
probability_engine_diagnostics.json
```

The probability file uses long format with one row per timestamp and registered model.

The uncertainty columns are present but remain empty with:

```text
PENDING_V3_3C
```

This prevents implementation probabilities from being misrepresented as final publishable probability evidence.

## Reproducibility

The manifest binds:

- selected market-structure input;
- causal-series input;
- complete engine configuration;
- mechanism-family score output;
- long-format probability output;
- registered model identifiers;
- dependence window and reference series.

Shuffled input order must produce the same ordered evidence and manifest identity.

## Execution

First install the repository package and development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Then execute:

```powershell
.\RUN_V3_G3B_PROBABILISTIC_ENGINE.ps1 `
  -Config "configs/v3_panic_regime_example.json" `
  -OutputDirectory "outputs/v3/panic_regime"
```

The wrapper also sets `PYTHONPATH` to the repository `src` directory, verifies the V3-3A lock, runs the isolated V3-3A and V3-3B tests, executes the engine, and verifies the V3-3B implementation lock.

## Model boundaries

Gate V3-3B does not establish that the market was psychologically panicked. It does not provide final uncertainty intervals, choose a preferred regime model, validate historical event alignment, evaluate RSI or Bollinger, forecast returns, estimate signal-failure risk, or authorize a trading action.

Its role is to implement causal and reproducible model probabilities under the locked identification contract. Final scientific use requires V3-3C diagnostics and V3-3D acceptance.
