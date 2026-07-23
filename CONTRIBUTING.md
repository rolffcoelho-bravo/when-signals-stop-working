# Contribution Standard

Contributions are accepted where they preserve the research contract and the institutional publication standard.

## Methodological requirements

- declare new targets, horizons, models, and parameter grids before evaluating locked data;
- preserve chronological validation and the forecast-horizon gap;
- report all declared candidates, including negative results;
- distinguish descriptive, predictive, economic, regime, and deterioration claims;
- add tests for new data, model, monitoring, and reporting behaviour;
- version any change that alters the frozen Version 1 experiment.

## Public-release requirements

- do not commit credentials, account data, private keys, `.env` files, or absolute local paths;
- update the replication manifest, checksums, references, and roadmap where relevant;
- preserve the institutional editorial standard in public documentation and generated reports;
- document model boundaries and data-rights implications.

## Version 2 protocol control

Changes to Version 2 targets, hypotheses, horizons, candidate grids, data partition, holdout rules, multiplicity procedures, or validation gates are protocol amendments. Before locked-evaluation access, an amendment must update the affected documents, regenerate `V2_PROTOCOL_LOCK.json`, and be committed with an explicit rationale. After locked-evaluation access, the same confirmatory claim cannot be redefined.

Version 1 result files and data snapshots listed as protected in `configs/v2_experiment_registry.json` must not be modified on the Version 2 branch.
