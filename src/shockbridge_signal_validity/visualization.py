from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from sklearn.calibration import calibration_curve

from .structural_change import add_structural_change_monitor

DISPLAY = {
    "rsi": "RSI",
    "bollinger": "Bollinger Bands",
    "combined": "Combined",
}
SIGNAL_ORDER = ["rsi", "bollinger", "combined"]
REGIME_ORDER = ["range", "trend", "stress"]

PALETTE = {
    "ink": "#132238",
    "muted": "#64748B",
    "grid": "#D9E2EC",
    "baseline": "#64748B",
    "rsi": "#2563EB",
    "bollinger": "#0F766E",
    "combined": "#7C3AED",
    "positive": "#0F766E",
    "negative": "#C2413B",
    "warning": "#B7791F",
    "range": "#94A3B8",
    "trend": "#2563EB",
    "stress": "#C2413B",
    "gold": "#D4A72C",
    "background": "#F8FAFC",
}

SOURCE_NOTE = (
    "Data: public exchange OHLCV via CCXT. Method: expanding-window OOS validation, "
    "training-only Gaussian Markov filtering, and one-sided CUSUM. References: "
    "Wilder (1978), Bollinger, Hamilton (1989), Page (1954)."
)


def configure_publication_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": PALETTE["grid"],
            "axes.labelcolor": PALETTE["ink"],
            "axes.titlecolor": PALETTE["ink"],
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "xtick.color": PALETTE["muted"],
            "ytick.color": PALETTE["muted"],
            "grid.color": PALETTE["grid"],
            "grid.alpha": 0.65,
            "grid.linewidth": 0.6,
            "legend.frameon": False,
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
        }
    )


def _downsample(frame: pd.DataFrame, max_points: int = 5000) -> pd.DataFrame:
    if len(frame) <= max_points:
        return frame
    positions = np.linspace(0, len(frame) - 1, max_points).astype(int)
    return frame.iloc[np.unique(positions)]


def _footer(figure: plt.Figure, text: str = SOURCE_NOTE) -> None:
    figure.text(
        0.01,
        0.006,
        text,
        ha="left",
        va="bottom",
        fontsize=6.8,
        color=PALETTE["muted"],
    )


def _save(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path.with_suffix(".svg"), format="svg")
    if os.getenv("SHOCKBRIDGE_RASTER", "0") == "1":
        figure.savefig(path.with_suffix(".png"), format="png", dpi=120)
    plt.close(figure)


def _date_axis(axis: plt.Axes) -> None:
    locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
    axis.xaxis.set_major_locator(locator)
    axis.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))


