# Gate V3-3B — Probabilistic Engine Implementation Checkpoint

## Gate status

> `IMPLEMENTATION_COMPLETE_AND_LOCKED`

Gate V3-3B is complete and locked as the causal probabilistic-engine implementation subgate.

This status means that the registered point-probability models, causal transformation layer, runner, outputs, tests, deterministic manifest, and implementation verifier are complete. It does not mean that the full Gate V3-3 methodology is complete. Probability intervals, transition evidence, duration, final occupancy reporting, mechanism contributions, cross-model disagreement, and the final Gate V3-3 lock remain pending V3-3C and V3-3D.

## Repository position

- frozen baseline: `v2.0.0`;
- baseline commit: `5a07299367b80c3940e652e7bbdd208ce86ba5ef`;
- Version 3 branch: `research/v3-adaptive-signal-validity`;
- parent gate: `V3-3A — Panic-Consistent Regime Identification Freeze`;
- parent lock: `V3_G3A_PANIC_REGIME_IDENTIFICATION_LOCK.json`;
- parent lock blob: `b8cabd84feb6389d727fbc5cb013fed7472c87e2`;
- V3-3B implementation boundary commit: `2a37f7ef11e71c8edc07c1a973ce159aacc78a81`;
- V3-3B lock commit: `2034ebb657051b900863382b30bcee0c6e7836c0`;
- V3-3B lock blob: `068fdb636e03188c075ad32cd877d1da51d9863a`;
- Version 1 and Version 2 determinations modified: none;
- V3-1, V3-2, V3-2B, and V3-3A protected files modified: none.

## Implemented components

### Causal mechanism-family transformation

`src/shockbridge_signal_validity/v3/panic_regime.py` implements the transformation from locked Gate V3-2B evidence into six mechanism families:

```text
spectral
network
liquidity
funding
volatility
downside
```

Market-level spectral and network features use the explicitly configured dependence window. Asset-level liquidity, funding, volatility, and downside features are aggregated cross-sectionally by the median at each timestamp. No panel, asset, dependence window, or feature direction is selected automatically.

### Prior-only robust scaling

Every admitted feature is directionally transformed and standardized using expanding historical median and median absolute deviation estimates from observations strictly earlier than the current timestamp.

The historical scaler is refreshed at a registered interval and held fixed between refresh points. This provides exact append-only invariance while keeping the cost of robust expanding estimation operationally manageable.

The standardized value is clipped to `[-5,5]` and converted to a bounded directional score through the logistic map.

### Family aggregation and evidence sufficiency

Feature scores are aggregated by the within-family median. A family is unavailable unless it satisfies both:

- the minimum registered number of available features;
- the minimum valid-feature fraction at the timestamp.

A probability is emitted only when:

- at least four mechanism families are available;
- structural evidence is available from spectral or network information;
- market-plumbing evidence is available from liquidity or funding information;
- price-risk evidence is available from volatility or downside information.

Otherwise the output remains:

```text
INSUFFICIENT_MECHANISM_EVIDENCE
```

### Transparent Version 2 challenger

`V2_TRANSPARENT_STATE_CHALLENGER_V1` is preserved as a mandatory, non-panic challenger.

It:

- uses a reference `asset@venue` series declared in configuration;
- constructs return, rolling volatility, and trend inputs causally;
- trains on a fixed initial historical segment;
- forward-filters subsequent observations;
- reports `p_range`, `p_trend`, and `p_stress`;
- never populates a panic-probability field;
- always reports `panic_probability_authorized = false`.

This preserves methodological continuity without permitting the earlier three-state filter to be reinterpreted as a panic classifier.

### Monotone mechanism score

`MONOTONE_MECHANISM_SCORE_V1` implements the predeclared equal-family composite:

\[
q_t
=
\frac{1}{|\mathcal{G}_t|}
\sum_{g\in\mathcal{G}_t}M_g(t),
\]

followed by

\[
p_t
=
\frac{1}{1+\exp\{-6(q_t-0.5)\}}.
\]

The raw probability is filtered through the registered causal EWMA. No external label, fitted family weight, favourable feature selection, or target information is used.

### Causal two-state Gaussian HMM

`CAUSAL_GAUSSIAN_HMM_V1` implements a deterministic diagonal-Gaussian hidden Markov model over the six family scores.

At each eligible refit origin:

1. the model is estimated only from the prefix ending before the forecast origin;
2. previous parameters are used only as a warm start;
3. the current observation enters through a one-step forward filter;
4. prior probabilities are never rewritten;
5. rows with insufficient mechanism evidence receive no published probability;
6. state labels are anchored by composite mechanism pressure;
7. the panic-consistent state must exceed the other state in at least four families;
8. minimum state occupancy is enforced;
9. failed anchoring or occupancy invalidates the model instead of relabelling it.

The implementation does not calculate or publish retrospective smoothed probabilities.

