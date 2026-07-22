# Version 1 Empirical Determination

## Executive determination

Under the frozen SOL/USDT four-hour specification, neither RSI nor Bollinger Bands established stable incremental predictive value over the common non-indicator benchmark. The combined specification also failed the establishment gate.

The result concerns incremental model contribution. It does not state that every historical threshold event was directionally incorrect. It establishes that the declared indicator information did not improve probability forecasts consistently across the chronological validation folds and did not produce a statistically reliable incremental economic contribution after the stated cost assumption.

## Evidence summary

| Candidate model | Positive predictive folds | Mean incremental log-loss contribution | Mean incremental net edge | 95% edge interval | Status |
|---|---:|---:|---:|---:|---|
| RSI | 1 / 5 | -0.001150 | 0.0000678 | [-0.0000541, 0.0001848] | `NOT_ESTABLISHED` |
| Bollinger Bands | 1 / 5 | -0.001104 | 0.0000438 | [-0.0000846, 0.0001760] | `NOT_ESTABLISHED` |
| Combined specification | 2 / 5 | -0.002617 | -0.0001223 | [-0.0002985, 0.0000539] | `NOT_ESTABLISHED` |

## Indicator-specific determinations

### RSI

The RSI specification improved predictive performance in one of five chronological folds. Its mean benchmark-relative probability contribution was negative, and the confidence interval for incremental economic edge included zero. Stable incremental value was therefore not established.

### Bollinger Bands

The Bollinger specification improved predictive performance in one of five chronological folds. The descriptive event evidence was inconclusive, and the benchmark-relative economic interval included zero. Stable incremental value was therefore not established.

### Combined specification

The combined model improved predictive performance in two of five folds but produced a negative mean incremental economic edge. The result does not support promotion of the combined specification over the standalone models.

## Institutional interpretation

The appropriate Version 1 determination is:

> No operational stopping point can be identified because the prerequisite of stable out-of-sample value was not met under the frozen specification.

This distinction is material for model governance. A deterioration or suspension decision is valid only after historical establishment. Where establishment fails, the status remains `NOT_ESTABLISHED`, irrespective of isolated favourable periods or visually compelling events.

## Decision implications

The Version 1 evidence supports four conclusions:

1. descriptive indicator events should not be treated as evidence of persistent forecasting value;
2. the common benchmark absorbs a material portion of the information represented by the indicators;
3. the combined specification does not overcome the instability observed in the standalone models;
4. further methodological development should test conditional validity without revising Version 1 post hoc.

## Next methodological phase

Version 2 will assess whether useful information is conditional on forecast horizon, target definition, market regime, nonlinear response, or continuation-versus-reversal interpretation. The design is predeclared in [`ROADMAP.md`](ROADMAP.md) and requires nested chronological selection, a locked final holdout, and complete reporting of all declared candidates.
