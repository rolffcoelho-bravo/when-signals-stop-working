# Contributing

Contributions are welcome when they preserve the research contract.

## Requirements

- declare new targets, horizons, models, and parameter grids before evaluating the locked holdout;
- use chronological validation and preserve the forecast-horizon gap;
- report every declared candidate, including negative results;
- add tests for new data, model, monitoring, and reporting behavior;
- never commit credentials, private account data, or absolute local paths;
- update the replication manifest, checksums, references, and roadmap where relevant.

Methodological changes that alter the frozen V1 experiment should be versioned as V2 or later rather than silently replacing V1.
