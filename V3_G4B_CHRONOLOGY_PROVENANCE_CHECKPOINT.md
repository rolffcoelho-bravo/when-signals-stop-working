# Gate V3-4B — Independent Chronology Compilation and Provenance Checkpoint

## Gate status

> `CHRONOLOGY_COMPILATION_AND_PROVENANCE_COMPLETE_AND_LOCKED`

Gate V3-4B is implemented, validated, and authoritatively locked. It compiles an independently documented, source-driven chronology of crypto-market dislocations across the frozen research sample without accessing Gate V3-3 probabilities, operational states, transitions, mechanism contributions, disagreement measures, or diagnostics.

The gate creates the chronology and provenance evidence required for Gate V3-4C. It does not execute event alignment and does not claim that the registry is a complete census of panic, crisis, or market stress.

## Repository position

- frozen baseline release: `v2.0.0`;
- frozen baseline commit: `5a07299367b80c3940e652e7bbdd208ce86ba5ef`;
- branch: `research/v3-adaptive-signal-validity`;
- parent gate: `V3-4A`;
- parent lock: `V3_G4A_CHRONOLOGY_SIGNAL_USE_CONTRACT_LOCK.json`;
- authoritative parent lock blob: `d3c4ce27808e60b001e7d58e0c5e36be8d8cac6a`;
- V3-4B finalization-preparation commit: `9ef6c80c45628973bb9d9d66fda1944495f5b24d`;
- authoritative V3-4B lock commit: `300ca7254876d6bfdc7adeb18f49d1375bdd1ed3`;
- authoritative V3-4B lock: `V3_G4B_CHRONOLOGY_PROVENANCE_LOCK.json`;
- authoritative V3-4B lock blob: `04ac09a177d2838e0e950c24f278a8e650d2e94a`;
- pre-finalization lock blob: `ceee8a9069b48a74db15e7e3da9e23b2bc0fdf91`;
- frozen sample start: `2021-01-01T00:00:00Z`;
- frozen sample end: `2026-07-22T08:00:00Z`;
- Version 1 and Version 2 determinations modified: none;
- Gate V3-3 model outputs accessed during chronology compilation: no;
- event-alignment evaluation executed: no.

The pre-finalization lock blob is retained only as historical evidence. Gate V3-4C may use only the authoritative blob `04ac09a177d2838e0e950c24f278a8e650d2e94a` as its parent.

## Status distinctions

| Dimension | Status | Evidence |
|---|---|---|
| Gate V3-4B approval | Approved | User authorization |
| Parent V3-4A contract | Locked | Blob `d3c4ce27808e60b001e7d58e0c5e36be8d8cac6a` |
| Source registry | Implemented | 27 documentary sources |
| Canonical event registry | Implemented | 17 canonical events |
| Provenance mapping | Implemented | Every source mapped to at least one canonical event |
| Merge governance | Implemented | Every candidate retained or merged with model access recorded as false |
| Chronology compilation | Validated | Four byte-identical deterministic outputs |
| Isolated and lineage tests | Validated | 19 tests passed |
| Cross-gate historical objects | Validated | 38 objects verified |
| Current latest-owner objects | Validated | 36 objects verified |
| Governed superseded paths | Validated | One cumulative path, `Findings.md` |
| Primary timing eligibility | Frozen | 12 confirmed events |
| Primary timing exclusions | Frozen | 5 boundary-uncertain events |
| Chronology completeness | Not claimed | Documentary registry, not complete ground truth |
| Model-output access | Prohibited and not performed | V3-4A and V3-4B controls |
| Event alignment | Not started | Requires authoritative V3-4B lock |
| Final lock verification | Implemented | Checkpoint-bound verifier in both launchers |
| Gate V3-4B lock | Locked | Blob `04ac09a177d2838e0e950c24f278a8e650d2e94a` |
| Next subgate | V3-4C | Independent event-alignment evaluation |

## Implementation inventory

### Source-driven registry

```text
configs/v3_external_chronology_registry.json
configs/v3_external_chronology_events.json
configs/v3_external_chronology_sources.json
configs/v3_external_chronology_source_map.json
configs/v3_external_chronology_merge_log.json
```

The control registry fixes the parent lock, frozen sample, source policy, component paths, chronology limitations, and the statement that model outputs were not accessed.

