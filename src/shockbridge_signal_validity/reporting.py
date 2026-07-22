from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


DISPLAY_NAMES = {
    "rsi": "RSI",
    "bollinger": "Bollinger Bands",
    "combined": "Combined RSI + Bollinger",
}


def save_outputs(
    output_directory: Path,
    stage_one: pd.DataFrame,
    folds: pd.DataFrame,
    predictions: pd.DataFrame,
    regimes: pd.DataFrame,
    verdicts: dict[str, dict],
    primary_signal: str,
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)

    stage_one.to_csv(output_directory / "stage_1_event_study.csv", index=False)
    folds.to_csv(output_directory / "stage_2_fold_results.csv", index=False)
    predictions.to_csv(output_directory / "stage_2_oos_predictions.csv")
    regimes.to_csv(output_directory / "stage_3_regime_summary.csv", index=False)

    with (output_directory / "final_verdicts.json").open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(verdicts, handle, indent=2)

    _write_markdown_report(
        output_directory / "research_report.md",
        stage_one=stage_one,
        folds=folds,
        regimes=regimes,
        verdicts=verdicts,
        primary_signal=primary_signal,
    )
    _plot_cumulative_returns(output_directory, predictions)
    _plot_rolling_edges(output_directory, predictions)
    _plot_structural_change(output_directory, predictions)


def _write_markdown_report(
    path: Path,
    stage_one: pd.DataFrame,
    folds: pd.DataFrame,
    regimes: pd.DataFrame,
    verdicts: dict[str, dict],
    primary_signal: str,
) -> None:
    lines = [
        "# ShockBridge Technical Signal Validity Report",
        "",
        "## Research questions",
        "",
        (
            "When does RSI stop working, and does the same establishment and "
            "failure logic apply to Richard's corrected Bollinger Band signal? "
            "Each indicator is tested separately against the same non-indicator "
            "benchmark."
        ),
        "",
        "## Three-stage protocol",
        "",
        "1. Event validity",
        "2. Incremental benchmark comparison",
        "3. Regime stability and failure monitoring",
        "",
        "## Executive conclusion",
        "",
        "The report preserves a separate verdict for RSI and Bollinger Bands.",
        "",
    ]

    primary = verdicts[primary_signal]
    lines.extend(
        [
            f"**Primary signal:** {DISPLAY_NAMES[primary_signal]}",
            "",
            f"**Operational status:** {primary['status']}",
            "",
            primary["explanation"],
            "",
            (
                f"Current inferred observable regime: "
                f"**{primary['current_regime']}**."
            ),
            (
                f"Historically strongest regime by incremental economic edge: "
                f"**{primary['best_historical_regime']}**."
            ),
            "",
        ]
    )

    lines.append("## Signal-by-signal verdicts")
    lines.append("")
    for signal, result in verdicts.items():
        lines.extend(
            [
                f"### {DISPLAY_NAMES[signal]}",
                "",
                f"- Stage 1: {result['stage_one_verdict']}",
                f"- Final status: {result['status']}",
                (
                    "- Mean incremental log-loss improvement: "
                    f"{result['overall_mean_incremental_log_loss']:.8f}"
                ),
                (
                    "- Mean incremental net edge: "
                    f"{result['overall_mean_incremental_net_edge']:.8f}"
                ),
                (
                    "- 95% edge interval: "
                    f"[{result['overall_edge_ci_95_lower']:.8f}, "
                    f"{result['overall_edge_ci_95_upper']:.8f}]"
                ),
                f"- Current filtered regime: {result['current_regime']}",
                f"- Structural-change alarm: {result['structural_change_alarm']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Interpretation rule",
            "",
            (
                "A signal is not said to have 'stopped working' unless it first "
                "demonstrated historical incremental value and then crossed the "
                "predeclared recent-window failure gate. When no reliable edge "
                "was established, the correct conclusion is NOT_ESTABLISHED, "
                "not SUSPENDED."
            ),
            "",
            "## Research boundary",
            "",
            (
                "This report is a research validation output. It is not an "
                "investment recommendation or evidence of future profitability."
            ),
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")


def _plot_cumulative_returns(
    output_directory: Path,
    predictions: pd.DataFrame,
) -> None:
    for signal, frame in predictions.groupby("signal"):
        ordered = frame.sort_index()
        figure, axis = plt.subplots(figsize=(10, 6))
        axis.plot(
            ordered.index,
            ordered["baseline_net_return"].cumsum(),
            label="Baseline",
        )
        axis.plot(
            ordered.index,
            ordered["signal_net_return"].cumsum(),
            label=DISPLAY_NAMES[signal],
        )
        axis.set_title(
            f"Out-of-Sample Cumulative Net Return: {DISPLAY_NAMES[signal]}"
        )
        axis.set_xlabel("Date")
        axis.set_ylabel("Cumulative log return")
        axis.legend()
        figure.tight_layout()
        figure.savefig(
            output_directory / f"cumulative_net_return_{signal}.png",
            dpi=180,
        )
        plt.close(figure)


def _plot_rolling_edges(
    output_directory: Path,
    predictions: pd.DataFrame,
) -> None:
    for signal, frame in predictions.groupby("signal"):
        ordered = frame.sort_index()
        rolling = ordered["incremental_net_edge"].rolling(
            180,
            min_periods=60,
        ).mean()
        figure, axis = plt.subplots(figsize=(10, 6))
        axis.plot(rolling.index, rolling)
        axis.axhline(0.0, linewidth=1)
        axis.set_title(
            f"Rolling Incremental Net Edge: {DISPLAY_NAMES[signal]}"
        )
        axis.set_xlabel("Date")
        axis.set_ylabel("Mean incremental net edge")
        figure.tight_layout()
        figure.savefig(
            output_directory / f"rolling_incremental_edge_{signal}.png",
            dpi=180,
        )
        plt.close(figure)


def _plot_structural_change(
    output_directory: Path,
    predictions: pd.DataFrame,
) -> None:
    from .structural_change import add_structural_change_monitor

    for signal, frame in predictions.groupby("signal"):
        monitored = add_structural_change_monitor(frame.sort_index())
        figure, axis = plt.subplots(figsize=(10, 6))
        axis.plot(monitored.index, monitored["structural_cusum"])
        axis.axhline(-8.0, linewidth=1)
        axis.set_title(
            f"Online Structural-Change Monitor: {DISPLAY_NAMES[signal]}"
        )
        axis.set_xlabel("Date")
        axis.set_ylabel("One-sided CUSUM")
        figure.tight_layout()
        figure.savefig(
            output_directory / f"structural_change_{signal}.png",
            dpi=180,
        )
        plt.close(figure)
