# Gate V3-3C — Governance and Diagnostics Checkpoint

## Gate status

> `GOVERNANCE_AND_DIAGNOSTICS_COMPLETE_AND_LOCKED`

Gate V3-3C is complete and locked as the uncertainty, transition, occupancy, duration, explainability, disagreement, coverage, and sensitivity subgate of the panic-consistent regime engine.

This does not authorize the final Gate V3-3 lock. Gate V3-3D must still execute the integrated V3-3A–V3-3C acceptance suite, verify every protected parent object, and create the final V3-3 checkpoint and lock.

## Repository position

- frozen baseline: `v2.0.0`;
- baseline commit: `5a07299367b80c3940e652e7bbdd208ce86ba5ef`;
- Version 3 branch: `research/v3-adaptive-signal-validity`;
- parent gate: `V3-3B — Probabilistic Engine Implementation`;
- parent lock: `V3_G3B_PROBABILISTIC_ENGINE_LOCK.json`;
- parent lock blob: `068fdb636e03188c075ad32cd877d1da51d9863a`;
- V3-3C implementation boundary commit: `c3bf4189e27e557acef54e0eec1c3c28df9357d6`;
- V3-3C lock commit: `49ecc7c8ddc8abe52f4aa46135e0017fd8868f2b`;
- V3-3C lock blob: `30553882746296d34114eef271fde6c64ae5e471`;
- Version 1 and Version 2 determinations modified: none;
- V3-1, V3-2, V3-2B, V3-3A, and V3-3B protected objects modified: none.

## Implemented components

### 1. Prefix-respecting probability uncertainty

The diagnostics layer estimates 95% uncertainty intervals for the two panic-authorized models using causal moving blocks of strictly prior probability-path innovations in logit space.

The central contract uses:

```text
bootstrap replications: 250
minimum valid replications: 200
coverage: 95%
history window: 500 observations
minimum interval history: 30 observations
block rule: max(2, ceil(1.5 * n_valid^(1/3)))
seed: deterministic by model and timestamp
```

The probability at time `t` never uses innovations observed at or after `t`.

A point estimate without enough prior uncertainty history remains visible but receives:

```text
probability_publishable = false
uncertainty_status = INSUFFICIENT_INTERVAL_HISTORY
model_validity = VALID_POINT_ESTIMATE_INTERVAL_UNAVAILABLE
```

The interval is therefore a publication gate, not a cosmetic range added to every available point estimate.

### 2. Causal operational-state confirmation

State entry and transition require two consecutive observations. The first observation creates a candidate state, and the second confirms it. The engine does not revise the state assigned to the first observation.

Insufficient evidence breaks the episode and resets the confirmation process.

### 3. Transition probabilities

The gate implements:

- operational-state transition matrices for every registered model;
- Dirichlet smoothing;
- posterior transition intervals;
- one-step transition probability to `PANIC_CONSISTENT_REGIME`;
- forward-filtered HMM posterior-implied binary transition evidence;
- row-sum validation.

No retrospective HMM smoothing is introduced.

### 4. State-duration evidence

`state_duration.csv` records:

- model;
- state;
- episode start and end;
- duration in observations;
- right-censoring;
- minimum-duration validity;
- confirmation that retrospective backfill was not performed.

### 5. Occupancy evidence

`occupancy_statistics.json` reports:

- state observations and fractions;
- episode counts;
- median and maximum durations;
- HMM binary panic/non-panic occupancy;
- minimum count and fraction boundaries;
- collapsed-state validity.

A collapsed HMM state remains `MODEL_INVALID_COLLAPSED_STATE`.

### 6. Exact monotone contribution decomposition

For the monotone model, the logit is exactly decomposed by mechanism family:

\[
\operatorname{logit}(p_t)
=
\sum_{g\in\mathcal G_t}
\frac{6[M_g(t)-0.5]}{|\mathcal G_t|}.
\]

The output also provides a neutral-value perturbation, replacing one family with 0.5 while holding the other families fixed.

### 7. Causal HMM contribution diagnostic

The HMM contribution layer estimates a causal ridge surrogate using only historical family scores and historical HMM logits. It then measures the probability change obtained by neutralizing one family.

Every row is explicitly labelled:

```text
VALID_DIAGNOSTIC_SURROGATE_NOT_EXACT_HMM_DECOMPOSITION
```

The framework does not represent the surrogate as an exact HMM likelihood decomposition.

### 8. Cross-model disagreement index

The index is:

\[
\Delta_t
=
|p_t^{\mathrm{monotone}}-p_t^{\mathrm{HMM}}|.
\]

It reports:

```text
LOW
MODERATE
HIGH_MODEL_RISK_ESCALATION
INSUFFICIENT_MODEL_EVIDENCE
```

It also records interval overlap. The index is diagnostic only. It cannot select a model, replace a model, or produce an ensemble probability.

### 9. Mechanism-coverage and data-investment evidence

Coverage is now machine-readable by:

- timestamp;
- market panel;
- `asset@venue`;
- source column;
- registered feature;
- mechanism family;
- structural, market-plumbing, or price-risk block.

The family summary translates missingness into a data-investment priority. This is particularly important for liquidity and funding, because missing both blocks forces insufficient mechanism evidence.

The governed `contagion_radius` exclusion remains visible in the coverage output.

### 10. Deterministic coverage figure

The runner generates:

```text
mechanism_coverage_heatmap.svg
```

The SVG uses a fixed Matplotlib hash salt and excludes wall-clock metadata from deterministic identity.

### 11. Sensitivity evidence

The gate reports without selecting among alternatives:

- three threshold systems;
- monotone EWMA alphas 0.20, 0.35, and 0.50;
- probability changes at robust-scaling refit boundaries;
- HMM probability changes at refit origins;
- valid and invalid HMM refits;
- HMM posterior saturation below 0.01 or above 0.99.

### 12. Reusable execution layer

The implementation adds:

```text
src/shockbridge_signal_validity/v3/panic_regime_governance_base.py
src/shockbridge_signal_validity/v3/panic_regime_transitions.py
src/shockbridge_signal_validity/v3/panic_regime_explainability.py
src/shockbridge_signal_validity/v3/panic_regime_sensitivity.py
src/shockbridge_signal_validity/v3/panic_regime_diagnostics.py
src/shockbridge_signal_validity/v3/panic_regime_diagnostics_runner.py
scripts/run_v3_panic_regime_diagnostics.py
configs/v3_panic_regime_diagnostics_example.json
RUN_V3_G3C_GOVERNANCE.ps1
RUN_V3_G3C_GOVERNANCE.sh
docs/V3_PANIC_REGIME_GOVERNANCE.md
scripts/verify_v3_g3c_governance.py
tests/test_v3_panic_regime_diagnostics.py
```

### 13. Consolidated findings record

`Findings.md` now records only the implemented and validated V3-3C contributions. External chronology, empirical regime claims, and conditional technical-signal results remain pending.

## Output contract

### Required V3-3 outputs completed by this gate

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

### Additional governance outputs

```text
cross_model_disagreement.csv
mechanism_coverage.csv
mechanism_coverage_summary.json
mechanism_coverage_heatmap.svg
sensitivity_diagnostics.json
```

## Acceptance evidence

The isolated analytical, causal, governance, explainability, reproducibility, and runner suite completed with:

```text
15 passed in 6.67s
```

The tests establish that:

1. invalid threshold systems fail closed;
2. valid intervals are bounded and contain their point estimates;
3. early estimates without interval history remain nonpublishable;
4. future appends cannot revise earlier intervals or diagnostics;
5. state confirmation does not backfill the first threshold crossing;
6. transition rows sum to one and one-step risks remain bounded;
7. duration evidence applies minimum-duration and no-backfill controls;
8. HMM occupancy exposes collapsed-state boundaries;
9. monotone family contributions sum exactly to the raw probability logit;
10. HMM contributions remain explicitly causal surrogate diagnostics;
11. cross-model disagreement remains bounded, diagnostic, and non-selective;
12. coverage is mapped by asset, venue, family, feature, and market panel;
13. the `contagion_radius` exclusion remains auditable;
14. sensitivity evidence is complete and does not select a model;
15. shuffled inputs preserve deterministic outputs and manifest identity;
16. missing feature-registry evidence fails closed;
17. the runner creates the complete governed output package.

The test count is 15 because several individual tests verify more than one acceptance property.

Full repository CI and Python 3.11–3.13 validation remain deferred to the final Version 3 audit gate and are not represented as completed here.

## Results

### Result 1 — Probability publication is now conditional on uncertainty evidence

The repository no longer treats every finite point estimate as publication-ready. A causal point probability may be valid as an implementation output but remain nonpublishable until sufficient historical innovations support its interval.

### Result 2 — Transition evidence remains causal

Two-observation confirmation prevents isolated crossings from creating a historical episode date. Operational transition matrices and HMM posterior-implied transition evidence are estimated without reconstructing future-informed latent paths.

### Result 3 — Model explanations have distinct epistemic status

The monotone probability has an exact decomposition because its mapping is algebraically transparent. The HMM does not. Its contribution layer is therefore reported as an approximate causal surrogate rather than dressed as exact attribution.

