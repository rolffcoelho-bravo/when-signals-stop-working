# Version 2 D4 verifier erratum

## Scope

The initial D4 asset verifier incorrectly encoded outcomes from the package-validation run as fixed verification requirements. Specifically, it expected exactly one positive locked subperiod and a negative primary-cost mean incremental net return.

Those values are empirical outcomes, not elements of the frozen methodology.

## Correction

The verifier now checks that:

- all three predefined locked subperiods are present;
- their row counts reconcile to the committed D3 predictions;
- each recorded sign agrees with its calculated mean;
- the positive-subperiod count agrees with the gate record;
- predictive and economic checks agree with the frozen thresholds;
- gate decisions, evidence grade, manifest and checksums are internally consistent;
- RSI remains `NO_PIPELINE_ADMITTED`;
- the frozen Bollinger pipeline and D3 predictions remain unchanged.

The narrative is also generated from the observed signs and gate outcomes rather than assuming a negative economic mean.

## Governance effect

This erratum does not change:

- the D3 predictions;
- the frozen Bollinger pipeline;
- any p-value, confidence interval or bootstrap draw;
- any cost, calibration, coverage or concentration threshold;
- the RSI exclusion;
- the panic-state separation;
- the confirmatory or economic gate definitions.

The correction affects verification and reporting only.