def market_signal_anatomy(
    directory: Path,
    data: pd.DataFrame,
    predictions: pd.DataFrame,
    primary_signal: str,
) -> None:
    primary = predictions.loc[predictions["signal"].eq(primary_signal)].sort_index()
    joined = data.join(
        primary[
            [
                "latent_prob_range",
                "latent_prob_trend",
                "latent_prob_stress",
            ]
        ],
        how="inner",
    )
    joined = _downsample(joined)

    figure, axes = plt.subplots(
        4,
        1,
        figsize=(14, 12),
        sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.1, 1.1, 1.0], "hspace": 0.16},
    )
    figure.suptitle(
        "Market and Signal Anatomy - Out-of-Sample Window",
        x=0.01,
        y=0.995,
        ha="left",
        fontsize=18,
        fontweight="bold",
        color=PALETTE["ink"],
    )
    figure.text(
        0.01,
        0.968,
        "Price location, momentum state, volatility-relative position, and filtered market-state probabilities",
        ha="left",
        color=PALETTE["muted"],
        fontsize=9.5,
    )

    ax = axes[0]
    ax.plot(joined.index, joined["sol_Close"], color=PALETTE["ink"], linewidth=1.15, label="SOL close")
    ax.plot(joined.index, joined["bb_middle"], color=PALETTE["gold"], linewidth=0.9, label="BB middle")
    ax.plot(joined.index, joined["bb_upper"], color=PALETTE["bollinger"], linewidth=0.7, alpha=0.9, label="BB upper/lower")
    ax.plot(joined.index, joined["bb_lower"], color=PALETTE["bollinger"], linewidth=0.7, alpha=0.9)
    ax.fill_between(joined.index, joined["bb_lower"], joined["bb_upper"], color=PALETTE["bollinger"], alpha=0.07)
    long_events = joined["bb_long_event"].eq(1.0)
    short_events = joined["bb_short_event"].eq(1.0)
    ax.scatter(joined.index[long_events], joined.loc[long_events, "sol_Close"], marker="^", s=22, color=PALETTE["positive"], label="Lower-band event", zorder=4)
    ax.scatter(joined.index[short_events], joined.loc[short_events, "sol_Close"], marker="v", s=22, color=PALETTE["negative"], label="Upper-band event", zorder=4)
    ax.set_yscale("log")
    ax.set_ylabel("SOL price (log)")
    ax.legend(ncol=5, loc="upper left")
    ax.grid(True, axis="y")

    ax = axes[1]
    ax.plot(joined.index, joined["rsi"], color=PALETTE["rsi"], linewidth=1.0)
    ax.axhline(70, color=PALETTE["negative"], linewidth=0.8, linestyle="--")
    ax.axhline(30, color=PALETTE["positive"], linewidth=0.8, linestyle="--")
    ax.fill_between(joined.index, 70, joined["rsi"], where=joined["rsi"].ge(70), color=PALETTE["negative"], alpha=0.10)
    ax.fill_between(joined.index, joined["rsi"], 30, where=joined["rsi"].le(30), color=PALETTE["positive"], alpha=0.10)
    ax.set_ylim(0, 100)
    ax.set_ylabel("RSI")
    ax.grid(True, axis="y")

    ax = axes[2]
    ax.plot(joined.index, joined["bb_percent_b"], color=PALETTE["bollinger"], linewidth=1.0)
    ax.axhline(1.0, color=PALETTE["negative"], linewidth=0.8, linestyle="--")
    ax.axhline(0.0, color=PALETTE["positive"], linewidth=0.8, linestyle="--")
    ax.axhline(0.5, color=PALETTE["muted"], linewidth=0.6, linestyle=":")
    ax.set_ylabel("Bollinger %B")
    ax.grid(True, axis="y")

    ax = axes[3]
    ax.stackplot(
        joined.index,
        joined["latent_prob_range"],
        joined["latent_prob_trend"],
        joined["latent_prob_stress"],
        labels=["Range", "Trend", "Stress"],
        colors=[PALETTE["range"], PALETTE["trend"], PALETTE["stress"]],
        alpha=0.78,
    )
    ax.set_ylim(0, 1)
    ax.set_ylabel("Filtered probability")
    ax.legend(ncol=3, loc="upper left")
    ax.grid(False)
    _date_axis(ax)
    _footer(figure)
    figure.subplots_adjust(bottom=0.075, top=0.93)
    _save(figure, directory / "figure_01_market_signal_anatomy")


