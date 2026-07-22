# Repository Structure

```text
when-signals-stop-working/
├── README.md
├── RESULTS.md
├── ROADMAP.md
├── RESEARCH_SCOPE.md
├── V2_DESIGN_FREEZE.md
├── V2_PROTOCOL_LOCK.json
├── START_HERE.md
├── CITATION.cff
├── REPLICATION_MANIFEST.json
├── REPLICATION_CHECKSUMS.sha256
├── PUBLIC_RELEASE_AUDIT.json
├── RUN_REPLICATION.ps1
├── RUN_REPLICATION.sh
├── PUBLISH_PUBLIC_REPLICATION.ps1
├── configs/
│   ├── sol_4h_primary.json
│   └── v2_experiment_registry.json
├── data/
│   ├── README.md
│   ├── raw/
│   └── processed/
├── environment/
├── outputs/
│   ├── README.md
│   └── figures/
├── scripts/
│   └── verify_v2_protocol_lock.py
├── src/shockbridge_signal_validity/
├── tests/
│   └── test_v2_design_freeze.py
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

## Version 2 implementation checkpoints

```text
RUN_V2_DEVELOPMENT_SCAFFOLD.*      D0 development partition and fold assets
RUN_V2_D1_CAUSAL_ENGINE.*          D1 causal features and filtered states
RUN_V2_D2A_SCREENING.*             D2A signal-specification screening
RUN_V2_D2B_SELECTION.*             D2B full nested pipeline selection
RUN_V2_D2C_ADMISSION.*             D2C development admission and pipeline freeze
configs/v2_d2b_selection.json      D2B fixed execution controls
src/.../v2/pipeline_selection.py   matched pipeline, calibration, and policy engine
data/processed/v2/development/     governed D0-D2B development evidence
outputs/v2/development/            checkpoint status records
```

## Version 2 D2B review sequence

1. `V2_D2B_SELECTION_CHECKPOINT.md`
2. `docs/V2_D2B_FULL_NESTED_SELECTION.md`
3. `configs/v2_d2b_selection.json`
4. `src/shockbridge_signal_validity/v2/pipeline_selection.py`
5. `data/processed/v2/development/d2b_selected_structural_pipelines.csv`
6. `data/processed/v2/development/d2b_selected_calibrations.csv`
7. `data/processed/v2/development/d2b_selected_decision_policies.csv`
8. `data/processed/v2/development/d2b_outer_fold_results.csv`
9. `data/processed/v2/development/d2b_family_horizon_summary.csv`
10. `V2_D2B_SELECTION_LOCK.json`

## Version 2 D2C review sequence

1. `V2_D2C_ADMISSION_CHECKPOINT.md`
2. `docs/V2_D2C_DEVELOPMENT_ADMISSION.md`
3. `configs/v2_d2c_admission.json`
4. `src/shockbridge_signal_validity/v2/development_admission.py`
5. `data/processed/v2/development/d2c_family_horizon_admission.csv`
6. `data/processed/v2/development/d2c_family_decisions.csv`
7. `data/processed/v2/development/d2c_frozen_pipeline_registry.json`
8. `outputs/v2/development/d2c_holdout_authorization.json`
9. `V2_D2C_ADMISSION_LOCK.json`
