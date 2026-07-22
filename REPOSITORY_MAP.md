# Repository Structure

```text
when-signals-stop-working/
├── README.md
├── RESULTS.md
├── ROADMAP.md
├── RESEARCH_SCOPE.md
├── V2_DESIGN_FREEZE.md
├── V2_PROTOCOL_LOCK.json
├── V2_IMPLEMENTATION_CHECKPOINT.md
├── START_HERE.md
├── CITATION.cff
├── REPLICATION_MANIFEST.json
├── REPLICATION_CHECKSUMS.sha256
├── PUBLIC_RELEASE_AUDIT.json
├── RUN_REPLICATION.ps1
├── RUN_REPLICATION.sh
├── RUN_V2_DEVELOPMENT_SCAFFOLD.ps1
├── RUN_V2_DEVELOPMENT_SCAFFOLD.sh
├── PUBLISH_PUBLIC_REPLICATION.ps1
├── configs/
│   ├── sol_4h_primary.json
│   ├── v2_experiment_registry.json
│   └── v2_runtime_defaults.json
├── data/
│   ├── README.md
│   ├── raw/
│   └── processed/
│       └── v2/development/
├── environment/
├── outputs/
│   ├── README.md
│   ├── figures/
│   └── v2/development/
├── scripts/
│   ├── verify_v2_protocol_lock.py
│   ├── build_v2_development_assets.py
│   └── verify_v2_development_scaffold.py
├── src/shockbridge_signal_validity/
│   └── v2/
│       ├── contracts.py
│       ├── inventory.py
│       ├── manifests.py
│       ├── partitions.py
│       ├── registry.py
│       ├── signals.py
│       ├── splits.py
│       └── targets.py
├── tests/
│   ├── test_v2_design_freeze.py
│   ├── test_v2_implementation_scaffold.py
│   └── test_v2_holdout_guard.py
├── docs/
│   ├── STATUS_GOVERNANCE.md
│   ├── REPLICATION_PACKAGE.md
│   ├── PUBLIC_RELEASE_POLICY.md
│   ├── MODEL_CONTRACT.md
│   ├── RESEARCH_PROTOCOL.md
│   ├── EDITORIAL_STANDARD.md
│   ├── V2_RESEARCH_PROTOCOL.md
│   ├── V2_MODEL_CONTRACT.md
│   ├── V2_VALIDATION_GATES.md
│   ├── V2_MULTIPLE_TESTING_CONTROL.md
│   ├── V2_DATA_AND_REPLICATION_PLAN.md
│   ├── V2_HOLDOUT_GOVERNANCE.md
│   ├── V2_IMPLEMENTATION_ARCHITECTURE.md
│   ├── V2_DEVELOPMENT_EXECUTION_PLAN.md
│   ├── FIGURE_CATALOG.md
│   └── REFERENCES.md
└── .github/workflows/ci.yml
```

## Version 1 review sequence

1. `README.md`
2. `RESULTS.md`
3. `RESEARCH_SCOPE.md`
4. `docs/MODEL_CONTRACT.md`
5. `docs/STATUS_GOVERNANCE.md`
6. `docs/REPLICATION_PACKAGE.md`
7. `outputs/research_report.md`

## Version 2 design-freeze review sequence

1. `V2_DESIGN_FREEZE.md`
2. `configs/v2_experiment_registry.json`
3. `docs/V2_RESEARCH_PROTOCOL.md`
4. `docs/V2_MODEL_CONTRACT.md`
5. `docs/V2_VALIDATION_GATES.md`
6. `docs/V2_MULTIPLE_TESTING_CONTROL.md`
7. `docs/V2_HOLDOUT_GOVERNANCE.md`
8. `docs/V2_DATA_AND_REPLICATION_PLAN.md`
9. `V2_PROTOCOL_LOCK.json`

## Version 2 D0 implementation review sequence

1. `V2_IMPLEMENTATION_CHECKPOINT.md`
2. `docs/V2_IMPLEMENTATION_ARCHITECTURE.md`
3. `docs/V2_DEVELOPMENT_EXECUTION_PLAN.md`
4. `configs/v2_runtime_defaults.json`
5. `src/shockbridge_signal_validity/v2/`
6. `scripts/build_v2_development_assets.py`
7. `scripts/verify_v2_development_scaffold.py`
8. `tests/test_v2_implementation_scaffold.py`
9. `tests/test_v2_holdout_guard.py`


## Version 2 D1 causal engine

- `V2_D1_CAUSAL_ENGINE_CHECKPOINT.md` - D1 checkpoint scope and governance.
- `configs/v2_d1_engine.json` - fixed D1 numerical and causal controls.
- `src/shockbridge_signal_validity/v2/causal_features.py` - benchmark and registered signal features.
- `src/shockbridge_signal_validity/v2/filtered_states.py` - fold-scoped forward state filter.
- `scripts/build_v2_d1_assets.py` - development-only D1 asset builder.
- `scripts/verify_v2_d1_assets.py` - generated-asset validation.
- `V2_D1_ENGINE_LOCK.json` - tamper-evident D1 code lock.


## D2A nested screening

- `configs/v2_d2a_screening.json`: fixed screening estimator and governance boundaries.
- `src/shockbridge_signal_validity/v2/predictive_screening.py`: matched predictive screening primitives.
- `scripts/build_v2_d2a_assets.py`: development-only nested screening execution.
- `scripts/verify_v2_d2a_assets.py`: generated-evidence verification.
- `V2_D2A_SELECTION_LOCK.json`: tamper-evident D2A implementation lock.
