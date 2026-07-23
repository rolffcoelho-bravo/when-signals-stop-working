# Version 2 Implementation Architecture

## Institutional purpose

This document defines the first implementation checkpoint after the Version 2 methodological design freeze. The checkpoint establishes governed software boundaries without fitting candidate models and without accessing locked-evaluation performance.

## Control objective

The implementation scaffold must prove that the repository can:

1. load and validate the frozen experiment registry;
2. separate development observations from the methodology-locked evaluation segment;
3. construct horizon-specific targets without crossing the partition boundary;
4. generate purged outer and inner chronological fold plans;
5. enumerate the complete confirmatory candidate space;
6. create repository-relative manifests and deterministic identifiers;
7. reject unauthorized holdout outputs;
8. preserve all Version 1 evidence and all locked Version 2 protocol files.

## Namespace

The scaffold introduces the package:

```text
src/shockbridge_signal_validity/v2/
```

The namespace is intentionally separate from Version 1 execution modules. The initial modules are:

| Module | Responsibility |
|---|---|
| `registry.py` | Frozen registry loading and validation |
| `partitions.py` | Development partition and holdout guard |
| `targets.py` | Horizon-specific causal targets |
| `splits.py` | Purged expanding outer and inner folds |
| `signals.py` | Registered RSI and Bollinger feature contracts |
| `inventory.py` | Confirmatory candidate and decision-policy inventories |
| `manifests.py` | Relative-path hashes and public manifests |
| `contracts.py` | Exceptions and immutable governance records |

## Development-only outputs

The scaffold may create only:

```text
data/processed/v2/development/
outputs/v2/development/
```

No file may be created under:

```text
outputs/v2/holdout/
```

before the pre-holdout approval checkpoint described in `docs/V2_HOLDOUT_GOVERNANCE.md`.

## Target-boundary control

A development forecast origin is eligible only when the realized target timestamp is no later than `2025-06-30T20:00:00Z`. The final `h` development origins are therefore unavailable for a horizon of `h` candles. This prevents a development label from using any return realized inside the locked segment.

## Fold architecture

For every horizon:

- five expanding outer folds are created;
- three expanding inner folds are created inside each outer training partition;
- the purge gap equals the horizon in candles;
- no random shuffle is permitted;
- timestamps and row counts are recorded in `nested_fold_plan.csv`.

## Candidate inventory

The confirmatory inventory includes only standalone RSI and Bollinger families. Each row identifies:

- horizon;
- signal parameters;
- interpretation;
- matched model family;
- estimation-window scheme;
- calibration method.

Model hyperparameters remain inner-fold choices within the bounded grids in the frozen registry. Abstention thresholds are recorded separately as decision policies so they do not obscure the predictive model identity.

## Explicit non-deliverables

This checkpoint does not:

- fit a Version 2 benchmark or candidate model;
- rank candidates;
- select a horizon;
- estimate a large-move threshold outside a training fold;
- inspect holdout predictive or economic performance;
- amend the frozen design;
- change a Version 1 result.