### Result 4 — Model disagreement becomes usable risk evidence

The difference between the monotone and HMM probabilities is now an explicit model-risk variable. High disagreement can reveal nonlinear-state transitions, sparse evidence, HMM saturation, anchoring instability, or model misspecification without suppressing either model.

### Result 5 — Missing data becomes a research and investment decision

The mechanism-coverage layer identifies which family, feature, asset, venue, or evidence block prevents a fully supported probability. This converts missingness into a transparent priority map for future data acquisition.

### Result 6 — Sensitivity is separated from selection

Threshold, EWMA, scaling-refit, and HMM-refit alternatives are reported as diagnostics. They cannot replace the central specification because they appear more favorable.

## Scientific assessment

The principal scientific value of V3-3C is the integration of probabilistic regime inference with explicit model governance.

The framework now separates:

1. a model-computable probability;
2. a probability with sufficient uncertainty history;
3. a confirmed operational state;
4. an episode with duration evidence;
5. a transition-risk estimate;
6. an interpretable mechanism contribution;
7. agreement or disagreement across model forms;
8. evidence coverage supporting the inference.

This layered architecture has higher publication and institutional value than a conventional HMM regime chart because it explains when a probability is usable, why it moved, whether models agree, whether the state persists, and whether the required data mechanisms were actually present.

## Model-risk assessment

### Interval semantics

The bootstrap interval quantifies probability-path innovation uncertainty under the registered model. It does not calibrate the probability against observed psychological panic because no such target is registered.

### Early-history boundary

Early finite point estimates may lack sufficient interval history. They remain available for implementation diagnostics but cannot be treated as publication-ready probabilities.

### HMM contribution approximation

The ridge surrogate can explain local associations between family scores and HMM logits. It does not reproduce the exact HMM likelihood. Its fit statistic and surrogate label must remain visible.

### Transition-state discretization

Operational transition matrices depend on registered probability thresholds. Threshold sensitivities therefore remain necessary, and transition evidence should not be treated as invariant to state definitions.

### Posterior-implied HMM transitions

The binary HMM transition diagnostic uses forward-filtered posterior outer products rather than the internal training transition matrix from each refit. This preserves causal output availability but must remain described as posterior-implied transition evidence.

### Occupancy sparsity

Short or calm samples may fail the minimum state-occupancy boundary. The correct result is model invalidity, not weaker occupancy requirements.

### Coverage selection risk

Coverage maps must never be used to retain only well-covered favorable periods. They are diagnostic and data-investment evidence, not a retrospective sample-selection device.

### Visualization boundary

The heatmap visualizes evidence availability. It is not a panic-intensity heatmap and must not be interpreted as a regime estimate.

## Perceived-value and problem-solving opportunities

### 1. Model-risk dashboard layer

The combination of probability intervals, transition risk, disagreement, contribution, and coverage can support a later decision-grade dashboard. This would materially improve institutional usability, but it should be implemented only after the final V3-3 lock.

### 2. Event-study chronology overlay

The approved external chronology can later evaluate whether high probabilities and transitions align with independently documented market dislocations. It must remain validation evidence and cannot train or retune the current models.

### 3. Contribution-stability inference

A later robustness layer could test whether family contributions are stable across market episodes, assets, venues, and data vintages. This could become a valuable manuscript contribution about changing stress-transmission mechanisms.

### 4. Probability-calibration research

If a credible external event ontology is later developed, the repository could compare model-implied mechanism consistency with event occurrence without converting the current unsupervised system into a retrospectively labeled classifier.

### 5. Data-value optimization

The coverage map creates the basis for estimating the marginal research value of adding order-book, liquidation, funding, or cross-venue history. This could become a separate data-acquisition optimization module.

These ideas require later approval and must not be added to the frozen V3-3C contract.

## Recommendation

Proceed to:

> **Gate V3-3D — Final Acceptance, Protected-Object Audit, and Lock**

V3-3D should:

1. verify the V3-3A, V3-3B, and V3-3C parent locks and all protected Git objects;
2. execute the complete V3-3 contract, engine, and governance test suites together;
3. execute parent V3-1, V3-2, and V3-2B portable verifiers;
4. verify every required V3-3 output schema;
5. verify deterministic repeat execution;
6. verify future-append invariance across the integrated engine;
7. verify no automatic selection, ensemble, or consensus probability exists;
8. verify external chronology was not used;
9. verify Version 1 and Version 2 determinations remain unchanged;
10. create:

```text
V3_G3_PANIC_REGIME_LOCK.json
V3_G3_PANIC_REGIME_CHECKPOINT.md
```

Gate V3-4 remains prohibited until V3-3D passes.