def validation_evidence(
    directory: Path,
    folds: pd.DataFrame,
    verdicts: dict[str, dict],
    regimes: pd.DataFrame,
) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(14, 10.5), gridspec_kw={"hspace": 0.38, "wspace": 0.24})
    figure.suptitle(
        "Benchmark-Relative Validation Evidence",
        x=0.01,
        y=0.995,
        ha="left",
        fontsize=18,
        fontweight="bold",
        color=PALETTE["ink"],
    )
    figure.text(0.01, 0.967, "Positive values favor the signal model over the common non-indicator benchmark", ha="left", color=PALETTE["muted"], fontsize=9.5)

    width = 0.24
    folds_order = sorted(folds["fold"].unique())
    x = np.arange(len(folds_order))
    for offset, signal in enumerate(SIGNAL_ORDER):
        subset = folds.loc[folds["signal"].eq(signal)].sort_values("fold")
        axes[0, 0].bar(x + (offset - 1) * width, subset["incremental_log_loss"], width=width, label=DISPLAY[signal], color=PALETTE[signal])
        axes[0, 1].bar(x + (offset - 1) * width, subset["incremental_mean_net_edge"], width=width, label=DISPLAY[signal], color=PALETTE[signal])
    for ax, title, ylabel in [
        (axes[0, 0], "Fold-level probability-score gain", "Baseline log loss - signal log loss"),
        (axes[0, 1], "Fold-level incremental economic edge", "Mean incremental net return"),
    ]:
        ax.axhline(0, color=PALETTE["ink"], linewidth=0.8)
        ax.set_xticks(x, [str(value) for value in folds_order])
        ax.set_xlabel("Chronological fold")
        ax.set_ylabel(ylabel)
        ax.set_title(title, loc="left")
        ax.grid(True, axis="y")
    axes[0, 0].legend(ncol=3, loc="upper left")

    y = np.arange(len(SIGNAL_ORDER))
    means = [verdicts[s]["overall_mean_incremental_net_edge"] for s in SIGNAL_ORDER]
    lowers = [verdicts[s]["overall_edge_ci_95_lower"] for s in SIGNAL_ORDER]
    uppers = [verdicts[s]["overall_edge_ci_95_upper"] for s in SIGNAL_ORDER]
    errors = np.vstack([np.array(means) - np.array(lowers), np.array(uppers) - np.array(means)])
    axes[1, 0].errorbar(means, y, xerr=errors, fmt="o", capsize=4, color=PALETTE["ink"], ecolor=PALETTE["muted"])
    for index, signal in enumerate(SIGNAL_ORDER):
        axes[1, 0].scatter(means[index], index, s=55, color=PALETTE[signal], zorder=4)
        axes[1, 0].text(
            0.98,
            index,
            verdicts[signal]["status"],
            transform=axes[1, 0].get_yaxis_transform(),
            fontsize=7.3,
            color=PALETTE["muted"],
            ha="right",
            va="center",
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": PALETTE["grid"], "linewidth": 0.5},
        )
    axes[1, 0].axvline(0, color=PALETTE["ink"], linewidth=0.8)
    axes[1, 0].set_yticks(y, [DISPLAY[s] for s in SIGNAL_ORDER])
    axes[1, 0].set_title("Overall net edge with 95% interval", loc="left", pad=10)
    axes[1, 0].set_xlabel("Incremental net edge")
    axes[1, 0].grid(True, axis="x")

    pivot = regimes.pivot(index="signal", columns="regime", values="mean_incremental_net_edge").reindex(index=SIGNAL_ORDER, columns=REGIME_ORDER)
    matrix = pivot.to_numpy(dtype=float)
    scale = np.nanmax(np.abs(matrix)) or 1.0
    image = axes[1, 1].imshow(matrix, aspect="auto", cmap="RdBu_r", vmin=-scale, vmax=scale)
    axes[1, 1].set_xticks(np.arange(len(REGIME_ORDER)), [name.title() for name in REGIME_ORDER])
    axes[1, 1].set_yticks(np.arange(len(SIGNAL_ORDER)), [DISPLAY[s] for s in SIGNAL_ORDER])
    axes[1, 1].set_title("Regime-conditioned economic edge", loc="left", pad=10)
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value = matrix[row, col]
            if np.isfinite(value):
                axes[1, 1].text(col, row, f"{value:.2e}", ha="center", va="center", fontsize=8, color=PALETTE["ink"])
    figure.colorbar(image, ax=axes[1, 1], fraction=0.046, pad=0.04)

    _footer(figure)
    figure.subplots_adjust(bottom=0.075, top=0.90)
    _save(figure, directory / "figure_02_validation_evidence")


