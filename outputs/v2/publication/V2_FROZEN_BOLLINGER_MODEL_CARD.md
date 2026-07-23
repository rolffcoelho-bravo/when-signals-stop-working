# Frozen Bollinger Pipeline Model Card

## Model identity

- Signal family: Bollinger Bands
- Frozen pipeline hash: `2f85b54f8f178ec59c2bfb8a06cd8dedb3e053e2bec4da40cb446d380def2851`
- Signal specification: `bollinger-p10-k2.5-continuation`
- Interpretation: `continuation`
- Model family: `shallow_hist_gradient_boosting`
- Estimation window: `expanding`
- Soft state conditioning: `True`
- Calibration: `none`
- Abstention distance: `0.05`
- Horizon: `4` hours

## Development admission

The family passed the D2C development-admission controls and was frozen before
the methodology-locked period was accessed. Development admission was not a
claim of final predictive or economic validity.

## Locked-evaluation determination

- Mean incremental log loss: `0.002108928`
- Raw one-sided p-value: `0.032339`
- Holm-adjusted p-value: `0.064677`
- Positive locked subperiods: `2 of 3`
- Mean incremental net return at 10 bps: `0.000130196`
- Economic 95% lower bound: `-0.000097020`
- Final evidence grade: `NO_INCREMENTAL_EVIDENCE`

## Model boundaries

The pipeline is not approved for operational deployment. The locked evidence
does not support a claim of stable incremental value. Positive average
contributions do not override multiplicity-adjusted inference, bootstrap
uncertainty, chronological instability, or economic confidence requirements.

The existing filtered stress state is descriptive. It does not establish
investor panic, liquidity causality, or liquidation causality. Those mechanisms
belong to the separately frozen V2.1 research programme.

## Governance

- Pipeline retuning after D3: prohibited and not performed.
- RSI re-entry: prohibited and not performed.
- Panic-state conditioning in V2: prohibited and not performed.
- Monitoring admission: not granted.
