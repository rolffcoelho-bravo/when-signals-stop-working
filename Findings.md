# Research Findings and Novel Contributions

## Governance rule

This file preserves findings that are supported by frozen empirical evidence, analytical fixtures, synthetic validation, or locked methodological results. It separates empirical market findings from methodological and implementation contributions. Proposed ideas are not recorded as findings until implemented and validated.

---

## Version 1 — Parsimonious technical-signal validation

### Empirical finding V1-F1

Under the frozen SOL/USDT four-hour design, stable incremental predictive value was not established for RSI, Bollinger Bands, or the combined specification.

- RSI contributed positively in 1 of 5 chronological folds.
- Bollinger Bands contributed positively in 1 of 5 chronological folds.
- The combined specification contributed positively in 2 of 5 chronological folds.
- All three received `NOT_ESTABLISHED` status.

### Methodological contribution V1-M1

The framework established the governance principle that deterioration or suspension cannot be claimed unless signal value was first established under a predeclared benchmark-relative and chronological validation contract.

---

## Version 2 — Conditional validity and inference hardening

### Empirical finding V2-F1

No RSI development pipeline satisfied the frozen admission requirements. The Version 2 RSI family received `NO_PIPELINE_ADMITTED` and was not allowed to enter locked evaluation.

### Empirical finding V2-F2

The sole admitted Bollinger pipeline produced favourable average contributions in parts of the locked sample, but stable incremental value was not established.

- Mean benchmark-relative log-loss contribution: `0.002108928`.
- Positive locked subperiods: 2 of 3.
- Raw one-sided p-value: `0.032339`.
- Holm-adjusted p-value: `0.064677`.
- Dependence-aware predictive and economic lower confidence bounds crossed zero.
- Final status: `NO_INCREMENTAL_EVIDENCE`.

### Methodological contribution V2-M1

The Version 2 programme demonstrated that favourable average results do not constitute establishment when multiplicity-adjusted, dependence-aware, chronological, economic, calibration, and concentration controls are not jointly satisfied.

### Methodological contribution V2-M2

The locked evaluation architecture prevented RSI re-entry, Bollinger retuning, panic-state rescue, and post-result hypothesis changes after development admission and holdout access.

---

## Version 3 Gate V3-1 — Canonical data and adapter layer

### Implementation contribution V3-G1-M1

The canonical schema and adapter interface decouple source-specific layouts from research logic. CSV, Parquet, exchange OHLCV, and governed optional-field sources can map into one deterministic market-data contract without changing model modules.

### Validation finding V3-G1-V1

The isolated conformance suite established that independently formatted source datasets map deterministically into the same canonical schema, while duplicate keys, invalid OHLC relationships, timestamp failures, and other critical schema defects fail closed.

---

## Version 3 Gate V3-2 — Causal spectral engine

### Methodological contribution V3-G2-M1

The spectral layer creates a fixed-panel, forward-measurable market-structure state using dominant eigenvalue share, eigenvalue gap, participation ratio, spectral entropy, first-eigenvector concentration, correlation statistics, and threshold-network descriptors without defining panic from any single measure.

### Validation finding V3-G2-V1

Analytical matrix fixtures establish that the spectral implementation reproduces expected identity, common-mode, and structured dependence behavior within registered numerical tolerances.

### Governance contribution V3-G2-M2

Panel membership and dependence windows are predeclared. Insufficient coverage remains visible and cannot be repaired by retrospective asset removal or favourable-window selection.

---

## Version 3 Gate V3-2B — Market-structure extension

### Methodological contribution V3-G2B-M1

The framework extends spectral concentration into threshold-network topology, deterministic community structure, and minimum-spanning-tree geometry while preserving the original V3-2 lock.

### Validation finding V3-G2B-V1

A synthetic two-block dependence fixture recovers two communities with positive modularity, while perfect common-mode dependence produces a complete network and one community.

### Validation finding V3-G2B-V2

Every deterministic minimum spanning tree contains exactly `N - 1` edges, remains invariant to shuffled member order under stable identifiers, and handles zero-distance common-mode edges after an identified edge-case remediation.

### Governance contribution V3-G2B-M2

Network threshold, community resolution, panel, and window selection remain configuration decisions. The extension does not search automatically for a favourable market structure.

---

## Version 3 Gate V3-3A — Panic-regime identification freeze

### Methodological contribution V3-G3A-M1

Panic-consistent inference is identified through concurrence across six economically distinct mechanism families: spectral, network, liquidity, funding, volatility, and downside dynamics.

A valid probability requires at least four families and evidence from structural, market-plumbing, and price-risk blocks. Otherwise the correct state is `INSUFFICIENT_MECHANISM_EVIDENCE`.

### Methodological contribution V3-G3A-M2

Without a governed external panic label, supervised logistic panic estimation is scientifically inadmissible. The permitted outputs are a transparent challenger, a governed mechanism-consistency probability, and a model-conditional forward-filtered latent-state posterior.

### Methodological contribution V3-G3A-M3

The model registry prohibits automatic model selection, automatic ensembles, champion promotion, and a hidden consensus probability. Cross-model disagreement remains observable model-risk evidence.

### Methodological contribution V3-G3A-M4

