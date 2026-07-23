# Version 3 Research Protocol

## 1. Primary objective

Version 3 develops and validates a reusable framework that determines:

1. whether RSI or Bollinger information adds predictive value beyond a matched benchmark;
2. whether that value is conditional on market structure and panic-consistent regimes;
3. whether the same indicator changes from mean-reversion to continuation behaviour across regimes;
4. whether any predictive contribution survives costs and uncertainty controls;
5. when the signal is degrading and the probability that it will breach its operational validation boundary within a declared horizon;
6. whether the complete process transports across assets, venues, and data vintages.

## 2. Primary scientific question

> Can a jointly validated regime, forecast, and signal-failure framework identify when RSI and Bollinger information is usable, when its economic interpretation changes, and when its use should be reduced, suspended, or revalidated?

## 3. Primary hypothesis families

### H1 — Conditional RSI contribution

At least one prospectively selected RSI interpretation improves benchmark-relative predictive loss and net economic contribution within a predeclared market-regime class, while satisfying multiplicity, calibration, coverage, stability, and transportability requirements.

### H2 — Conditional Bollinger contribution

At least one prospectively selected Bollinger interpretation improves benchmark-relative predictive loss and net economic contribution within a predeclared market-regime class, while satisfying multiplicity, calibration, coverage, stability, and transportability requirements.

### H3 — Interpretation transition

The direction of incremental signal contribution differs across registered regimes in a manner consistent with a predeclared transition between mean-reversion and continuation interpretations.

### H4 — Failure-risk forecasting

A prospectively selected validity model estimates the probability of a registered signal failure event within future horizon \(H\) with acceptable discrimination, calibration, and decision utility under chronological validation.

### H5 — External transportability

The signal-validity and failure-risk methodology retains acceptable performance on declared assets or venues not used to select the primary pipeline.

## 4. Non-confirmatory analyses

The following are secondary unless explicitly promoted before any locked evaluation:

- unrestricted indicator combinations;
- isolated parameter findings;
- unregistered regime labels;
- retrospective crisis narratives;
- individual event studies;
- transaction-cost assumptions outside the frozen grid;
- unconstrained machine-learning models;
- causal claims of investor panic;
- post-hoc asset or venue selection.

## 5. Data architecture

### 5.1 Canonical observations

Each observation is uniquely identified by:

```text
timestamp × asset × venue × interval
```

Required OHLCV fields and governed optional stress fields are defined in `V3_DESIGN_FREEZE.md`.

### 5.2 Source adapters

Each source adapter must:

- preserve source timestamps and timezone metadata;
- map fields into the canonical schema;
- report duplicates, gaps, non-positive prices, crossed OHLC values, and volume anomalies;
- record source, retrieval time, symbol mapping, interval, and transformation history;
- produce a deterministic adapter manifest;
- fail closed on unresolved schema violations.

### 5.3 Minimum panel requirement

Spectral-regime estimation requires a declared liquid-asset panel with sufficient contemporaneous coverage. The panel construction rule, inclusion threshold, rebalance schedule, and missing-data policy must be frozen before model selection.

## 6. Targets

For forecast horizon \(h\):

\[
r_{t,h}=\log\!\left(\frac{P_{t+h}}{P_t}\right),
\]

\[
y^{\mathrm{dir}}_{t,h}=\mathbf{1}(r_{t,h}>0),
\]

\[
y^{\mathrm{tail}}_{t,h}=\mathbf{1}\!\left(|r_{t,h}|>q^{\mathrm{train}}_{\alpha,h}\right).
\]

Primary forecast targets are:

- directional probability;
- expected cumulative return;
- large-move probability.

Failure-model targets are derived only from prospectively registered monitoring rules and persistence requirements.

## 7. Forecast horizons

The initial declared forecast set is:

```text
4 hours
8 hours
12 hours
24 hours
48 hours
72 hours
```

The initial declared failure-risk set is:

```text
24 hours
72 hours
7 days
30 days
```

A horizon may be excluded only through a documented pre-evaluation feasibility rule, not because its results are unfavourable.

## 8. Regime architecture

### 8.1 Transparent challenger

The Version 2 forward-only range/trend/stress filter remains a challenger and continuity benchmark.

### 8.2 Spectral dependence engine

At time \(t\), the regime engine estimates a causal rolling dependence matrix \(R_t\) from the registered panel. Candidate features include:

\[
m_t=\frac{\lambda_{1,t}}{\operatorname{tr}(R_t)},
\]

\[
g_t=\lambda_{1,t}-\lambda_{2,t},
\]

\[
\mathrm{PR}_t=\frac{\left(\sum_j\lambda_{j,t}\right)^2}{\sum_j\lambda_{j,t}^2},
\]

and normalized spectral entropy:

\[
H_t=-\frac{1}{\log N}\sum_{j=1}^{N}p_{j,t}\log p_{j,t},
\qquad
p_{j,t}=\frac{\lambda_{j,t}}{\sum_k\lambda_{k,t}}.
\]

The engine also records eigenvector concentration, average correlation, correlation dispersion, and causal changes in these quantities.

### 8.3 Panic-consistent composite

The panic-consistent layer combines spectral concentration with registered downside, volatility, volume, liquidity, leverage, liquidation, and cross-venue evidence. It produces a probability rather than a retrospective hard label:

\[
\pi^{\mathrm{panic}}_t
=
P(\mathrm{PANIC\_CONSISTENT\_REGIME}_t\mid\mathcal{F}_t).
\]

### 8.4 Regime validation

Regime validation must assess:

- causal availability;
- transition stability;
- duration and occupancy;
- calibration where probabilistic labels are available;
- sensitivity to panel composition and window length;
- event concentration;
- economic interpretability;
- sufficient observations for conditional signal claims.

