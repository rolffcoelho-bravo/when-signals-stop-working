# Gate V3-4B - Independent Chronology Compilation and Provenance

## Purpose

Gate V3-4B compiles and locks an independently documented chronology of crypto-market dislocations covering the frozen research sample from 1 January 2021, 00:00 UTC through 22 July 2026, 08:00 UTC. The chronology is created without access to Gate V3-3 probabilities, operational states, transitions, contributions, disagreement measures, or diagnostics.

The gate creates validation evidence for the later V3-4C event-alignment evaluation. It does not evaluate alignment itself and does not assert that the chronology is a complete census of panic or stress.

## Parent boundary

The only authorized parent is:

```text
V3_G4A_CHRONOLOGY_SIGNAL_USE_CONTRACT_LOCK.json
d3c4ce27808e60b001e7d58e0c5e36be8d8cac6a
```

Gate V3-4B preserves:

- frozen Version 1 and Version 2 determinations;
- all Gate V3-3 probabilities, thresholds, and protected objects;
- the prohibition on model-derived event inclusion;
- the prohibition on chronology-driven threshold or model selection;
- RSI and Bollinger ineligibility for conditional rescue.

## Reproducible architecture

The source-driven input is:

```text
configs/v3_external_chronology_registry.json
```

The deterministic compiler is:

```text
src/shockbridge_signal_validity/v3/chronology_registry.py
scripts/run_v3_g4b_chronology.py
```

It generates:

```text
outputs/v3/g4b_chronology/external_chronology.csv
outputs/v3/g4b_chronology/chronology_provenance.json
outputs/v3/g4b_chronology/chronology_merge_log.csv
outputs/v3/g4b_chronology/chronology_manifest.json
```

Identical registry input produces byte-identical output files and manifest hashes.

### Checkout line-ending boundary

Git may transform LF text blobs to CRLF working-tree files on Windows when `core.autocrlf` is enabled. That checkout transformation is not a change to the tracked evidence object and must not create a false reproducibility failure.

The tracked-evidence test therefore compares compiler output with the immutable `HEAD:<path>` Git blob obtained through `git show`, rather than comparing with platform-transformed working-tree bytes. Manifest SHA-256 checks remain calculated from the canonical LF compiler output. A genuine tracked-object change still fails because the Git blob changes; a Windows-only checkout transformation does not.

## Chronology composition

The compiled package contains:

```text
canonical events: 17
provenance sources: 27
confirmed events eligible for primary timing metrics: 12
boundary-uncertain events excluded from primary timing metrics: 5
source-conflict events: 0
```

The registry includes externally documented downside dislocations, liquidation cascades, market-structure breaks, crypto-credit contagion, exchange or venue disruptions, funding stress, and cross-market contagion.

The event set is deliberately incomplete. It is a governed documentary registry, not a claim that every stress episode has been observed.

## Source governance

Permitted evidence comes only from the V3-4A source classes:

- regulators and central banks;
- exchange or venue notices;
- clearing or settlement notices;
- official market operators;
- peer-reviewed or institutional research;
- reputable time-stamped news archives.

Every source has:

- a stable source identifier;
- source type and publisher;
- title and HTTPS locator;
- publication timestamp and precision;
- retrieval timestamp;
- one or more mapped canonical events.

Every canonical event has a primary source. Supporting sources are retained through the provenance map and merge log.

## Boundary governance

A `CONFIRMED` event can enter the V3-4C primary timing metrics.

A `BOUNDARY_UNCERTAIN` or `SOURCE_CONFLICT` event remains in the chronology but is excluded from primary timing metrics. It can appear in secondary robustness reporting only under the frozen V3-4A contract.

Uncertain multi-day cases include extended collapse or contagion phases where a single exact onset would create false precision. The February 2026 institutional-liquidity interruption is also boundary-uncertain because the pause start was reported retrospectively.

## Duplicate and merge governance

The merge log records every documentary candidate and one of two actions:

```text
RETAINED_AS_CANONICAL
MERGED_SUPPORTING_SOURCE
```

Every canonical event must have one retained candidate. Supporting documentary records can be merged only as provenance; they cannot change the canonical boundary after model access. Every merge row records:

```text
model_outputs_consulted = false
```

## Cross-gate ownership

The earlier standalone V3-3 verifier compares all V3-3 protected files with the current tree. That point-in-time rule is expected to fail after V3-4A legitimately becomes the latest owner of `Findings.md`.

Gate V3-4B therefore adds:

```text
src/shockbridge_signal_validity/v3/cross_gate_lineage.py
scripts/verify_v3_cross_gate_lineage.py
```

The cross-gate audit separately verifies:

1. every V3-3 protected object at the V3-3 lock-preparation commit;
2. every V3-4A protected object at the V3-4A finalization-preparation commit;
3. exact authoritative lock blobs and the parent-lock chain;
4. every current object against its latest owning lock;
5. governed supersession of `Findings.md` from V3-3 to V3-4A and then V3-4B.

The frozen V3-3 lock and verifier are not rewritten. The cross-gate audit resolves historical and latest ownership, while `scripts/verify_v3_g4b_chronology_lock.py` separately binds the current V3-4B lock to its checkpoint and protected objects. This avoids a circular self-reference in which a verifier hard-codes the blob of the lock that protects the verifier.

## Validation suite

The isolated Gate V3-4B suite contains 19 tests covering:

- complete package validation;
- authoritative V3-4A parent binding;
- exact regeneration of all tracked Git evidence objects independent of checkout line-ending conversion;
- manifest hash verification;
- frozen sample boundaries;
- exclusion of uncertain events from primary timing metrics;
- zero model-output consultation in merge decisions;
- failure on model-output access or chronology-completeness claims;
- failure on parent-lock mutation;
- failure on out-of-sample events;
- failure on source mismatch or missing provenance;
- failure on merge decisions using model output;
- deterministic ordering under shuffled inputs;
- governed cross-gate `Findings.md` supersession;
- rejection of ungoverned latest-owner changes;
- rejection of parent-lock mismatch;
- Windows and POSIX user-site launcher compatibility.

## Scientific boundary

Gate V3-4B supports only the following conclusion:

> An independently sourced, provenance-complete, boundary-aware chronology has been compiled and locked without model-output access.

It does not support conclusions about:

- model-event alignment;
- lead or lag performance;
- false-alert burden;
- model superiority;
- causal attribution;
- empirical regime probabilities;
- RSI or Bollinger conditional validity.

Those remain unavailable until later gates.

## Next gate

Gate V3-4C may access the locked Gate V3-3 outputs only after the V3-4B chronology and provenance lock is complete. V3-4C must use all registered models, horizons, confirmed events, and negative results without chronology-driven retuning or event deletion.