HMM state identity is governed by an economic anchor: the panic-consistent state must exhibit the highest composite mechanism pressure and higher pressure in at least four of six families. Failed anchoring invalidates the model rather than permitting convenient relabelling.

---

## Version 3 Gate V3-3B — Probabilistic engine implementation

### Implementation contribution V3-G3B-M1

The engine implements causal robust scaling with expanding prior-only median and median absolute deviation estimates, refreshed on a predeclared interval and held fixed between refresh points. Appending future observations cannot revise previously emitted scores or probabilities.

### Implementation contribution V3-G3B-M2

The engine reports three mandatory models in long format for every timestamp:

1. `V2_TRANSPARENT_STATE_CHALLENGER_V1`;
2. `MONOTONE_MECHANISM_SCORE_V1`;
3. `CAUSAL_GAUSSIAN_HMM_V1`.

No model is automatically selected or averaged.

### Synthetic validation finding V3-G3B-V1

In a preconstructed synthetic transition where spectral concentration, network integration, liquidity deterioration, funding stress, volatility, and downside pressure rise jointly, the monotone mechanism probability increases materially after the transition while remaining bounded in `[0,1]`.

This is an implementation-validation result, not an empirical claim about a historical market episode.

### Synthetic validation finding V3-G3B-V2

Future-append mutation tests confirm exact earlier-probability invariance for the transparent challenger, monotone mechanism score, and causal HMM outputs.

### Synthetic validation finding V3-G3B-V3

Removing both liquidity and funding evidence forces the engine to return `INSUFFICIENT_MECHANISM_EVIDENCE`, even when spectral, network, volatility, and downside pressure are elevated. The implementation therefore does not allow price-only stress to impersonate a fully supported panic mechanism.

### Synthetic validation finding V3-G3B-V4

The causal HMM produces bounded forward-filtered probabilities only after sufficient prior history and state anchoring. Refits that fail the four-family directional anchor or minimum occupancy remain invalid rather than being relabelled.

### Methodological finding V3-G3B-M3

The upstream `contagion_radius` variable is a radius in correlation-distance space and does not possess a universally monotone panic direction in raw form. Stronger common dependence can reduce the radius, while fragmentation can increase it. Gate V3-3B therefore excludes it from the default probability score and records the exclusion explicitly instead of assigning a silent sign.

### Reproducibility finding V3-G3B-V5

Shuffling market-level and asset-level input order produces identical ordered probabilities and deterministic manifest identity.

---

## Version 3 Gate V3-3C — Governance and diagnostics

### Methodological contribution V3-G3C-M1

The framework separates a computable point probability from a publishable probability. Panic-authorized point estimates receive deterministic, prefix-respecting moving-block intervals in logit-innovation space. Estimates with insufficient prior interval history remain visible but are explicitly nonpublishable.

This prevents a functioning probability formula from being presented as complete uncertainty evidence.

### Synthetic validation finding V3-G3C-V1

The registered interval procedure produces bounded intervals containing the contemporaneous point probability, while future-append tests confirm that later observations cannot revise earlier intervals, publishability status, confirmed states, transition risks, or disagreement diagnostics.

### Methodological contribution V3-G3C-M2

Operational episodes and transitions use two-observation causal confirmation without retrospective backfill. An isolated threshold crossing cannot rewrite the first crossing date or create a completed episode retrospectively.

### Methodological contribution V3-G3C-M3

Transition evidence combines Dirichlet-smoothed operational-state matrices with a forward-filtered HMM posterior-implied binary transition diagnostic. Every estimated transition row is constrained to sum to one, and no retrospectively smoothed latent path is introduced.

### Methodological contribution V3-G3C-M4

The monotone mechanism model admits an exact family decomposition in logit space. The HMM receives a separate causal ridge-surrogate neutral-perturbation diagnostic that is explicitly labelled as approximate rather than presented as an exact likelihood decomposition.

### Methodological contribution V3-G3C-M5

Cross-model disagreement is formalized as the absolute difference between the monotone and HMM probabilities, with interval-overlap evidence and a `HIGH_MODEL_RISK_ESCALATION` class. The index remains diagnostic and cannot select a preferred model or create an ensemble.

### Methodological contribution V3-G3C-M6

The mechanism-coverage layer maps evidence by timestamp, market panel, `asset@venue`, feature, family, and evidence block. Missingness becomes an auditable data-investment map rather than an invisible preprocessing issue. The governed exclusion of `contagion_radius` remains visible in the coverage evidence.

### Synthetic validation finding V3-G3C-V2

The isolated governance suite establishes deterministic transition matrices, duration and occupancy outputs, exact monotone contribution accounting, causal HMM surrogate diagnostics, non-selective disagreement evidence, coverage-map determinism, and threshold, EWMA, scaling-refit, and HMM-refit sensitivity reporting.

### Governance contribution V3-G3C-M7

All sensitivity alternatives are reported without model selection. External market-dislocation chronology remains deferred and cannot train the current models, select thresholds, or redefine the latent regime after observing results.

---

## Findings pending later gates

The following are approved development directions but are not yet findings:

- final integrated V3-3 protected-object acceptance and lock;
- external event-chronology validation;
- conditional RSI and Bollinger validity under the inferred regimes;
- empirical real-market regime probabilities and episode interpretation;
- cross-asset and cross-venue transportability of the regime engine.

They will be moved into the findings sections only after implementation and validation.
