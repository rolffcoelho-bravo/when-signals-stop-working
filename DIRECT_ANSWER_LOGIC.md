# Direct-Answer Logic

## Purpose

This document prevents methodological sophistication from displacing the repository's practical question. Every research layer must terminate in an explicit answer about signal establishment, conditional validity, deterioration, failure risk, or permitted use.

## Decision hierarchy

### Stage 0 — Data and contract eligibility

A signal claim is unavailable when the declared data, timestamps, target, benchmark, costs, or chronological split fail their registered contract.

Possible result:

```text
INELIGIBLE_DATA_OR_CONTRACT
```

### Stage 1 — Signal establishment

Compare a matched pair:

```text
benchmark = common non-signal information
candidate = identical information + registered signal information
```

The signal can be established only when all applicable predictive, economic, chronological, calibration, coverage, concentration, and data-quality gates pass.

Possible results:

```text
ESTABLISHED
NOT_ESTABLISHED
NO_PIPELINE_ADMITTED
NO_INCREMENTAL_EVIDENCE
```

### Stage 2 — Conditional validity

Conditional claims are admissible only for a pipeline that passed Stage 1 under a frozen unconditional contract.

Possible results:

```text
UNCONDITIONALLY_VALID
CONDITIONALLY_VALID
CONDITIONAL_VALUE_NOT_ESTABLISHED
```

Regime conditioning cannot rescue a rejected or non-established signal.

### Stage 3 — Deterioration

Deterioration requires historical establishment plus prospectively registered evidence that recent benchmark-relative predictive, economic, calibration, coverage, stability, or data-quality performance has weakened for the required persistence period.

Possible results:

```text
ACTIVE
DEGRADING
REDUCED
REVALIDATION_REQUIRED
```

### Stage 4 — Failure probability

A future failure probability may be estimated only when:

1. an established signal pipeline exists;
2. failure is prospectively and deterministically defined;
3. sufficient failure and non-failure histories exist;
4. the failure model is calibrated chronologically;
5. warning lead time and false-alert burden are reported.

Possible outputs:

```text
p_failure_24h
p_failure_72h
p_failure_7d
p_failure_30d
```

When no established pipeline exists, the correct result is:

```text
FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED
```

### Stage 5 — Governed action

Permitted actions must follow the evidence state and fail closed:

```text
USE_WITHIN_REGISTERED_BOUNDARIES
USE_ONLY_IN_APPROVED_REGIMES
REDUCE_RELIANCE
SUSPEND_NEW_DECISIONS
REVALIDATE_BEFORE_REUSE
DO_NOT_USE
```

A favourable market forecast cannot override failed signal-establishment or failure-risk governance.

## Frozen current answer

### RSI

```text
Version 1: NOT_ESTABLISHED
Version 2: NO_PIPELINE_ADMITTED
Deterioration claim: INADMISSIBLE
Failure-probability model: INADMISSIBLE_BASELINE_NOT_ESTABLISHED
```

### Bollinger Bands

```text
Version 1: NOT_ESTABLISHED
Version 2: NO_INCREMENTAL_EVIDENCE
Deterioration claim: INADMISSIBLE
Failure-probability model: INADMISSIBLE_BASELINE_NOT_ESTABLISHED
```

## Role of Version 3 supporting layers

| Supporting layer | Permitted contribution | Prohibited substitution |
|---|---|---|
| Spectral/eigenvalue engine | Describe dependence concentration and market-mode structure | Cannot establish RSI or Bollinger value |
| Network/MST engine | Describe topology, integration, and fragmentation | Cannot declare signal failure |
| Panic-consistent engine | Estimate model-conditional stress-regime probabilities | Cannot rescue a rejected signal |
| External chronology | Validate temporal correspondence of regime outputs | Cannot become a complete failure label by assumption |
| Lock and lineage controls | Protect evidence and historical decisions | Cannot be presented as empirical signal evidence |

## Publication language boundary

Permitted:

> Stable incremental value was not established under the registered design.

Permitted after a future complete Version 3 pass:

> The signal was established within registered boundaries and later breached its prospectively defined operational standard.

Prohibited without establishment:

> The signal stopped working.

Prohibited without calibrated prospective evidence:

> The signal will fail on a specific date.
