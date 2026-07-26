# Gate V3-3C — Panic-Regime Governance and Diagnostics

## Purpose

Gate V3-3C converts the locked V3-3B point-probability engine into a governed evidence layer. It does not refit, select, average, or replace the registered models. It adds uncertainty, state-transition, occupancy, duration, explanation, disagreement, coverage, and sensitivity evidence while preserving every V3-3B protected Git object.

## Probability publication boundary

A point probability is not automatically a publishable probability. For each panic-authorized model, the diagnostics layer estimates a 95% prefix-respecting moving-block interval from strictly prior probability-path innovations in logit space.

The interval uses:

- 250 registered bootstrap replications;
- at least 200 valid replications;
- a deterministic timestamp- and model-specific seed;
- a block length of `max(2, ceil(1.5 * n_valid^(1/3)))`;
- no future observations;
- no retrospective state smoothing.

A row without sufficient interval history remains visible, but receives:

```text
probability_publishable = false
uncertainty_status = INSUFFICIENT_INTERVAL_HISTORY
model_validity = VALID_POINT_ESTIMATE_INTERVAL_UNAVAILABLE
```

The interval describes uncertainty in the causal probability path under the registered model. It is not an externally calibrated confidence interval for the frequency of psychological panic or future crashes.

## Causal state confirmation

Operational states require two consecutive qualifying observations. Confirmation is forward-only:

1. the first observation creates a candidate state;
2. the second consecutive observation confirms it;
3. the first observation is not rewritten;
4. transitions require the same two-observation confirmation;
5. insufficient evidence resets the confirmation process.

This rule prevents isolated threshold crossings from creating or backfilling episodes.

## Transition evidence

The layer reports:

- Dirichlet-smoothed operational-state transition matrices for every registered model;
- 95% posterior intervals for each transition probability;
- one-step probability of transition to `PANIC_CONSISTENT_REGIME`;
- a forward-filtered HMM binary transition diagnostic based on posterior-implied expected transition counts.

Every transition row must sum to one. HMM transition evidence uses only forward-filtered probabilities and does not reconstruct smoothed latent paths.

## Duration and occupancy

`state_duration.csv` records:

- model and state;
- episode start and end;
- observation duration;
- right-censoring;
- minimum-duration validity;
- explicit confirmation that no retroactive backfill occurred.

`occupancy_statistics.json` reports state counts, fractions, episode counts, and duration summaries. The HMM binary occupancy diagnostic applies the frozen minimum-count and minimum-fraction boundaries. A collapsed state remains a model-invalidity result.

## Mechanism contributions

### Monotone model

The monotone model receives an exact decomposition in logit space. With available family set \(\mathcal G_t\),

\[
\operatorname{logit}(p_t)
=
\sum_{g\in\mathcal G_t}
\frac{6\,[M_g(t)-0.5]}{|\mathcal G_t|}.
\]

The output also reports the probability change obtained by replacing one family score with the neutral value 0.5 while holding the other families fixed.

### HMM

The HMM receives a causal ridge-surrogate perturbation diagnostic. At registered refit origins, a ridge model is estimated using only prior family scores and prior HMM logits. Each family is then neutralized at 0.5 to approximate its local posterior contribution.

This is explicitly labelled:

```text
VALID_DIAGNOSTIC_SURROGATE_NOT_EXACT_HMM_DECOMPOSITION
```

It is not presented as an exact decomposition of the HMM likelihood.

## Cross-model disagreement

The disagreement index is:

\[
\Delta_t
=
|p_t^{\mathrm{monotone}}-p_t^{\mathrm{HMM}}|.
\]

Registered diagnostic classes are:

```text
LOW
MODERATE
HIGH_MODEL_RISK_ESCALATION
INSUFFICIENT_MODEL_EVIDENCE
```

The output also reports probability-interval overlap. Disagreement is a model-risk signal. It cannot select a model, produce a champion, or create an ensemble probability.

## Mechanism coverage and data-investment map

Coverage is reported by:

- timestamp;
- `asset@venue` series;
- market panel;
- source column;
- registered feature;
- mechanism family;
- evidence block.

The summary classifies data-investment priority from the observed coverage, with special attention to liquidity and funding evidence. The governed exclusion of raw `contagion_radius` remains visible in the coverage table rather than disappearing from the audit trail.

The runner creates a deterministic SVG mechanism-coverage heatmap.

## Sensitivity evidence

The layer reports all predeclared alternatives without selecting among them:

- central and neighboring probability thresholds;
- monotone EWMA alphas 0.20, 0.35, and 0.50;
- probability jumps at robust-scaling refit boundaries;
- HMM probability jumps at refit origins;
- valid and invalid HMM refits;
- HMM saturation below 0.01 or above 0.99.

Sensitivity results cannot change the central probability, model identity, or registered thresholds.

## Required outputs

```text
panic_regime_probability.csv
transition_matrix.json
state_duration.csv
occupancy_statistics.json
mechanism_contributions.csv
probability_diagnostics.json
regime_manifest.json
regime_validation_report.json
```

Additional decision-grade outputs are:

```text
cross_model_disagreement.csv
mechanism_coverage.csv
mechanism_coverage_summary.json
mechanism_coverage_heatmap.svg
sensitivity_diagnostics.json
```

## External chronology boundary

The approved external market-dislocation chronology remains deferred to a later robustness gate. It is not used to train models, select thresholds, identify states, or redefine the probability methodology in V3-3C.

## Gate boundary

V3-3C does not:

- modify the V3-3B engine;
- alter Version 1 or Version 2 findings;
- select a preferred probability model;
- average model probabilities;
- claim psychological panic;
- perform external chronology validation;
- authorize the final V3-3 lock.

The next subgate is V3-3D, which must verify all V3-3A, V3-3B, and V3-3C protected objects, execute the complete isolated acceptance suite, and create the final Gate V3-3 lock and checkpoint.
