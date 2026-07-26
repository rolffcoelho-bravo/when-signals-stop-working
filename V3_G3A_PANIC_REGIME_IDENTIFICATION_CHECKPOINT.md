# Gate V3-3A — Panic-Consistent Regime Identification Checkpoint

## Gate status

> `IDENTIFICATION_CONTRACT_COMPLETE_AND_LOCKED`

Gate V3-3A is complete and locked as an identification and model-contract subgate. The probabilistic engine itself is not yet implemented, empirically evaluated, or authorized for the final V3-3 lock.

## Repository position

- frozen baseline: `v2.0.0`;
- baseline commit: `5a07299367b80c3940e652e7bbdd208ce86ba5ef`;
- Version 3 branch: `research/v3-adaptive-signal-validity`;
- parent gate: `V3-2B — Market Structure Extension`;
- parent lock: `V3_G2B_MARKET_STRUCTURE_LOCK.json`;
- parent lock blob: `1aa5e990c9d352d50b1d8da265811a16bca00bac`;
- V3-3A identification boundary commit: `50e9cc433324281fc1270fae57aeea2656ba69fc`;
- V3-3A lock commit: `3dd9556bdba262da43f76b51081faf0401b9ed3d`;
- V3-3A lock blob: `b8cabd84feb6389d727fbc5cb013fed7472c87e2`;
- Version 1 and Version 2 determinations modified: none;
- V3-2 and V3-2B protected files modified: none.

## Implemented components

### Machine-readable identification contract

`configs/v3_panic_regime_identification.json` freezes:

- the latent estimand;
- causal claim boundaries;
- the six mechanism families;
- feature directions and aggregation rules;
- expanding robust historical scaling;
- evidence-sufficiency requirements;
- fail-closed behaviour;
- operational interpretation thresholds;
- threshold and smoothing sensitivity policies;
- uncertainty methodology;
- transition requirements;
- occupancy and duration rules;
- label-switching controls;
- deterministic-manifest requirements;
- required final V3-3 outputs;
- prohibited operations and interpretations.

### Governed model registry

`configs/v3_panic_regime_model_registry.json` registers three mandatory, non-ranked models:

1. `V2_TRANSPARENT_STATE_CHALLENGER_V1`;
2. `MONOTONE_MECHANISM_SCORE_V1`;
3. `CAUSAL_GAUSSIAN_HMM_V1`.

All enabled models must be reported. Automatic model selection, champion promotion, automatic ensembles, and a consensus probability are prohibited.

### Scientific documentation

`docs/V3_PANIC_REGIME_IDENTIFICATION.md` documents the estimand, mechanism system, causal scaling, model semantics, uncertainty, thresholds, occupancy, label anchoring, protected boundaries, and remaining V3-3 sequence.

### Acceptance tests

`tests/test_v3_panic_regime_contract.py` contains eight tests covering:

1. latent-state and causal-claim boundaries;
2. strictly prior robust scaling and prefix invariance;
3. minimum mechanism breadth and fail-closed evidence sufficiency;
4. registration of all six mechanism families;
5. prohibition of model selection, automatic ensembles, and consensus probabilities;
6. mandatory non-ranked reporting of all three registered models;
7. prohibition of supervised logistic estimation without external labels;
8. uncertainty, occupancy, label-switching, and final-output contracts.

### Portable lock verifier

`scripts/verify_v3_g3a_identification.py` verifies:

- the exact V3-2B parent-lock Git object;
- every protected V3-3A Git object;
- the status and acceptance evidence;
- the absence of automatic model selection;
- that engine implementation has not been falsely claimed;
- that the final V3-3 lock remains unauthorized.

## Test evidence

The isolated Gate V3-3A contract suite completed with:

```text
8 passed
```

The test execution validates the exact contract and registry content committed to the branch. Full repository and Python 3.11–3.13 CI remain deferred to the Version 3 audit gate and are not represented as completed here.

## Methodological results

