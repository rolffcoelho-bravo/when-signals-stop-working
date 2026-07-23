
# Version 2 D4 Confirmatory Inference and Economic Gates

## Purpose

D4 converts the immutable D3 prediction record into the predeclared confirmatory and economic determinations. It does not refit, recalibrate, replace, or retune the frozen Bollinger pipeline.

## Confirmatory family

The family remains H1 RSI direction and H2 Bollinger direction. RSI received `NO_PIPELINE_ADMITTED` at D2C and therefore enters the Holm family with a confirmatory p-value of 1.0. This preserves the frozen family size without creating an RSI holdout result.

Bollinger is evaluated using benchmark-minus-candidate observation-level log-loss differentials. Positive values favour the candidate. The one-sided statistic uses horizon-overlap-aware Newey-West covariance. The four-hour pipeline has a one-candle horizon, so the overlap lag is zero.

The predictive gate requires all of the following:

- positive mean incremental log loss;
- Holm-adjusted p-value below 0.05;
- positive 95 percent moving-block-bootstrap lower bound;
- positive contribution in at least two of three locked subperiods;
- no material calibration failure relative to the matched benchmark.

## Economic comparison

D4 applies the frozen 0.05 probability-distance threshold to both the candidate and matched benchmark probabilities. It computes candidate-minus-benchmark gross and net returns under identical one-way costs.

The primary gate uses 10 basis points. Five and 20 basis points are sensitivities. Admission requires positive mean incremental net contribution, a positive 95 percent bootstrap lower bound, at least 10 percent candidate coverage, and at least 100 nonzero candidate decisions.

## Result interpretation

A positive average loss differential alone is insufficient. Multiplicity, dependence-aware uncertainty, chronological consistency, calibration, and economic contribution jointly govern the result.

D4 may assign:

- `NO_INCREMENTAL_EVIDENCE` when the locked predictive gate fails;
- `PREDICTIVE_EVIDENCE_ONLY` when predictive evidence passes but economic or later robustness controls do not;
- no `PRIMARY_CASE_ESTABLISHED` grade until the robustness and concentration gate is complete.

## Scope controls

D4 cannot:

- reintroduce RSI;
- execute an alternative Bollinger pipeline;
- change the signal, horizon, model, calibration, window, or decision threshold;
- use the V2.1 panic-state extension in the confirmatory verdict;
- revise D3 predictions.
