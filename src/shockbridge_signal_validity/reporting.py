from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import pandas as pd
import sklearn

from .visualization import DISPLAY, generate_figure_suite


REFERENCES = [
    "Wilder, J. W. (1978). New Concepts in Technical Trading Systems.",
    "Bollinger, J. Official Bollinger Bands explanation and rules.",
    "Hamilton, J. D. (1989). A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle.",
    "Page, E. S. (1954). Continuous Inspection Schemes.",
    "Diebold, F. X., & Mariano, R. S. (1995). Comparing Predictive Accuracy.",
    "Hansen, P. R. (2005). A Test for Superior Predictive Ability.",
    "scikit-learn TimeSeriesSplit, LogisticRegression, and calibration documentation.",
    "CCXT unified public OHLCV API manual.",
]


def _institutional_determination(signal: str, result: dict) -> str:
    label = DISPLAY[signal]
    status = result["status"]
    if status == "NOT_ESTABLISHED":
        return (
            f"Under the frozen Version 1 specification, {label} did not "
            "demonstrate stable incremental predictive and economic "
            "contribution over the common non-indicator benchmark. The "
            "appropriate operational status is NOT_ESTABLISHED."
        )
    if status == "ACTIVE":
        return (
            f"{label} satisfied the historical establishment requirement and "
            "remains ACTIVE under the current market-state and monitoring "
            "evidence."
        )
    if status == "REDUCED":
        return (
            f"{label} satisfied the historical establishment requirement, but "
            "current evidence is uncertain, regime-dependent, or deteriorating. "
            "The appropriate operational status is REDUCED."
        )
    return (
        f"{label} previously satisfied the historical establishment requirement. "
        "The structural-deterioration and recent-performance gates support a "
        "SUSPENDED operational status."
    )