The component registries separate:

1. canonical event definitions;
2. documentary source records;
3. event-to-source provenance;
4. candidate-to-canonical merge decisions.

### Deterministic compiler

```text
src/shockbridge_signal_validity/v3/chronology_registry.py
scripts/run_v3_g4b_chronology.py
```

The compiler validates the registry and deterministically generates:

```text
outputs/v3/g4b_chronology/external_chronology.csv
outputs/v3/g4b_chronology/chronology_provenance.json
outputs/v3/g4b_chronology/chronology_merge_log.csv
outputs/v3/g4b_chronology/chronology_manifest.json
```

### Cross-gate lineage layer

```text
src/shockbridge_signal_validity/v3/cross_gate_lineage.py
scripts/verify_v3_cross_gate_lineage.py
```

The lineage layer verifies gate-specific historical protection boundaries and current latest ownership across:

```text
V3_G3_PANIC_REGIME_LOCK.json
V3_G4A_CHRONOLOGY_SIGNAL_USE_CONTRACT_LOCK.json
V3_G4B_CHRONOLOGY_PROVENANCE_LOCK.json
```

### Final lock verification

```text
scripts/verify_v3_g4b_chronology_lock.py
```

This verifier independently binds:

- the authoritative parent lock;
- all 20 protected objects;
- chronology counts and output hashes;
- the current lock blob;
- this checkpoint.

The lineage verifier reads the current V3-4B lock object rather than hard-coding the blob of the lock that protects the verifier. The separate final-lock verifier then binds the lock to the checkpoint. This prevents circular self-reference while preserving tamper detection.

### Validation and execution

```text
tests/test_v3_external_chronology_registry.py
tests/test_v3_cross_gate_lineage.py
RUN_V3_G4B_CHRONOLOGY.ps1
RUN_V3_G4B_CHRONOLOGY.sh
docs/V3_EXTERNAL_CHRONOLOGY_COMPILATION.md
```

Both launchers preserve active interpreter package visibility, run the complete 19-test suite, verify cross-gate lineage, regenerate the chronology package, and execute final-lock verification.

### Consolidated findings

`Findings.md` records only implemented and validated V3-4B methodological, reproducibility, and governance contributions. Model-event alignment, lead-lag evidence, false-alert burden, empirical regime performance, and conditional signal conclusions remain pending.

## Chronology composition

The locked registry contains:

```text
canonical events: 17
provenance sources: 27
confirmed events: 12
boundary-uncertain events: 5
source-conflict events: 0
```

### Event-type composition

```text
CROSS_MARKET_CONTAGION: 6
DOWNSIDE_DISLOCATION: 1
EXCHANGE_OR_VENUE_DISRUPTION: 2
FUNDING_STRESS: 1
LIQUIDATION_CASCADE: 5
MARKET_STRUCTURE_BREAK: 2
```

The chronology spans externally documented:

- downside dislocations;
- forced-liquidation cascades;
- stablecoin and market-structure breaks;
- crypto-credit contagion;
- venue disruption and exceptional withdrawal pressure;
- institutional funding and liquidity interruption;
- global risk-off transmission into crypto markets.

## Primary timing eligibility

The following 12 events are `CONFIRMED` and eligible for the registered V3-4C primary timing metrics:

```text
EVT-2021-05-19
EVT-2021-09-07
EVT-2021-12-04
EVT-2023-03-USDC
EVT-2023-08-17
EVT-2024-03-05
EVT-2024-04-13
EVT-2024-08-05
EVT-2024-12-05
EVT-2025-02-03
EVT-2025-02-21-BYBIT
EVT-2025-10-10
```

The following five events remain in the chronology but are excluded from primary timing because their boundaries are explicitly uncertain:

```text
EVT-2022-05-TERRA
EVT-2022-06-CREDIT
EVT-2022-11-FTX
EVT-2026-02-RISKOFF
EVT-2026-02-BLOCKFILLS
```

They may enter only secondary robustness reporting under the frozen V3-4A contract. Their exclusion from primary timing is protection against false precision, not a judgment that the episodes were unimportant.

## Source and provenance governance

Every documentary source has:

- stable `source_id`;
- source type;
- publisher;
- title;
- HTTPS locator;
- publication timestamp;
- publication-time precision;
- retrieval timestamp.

