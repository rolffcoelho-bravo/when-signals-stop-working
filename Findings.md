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

## Version 3 Gate V3-3D — Final acceptance and protected-object lock

### Governance contribution V3-G3D-M1

The final acceptance architecture distinguishes a lock's creation commit from its governed finalization commit. Parent locks are anchored to the exact `parent_lock_blob_sha` recorded by the next gate when that reference exists, while the latest unreferenced lock remains anchored to its creation blob. This permits legitimate pre-freeze finalization without treating it as corruption and still rejects every modification after the governed finalization boundary.

### Validation finding V3-G3D-V1

The integrated Gate V3-3 acceptance suite completed with `46 passed`. The audit verified 59 historical protected objects at their governed finalization points, 58 current objects against their latest owning locks, and one intentional supersession of `src/shockbridge_signal_validity/v3/__init__.py` from V3-1 to V3-2.

### Governance contribution V3-G3D-M2

The final gate preserves an explicit three-state chronology contract: external chronology validation is incomplete, deliberately deferred to the later robustness gate, and not used in estimation, selection, or interpretation. Missing or contradictory chronology fields fail closed.

### Reproducibility finding V3-G3D-V2

The portable V3-3A, V3-3B, and V3-3C lock verifiers all passed under the integrated runner. Automatic model selection, automatic ensembles, and consensus probability remained prohibited, and the frozen Version 1 and Version 2 determinations were not modified.

---

## Version 3 Gate V3-4A — Independent chronology and signal-use eligibility contract

### Methodological contribution V3-G4A-M1

The external chronology must be compiled and locked before model-output overlay. Model-derived event inclusion, chronology-driven threshold selection, chronology-driven model selection, retrospective event deletion, and retrospective event-boundary tuning are prohibited. This creates an independent validation layer rather than an event list reconstructed around model peaks.

### Methodological contribution V3-G4A-M2

Conditional signal degradation is admissible only when unconditional incremental value was established under a frozen pre-regime contract. Because RSI received `NO_PIPELINE_ADMITTED` and Bollinger received `NO_INCREMENTAL_EVIDENCE`, both remain `INELIGIBLE_BASELINE_NOT_ESTABLISHED` and may enter only descriptive regime-sensitivity analysis. Regime conditioning cannot promote either signal or revise either frozen verdict.

### Methodological contribution V3-G4A-M3

The event-alignment protocol separates temporal validation from supervised classification. External chronology is treated as incomplete evidence rather than complete ground truth, and the registered metrics focus on transition capture, overlap, lead time, false-alert burden, post-event decay, probability-rank shift, and cross-model disagreement. Classification metrics remain prohibited unless chronology completeness is established in a later gate.

### Validation finding V3-G4A-V1

The isolated contract suite completed with `15 passed`. Exact Git blob matching confirmed that the tested contract, validator, test, and launcher objects are the objects committed to the repository. Mutation tests fail closed when the parent lock changes, model outputs become visible during chronology compilation, chronology-driven threshold selection is permitted, regime conditioning can promote a signal, signal retuning is allowed, or launcher environment settings hide user-site packages.

---

## Version 3 Gate V3-4B — Independent chronology compilation and provenance

### Methodological contribution V3-G4B-M1

The chronology is represented as a source-driven control registry with separate event, source, event-source, and merge components and a deterministic compiler. Every canonical event requires a primary documentary source, while all supporting candidates remain auditable through the provenance map and merge log. Every retain-or-merge decision records that model outputs were not consulted.

### Methodological contribution V3-G4B-M2

Timestamp precision and boundary uncertainty are explicit research objects. `CONFIRMED` events are eligible for the later primary timing metrics, while `BOUNDARY_UNCERTAIN` and `SOURCE_CONFLICT` events remain visible but are excluded from primary timing. This prevents multi-day collapse, contagion, and retrospectively reported interruption windows from being converted into false point precision.

### Reproducibility finding V3-G4B-V1

The isolated chronology and cross-gate suite completed with `19 passed`. The deterministic compiler reproduced four byte-identical evidence outputs containing 17 canonical events supported by 27 provenance sources. Twelve events are confirmed and timing-eligible, five retain boundary uncertainty and are timing-excluded, and no source-conflict event was forced into the primary set. No Gate V3-3 model output was accessed and no event-alignment analysis was executed.

### Governance contribution V3-G4B-M3

A cross-gate latest-owner audit separates historical integrity from current ownership. It verifies historical protected objects at their governed boundaries while recognizing legitimate later ownership. Frozen prior locks and point-in-time verifiers remain unchanged.

---

## Version 3 repository realignment

### Governance contribution V3-RL-M1

The realignment restores the practitioner's practical question and the scientific priority ordering `ESTABLISHMENT → CONDITIONAL_VALIDITY → DETERIORATION → FAILURE_PROBABILITY → OPERATIONAL_ACTION`. Supporting spectral, panic-consistent, chronology, portability, and lock layers may not substitute for this signal-establishment chain.

### Governance contribution V3-RL-M2

Historical chronology work is preserved without renaming or rewriting its lock objects and is scientifically reclassified as `V3-RV1` and `V3-RV2`. Proposed event alignment is reclassified as `V3-RV3`, paused, and not started. The true Gate V3-4 is restored as the Unified RSI and Bollinger Interpretation Engine.

### Validation finding V3-RL-V1