## 9. Signal architecture

RSI and Bollinger features are generated by one common causal signal engine. Every feature record includes its parameterization, orientation, persistence, and interpretation.

The primary comparison is always:

```text
candidate = matched benchmark + registered signal and regime interactions
```

The benchmark, candidate, preprocessing, model class, training sample, calibration, horizon, costs, and decision threshold must otherwise be identical.

## 10. Forecast model classes

The restrained initial model set comprises:

1. regularized logistic and ridge models;
2. spline-augmented regularized models;
3. shallow histogram gradient boosting;
4. time-varying regularized generalized linear models;
5. state-space or Markov-switching response models where identifiability gates pass.

Unbounded automated search, deep neural networks, and post-hoc model insertion are prohibited before the first complete Version 3 evaluation.

## 11. Validity and failure model

### 11.1 Monitoring evidence

At time \(t\), the validity model may use only information available through \(t\), including:

- rolling benchmark-relative loss differential;
- rolling net economic contribution;
- calibration error and drift;
- decision coverage and turnover;
- feature and parameter drift;
- regime-transition probabilities;
- spectral concentration and panic-consistent probability;
- cost sensitivity;
- sequential structural-break statistics;
- data-quality indicators.

### 11.2 Failure time

For signal pipeline \(k\), define:

\[
\tau^{(k)}_{\mathrm{fail}}
=
\inf\{t: B^{(k)}_t=1\},
\]

where \(B^{(k)}_t\) is a predeclared persistent boundary breach. Boundary construction must not use future observations at inference time.

### 11.3 Candidate validity models

The initial restrained set includes:

- discrete-time logistic hazard;
- regularized survival model;
- Bayesian online change-point features followed by calibrated hazard estimation;
- hidden semi-Markov validity state model;
- calibrated gradient-boosting challenger.

### 11.4 Competing failure reasons

Where sample size permits, failure is decomposed into competing reasons:

```text
PREDICTIVE_DECAY
ECONOMIC_DECAY
CALIBRATION_DRIFT
REGIME_TRANSPORT_FAILURE
DATA_QUALITY_FAILURE
COVERAGE_FAILURE
```

## 12. Decision policy

The decision engine produces two separate outputs:

1. **market forecast output** — direction, return, tail-risk, and uncertainty;
2. **signal-governance output** — validity state, failure probability, evidence gates, and permitted use.

A positive directional forecast cannot override a failed signal-governance state.

Example policy logic:

```text
VALID:
    all required gates pass and failure risk is below the approved threshold

CONDITIONALLY_VALID:
    all required gates pass only within declared regimes

DEGRADING:
    no suspension boundary has yet been crossed, but failure risk or drift exceeds warning level

SUSPENDED:
    a persistent operational boundary is crossed

REVALIDATION_REQUIRED:
    material data, regime, calibration, or structural change invalidates the current approval basis

INVALID:
    establishment gates fail or a confirmed failure persists beyond the registered recovery rule
```

## 13. Selection and evaluation

### 13.1 Development

- nested expanding and rolling chronological folds;
- purging equal to the target horizon;
- embargo where overlapping panel information requires it;
- all transformations, panels, regimes, thresholds, and calibrators fitted within training partitions;
- stability and complexity controls;
- complete reporting of selection frequencies.

### 13.2 Locked evaluation

A final evaluation segment is accessed only after:

- the data contract is frozen;
- all candidate grids are frozen;
- the panel and regime rules are frozen;
- the signal pipelines are frozen;
- failure events and decision thresholds are frozen;
- code and evidence locks pass.

### 13.3 Prospective monitoring simulation

The selected pipeline must then be evaluated in a sequential simulation in which forecasts, monitoring statistics, failure probabilities, and operational states are generated exactly as they would have been available through time.

## 14. Multiplicity and uncertainty

Version 3 must specify before evaluation:

- confirmatory family definitions;
- family-wise or false-discovery controls;
- moving-block or stationary-bootstrap rules;
- confidence-interval methods for predictive and economic contribution;
- calibration intervals for failure probability;
- uncertainty around regime probabilities;
- minimum regime occupancy and decision counts.

## 15. Economic assessment

Economic assessment must include:

- declared one-way fees and slippage;
- sensitivity across at least three cost levels;
- turnover and coverage;
- net contribution relative to the matched benchmark policy;
- dependence-aware lower confidence bounds;
- concentration by event, month, asset, venue, and regime;
- capacity and market-impact boundaries where data permit.

## 16. External replication

The minimum replication design includes SOL, BTC, and ETH, with at least one independent venue where comparable history is available. A broader liquid-asset panel supports spectral-regime estimation.

Claims are classified as:

```text
PRIMARY_CASE_ONLY
CROSS_ASSET_SUPPORTED
CROSS_VENUE_SUPPORTED
MULTI_ASSET_TRANSPORTABLE
NOT_TRANSPORTABLE
```

## 17. Final user-facing outputs

For each timestamp, asset, horizon, and approved pipeline, the framework must be able to produce:

```text
forecast_probability_up
forecast_expected_return
forecast_large_move_probability
forecast_uncertainty
regime_probabilities
panic_consistent_probability
signal_interpretation
incremental_predictive_score
expected_net_contribution
failure_probability_by_horizon
validity_state
permitted_action
boundary_reasons
model_version
data_manifest_id
pipeline_id
```

## 18. Completion standard

Version 3 is complete only when a user can provide a conforming dataset and configuration, execute one documented command, and receive:

- validated data and feature manifests;
- selected and frozen models;
- chronological and locked evidence;
- external-replication evidence;
- sequential failure-risk outputs;
- decision states;
- model cards and an auditable evidence report.

A notebook demonstration alone does not satisfy completion.