### Ambiguous topology remediation

The raw Gate V3-2B `contagion_radius` metric is excluded from the default mechanism score.

The variable is a network radius in correlation-distance space. Stronger common dependence can reduce the distance radius, whereas fragmentation can increase it. The raw measure therefore does not have a universally monotone panic direction.

Rather than assigning a convenient sign, the engine:

- excludes the feature by default;
- records the exclusion in diagnostics;
- leaves future admission subject to a separately frozen transformation or challenger specification.

This is a methodological remediation discovered during V3-3B implementation.

### Reusable execution layer

The gate adds:

```text
src/shockbridge_signal_validity/v3/panic_regime.py
src/shockbridge_signal_validity/v3/panic_regime_runner.py
scripts/run_v3_panic_regime.py
configs/v3_panic_regime_example.json
RUN_V3_G3B_PROBABILISTIC_ENGINE.ps1
RUN_V3_G3B_PROBABILISTIC_ENGINE.sh
docs/V3_PANIC_REGIME_ENGINE.md
scripts/verify_v3_g3b_probabilistic_engine.py
tests/test_v3_panic_regime.py
```

The Windows and Unix workflows add the repository `src` directory to `PYTHONPATH`. This prevents the direct-script import error observed when the package has not yet been installed.

Normal repository use should still install the package through:

```text
python -m pip install -e ".[dev]"
```

### Consolidated findings record

`Findings.md` now preserves verified empirical findings, methodological contributions, analytical-fixture results, and synthetic-validation results across Versions 1, 2, and the completed Version 3 gates.

Approved but unimplemented ideas remain outside the findings sections until validation.

## Output contract

The runner creates:

```text
panic_regime_probability.csv
mechanism_family_scores.csv
regime_manifest.json
regime_validation_report.json
probability_engine_diagnostics.json
```

### Probability output

`panic_regime_probability.csv` is long format with one row per timestamp and registered model. It includes:

```text
timestamp
model_id
raw_probability
filtered_probability
lower_95
upper_95
p_range
p_trend
p_stress
operational_state
available_mechanism_count
evidence_sufficiency
model_validity
panic_probability_authorized
uncertainty_status
```

The interval columns intentionally remain empty and are marked `PENDING_V3_3C` for panic-authorized models.

### Mechanism scores

`mechanism_family_scores.csv` exposes every admitted feature score, family score, valid-feature count, registered-feature count, evidence-block availability, available-family count, sufficiency result, and composite mechanism score.

### Manifest

`regime_manifest.json` binds:

- market-structure input identity;
- causal-series input identity;
- complete configuration identity;
- mechanism-score output identity;
- probability output identity;
- fixed dependence window;
- fixed reference series;
- all registered model identifiers;
- explicit non-selection and non-ensemble status.

### Preliminary validation report

`regime_validation_report.json` states explicitly that:

- implementation is complete;
- uncertainty intervals are incomplete;
- transitions are incomplete;
- duration and final occupancy outputs are incomplete;
- contribution decomposition is incomplete;
- the final V3-3 lock is not permitted;
- V3-3C is the next subgate.

## Acceptance evidence

The isolated analytical, causal, governance, and runner suite completed with:

```text
11 passed in 3.65s
```

The tests establish that:

1. configuration requires a stable `asset@venue` reference identifier;
2. every registered model is reported without selection or an ensemble;
3. the monotone probability remains within `[0,1]` and rises under synthetic multi-mechanism concurrence;
4. absence of both liquidity and funding evidence fails closed;
5. appending future observations cannot change any earlier model probability or state;
6. shuffled input order produces identical probability evidence and manifest identity;
7. the transparent challenger cannot claim a panic probability;
8. the HMM emits bounded forward-filtered probabilities only after valid anchoring;
9. ineligible upstream market-structure rows cannot provide structural evidence;
10. ambiguous `contagion_radius` is excluded and documented;
11. the runner emits the complete governed preliminary evidence package.

The synthetic stress fixture is an implementation test. It is not historical market evidence and does not establish that a real panic-consistent regime occurred.

Full repository tests and Python 3.11–3.13 CI remain deferred to the final Version 3 audit gate and are not represented as completed here.

## Results

### Result 1 — The complete mechanism path is executable

The repository can now transform causal spectral, network, liquidity, funding, volatility, and downside evidence into timestamp-level family scores and registered model probabilities.

### Result 2 — Price-only stress cannot obtain a valid panic probability

Removing both market-plumbing families forces an insufficient-evidence output even when spectral, network, volatility, and downside conditions are elevated.

This is a meaningful model-risk control because many conventional crisis classifiers effectively reduce panic to returns and volatility.

### Result 3 — All probability models preserve append-only causality

Future-append tests show that later observations cannot change earlier transparent-state probabilities, monotone probabilities, HMM probabilities, model-validity states, or operational interpretations.

