# Version 2 Checkpoint D2C

D2C is the development-admission and family-level pipeline-freeze checkpoint.

It consumes the frozen D2A and D2B development evidence, applies the predeclared stability, calibration, coverage, and concentration controls, and records one of two outcomes for each confirmatory family:

- `PIPELINE_ADMITTED_FOR_METHODOLOGY_LOCKED_EVALUATION`; or
- `NO_PIPELINE_ADMITTED`.

For each admitted family, D2C freezes a signal definition, structural model, estimation window, state-conditioning choice, calibration method, and abstention threshold. Each complete pipeline is serialized canonically and assigned a SHA-256 hash.

D2C does not evaluate the final economic gate. It does not authorize or access the methodology-locked evaluation period. The next checkpoint is a separate D3 authorization and execution boundary.