### Result 1 — Panic is identified through mechanism concurrence

The regime cannot be inferred from volatility, drawdown, funding, or dependence alone. A valid probability requires at least four of six mechanism families and evidence from structural, market-plumbing, and price-risk blocks.

### Result 2 — The probability has an explicit semantic boundary

Without an approved external panic label, the output is a model-implied mechanism-consistency probability or latent-state posterior. It is not an externally calibrated frequency of psychological panic or future crashes.

### Result 3 — Supervised logistic estimation is currently inadmissible

A supervised logistic model requires a separately governed external label registry, provenance, timing rule, reliability assessment, calibration contract, and frozen development/evaluation split. None is silently assumed.

### Result 4 — Model uncertainty remains visible

The transparent challenger, monotone mechanism score, and causal HMM are all reported. Disagreement is retained as diagnostic evidence rather than concealed by automatic selection or averaging.

### Result 5 — State identity is governed

The HMM panic-consistent state must be anchored by the highest composite mechanism pressure and higher pressure in at least four mechanism families. Failed anchoring invalidates the model instead of permitting convenient relabelling.

## Scientific and model-risk assessment

The gate materially improves the research design because it separates three questions that are commonly conflated:

1. whether stress indicators are elevated;
2. whether several independent mechanisms jointly describe a panic-consistent structure;
3. whether a latent-state model assigns high posterior probability to that structure.

The strongest feature of the contract is its fail-closed identification logic. The principal remaining model risk is not computational. It is observational coverage. Liquidity, funding, order-book, liquidation, and cross-venue evidence may be incomplete for some historical periods. The engine must therefore be expected to publish `INSUFFICIENT_MECHANISM_EVIDENCE` frequently rather than manufacture complete histories.

A second risk is probability interpretation. The monotone score is governed and reproducible, but it is not learned from external panic outcomes. It must remain described as a mechanism-consistency probability. The HMM posterior is conditional on model specification and state anchoring, not proof that panic exists objectively.

A third risk is state sparsity. Minimum occupancy and duration rules may invalidate a latent state in short or calm samples. This is an appropriate scientific outcome and must not be repaired through threshold weakening.

## Perceived-value and problem-solving opportunities

The following additions could materially increase the repository's research, institutional, and publication value, but should be decided in later subgates rather than inserted silently now.

### Mechanism-contribution decomposition

Recommended for V3-3C. A timestamp-level decomposition showing how spectral, network, liquidity, funding, volatility, and downside evidence contribute to each probability would make the engine auditable and decision-grade.

### Cross-model disagreement index

Recommended for V3-3C. The spread between the monotone score and HMM posterior can become a formal model-risk diagnostic. High disagreement may indicate transition uncertainty, sparse mechanisms, or latent-state misspecification.

### External chronology validation

Recommended as a later robustness layer, not as a training label. A predeclared chronology of independently documented market-dislocation events could test whether high probabilities align with known episodes without contaminating identification or enabling retrospective threshold tuning.

### Mechanism-coverage map

Recommended for the evidence report. A coverage heatmap by timestamp, asset, venue, and mechanism would make `INSUFFICIENT_MECHANISM_EVIDENCE` interpretable and expose where data investment has the highest marginal value.

## Recommendation

Proceed to **Gate V3-3B — Probabilistic Engine Implementation**.

The correct sequence is:

1. build the causal mechanism-family transformation layer;
2. implement the transparent challenger output;
3. implement the monotone mechanism score;
4. implement the expanding-prefix causal Gaussian HMM;
5. emit long-format probabilities for every registered model;
6. verify probability bounds, prefix invariance, deterministic identity, insufficient-evidence behaviour, and label anchoring.

Transitions, duration summaries, occupancy statistics, contribution decomposition, uncertainty diagnostics, and final portable evidence remain the responsibility of V3-3C. The final `V3_G3_PANIC_REGIME_LOCK.json` and checkpoint remain prohibited until V3-3D passes.