def probability_calibration(directory: Path, predictions: pd.DataFrame) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(14, 4.7), sharex=True, sharey=True)
    figure.suptitle("Out-of-Sample Probability Calibration", x=0.01, y=0.995, ha="left", fontsize=18, fontweight="bold", color=PALETTE["ink"])
    figure.text(0.01, 0.945, "Calibration separates useful probability information from directional accuracy alone", ha="left", color=PALETTE["muted"], fontsize=9.5)

    for axis, signal in zip(axes, SIGNAL_ORDER):
        frame = predictions.loc[predictions["signal"].eq(signal)].sort_index()
        target = frame["target_up"].to_numpy()
        for label, column, color in [
            ("Benchmark", "baseline_probability", PALETTE["baseline"]),
            (DISPLAY[signal], "signal_probability", PALETTE[signal]),
        ]:
            observed, predicted = calibration_curve(target, frame[column].to_numpy(), n_bins=10, strategy="quantile")
            axis.plot(predicted, observed, marker="o", linewidth=1.2, markersize=3.5, label=label, color=color)
        axis.plot([0, 1], [0, 1], linestyle="--", linewidth=0.8, color=PALETTE["grid"])
        axis.set_title(DISPLAY[signal], loc="left")
        axis.set_xlabel("Mean predicted probability")
        axis.grid(True)
    axes[0].set_ylabel("Observed frequency")
    axes[0].legend(loc="upper left")
    _footer(figure, SOURCE_NOTE + " Calibration uses quantile bins; it is diagnostic, not a post-hoc recalibration step.")
    figure.subplots_adjust(bottom=0.17, top=0.86, wspace=0.18)
    _save(figure, directory / "figure_03_probability_calibration")


def regime_evidence_matrix(directory: Path, regimes: pd.DataFrame) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    figure.suptitle("Regime-Conditioned Evidence Matrix", x=0.01, y=0.995, ha="left", fontsize=18, fontweight="bold", color=PALETTE["ink"])
    figure.text(0.01, 0.945, "The same signal may have different predictive and economic value across latent market states", ha="left", color=PALETTE["muted"], fontsize=9.5)

    specifications = [
        ("mean_incremental_log_loss", "Predictive gain", "RdBu_r"),
        ("mean_incremental_net_edge", "Economic edge", "RdBu_r"),
    ]
    for axis, (column, title, cmap) in zip(axes, specifications):
        pivot = regimes.pivot(index="signal", columns="regime", values=column).reindex(index=SIGNAL_ORDER, columns=REGIME_ORDER)
        matrix = pivot.to_numpy(dtype=float)
        scale = np.nanmax(np.abs(matrix)) or 1.0
        image = axis.imshow(matrix, aspect="auto", cmap=cmap, vmin=-scale, vmax=scale)
        axis.set_xticks(np.arange(len(REGIME_ORDER)), [name.title() for name in REGIME_ORDER])
        axis.set_yticks(np.arange(len(SIGNAL_ORDER)), [DISPLAY[s] for s in SIGNAL_ORDER])
        axis.set_title(title, loc="left")
        for row in range(matrix.shape[0]):
            for col in range(matrix.shape[1]):
                value = matrix[row, col]
                if np.isfinite(value):
                    axis.text(col, row, f"{value:.2e}", ha="center", va="center", fontsize=8, color=PALETTE["ink"])
        figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    _footer(figure)
    figure.subplots_adjust(bottom=0.14, top=0.84, wspace=0.25)
    _save(figure, directory / "figure_04_regime_evidence_matrix")


