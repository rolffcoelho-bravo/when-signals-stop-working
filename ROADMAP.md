# Methodology Roadmap

## V1 - Transparent signal-validity framework (current)

V1 is the simplest defensible implementation. It is designed to make the research question auditable before adding complexity.

- conventional RSI and Bollinger event studies;
- a common non-indicator benchmark;
- regularized logistic probability models;
- expanding-window out-of-sample validation with a forecast-horizon gap;
- transaction-cost-adjusted incremental edge;
- a three-state Gaussian Markov forward filter initialized only from training data;
- a one-sided CUSUM for sequential deterioration;
- separate verdicts: `NOT_ESTABLISHED`, `ACTIVE`, `REDUCED`, and `SUSPENDED`.

V1 is intentionally not an optimization engine. Its role is to establish whether a signal contains information beyond simpler market variables and whether that information remains operationally credible.

## V2 - Inference hardening and replication

The next layer strengthens statistical claims without changing the core research question.

- locked final holdout period;
- exchange and quote-currency replication;
- probability calibration and calibration drift;
- Diebold-Mariano tests for pairwise forecast comparison;
- Superior Predictive Ability testing when multiple configurations are evaluated;
- block-bootstrap cost and threshold sensitivity;
- explicit data-vintage and run-manifest controls.

## V3 - Dynamic signal coefficients and richer regimes

Replace fixed indicator effects with time-varying parameter models.

- dynamic logistic or state-space coefficients;
- posterior or filtered probability that the signal coefficient is positive;
- maximum-likelihood or Bayesian hidden Markov regimes;
- regime-dependent transition probabilities;
- duration dependence and semi-Markov extensions;
- model averaging across transparent and latent regime specifications.

## V4 - Online changepoints and failure probability

Move from a binary deterioration alarm to a probabilistic failure layer.

- Bayesian online changepoint detection;
- posterior run-length distribution;
- probability of a structural break in the recent window;
- horizon-specific signal-failure hazard;
- decision thresholds calibrated to false-alarm and detection-delay objectives;
- adaptive retraining only after a validated change in the predictive mechanism.

## V5 - Transmission, microstructure, and production governance

Extend the framework from a single-market indicator test to a decision-grade research system.

- funding rates, open interest, liquidation intensity, spreads, and order-book imbalance;
- BTC, ETH, and market-wide transmission variables;
- multivariate state-space, network, or point-process propagation models;
- venue-specific execution and capacity constraints;
- versioned data snapshots, model registry, automated validation evidence, and CI gates;
- scheduled monitoring with documented promotion, reduction, suspension, and reactivation rules.

## Promotion principle

A more complex version is promoted only if it improves locked out-of-sample evidence, interpretability, or operational control. Complexity is not treated as evidence by itself.
