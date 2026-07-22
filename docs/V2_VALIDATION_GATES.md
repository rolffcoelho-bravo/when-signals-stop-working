# Version 2 Validation Gates

## Gate 0 - Protocol integrity

Required evidence:

- `V2_PROTOCOL_LOCK.json` verifies;
- implementation commit is recorded;
- experiment registry validates;
- no locked-evaluation output exists before authorised access;
- public-information audit passes.

Failure blocks all holdout access.

## Gate 1 - Data integrity and chronology

Required evidence:

- unique UTC timestamps;
- no missing OHLCV fields;
- declared interval consistency;
- causal alignment across SOL, BTC, and any external series;
- horizon-specific target truncation;
- training-only target quantiles and preprocessing;
- purge gap equal to the forecast horizon.

Failure blocks model comparison for the affected dataset.

## Gate 2 - Development predictive stability

For a confirmatory signal family to enter the locked evaluation:

- mean outer-fold incremental directional log-loss contribution must be positive;
- at least three of five outer folds must be positive;
- no single outer fold may account for more than 60% of total positive loss reduction;
- selected pipeline identity and inner-selection frequency must be recorded;
- the candidate must not be dominated by its matched benchmark in calibration and primary loss jointly.

Failure produces `DEVELOPMENT_NOT_ESTABLISHED` and the family does not access holdout.

## Gate 3 - Locked-evaluation predictive superiority

Required evidence:

- positive mean benchmark-relative directional log-loss contribution;
- one-sided predictive-superiority test with Holm-adjusted `p < 0.05` across H1 and H2;
- positive contribution in at least two of three approximately equal chronological holdout subperiods;
- no material calibration failure relative to the benchmark.

Failure prevents an establishment determination regardless of secondary results.

## Gate 4 - Economic contribution

At the primary ten-basis-point one-way cost:

- mean incremental net contribution must be positive;
- moving-block-bootstrap 95% lower confidence bound must exceed zero;
- decision coverage must be at least 10%;
- at least 100 non-zero holdout decisions are required;
- turnover and gross-to-net attrition must be reported.

Predictive superiority without this gate is reported as predictive evidence only and does not support operational promotion.

## Gate 5 - Robustness and concentration

Required evidence:

- result is not supported exclusively by one narrow parameter value;
- direction is consistent under at least two estimation-window schemes;
- result is not reversed at the twenty-basis-point sensitivity solely through extreme turnover;
- no single calendar month contributes more than 40% of cumulative positive net contribution;
- alternate block lengths do not reverse the uncertainty conclusion;
- signal coverage and performance remain jointly interpretable.

Failure produces a conditional or fragile evidence grade, not an established signal.

## Gate 6 - External transportability

External replication is graded separately:

- same-asset, independent-venue replication has priority;
- BTC and ETH are secondary cross-asset cases;
- dataset eligibility is determined by predeclared coverage and quality rules, not performance;
- directionally consistent benchmark-relative loss contribution is required;
- all eligible replications are reported.

External replication upgrades evidence from `PRIMARY_CASE_ESTABLISHED` to `EXTERNALLY_REPLICATED`. Failure does not alter the primary-case statistics but restricts generalisation.

## Gate 7 - Operational admission

An `ACTIVE` operational status requires:

- primary-case establishment;
- external replication or a formally approved transportability exception;
- a prospective monitoring period after model freeze;
- approved deterioration thresholds;
- documented ownership, review frequency, and escalation process.

Until Gate 7 passes, Version 2 findings remain research evidence rather than a production signal designation.

## Evidence grades

| Grade | Interpretation |
|---|---|
| `NO_INCREMENTAL_EVIDENCE` | Development or holdout predictive gate failed. |
| `PREDICTIVE_EVIDENCE_ONLY` | Predictive gate passed; economic or robustness gate failed. |
| `PRIMARY_CASE_ESTABLISHED` | Primary predictive, economic, and robustness gates passed. |
| `EXTERNALLY_REPLICATED` | Primary establishment and declared external replication passed. |
| `MONITORING_READY` | Replicated evidence and operational controls are complete. |

The Version 1 operational statuses remain unchanged. Evidence grades document the route to any later operational promotion.
