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