The corrected repository realignment suite completed with `7 passed`. It verifies the practitioner's question, frozen Version 1 and Version 2 determinations, chronology reclassification, the establishment-before-failure sequence, final V3-4 lock, active V3-5 contract boundary, and fail-closed protection of the V3-9 final-framework reserve.

---

## Version 3 Gate V3-4 — Unified RSI and Bollinger interpretation engine

### Implementation contribution V3-G4-M1

A compact, bounded, machine-readable registry expands deterministically to 48 stable signal specifications: 44 base specifications, four explicit market-state interactions, and two training-only adaptive templates. Every expanded identifier encodes family, window, parameters, orientation, interpretation, crossing, persistence, normalization, interaction policy, registry version, and parameter policy. Automatic candidate selection is prohibited.

### Implementation contribution V3-G4-M2

The engine implements target-blind causal RSI and Bollinger interpretation families. RSI includes level, centered level, slope, acceleration, range, divergence, mean-reversion, continuation, crossings, duration, persistence, and extreme-exit features. Bollinger includes percentage-B, normalized distances, mean-reversion, breakout and breakdown, re-entry, bandwidth dynamics, squeeze transitions, persistence, and event timing.

Adaptive candidates are not silently estimated by the engine. They remain visible as `INELIGIBLE_TRAINING_PARAMETER_REQUIRED` until training-only parameters are supplied. Invalid supplied thresholds fail closed.

### Implementation contribution V3-G4-M3

The engine emits every registered specification for every canonical source row in deterministic long format. Missing context remains visible as `INELIGIBLE_CONTEXT_UNAVAILABLE`; early-history and undefined values remain explicit; no sparse or unpromising candidate is deleted. Four registered interactions preserve `base_signal_value`, `context_value`, and their product separately.

### Authoritative validation finding V3-G4-V1

The authoritative Windows execution passed the corrected seven-test realignment suite and exact nineteen-test signal-engine suite. The frozen SOL source produced 12,171 canonical rows and 584,208 feature rows across 48 registered specifications, exactly satisfying `source rows × signal count`. Target access, chronology access, automatic selection, predictive claims, economic claims, deterioration claims, failure claims, and tracked working-tree mutation all remained false.

### Reproducibility finding V3-G4-V2

The validated implementation is frozen at commit `ff2e7ecba3fa69f22e0b109437d23b52d30fba2b`. Compact evidence was materialized at commit `705511de9e8ee22a9f8aff34506aebb6c26223e7`, and the final lock status is `IMPLEMENTATION_VALIDATED_AND_LOCKED`. The large 584,208-row feature table remains untracked and is bound by SHA-256; seven compact manifests are committed under `evidence/v3/g4_signal_lock/`.

### Scientific boundary V3-G4-B1

Gate V3-4 establishes only that the signal-information engine is reproducible, causal, bounded, and locked. It does not establish predictive or economic value for RSI or Bollinger and does not make deterioration or failure modelling admissible.

---

## Version 3 Gate V3-5 — Matched benchmark-versus-signal forecast selection

### Methodological contribution V3-G5-M1

The Gate V3-5 contract freezes the matched comparison before target access:

```text
candidate = benchmark information + registered signal information
```

Benchmark and candidate must otherwise share model class, rows, preprocessing, hyperparameter selection, calibration, target, horizon, decision policy, and transaction-cost treatment. Candidate-specific missingness is handled through a matched row intersection, preventing raw metric comparisons across unequal samples.

### Methodological contribution V3-G5-M2

The contract preserves Version 2 continuity at 4, 8, 12, and 24 hours and adds the declared Version 3 horizons of 48 and 72 hours. Direction remains confirmatory; expected return and training-defined large-move probability remain secondary. Confirmatory RSI and Bollinger families use Holm control at five percent, while secondary analyses use Benjamini–Hochberg control at `q = 0.10`.

### Methodological contribution V3-G5-M3

The frozen data partition separates development selection through 30 June 2025, a signal-establishment segment from 1 July through 31 December 2025, and a final-framework reserve from 1 January through 22 July 2026. Gate V3-5 cannot access the 2026 reserve, which is reserved for Gate V3-9 evaluation of the complete forecast, failure-risk, and decision pipeline. Early access fails closed as `PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED`.

### Methodological contribution V3-G5-M4

The candidate space accepts all 48 locked signal specifications, eight predeclared within-family blocks, and a secondary combined-family block while prohibiting unrestricted Cartesian combinations, deep neural networks, unbounded automated search, post-result model insertion, silent candidate deletion, and regime-based rescue tuning.

### Current validation boundary V3-G5-B1

Gate V3-5 implementation has started only at the contract-freeze stage. Target generation, chronological folds, benchmark assembly, model fitting, pipeline admission, establishment authorization, establishment-segment access, and empirical determination have not started. No predictive or economic finding is recorded for Gate V3-5 yet.

---

## Findings pending later gates

The following are approved development directions but are not yet findings:

- Gate V3-5 target, fold, benchmark, matched candidate, development selection, admission, establishment, and inference implementation;
- any Gate V3-5 empirical signal-establishment determination;
- prospective failure-event construction, only for an established signal;
- signal-failure probability, only after an admissible failure definition;
- Gate V3-9 final-framework evaluation using the protected 2026 reserve;
- independent regime-event alignment under `V3-RV3`;
- empirical real-market regime probabilities and episode interpretation;
- cross-asset and cross-venue transportability.

They will be moved into findings sections only after implementation and validation. The frozen Version 1 and Version 2 determinations remain unchanged, and Gate V3-4 does not establish predictive value, economic value, deterioration, or failure probability.
