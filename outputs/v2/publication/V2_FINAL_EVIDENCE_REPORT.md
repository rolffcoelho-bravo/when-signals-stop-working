# Version 2 Final Evidence Report

## Executive determination

Version 2 did not establish stable incremental value for either confirmatory
technical-signal family.

RSI did not pass development admission and therefore did not enter the locked
evaluation. The sole admitted Bollinger pipeline produced a positive average
benchmark-relative loss differential and favourable mean economic contribution,
but the full confirmatory predictive and economic gates failed.

The immutable Version 2 evidence grade is:

> `NO_INCREMENTAL_EVIDENCE`

## Confirmatory evidence

| Measure | Result |
|---|---:|
| Bollinger mean incremental log loss | 0.002108928 |
| Raw one-sided p-value | 0.032339 |
| Holm-adjusted p-value | 0.064677 |
| Primary predictive bootstrap lower bound | -0.000390157 |
| Positive locked subperiods | 2 of 3 |
| Mean incremental net return at 10 bps | 0.000130196 |
| Economic 95% lower bound | -0.000097020 |
| Candidate coverage | 14.67% |
| Candidate decisions | 340 |

## Robustness and concentration

The D5 diagnostics found that favourable means were not driven by a single
calendar month and remained positive under leave-one-month-out and registered
joint-tail-trimming checks. Mean economic contribution also remained positive
at 5, 10 and 20 basis points.

These favourable diagnostics do not establish validity. Predictive and
economic bootstrap lower bounds crossed zero across every registered block
length, the Holm-adjusted p-value exceeded 0.05, one locked subperiod had a
negative predictive contribution, exact signal-parameter selection was diffuse
across development folds, and active-confidence strata did not show uniform
economic contribution.

Robustness determination:

> `FAVOURABLE_MEANS_NOT_CONFIDENCE_ROBUST`

Fragility classification:

> `UNCERTAINTY_AND_PARAMETER_SPECIFICATION_SENSITIVE`

## State evidence boundary

The locked sample contains only 37 observations labelled as
stress by the existing filtered-state engine. This is insufficient for a
confirmatory panic interpretation. State-stratified outputs are descriptive
only and cannot change the Version 2 verdict.

## Institutional interpretation

The evidence supports a governance conclusion rather than a trading claim:

> Technical-signal use should not be authorized merely because average
> contributions are favourable. Establishment requires multiplicity-adjusted,
> dependence-aware, chronologically stable and economically bounded evidence.

Version 2 therefore closes with no RSI admission, no established Bollinger
incremental value, no operational deployment authorization, and no monitoring
status.

## V2.1 separation

V2.1 will test whether independently defined panic-consistent, liquidity-stress
or liquidation regimes can govern signal interpretation, degradation,
suspension or revalidation. It cannot alter any Version 2 decision.
