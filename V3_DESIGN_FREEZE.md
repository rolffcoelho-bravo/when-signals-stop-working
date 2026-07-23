# Version 3 Design Freeze

## 1. Programme identity

**Name:** Adaptive Signal Validity, Regime, and Failure Framework  
**Version:** 3.0 research programme  
**Branch:** `research/v3-adaptive-signal-validity`  
**Frozen baseline:** institutional `v2.0.0` release  

Version 3 is a new governed methodology. It does not amend, rescue, or reinterpret any Version 2 decision.

## 2. Decision problem

Version 3 answers the operational question:

> When does a technical signal contain usable incremental predictive and economic information, under which market structures does that information change, and what is the probability that the signal will cease to satisfy its validation standard within a declared future horizon?

The intended output is not a deterministic expiry date. It is a calibrated conditional statement:

\[
P\!\left(\tau_{\mathrm{fail}} \le t+H \mid \mathcal{F}_t\right),
\]

where \(\tau_{\mathrm{fail}}\) is the first future time at which the signal breaches a predeclared predictive, economic, calibration, stability, or data-quality boundary.

## 3. Final product requirement

Version 3 must deliver a reusable research and decision-support package, not a one-off backtest.

A user must be able to:

1. map a new dataset into the canonical data contract;
2. run data-quality and causal-feature validation;
3. estimate market-regime and panic-consistent probabilities;
4. evaluate RSI and Bollinger interpretations, including continuation and mean-reversion forms;
5. compare each signal model with a matched non-signal benchmark;
6. estimate conditional predictive and economic contribution;
7. estimate signal-failure probability over declared horizons;
8. obtain an operational validity state and governed action;
9. reproduce all evidence through manifests, locks, tests, and reports.

## 4. System architecture

Version 3 contains two distinct model layers and one governed decision layer.

### 4.1 Forecast layer

The forecast layer estimates direction, expected return, and large-move probability using:

\[
\widehat{Y}_{t,h}
=
 f\!\left(X_t, S_t, Z_t, S_t \otimes Z_t\right),
\]

where:

- \(X_t\) is the matched benchmark information set;
- \(S_t\) contains registered RSI and Bollinger features;
- \(Z_t\) contains filtered regime, spectral-dependence, liquidity, volatility, leverage, and stress features;
- \(S_t \otimes Z_t\) represents predeclared conditional interactions.

### 4.2 Validity and failure layer

The validity layer estimates whether the forecast layer continues to satisfy the registered standard:

\[
q_{t,H}
=
P\!\left(\tau_{\mathrm{fail}} \le t+H \mid \mathcal{G}_t\right),
\]

where \(\mathcal{G}_t\) includes recent benchmark-relative loss, net economic contribution, calibration drift, regime-transition risk, parameter instability, coverage, cost sensitivity, data quality, and structural-break evidence.

### 4.3 Decision layer

The decision layer combines forecast value and failure risk. It does not convert a weak forecast into an authorized signal.

Permitted operational states are:

```text
VALID
CONDITIONALLY_VALID
DEGRADING
SUSPENDED
REVALIDATION_REQUIRED
INVALID
```

Permitted governed actions are:

```text
USE_WITHIN_REGISTERED_BOUNDARIES
USE_ONLY_IN_APPROVED_REGIMES
REDUCE_RELIANCE
SUSPEND_NEW_DECISIONS
REVALIDATE_BEFORE_REUSE
DO_NOT_USE
```

## 5. Panic-consistent regime boundary

Version 3 may estimate `PANIC_CONSISTENT_REGIME` probability. It must not claim causal investor panic unless the available information includes sufficient leverage, liquidation, liquidity, order-book, derivatives, cross-venue, and market-transmission evidence.

The regime layer must include spectral dependence measures but may not define panic from the largest eigenvalue alone.

Required spectral candidates include:

- dominant-eigenvalue share;
- eigenvalue gap;
- participation ratio;
- spectral entropy;
- first-eigenvector concentration;
- change in dominant-eigenvalue share;
- average and dispersion of pairwise correlations;
- network-density or dependence-concentration measures.

## 6. Signal interpretations

Version 3 must not treat an indicator as having one invariant interpretation.

### RSI