Every canonical event has:

- one primary source;
- one or more source identifiers in the event-source map;
- a complete merge-log reconstruction;
- explicit event boundary and precision fields;
- documentation and severity status;
- a note preserving material interpretation boundaries.

The allowed source classes remain those frozen by V3-4A:

```text
regulator_or_central_bank
exchange_or_venue_notice
clearing_or_settlement_notice
official_market_operator
peer_reviewed_or_institutional_research
reputable_time_stamped_news_archive
```

## Merge governance

The candidate merge log permits only:

```text
RETAINED_AS_CANONICAL
MERGED_SUPPORTING_SOURCE
```

Every canonical event requires one retained candidate. Supporting sources can strengthen provenance but cannot silently alter the canonical event boundary.

Every merge decision records:

```text
model_outputs_consulted = false
```

No documentary candidate was deleted because it aligned poorly with a model, and no event boundary was tuned against a Gate V3-3 probability or transition.

## Deterministic evidence hashes

```text
chronology_manifest.json
3e968b1432cf9e95dd26984d1dd80297825b3c94e676c70982cb5c68ef357a00

chronology_merge_log.csv
93c64dc662f788eb4634921f6060402e71156ce81fbed033d5f38ba7bd153c44

chronology_provenance.json
c7d23a74ccacae2be7bce5827205ee8285e547bac96553f1e23c144f1056c67f

external_chronology.csv
7eb99d1e1492685bfc8efee04b0cec9dbd776f8f176358f5b6d5d89ba0e53f53
```

Reversing the event, source, source-map, and merge-log input order produces the same byte-identical outputs.

## Validation evidence

The final isolated chronology and cross-gate suite completed with:

```text
19 passed in 0.47s
```

The tests establish that:

1. the complete independent registry validates;
2. the authoritative V3-4A parent lock is required;
3. every tracked output is reproduced exactly;
4. every manifest file hash is correct;
5. every event remains inside the frozen sample;
6. uncertain events are excluded from primary timing;
7. merge decisions never consult model output;
8. model-output access fails closed;
9. a chronology-completeness claim fails closed;
10. parent-lock mutation fails closed;
11. out-of-sample events fail closed;
12. primary-source mismatches fail closed;
13. missing source provenance fails closed;
14. model-informed merge decisions fail closed;
15. shuffled registry input remains deterministic;
16. governed `Findings.md` supersession across V3-3, V3-4A, and V3-4B is accepted;
17. ungoverned latest-owner changes are rejected;
18. parent-lock lineage mismatch is rejected;
19. Windows and POSIX launchers preserve active interpreter package visibility and execute the complete gate path, including final-lock verification.

## Cross-gate ownership resolution

The earlier standalone V3-3 final-lock verifier was designed as a point-in-time current-tree verifier. It therefore reports a mismatch after later gates legitimately update `Findings.md`.

This does not indicate corruption of the V3-3 lock.

The authoritative cross-gate audit verifies simultaneously that:

1. the V3-3 `Findings.md` blob remains exactly preserved at the V3-3 preparation commit;
2. the V3-4A `Findings.md` blob remains exactly preserved at the V3-4A finalization-preparation commit;
3. the V3-4B `Findings.md` blob remains exactly preserved at the V3-4B finalization-preparation commit;
4. V3-4B is the current governed owner;
5. every other protected object remains bound to its latest owning lock;
6. the parent-lock chain and authoritative earlier lock blobs remain unchanged.

The frozen V3-3 and V3-4A locks and their original verifiers were not modified.

## Results

### Result 1 — The chronology is independent of model output

Event inclusion, source inclusion, canonical boundaries, documentation status, severity, and merge decisions were compiled before any Gate V3-3 output was exposed to this gate.

### Result 2 — Boundary uncertainty becomes explicit evidence

The gate does not force complex multi-day collapses, contagion phases, or retrospectively reported interruptions into artificial point timestamps. Uncertain episodes remain auditable and available for secondary robustness while being excluded from the primary timing analysis.

### Result 3 — Provenance is reproducible rather than narrative

A deterministic compiler reconstructs the chronology, source provenance, candidate merge history, and evidence manifest from frozen machine-readable inputs.

