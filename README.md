# When Signals Stop Working

## Technical Signal Validity, Conditional Reliability, and Failure-Risk Framework

[![CI](https://github.com/rolffcoelho-bravo/when-signals-stop-working/actions/workflows/ci.yml/badge.svg)](https://github.com/rolffcoelho-bravo/when-signals-stop-working/actions/workflows/ci.yml)

## The question this repository must answer

Richard asked:

> When will RSI stop working?

He later clarified that the indicator used in practice was Bollinger Bands. The repository therefore evaluates RSI and Bollinger Bands separately and follows one non-negotiable rule:

> A signal cannot be classified as deteriorated, failed, reduced, or suspended unless stable incremental value was first established under a predeclared benchmark-relative and chronological validation contract.

The complete research anchor is documented in [`RICHARD_QUESTION.md`](RICHARD_QUESTION.md). The decision sequence is documented in [`DIRECT_ANSWER_LOGIC.md`](DIRECT_ANSWER_LOGIC.md).

## Direct answer from the frozen evidence

### Version 1

The frozen Version 1 sample contains 12,171 aligned Binance spot observations from **1 January 2021, 00:00 UTC** through **22 July 2026, 08:00 UTC**.

| Candidate model | Chronological folds with positive predictive contribution | Frozen status |
|---|---:|---|
| RSI | 1 of 5 | `NOT_ESTABLISHED` |
| Bollinger Bands | 1 of 5 | `NOT_ESTABLISHED` |
| Combined specification | 2 of 5 | `NOT_ESTABLISHED` |

### Version 2

Version 2 tested broader horizons, continuation and mean-reversion interpretations, restrained nonlinear candidates, estimation windows, filtered-state conditioning, probability calibration, and selective abstention under nested chronological development and one methodology-locked evaluation.

| Confirmatory family | Development decision | Locked-evaluation decision | Frozen status |
|---|---|---|---|
| RSI | `NO_PIPELINE_ADMITTED` | Not evaluated | `NO_PIPELINE_ADMITTED` |
| Bollinger Bands | One continuation pipeline admitted | Complete predictive and economic gates failed | `NO_INCREMENTAL_EVIDENCE` |

The frozen Bollinger pipeline produced a positive mean benchmark-relative log-loss contribution of `0.002108928`, and two of three locked subperiods were positive. The raw one-sided p-value was `0.032339`, but the Holm-adjusted value was `0.064677`; dependence-aware predictive and economic lower confidence bounds crossed zero.

### Current answer to Richard

> Under the tested SOL/USDT four-hour contracts, neither RSI nor Bollinger Bands can be said to have stopped working because stable incremental value was not established first. RSI failed Version 2 development admission. Bollinger Bands showed suggestive average evidence but failed the complete multiplicity-adjusted, dependence-aware, chronological, and economic establishment standard.

This is specific to the declared venue, asset, frequency, sample, target, benchmark, cost policy, and validation design. It is not a universal claim that technical indicators can never contain information.

The complete Version 2 evidence is in [`outputs/v2/publication/V2_FINAL_EVIDENCE_REPORT.md`](outputs/v2/publication/V2_FINAL_EVIDENCE_REPORT.md).

## Evidence hierarchy

```text
Indicator description
        ↓
Matched non-signal benchmark
        ↓
Chronological out-of-sample comparison
        ↓
Predictive and economic establishment
        ↓
Conditional validity
        ↓
Prospective deterioration definition
        ↓
Failure probability
        ↓
Governed permitted action
```

Spectral, network, panic-consistent, liquidity, funding, volatility, downside, and external-event layers provide market context. They cannot substitute for signal establishment.

## Version 3 repository realignment

A full branch review found that Version 3 correctly completed the canonical data, spectral, network, and panic-consistent regime layers, but the implementation sequence diverged after V3-3.

The frozen plan defined V3-4 as the **Unified RSI and Bollinger Interpretation Engine**. Historical development instead used the V3-4A and V3-4B labels for external chronology work and proposed V3-4C for event alignment.

The chronology work is preserved but reclassified as a separate regime-validation extension:

| Historical identifier | Realigned identifier | Scientific role | Current status |
|---|---|---|---|
| V3-4A | V3-RV1 | Independent regime-validation contract | Complete and historically locked |
| V3-4B | V3-RV2 | Independent chronology and provenance | Complete and historically locked; portability revision open |
| Proposed V3-4C | V3-RV3 | Regime-event alignment | Paused and not started |

Historical files and lock objects are not renamed or rewritten.

The controlling correction is recorded in [`V3_REALIGNMENT_DECISION.md`](V3_REALIGNMENT_DECISION.md), with the current gate map in [`docs/V3_REALIGNED_GATE_MAP.md`](docs/V3_REALIGNED_GATE_MAP.md).

## Current Version 3 status

| Core gate | Purpose | Status |
|---|---|---|
| V3-0 | Design and product freeze | Complete |
| V3-1 | Canonical data and adapter layer | Complete |
| V3-2 | Causal feature and spectral engine | Complete |
| V3-2B | Network and market-structure extension | Complete |
| V3-3 | Panic-consistent probabilistic regime engine | Complete |
| **V3-4** | **Unified RSI and Bollinger interpretation engine** | **Approved and reopened; implementation not started** |
| V3-5 | Matched benchmark-versus-signal forecast selection | Not started |
| V3-6 | Prospective failure-event definition | Not started |
| V3-7 | Signal-validity and failure-probability model | Not started |
| V3-8 | Economic and operational decision engine | Not started |
| V3-9 | Methodology-locked evaluation | Not started |
| V3-10 | External replication and transportability | Not started |
| V3-11 | Reusable package and scoring workflow | Not started |
| V3-12 | Final audit and institutional release | Not started |

The true V3-4 scope is frozen in [`docs/V3_G4_SIGNAL_ENGINE_SCOPE.md`](docs/V3_G4_SIGNAL_ENGINE_SCOPE.md).

## What the completed V3 infrastructure contributes

### Canonical data and adapters

Source-specific layouts are mapped into one deterministic schema. Model modules consume canonical fields rather than venue-specific names or paths.

### Spectral and eigenvalue structure

The causal fixed-panel engine reports:

- dominant eigenvalue and dominant-eigenvalue share;
- normalized eigenvalue gap;
- participation ratio and effective dimension;
- spectral entropy;
- first-eigenvector concentration and stability;
- average correlation and dispersion;
- full eigenvalue spectrum.

These measures describe whether market dependence is concentrating into a common mode. They do not establish RSI or Bollinger value by themselves.

### Network and market structure

The extension adds threshold networks, deterministic communities, minimum spanning trees, centrality concentration, path descriptors, and causal dynamics.

### Panic-consistent regime probabilities

The regime engine reports three registered models without automatic selection, ensemble, or consensus probability:

```text
V2_TRANSPARENT_STATE_CHALLENGER_V1
MONOTONE_MECHANISM_SCORE_V1
CAUSAL_GAUSSIAN_HMM_V1
```

These outputs may become candidate context variables in later signal evaluation. They cannot rescue the frozen Version 2 verdicts.

## Stop rule for the failure programme

Version 3 must first establish at least one RSI or Bollinger pipeline under the complete matched predictive and economic standard.

When no signal pipeline passes establishment, the scientifically correct output is:

```text
FAILURE_MODEL_INADMISSIBLE_BASELINE_NOT_ESTABLISHED
```

The regime engine may still support a separate market-structure paper or product, but it cannot be presented as evidence that a non-established signal stopped working.

## Reproducibility

The public repository preserves the frozen Version 1 and Version 2 evidence chain:

```text
data/raw/                 frozen OHLCV snapshot and provenance
data/processed/           aligned data, features, and fold boundaries
outputs/                  verdicts, predictions, reports, and figures
environment/              sanitized package-version record
REPLICATION_MANIFEST.json public evidence map
REPLICATION_CHECKSUMS.sha256 integrity record
PUBLIC_RELEASE_AUDIT.json public-tree audit
```

### Version 1/2 replication on Windows

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\RUN_REPLICATION.ps1
```

### Version 3 realignment verification on Windows

```powershell
.\RUN_V3_REALIGNMENT.ps1
```

The realignment runner temporarily restores Python user-site visibility for the process, executes the realignment contract tests, and verifies the corrected gate sequence.

## Status governance

- `NOT_ESTABLISHED` — stable incremental value was not demonstrated.
- `ACTIVE` — established value remains positive within registered boundaries.
- `CONDITIONALLY_VALID` — established value is authorized only under approved conditions.
- `DEGRADING` or `REDUCED` — historical establishment exists, but current evidence has weakened.
- `SUSPENDED` — a previously established signal crossed prospectively defined failure boundaries.
- `REVALIDATION_REQUIRED` — use cannot resume without a governed new validation.
- `INVALID` — the required evidence standard is not met.

## Key documentation

- Richard question: [`RICHARD_QUESTION.md`](RICHARD_QUESTION.md)
- Direct-answer logic: [`DIRECT_ANSWER_LOGIC.md`](DIRECT_ANSWER_LOGIC.md)
- Empirical determination: [`RESULTS.md`](RESULTS.md)
- Version 2 evidence report: [`outputs/v2/publication/V2_FINAL_EVIDENCE_REPORT.md`](outputs/v2/publication/V2_FINAL_EVIDENCE_REPORT.md)
- Version 3 design freeze: [`V3_DESIGN_FREEZE.md`](V3_DESIGN_FREEZE.md)
- Original Version 3 implementation plan: [`docs/V3_IMPLEMENTATION_PLAN.md`](docs/V3_IMPLEMENTATION_PLAN.md)
- Version 3 realignment decision: [`V3_REALIGNMENT_DECISION.md`](V3_REALIGNMENT_DECISION.md)
- Realigned gate map: [`docs/V3_REALIGNED_GATE_MAP.md`](docs/V3_REALIGNED_GATE_MAP.md)
- True V3-4 scope: [`docs/V3_G4_SIGNAL_ENGINE_SCOPE.md`](docs/V3_G4_SIGNAL_ENGINE_SCOPE.md)
- Current roadmap: [`ROADMAP.md`](ROADMAP.md)
- Status governance: [`docs/STATUS_GOVERNANCE.md`](docs/STATUS_GOVERNANCE.md)
- References: [`docs/REFERENCES.md`](docs/REFERENCES.md)

## Scope boundaries

The findings are specific to the declared instruments, venue, frequency, sample, target, benchmark, validation design, and cost assumptions. The repository provides reproducible research evidence; it does not constitute investment advice, a trading recommendation, or a guarantee of future performance.

## Citation

Pereira, Rodolfo. (2026). *When Signals Stop Working: Technical Signal Validity Framework*. ShockBridge Pulse Research. Python research software.
