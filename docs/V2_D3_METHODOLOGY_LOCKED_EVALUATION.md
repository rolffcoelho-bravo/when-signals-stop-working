# Version 2 D3 Methodology-Locked Evaluation

D3 is the first irreversible Version 2 evaluation checkpoint. It authorizes and executes one methodology-locked evaluation for the single Bollinger pipeline frozen at D2C.

## Authorized object

- family: Bollinger Bands;
- horizon: four hours;
- signal: 10-period, 2.5-standard-deviation continuation interpretation;
- model: shallow histogram gradient boosting;
- estimation window: expanding;
- state conditioning: soft filtered-state interactions;
- calibration: none;
- abstention distance: 0.05;
- canonical pipeline hash: `2f85b54f8f178ec59c2bfb8a06cd8dedb3e053e2bec4da40cb446d380def2851`.

RSI is not authorized to re-enter D3 because D2C recorded `NO_PIPELINE_ADMITTED`.

## Single-access sequence

1. commit and push the D3 evaluation engine;
2. create, commit, and push the explicit authorization record before result access;
3. set the required local authorization environment variable;
4. fit all preprocessing, state estimation, benchmark, candidate, and calibration components from development information only;
5. apply the frozen pipeline once to the methodology-locked period;
6. preserve prediction-level evidence, state parameters, hashes, and raw metrics;
7. commit the evidence without modifying the pipeline.

D3 exposes raw locked-evaluation evidence but does not issue a confirmatory statistical, economic, robustness, or operational verdict. Those gates remain assigned to D4 and later checkpoints.