### Result 4 — Model disagreement remains observable

The engine reports each model separately. It does not hide disagreement through selection or averaging. This creates the necessary basis for the approved V3-3C cross-model disagreement index.

### Result 5 — Implementation probabilities are not presented as final scientific evidence

The engine exposes point probabilities but labels their uncertainty as pending. It therefore refuses to treat a functioning probability formula as a fully validated probability methodology.

## Scientific assessment

Gate V3-3B materially advances the repository from descriptive market measurement to executable latent-regime inference.

Its strongest contribution is not the HMM by itself. Two-state HMMs are established methods. The higher-value contribution is the governed architecture combining:

- economically distinct mechanism families;
- strictly causal robust scaling;
- fail-closed evidence breadth;
- multiple mandatory models;
- model-specific probability semantics;
- state-label anchoring;
- no automatic selection;
- exact append-only invariance;
- explicit separation between implementation probability and publishable probability evidence.

This architecture is more defensible than a standard volatility-state classifier because the market state must be supported by structural, plumbing, and price-risk mechanisms simultaneously.

## Model-risk assessment

### Observational coverage risk

Liquidity, order-book, funding, liquidation, and cross-venue fields may be sparse or absent over long historical periods. The expected consequence is frequent insufficient-evidence output. This is a model boundary, not a defect to be hidden through imputation.

### HMM saturation risk

A sharply separated synthetic fixture can produce probabilities close to zero or one. Real-data validation must determine whether the HMM becomes overconfident under strong but noisy separation. V3-3C uncertainty and calibration diagnostics must examine this directly.

### Distributional risk

Diagonal Gaussian emissions simplify dependence among mechanism families. The model is transparent and identifiable, but it may understate correlated family uncertainty. A richer covariance structure should not be introduced until sample size, conditioning, and numerical stability justify it.

### Scaling-refit risk

Robust scaling parameters are refreshed discretely rather than continuously. The interval is predeclared and causal, but V3-3C must report sensitivity to the approved refit and EWMA policies.

### Mechanism redundancy risk

Some inputs within or across families are related, such as spectral concentration and network density, or realised volatility and downside semivariance. Equal family weighting limits feature-count dominance, but contribution and disagreement diagnostics remain necessary.

### State-anchor risk

The four-family directional anchor prevents arbitrary switching, but it does not prove that the anchored state is objectively panic. It identifies the higher-pressure latent state under the model. Language must remain `PANIC_CONSISTENT_REGIME`.

## Perceived-value and problem-solving opportunities

The user approved the following V3-3C developments.

### Mechanism-contribution decomposition — approved

V3-3C should expose the timestamp-level contribution of each family to the monotone probability and a model-consistent contribution or perturbation diagnostic for the HMM.

Institutional value:

- makes probability movements auditable;
- supports risk-committee explanation;
- distinguishes price stress from plumbing stress;
- identifies the mechanism responsible for escalation;
- improves manuscript figures and case-study interpretation.

### Cross-model disagreement index — approved

V3-3C should formalize disagreement between the monotone mechanism probability and HMM posterior.

Recommended interpretation:

- low disagreement: model-form agreement;
- moderate disagreement: transition or nonlinear-state uncertainty;
- high disagreement: model-risk escalation, sparse evidence, state instability, or misspecification.

The index must remain diagnostic. It cannot select a preferred model or create a hidden ensemble.

### Mechanism-coverage map — approved

V3-3C should generate machine-readable and visual coverage evidence by timestamp, asset, venue, feature, family, and evidence block.

This could materially improve the perceived value of the repository because it converts missingness from a technical nuisance into a transparent data-investment map.

### External chronology validation — approved for later robustness

An independently sourced and predeclared chronology of market dislocations may be used to evaluate temporal alignment and event concentration after the probability methodology is frozen.

It must not:

- train the current unsupervised models;
- select thresholds retrospectively;
- redefine the state after viewing results;
- become an ungoverned crisis label.

## Recommendation

Proceed to:

> **Gate V3-3C — Governance and Diagnostics**

The recommended implementation order is:

1. prefix-respecting moving-block probability intervals;
2. transition-matrix and one-step transition-risk evidence;
3. duration and occupancy outputs;
4. monotone mechanism-contribution decomposition;
5. HMM family-perturbation contribution diagnostics;
6. approved cross-model disagreement index;
7. mechanism-coverage map and evidence table;
8. threshold, EWMA, scaling-refit, and HMM sensitivity diagnostics;
9. expanded validation report and model-risk findings;
10. deterministic output and portable verification tests.

Only after V3-3C passes should V3-3D verify all V3-3 protected objects, execute the complete isolated acceptance suite, and create:

```text
V3_G3_PANIC_REGIME_LOCK.json
V3_G3_PANIC_REGIME_CHECKPOINT.md
```

Gate V3-4 remains prohibited until that final lock passes.