- overbought mean reversion;
- oversold mean reversion;
- overbought continuation;
- oversold continuation;
- threshold crossings;
- threshold duration and persistence;
- RSI slope and acceleration;
- price-RSI divergence;
- regime-adaptive thresholds where selected exclusively in training data.

### Bollinger Bands

- upper-band mean reversion;
- lower-band mean reversion;
- upper-band breakout;
- lower-band breakdown;
- percentage-B position;
- band-distance magnitude;
- bandwidth level and expansion;
- squeeze and post-squeeze transition;
- persistence outside the bands.

## 7. Canonical data contract

### Required fields

```text
timestamp
asset
venue
open
high
low
close
volume
```

### Optional but governed fields

```text
benchmark_asset_returns
funding_rate
open_interest
long_liquidations
short_liquidations
bid_ask_spread
order_book_depth
order_book_imbalance
exchange_inflows
exchange_outflows
stablecoin_flow
cross_venue_price_dispersion
realised_volatility
```

Every source must be mapped through an adapter into the canonical schema. Source-specific fields may not enter model code directly.

## 8. Validation architecture

The programme must use:

- nested chronological development selection;
- purge gaps matched to forecast horizons;
- no random shuffle;
- training-only preprocessing and regime estimation;
- matched benchmark-versus-signal comparisons;
- a frozen final evaluation segment;
- multiplicity control;
- dependence-aware intervals;
- cost-adjusted economic gates;
- calibration, coverage, concentration, and stability controls;
- external asset and venue replication;
- prospective monitoring simulation.

## 9. Required evidence gates

No signal may receive `VALID` or `CONDITIONALLY_VALID` status unless all applicable gates pass:

1. **Predictive gate:** positive benchmark-relative predictive contribution with registered uncertainty control.
2. **Economic gate:** positive net contribution after declared costs with a positive lower confidence bound.
3. **Chronological gate:** no unacceptable concentration in one fold, month, event, or subperiod.
4. **Calibration gate:** acceptable probability calibration and no material calibration drift.
5. **Coverage gate:** sufficient actionable observations and decisions.
6. **Regime gate:** conditional claims supported by sufficient observations in each approved regime.
7. **Failure-model gate:** calibrated and discriminative failure-risk estimates under prospective validation.
8. **Transportability gate:** declared external-replication evidence for any general claim.
9. **Data-quality gate:** no unresolved missingness, timestamp, duplication, leakage, or source-consistency failure.

## 10. Failure event definition

A failure event must be declared prospectively and cannot be created after observing results.

A candidate failure event may be triggered when a registered monitoring window breaches one or more of the following for the required persistence period:

- benchmark-relative predictive contribution below the approved tolerance;
- net economic contribution below zero after costs;
- calibration error above the approved boundary;
- coverage below the minimum operational level;
- structural-break posterior above its escalation threshold;
- parameter or feature instability above tolerance;
- regime transport failure;
- critical data-quality failure.

Single adverse observations or isolated losing trades do not constitute signal failure.

## 11. External replication requirement

Version 3 must not rely on SOL alone. At minimum, the framework must support:

- SOL as the historical continuity case;
- BTC and ETH as cross-asset replication cases;
- more than one venue where comparable data rights and history permit;
- a broader liquid-crypto panel for spectral dependence and panic-consistent estimation.

Assets used to define a market regime must be separated from the target asset where required to prevent mechanical leakage.

## 12. Reusable deliverables

The final Version 3 release must include:

- canonical schema and source-adapter interface;
- data validation and quality report;
- causal feature engine;
- spectral and panic-consistent regime engine;
- RSI and Bollinger signal engine;
- matched benchmark and candidate forecast engine;
- validity and failure-probability engine;
- economic decision-policy engine;
- nested development and locked-evaluation runner;
- external-replication runner;
- prospective monitoring simulator;
- CLI and configuration templates;
- machine-readable prediction, validity, and decision outputs;
- model cards, evidence report, manifests, tests, and checkpoint locks.

## 13. Non-rescue rule

Version 3 may discover useful conditional structures, but it may not rewrite the frozen Version 2 conclusions. RSI and Bollinger must earn new Version 3 status through the complete Version 3 process.

## 14. Model boundary

Version 3 is a governed quantitative research and decision-support framework. It is not a guarantee of profit, a deterministic market oracle, an execution engine, or an authorization to ignore liquidity, capacity, market-impact, legal, tax, operational, or venue risk.