# V1 Empirical Results

## Executive conclusion

Under the frozen SOL/USDT four-hour specification, neither RSI nor Bollinger Bands established stable incremental predictive value over the non-indicator benchmark. The combined model also failed the establishment gate.

This does **not** show that every historical indicator event was wrong. It shows that the declared indicator information did not improve benchmark-relative probability forecasts consistently across chronological folds and did not establish a statistically reliable incremental economic edge after the cost assumption.

## Summary

| Model | Positive predictive folds | Mean incremental log-loss gain | Mean incremental net edge | 95% edge interval | V1 status |
|---|---:|---:|---:|---:|---|
| RSI | 1 / 5 | -0.001150 | 0.0000678 | [-0.0000541, 0.0001848] | `NOT_ESTABLISHED` |
| Bollinger Bands | 1 / 5 | -0.001104 | 0.0000438 | [-0.0000846, 0.0001760] | `NOT_ESTABLISHED` |
| Combined | 2 / 5 | -0.002617 | -0.0001223 | [-0.0002985, 0.0000539] | `NOT_ESTABLISHED` |

## Direct answer

The correct V1 answer to “When will RSI stop working?” is:

> A stopping point cannot be identified until stable out-of-sample value is established. Under this frozen test, RSI's incremental edge was not established.

The same conclusion applies independently to Bollinger Bands.

## Why V2 exists

The V1 result motivates a stronger predeclared test of whether useful information is conditional on horizon, target, regime, nonlinear response, or reversal-versus-continuation interpretation. The full design is in [`ROADMAP.md`](ROADMAP.md).
