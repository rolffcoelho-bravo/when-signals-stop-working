# When Signals Stop Working

## Technical Signal Validity, Regime Dependence, and Structural Deterioration Framework

[![CI](https://github.com/rolffcoelho-bravo/when-signals-stop-working/actions/workflows/ci.yml/badge.svg)](https://github.com/rolffcoelho-bravo/when-signals-stop-working/actions/workflows/ci.yml)

## Executive overview

This repository provides a governed, fully reproducible framework for determining whether technical indicators contribute incremental predictive and economic information beyond a transparent market-state benchmark.

The Version 1 assessment evaluates Relative Strength Index and Bollinger Band information on four-hour SOL/USDT data, with BTC/USDT included as broader market context. The framework separates descriptive indicator behaviour from benchmark-relative forecasting value, regime dependence, and structural deterioration.

The central governance principle is explicit:

> A signal cannot be classified as deteriorated or suspended unless stable out-of-sample value was first established under a predeclared validation contract.

Where that establishment requirement is not met, the appropriate status is `NOT_ESTABLISHED`.

## Published Version 1 determination

The frozen Version 1 sample contains 12,171 aligned Binance spot observations from **1 January 2021, 00:00 UTC** through **22 July 2026, 08:00 UTC**.

| Candidate model | Chronological folds with positive predictive contribution | Version 1 status |
|---|---:|---|
| RSI | 1 of 5 | `NOT_ESTABLISHED` |
| Bollinger Bands | 1 of 5 | `NOT_ESTABLISHED` |
| Combined specification | 2 of 5 | `NOT_ESTABLISHED` |

Under the frozen specification, none of the candidate models demonstrated sufficiently stable incremental value to pass the establishment gate. This determination does not imply that all historical indicator events were incorrect. It means that the incremental forecasting claim did not survive the declared benchmark-relative and chronological validation requirements.

The complete determination is documented in [`RESULTS.md`](RESULTS.md) and the generated [`outputs/research_report.md`](outputs/research_report.md).


## Version 2 primary-case determination

Version 2 tested whether broader horizons, continuation-versus-contrarian
interpretations, nonlinear models, estimation windows, filtered state
conditioning, calibration, and selective abstention could establish stable
incremental value under a frozen nested-validation and methodology-locked
evaluation design.

| Confirmatory family | Development decision | Locked-evaluation decision | Final Version 2 status |
|---|---|---|---|
| RSI | `NO_PIPELINE_ADMITTED` | Not evaluated | `NO_PIPELINE_ADMITTED` |
| Bollinger Bands | One pipeline admitted and frozen | Predictive and economic gates failed | `NO_INCREMENTAL_EVIDENCE` |

For the frozen Bollinger pipeline, the mean benchmark-relative log-loss
contribution was positive (`0.002108928`) and two of three locked subperiods
were positive. The raw one-sided p-value was `0.032339`, but the
Holm-adjusted p-value was `0.064677`; dependence-aware predictive and economic
lower confidence bounds also crossed zero. Stable incremental value was
therefore not established.

The complete Version 2 determination is documented in
[`outputs/v2/publication/V2_FINAL_EVIDENCE_REPORT.md`](outputs/v2/publication/V2_FINAL_EVIDENCE_REPORT.md).
The frozen pipeline boundaries are documented in
[`outputs/v2/publication/V2_FROZEN_BOLLINGER_MODEL_CARD.md`](outputs/v2/publication/V2_FROZEN_BOLLINGER_MODEL_CARD.md).

> Favourable average contributions are not sufficient for establishment when
> multiplicity-adjusted, dependence-aware, chronological, and economic
> confidence requirements are not satisfied.


## Version 2 governed development

Version 2 was developed on `research/v2-conditional-signal-validity` from the frozen `v1.2.0` release. The primary-case design, development admission, single-access locked evaluation, confirmatory inference, and robustness publication layer are now complete on the research branch. Version 1 remains unchanged.

The Version 2 design predeclares:

- separate confirmatory RSI and Bollinger directional hypotheses;
- 4-, 8-, 12-, and 24-hour horizons selected only through nested development validation;
- expected-return and large-move targets as secondary analyses;
- contrarian, continuation, and soft regime-conditioned signal interpretations;
- matched benchmark and candidate model classes;
- expanding, one-year rolling, and two-year rolling estimation windows;
- a methodology-locked evaluation segment;
- Holm family-wise control for the two confirmatory hypotheses;
- explicit predictive, economic, robustness, and external-replication gates.

The frozen design is documented in [`V2_DESIGN_FREEZE.md`](V2_DESIGN_FREEZE.md). The machine-readable experiment space is defined in [`configs/v2_experiment_registry.json`](configs/v2_experiment_registry.json) and protected by [`V2_PROTOCOL_LOCK.json`](V2_PROTOCOL_LOCK.json).

## Institutional relevance

The repository is designed for quantitative research, model validation, investment research governance, and reproducible methodological review. It demonstrates:

- predeclared research assumptions;
- common-benchmark model comparison;
- chronological out-of-sample validation;
- explicit separation of predictive and economic evidence;
- regime-conditioned analysis;
- sequential deterioration monitoring;
- reproducible data, features, folds, predictions, figures, and manifests;
- disciplined publication of negative findings.

## Frozen Version 1 specification

| Component | Specification |
|---|---|
| Research asset | SOL/USDT spot |
| Market context | BTC/USDT spot |
| Data venue | Binance |
| Frequency | Four-hour observations |
| Forecast horizon | Next four-hour return |
| RSI specification | 14 periods; 30/70 threshold events |
| Bollinger specification | 20 periods; 2 standard deviations |
| Validation design | Five expanding chronological folds with a forecast-horizon gap |
| Economic cost assumption | 10 basis points per one-way position change |
| Market-state layer | Filtered range, trend, and stress probabilities |
| Deterioration monitor | Robust one-sided CUSUM |

These settings are fixed research assumptions. They are not presented as optimal trading parameters.

## Evidence architecture

```text
Indicator event description
        ↓
Common non-indicator benchmark
        ↓
Chronological out-of-sample comparison
        ↓
Predictive and economic evidence
        ↓
Filtered market-state assessment
        ↓
Sequential deterioration monitoring
        ↓
NOT_ESTABLISHED / ACTIVE / REDUCED / SUSPENDED
```

## Reproducibility package

The public repository contains the complete evidence chain required to reproduce Version 1:

```text
data/raw/                 frozen OHLCV snapshot, provenance, and validation
data/processed/           aligned data, features, fold boundaries, assignments
outputs/                  report, verdicts, predictions, summaries, SVG figures
environment/              sanitized package-version record
REPLICATION_MANIFEST.json public evidence map and snapshot definition
REPLICATION_CHECKSUMS.sha256 file-integrity record
PUBLIC_RELEASE_AUDIT.json sensitive-information audit
```

No private account data, credentials, or authenticated trading interfaces are required.

## Execution

### Windows

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\RUN_REPLICATION.ps1
```

### macOS or Linux

```bash
chmod +x RUN_REPLICATION.sh
./RUN_REPLICATION.sh
```

The replication process validates the tracked data snapshot, executes the implementation tests, regenerates the analytical outputs and vector figures, rebuilds the replication assets, audits the public tree, and verifies the published checksums.

For a governed replication followed by Git commit and push, use `PUBLISH_PUBLIC_REPLICATION.ps1`.

## Status governance

- `NOT_ESTABLISHED` - stable incremental value was not demonstrated under the declared validation contract.
- `ACTIVE` - established value remains positive under the current evidence and monitoring rules.
- `REDUCED` - historical value exists, but current evidence is uncertain, regime-concentrated, or deteriorating.
- `SUSPENDED` - previously established value has crossed both the structural-deterioration and recent-performance gates.

The complete status logic is documented in [`docs/STATUS_GOVERNANCE.md`](docs/STATUS_GOVERNANCE.md).

## Methodological development programme

Version 1 is intentionally parsimonious. Later phases increase complexity only where it improves out-of-sample evidence, uncertainty quantification, or operational control.

The approved programme covers:

1. conditional validity across horizons, targets, regimes, and signal interpretations;
2. dynamic coefficients and fully estimated latent-state models;
3. online failure probabilities and Bayesian changepoint inference;
4. cross-market transmission, liquidity, and production-governance layers.

See [`ROADMAP.md`](ROADMAP.md).

## Documentation

- Empirical determination: [`RESULTS.md`](RESULTS.md)
- Research scope: [`RESEARCH_SCOPE.md`](RESEARCH_SCOPE.md)
- Replication guide: [`START_HERE.md`](START_HERE.md)
- Model contract: [`docs/MODEL_CONTRACT.md`](docs/MODEL_CONTRACT.md)
- Research protocol: [`docs/RESEARCH_PROTOCOL.md`](docs/RESEARCH_PROTOCOL.md)
- Status governance: [`docs/STATUS_GOVERNANCE.md`](docs/STATUS_GOVERNANCE.md)
- Replication package: [`docs/REPLICATION_PACKAGE.md`](docs/REPLICATION_PACKAGE.md)
- Public release policy: [`docs/PUBLIC_RELEASE_POLICY.md`](docs/PUBLIC_RELEASE_POLICY.md)
- Figure catalogue: [`docs/FIGURE_CATALOG.md`](docs/FIGURE_CATALOG.md)
- References: [`docs/REFERENCES.md`](docs/REFERENCES.md)
- Citation metadata: [`CITATION.cff`](CITATION.cff)
- Version 2 design freeze: [`V2_DESIGN_FREEZE.md`](V2_DESIGN_FREEZE.md)
- Version 2 research protocol: [`docs/V2_RESEARCH_PROTOCOL.md`](docs/V2_RESEARCH_PROTOCOL.md)
- Version 2 validation gates: [`docs/V2_VALIDATION_GATES.md`](docs/V2_VALIDATION_GATES.md)

## Scope boundaries

The findings are specific to the declared venue, instruments, frequency, sample, target, benchmark, validation design, and cost assumption. Version 1 does not include funding rates, open interest, liquidations, order-book depth, venue-specific slippage, market capacity, taxation, or live execution.

The repository provides reproducible research evidence. It does not constitute investment advice, a trading recommendation, or a claim of universal indicator validity.

## License and data notice

ShockBridge-authored code and documentation are licensed under the MIT License. Third-party market data are included exclusively to support transparent replication and remain subject to the source venue's applicable terms and availability.

## Citation

Pereira, Rodolfo. (2026). *When Signals Stop Working: Technical Signal Validity Framework*. ShockBridge Pulse Research. Python research software. https://github.com/rolffcoelho-bravo/when-signals-stop-working

## BibTeX

```bibtex
@software{pereira2026whensignalsstopworking,
  author = {Pereira, Rodolfo},
  title = {When Signals Stop Working: Technical Signal Validity Framework},
  year = {2026},
  publisher = {ShockBridge Pulse Research},
  type = {Python research software},
  url = {https://github.com/rolffcoelho-bravo/when-signals-stop-working}
}
```

## Version 2 checkpoint D2B

The active research branch now includes full development-only nested selection across the frozen model families, hyperparameters, estimation windows, soft state conditioning, confirmatory calibration methods, and abstention thresholds. D2B uses only D2A-selected signal specifications, evaluates each selected pipeline once on its untouched outer development fold, and does not access or freeze the methodology-locked evaluation pipeline.

## Version 2 checkpoint D2C

The active research branch now includes development admission and family-level pipeline freezing. D2C applies the frozen predictive-stability, calibration, coverage, and fold-concentration controls to RSI and Bollinger horizons, records an explicit admission or rejection for each family, and assigns a canonical hash to every admitted pipeline. The final economic gate and methodology-locked evaluation remain unopened.

## Version 2 checkpoint D3

D3 authorizes a single methodology-locked evaluation for the sole D2C-admitted Bollinger pipeline. The authorization record is committed before result access, RSI remains excluded, and the frozen pipeline cannot be retuned after the locked evidence is exposed. D3 records raw prediction-level evidence for subsequent inference.

## Version 2 checkpoint D4

D4 applies the frozen confirmatory family, one-sided benchmark-relative loss comparison, Holm control, dependence-aware bootstrap intervals, locked-subperiod consistency checks, calibration controls, and matched economic evidence. It records the final predictive and economic determinations without altering the D3 pipeline or predictions. The complete parameter-neighbourhood and estimation-window robustness gate remains separate.

## Version 2 checkpoint D5

D5 completes concentration, leave-one-month-out, influence, state,
active-confidence, and development-component diagnostics; produces the final
model card and publication figures; and freezes the primary-case evidence grade
at `NO_INCREMENTAL_EVIDENCE`. D5 does not execute alternative pipelines on the
locked period and cannot upgrade or reverse the D4 verdict.

## Version 2.1 panic-state diagnostic

A separate V2.1 extension is approved to build and validate a mechanism for
determining when technical-signal interpretation, reliability, and permitted
use should change under panic-consistent, liquidity-stress, or liquidation
regimes. It is not an indicator-rescue exercise. It cannot alter the RSI
rejection, the frozen Bollinger pipeline, D3 evidence, or the Version 2
confirmatory verdict.