### Result 4 — Negative and incomplete documentation remains visible

The registry does not claim completeness, does not delete uncertain events, and does not convert the absence of an event record into a definitive non-event label.

### Result 5 — Historical and current lock ownership are separated

Cross-gate lineage verification prevents a later legitimate cumulative findings update from being misclassified as corruption of an earlier lock, while still rejecting ungoverned current changes.

## Scientific assessment

The scientific value of V3-4B lies in constructing an independent validation layer before seeing regime results.

The chronology can support later tests of temporal correspondence, transition capture, lead time, overlap, decay, rank shifts, and false-alert burden without allowing those results to determine which events are retained.

The design preserves:

1. documentary provenance;
2. publication-time precision;
3. event-boundary uncertainty;
4. candidate merge history;
5. chronology incompleteness;
6. separation from model output;
7. deterministic regeneration;
8. cross-gate lock ownership.

The gate does not establish that V3-3 probabilities correspond to external dislocations. That is the purpose of V3-4C and remains unopened.

## Model-risk assessment

### Incomplete-registry risk

The chronology is not a complete census. A later apparent false alert may correspond to an undocumented dislocation rather than a model error. V3-4C must report false-alert burden with this limitation visible.

### Boundary risk

A multi-day event can have several economically defensible start points. The primary analysis excludes uncertain boundaries rather than selecting a point that improves model alignment.

### Publication-delay risk

Some documentary sources were published after event onset. Publication timestamp and event timestamp remain separate fields.

### Source-dependence risk

Several events use multiple sources. The event-source map and merge log preserve that dependence rather than representing every source as a separate event.

### Taxonomy risk

Event types are documentary classifications. They are not inferred latent states and must not be used as supervised labels to retrain V3-3 models.

### Coverage risk

The registry has stronger coverage for large publicly reported dislocations than for smaller liquidity or funding interruptions. This asymmetry must remain visible in V3-4C interpretation.

### Verification circularity risk

A verifier cannot hard-code the blob of a lock that protects that verifier without creating a circular dependency. V3-4B resolves this through dynamic latest-lock lineage plus an independent checkpoint-bound final-lock verifier.

## Perceived-value and problem-solving opportunities

### Independent model-validation product

The chronology and provenance package can support an audit-ready service evaluating whether a stress model detects independently documented market dislocations without retrospective event selection.

### Event registry product

The source, precision, uncertainty, and merge architecture can become a reusable governed crypto-market dislocation registry rather than a static event list.

### Model-risk dashboard

The later combination of locked chronology, regime probability, transition evidence, cross-model disagreement, and coverage can provide a decision-grade validation dashboard.

### Signal permissioning

Once alignment and conditional diagnostics are complete, the architecture can separate research-only observations from admissible signal use without upgrading RSI or Bollinger from their frozen negative baseline statuses.

### Publication value

The chronology-before-overlay design, explicit uncertainty exclusions, deterministic provenance, and cross-gate ownership logic strengthen the methodological contribution beyond a conventional post hoc event study.

## Scientific and publication boundaries

Gate V3-4B supports the conclusion that an independently sourced, provenance-complete, boundary-aware chronology has been compiled and locked without model-output access.

Gate V3-4B does not support claims about:

- model-event alignment;
- transition capture;
- lead or lag performance;
- false-alert burden;
- model ranking or superiority;
- causal event attribution;
- empirical panic-regime accuracy;
- RSI degradation, recovery, rescue, restriction, or suspension;
- Bollinger degradation, recovery, rescue, restriction, or suspension.

## Next subgate

The next permitted subgate is:

```text
Gate V3-4C — Independent Event-Alignment Evaluation
```

Gate V3-4C may access frozen Gate V3-3 outputs only after this authoritative lock. It must:

- use V3-4B lock blob `04ac09a177d2838e0e950c24f278a8e650d2e94a` as its parent;
- retain all registered models and horizons;
- use all 12 confirmed primary events;
- keep the five uncertain events in secondary robustness only;
- preserve chronology boundaries and sources;
- prohibit chronology-driven threshold selection;
- prohibit model selection or ensemble creation;
- retain negative and insufficient results;
- refrain from conditional RSI or Bollinger diagnostics reserved for V3-4D.

Gate V3-4C has not started and requires separate approval.