def save_outputs(
    output_directory: Path,
    data: pd.DataFrame,
    stage_one: pd.DataFrame,
    folds: pd.DataFrame,
    predictions: pd.DataFrame,
    regimes: pd.DataFrame,
    verdicts: dict[str, dict],
    primary_signal: str,
    config: object,
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    figure_directory = output_directory / "figures"

    stage_one.to_csv(output_directory / "stage_1_event_study.csv", index=False)
    folds.to_csv(output_directory / "stage_2_fold_results.csv", index=False)
    predictions.to_csv(output_directory / "stage_2_oos_predictions.csv")
    regimes.to_csv(output_directory / "stage_3_regime_summary.csv", index=False)

    with (output_directory / "final_verdicts.json").open("w", encoding="utf-8") as handle:
        json.dump(verdicts, handle, indent=2)

    figure_paths = generate_figure_suite(
        directory=figure_directory,
        data=data,
        folds=folds,
        predictions=predictions,
        regimes=regimes,
        verdicts=verdicts,
        primary_signal=primary_signal,
    )

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sample_start": str(data.index.min()),
        "sample_end": str(data.index.max()),
        "usable_observations": int(len(data)),
        "out_of_sample_observations_per_signal": {
            signal: int(len(predictions.loc[predictions["signal"].eq(signal)]))
            for signal in sorted(predictions["signal"].unique())
        },
        "configuration": {
            "signals": list(config.signals),
            "primary_signal": config.primary_signal,
            "splits": config.splits,
            "lower_probability": config.lower_probability,
            "upper_probability": config.upper_probability,
            "bootstrap_samples": config.bootstrap_samples,
            "block_size": config.block_size,
            "monitor_window": config.monitor_window,
            "feature": asdict(config.feature),
        },
        "runtime": {
            "python": ".".join(map(str, sys.version_info[:3])),
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "figure_files": figure_paths,
        "reference_file": "../docs/REFERENCES.md",
    }
    with (output_directory / "run_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    _write_markdown_report(
        output_directory / "research_report.md",
        data=data,
        stage_one=stage_one,
        folds=folds,
        regimes=regimes,
        verdicts=verdicts,
        primary_signal=primary_signal,
        figure_paths=figure_paths,
        config=config,
    )


def _write_markdown_report(
    path: Path,
    data: pd.DataFrame,
    stage_one: pd.DataFrame,
    folds: pd.DataFrame,
    regimes: pd.DataFrame,
    verdicts: dict[str, dict],
    primary_signal: str,
    figure_paths: list[str],
    config: object,
) -> None:
    lines = [
        "# Technical Signal Validity Framework - Version 1 Evidence Report",
        "",
        "> Institutional benchmark-relative assessment of RSI and Bollinger Band information on four-hour SOL/USDT data.",
        "",
        "## Executive determination",
        "",
        _institutional_determination("rsi", verdicts["rsi"]),
        "",
        _institutional_determination("bollinger", verdicts["bollinger"]),
        "",
        (
            "The combined model is secondary. It tests complementarity between "
            "momentum and volatility-relative price location and does not "
            "replace either standalone conclusion."
        ),
        "",
        "## Assessment scope",
        "",
        f"- Sample: **{data.index.min()}** to **{data.index.max()}**",
        f"- Usable observations: **{len(data):,}**",
        f"- Forecast horizon: **{config.feature.horizon} four-hour candle(s)**",
        f"- Chronological folds: **{config.splits}**",
        f"- Cost assumption: **{config.feature.cost_bps:.1f} bps per one-way position change**",
        f"- Primary empirical signal: **{DISPLAY[primary_signal]}**",
        "",
        "## Evidence hierarchy",
        "",
        "The framework separates four evidence layers:",
        "",
        "1. a threshold event was followed by a movement;",
        "2. the signal improved a probability forecast beyond market variables;",
        "3. the improvement remained economically positive after assumed costs;",
        "4. any established contribution survived regime change and sequential monitoring.",
        "",
        "This hierarchy prevents descriptive indicator behaviour from being treated as evidence of stable incremental predictability.",
        "",
        "## Candidate-model determinations",
        "",
        "| Signal | Stage 1 | Status | Predictive gain | Net edge | 95% interval | Current regime | Change alarm |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    stage_lookup = stage_one.set_index("signal")
    for signal in ["rsi", "bollinger", "combined"]:
        result = verdicts[signal]
        lines.append(
            f"| {DISPLAY[signal]} | {stage_lookup.loc[signal, 'stage_one_verdict']} | "
            f"{result['status']} | {result['overall_mean_incremental_log_loss']:.3e} | "
            f"{result['overall_mean_incremental_net_edge']:.3e} | "
            f"[{result['overall_edge_ci_95_lower']:.3e}, {result['overall_edge_ci_95_upper']:.3e}] | "
            f"{result['current_regime']} | {result['structural_change_alarm']} |"
        )

    lines.extend([
        "",
        "## Market-state-conditioned evidence",
        "",
        "| Signal | Regime | Observations | Predictive gain | Net edge | Mean state probability |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for _, row in regimes.sort_values(["signal", "regime"]).iterrows():
        lines.append(
            f"| {DISPLAY[str(row['signal'])]} | {str(row['regime']).title()} | "
            f"{int(row['observations']):,} | {row['mean_incremental_log_loss']:.3e} | "
            f"{row['mean_incremental_net_edge']:.3e} | {row['mean_filtered_probability']:.3f} |"
        )

    lines.extend([
        "",
        "## Figures",
        "",
    ])
    captions = {
        "figures/figure_01_market_signal_anatomy.svg": "Market and signal anatomy",
        "figures/figure_02_validation_evidence.svg": "Benchmark-relative validation dashboard",
        "figures/figure_03_probability_calibration.svg": "Out-of-sample probability calibration",
        "figures/figure_04_regime_evidence_matrix.svg": "Regime-conditioned evidence matrix",
        "figures/monitoring_rsi.svg": "RSI online monitoring",
        "figures/monitoring_bollinger.svg": "Bollinger Bands online monitoring",
        "figures/monitoring_combined.svg": "Combined-model online monitoring",
    }
    for figure in figure_paths:
        lines.extend([f"### {captions[figure]}", "", f"![{captions[figure]}]({figure})", ""])

    lines.extend([
        "## Institutional interpretation",
        "",
        "A `NOT_ESTABLISHED` determination is substantive: the candidate may describe market conditions without adding information beyond trend, volatility, recent returns, volume, and BTC context. It does not imply that every historical indicator event was wrong; it means the incremental claim did not survive the declared validation contract.",
        "",
        "A structural-deterioration alarm is not sufficient to suspend a candidate that did not pass establishment. The status hierarchy requires establishment before deterioration and deterioration before suspension.",
        "",
        "## Scope boundaries",
        "",
        "The V1 results are venue-, symbol-, timeframe-, sample-, and cost-specific. They exclude order-book depth, funding, open interest, liquidation intensity, venue-specific slippage, capacity, taxation, and live execution. The outputs constitute research evidence and do not represent investment advice or a trading recommendation.",
        "",
        "## Sources, methodology, and reproducibility",
        "",
        "**Data route.** Public exchange OHLCV accessed through the CCXT unified API. The data-validation record and run manifest document the usable sample and runtime configuration.",
        "",
        "**Method frame.** RSI follows Wilder's formulation; Bollinger features include %B and BandWidth; market-state filtering is motivated by Hamilton's regime-switching framework; sequential monitoring uses Page's CUSUM principle; chronological splits follow time-series validation practice.",
        "",
        "**Primary references.**",
        "",
    ])
    for index, reference in enumerate(REFERENCES, start=1):
        lines.append(f"{index}. {reference}")
    lines.extend([
        "",
        "Full links and bibliographic details: [`../docs/REFERENCES.md`](../docs/REFERENCES.md).",
        "",
        "Reproducibility manifest: [`run_manifest.json`](run_manifest.json).",
    ])

    path.write_text("\n".join(lines), encoding="utf-8")
