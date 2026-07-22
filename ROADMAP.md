# Methodology Roadmap

## V1 — Transparent signal-validity framework (current)

V1 is the simplest defensible implementation. It establishes whether fixed RSI and Bollinger specifications add information beyond a market-state benchmark before complexity is introduced.

- conventional event studies;
- common non-indicator benchmark;
- regularized logistic probability models;
- five expanding chronological folds with a horizon gap;
- cost-adjusted incremental edge and block-bootstrap intervals;
- training-only three-state Gaussian Markov forward filter;
- robust one-sided CUSUM monitoring;
- complete public replication package.

**Published finding:** RSI, Bollinger Bands, and their combined specification are `NOT_ESTABLISHED` under the frozen SOL four-hour V1 design.

## V2 — Conditional validity and inference hardening

V2 addresses the low fold stability without tuning V1 until it becomes positive. Every extension is predeclared and evaluated on nested chronological validation with a locked final holdout.

### Targets

- next-period direction;
- expected cumulative return;
- large-move or tail-event probability.

### Horizons

- 4, 8, 12, and 24 hours, all reported;
- no selection of only the best horizon after observing the holdout.

### Signal interpretation

- contrarian or mean-reversion interpretation;
- continuation or breakout interpretation;
- regime-conditioned choice defined inside training data.

### Conditional structure

- interactions with filtered range, trend, and stress probabilities;
- nonlinear splines or shallow boosted trees alongside regularized logistic regression;
- abstention thresholds with both performance and coverage reported.

### Selection and inference

- nested walk-forward selection of a restrained RSI and Bollinger parameter grid;
- expanding versus one-year and two-year rolling windows;
- locked final holdout;
- probability calibration and calibration drift;
- Diebold–Mariano comparison for fixed alternatives;
- Superior Predictive Ability controls when many candidates are evaluated;
- cost and threshold sensitivity with dependence-aware bootstrap intervals.

### Replication

- Binance SOL/USDT remains the primary case;
- independent venue replication where comparable history exists;
- BTC and ETH secondary cross-asset validation.

V2 succeeds only if the improvement survives the locked holdout and is not dependent on one venue, one horizon, or one narrow parameter choice.

## V3 — Dynamic signal coefficients and richer regimes

- time-varying logistic or state-space coefficients;
- filtered probability that each signal coefficient is positive;
- fully estimated hidden Markov or semi-Markov regimes;
- regime-dependent transition probabilities and duration dependence;
- transparent-versus-latent regime model averaging.

## V4 — Online changepoints and failure probability

- Bayesian online changepoint detection;
- posterior run-length distribution;
- probability of recent structural break;
- horizon-specific signal-failure hazard;
- false-alarm and detection-delay calibration;
- governed retraining, suspension, and reactivation rules.

This version approaches the literal forward-looking question:

\[
P(	ext{signal failure within the next } H 	ext{ periods}\mid\mathcal F_t).
\]

## V5 — Transmission, microstructure, and production governance

- funding, open interest, liquidations, spreads, and order-book imbalance;
- BTC, ETH, and market-wide transmission variables;
- multivariate state-space, network, or point-process propagation models;
- venue-specific execution, capacity, and slippage controls;
- versioned snapshots, model registry, CI gates, and scheduled monitoring.

## Promotion principle

A more complex version is promoted only when it improves locked out-of-sample evidence, uncertainty quantification, interpretability, or operational control. Complexity is never treated as evidence by itself.