def monitoring_panel(directory: Path, predictions: pd.DataFrame, signal: str) -> None:
    frame = predictions.loc[predictions["signal"].eq(signal)].sort_index()
    monitored = add_structural_change_monitor(frame)
    plot_frame = _downsample(monitored)
    rolling_window = min(180, max(30, len(monitored) // 20))
    rolling_edge = monitored["incremental_net_edge"].rolling(rolling_window, min_periods=max(15, rolling_window // 3)).mean()

    figure, axes = plt.subplots(3, 1, figsize=(13.5, 9.5), sharex=True, gridspec_kw={"hspace": 0.18})
    figure.suptitle(f"Online Signal Monitoring - {DISPLAY[signal]}", x=0.01, y=0.992, ha="left", fontsize=18, fontweight="bold", color=PALETTE["ink"])
    figure.text(0.01, 0.952, "Benchmark-relative economic evidence, rolling contribution, and sequential deterioration state", ha="left", color=PALETTE["muted"], fontsize=9.5)

    axes[0].plot(plot_frame.index, plot_frame["baseline_net_return"].cumsum(), label="Benchmark", color=PALETTE["baseline"], linewidth=1.05)
    axes[0].plot(plot_frame.index, plot_frame["signal_net_return"].cumsum(), label=DISPLAY[signal], color=PALETTE[signal], linewidth=1.2)
    axes[0].set_ylabel("Cumulative log return")
    axes[0].set_title("Out-of-sample net evidence", loc="left")
    axes[0].legend(ncol=2, loc="upper left")
    axes[0].grid(True, axis="y")

    rolling_plot = _downsample(rolling_edge.dropna().to_frame("rolling"))
    axes[1].plot(rolling_plot.index, rolling_plot["rolling"], color=PALETTE[signal], linewidth=1.15)
    axes[1].axhline(0, color=PALETTE["ink"], linewidth=0.8)
    axes[1].fill_between(rolling_plot.index, 0, rolling_plot["rolling"], where=rolling_plot["rolling"].ge(0), color=PALETTE["positive"], alpha=0.12)
    axes[1].fill_between(rolling_plot.index, 0, rolling_plot["rolling"], where=rolling_plot["rolling"].lt(0), color=PALETTE["negative"], alpha=0.12)
    axes[1].set_ylabel("Incremental edge")
    axes[1].set_title(f"Rolling benchmark-relative edge ({rolling_window} observations)", loc="left")
    axes[1].grid(True, axis="y")

    axes[2].plot(plot_frame.index, plot_frame["structural_deterioration_index"], color=PALETTE["warning"], linewidth=1.15, label="Deterioration index")
    alarm_level = np.log(2.0)
    axes[2].axhline(alarm_level, color=PALETTE["negative"], linewidth=0.9, linestyle="--", label="Alarm threshold")
    alarm = plot_frame["structural_change_alarm"].astype(bool)
    axes[2].fill_between(
        plot_frame.index,
        0.0,
        plot_frame["structural_deterioration_index"],
        where=alarm,
        color=PALETTE["negative"],
        alpha=0.10,
        label="Alarm active",
    )
    axes[2].set_ylabel("log(1 + threshold multiple)")
    axes[2].set_title("Sequential structural-deterioration monitor", loc="left")
    axes[2].legend(ncol=3, loc="lower left")
    axes[2].grid(True, axis="y")
    _date_axis(axes[2])

    _footer(figure)
    figure.subplots_adjust(bottom=0.085, top=0.895)
    _save(figure, directory / f"monitoring_{signal}")


def generate_figure_suite(
    directory: Path,
    data: pd.DataFrame,
    folds: pd.DataFrame,
    predictions: pd.DataFrame,
    regimes: pd.DataFrame,
    verdicts: dict[str, dict],
    primary_signal: str,
) -> list[str]:
    configure_publication_style()
    directory.mkdir(parents=True, exist_ok=True)
    market_signal_anatomy(directory, data, predictions, primary_signal)
    validation_evidence(directory, folds, verdicts, regimes)
    probability_calibration(directory, predictions)
    regime_evidence_matrix(directory, regimes)
    for signal in SIGNAL_ORDER:
        monitoring_panel(directory, predictions, signal)
    return [
        "figures/figure_01_market_signal_anatomy.svg",
        "figures/figure_02_validation_evidence.svg",
        "figures/figure_03_probability_calibration.svg",
        "figures/figure_04_regime_evidence_matrix.svg",
        "figures/monitoring_rsi.svg",
        "figures/monitoring_bollinger.svg",
        "figures/monitoring_combined.svg",
    ]
