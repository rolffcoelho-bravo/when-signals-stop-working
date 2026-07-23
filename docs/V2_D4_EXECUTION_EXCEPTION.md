
# D4 Execution Exception: Bootstrap Block-Length Materialization

## Recorded exception

The Version 2 protocol required the primary moving-block-bootstrap length to be selected from development dependence diagnostics and frozen before holdout access. D0 through D3 preserved the bootstrap method but did not materialize an explicit numeric block length before D3 execution.

This omission is disclosed rather than retroactively described as predeclared.

## Non-discretionary resolution

Before D4 inference execution, the implementation fixes a deterministic development-only rule:

1. use SOL four-hour log returns ending on 2025-06-30 20:00 UTC;
2. square the returns to represent volatility dependence;
3. calculate autocorrelation for lags 1 through 48;
4. select the first lag at which absolute autocorrelation is at or below 0.10 for three consecutive lags;
5. use adjacent sensitivity lengths of 14 and 28 observations.

The rule resolves a primary length of 21 observations. No D3 probability, loss, return, subperiod, or gate result enters this calculation.

## Governance consequence

This is a late materialization and execution exception, not a change to the signal pipeline or establishment gates. D4 reports all three block lengths. Where conclusions differ, the conservative result governs. The exception remains visible in the D4 manifest and final report.
