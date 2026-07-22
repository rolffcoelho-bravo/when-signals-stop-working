from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .structural_change import add_structural_change_monitor

from .statistics import (
    matched_random_event_pvalue,
    moving_block_bootstrap_mean_ci,
)


_EVENT_POSITION = {
    "rsi": "rsi_event_position",
    "bollinger": "bb_event_position",
    "combined": "bridge_event_position",
}


def stage_one_event_study(
    data: pd.DataFrame,
    signals: list[str],
    cost_bps: float,
    bootstrap_samples: int,
    block_size: int,
) -> pd.DataFrame:
    rows: list[dict] = []
    cost_rate = cost_bps / 10_000.0

    for signal in signals:
        position_column = _EVENT_POSITION[signal]
        events = data.loc[data[position_column].ne(0.0)].copy()
        positions = events[position_column].to_numpy()
        net_signed_return = (
            positions * events["future_return"].to_numpy()
            - 2.0 * cost_rate
        )

        if len(events) == 0:
            rows.append(
                {
                    "signal": signal,
                    "event_count": 0,
                    "long_events": 0,
                    "short_events": 0,
                    "mean_net_signed_return": float("nan"),
                    "ci_95_lower": float("nan"),
                    "ci_95_upper": float("nan"),
                    "win_rate_after_cost": float("nan"),
                    "matched_random_pvalue": float("nan"),
                    "stage_one_verdict": "INSUFFICIENT_EVENTS",
                }
            )
            continue

        mean_value, lower, upper = moving_block_bootstrap_mean_ci(
            net_signed_return,
            samples=bootstrap_samples,
            block_size=min(block_size, len(net_signed_return)),
        )
        pvalue = matched_random_event_pvalue(
            future_returns=data["future_return"].to_numpy(),
            event_positions=positions,
            observed_mean=mean_value,
            cost_rate=cost_rate,
            samples=bootstrap_samples,
        )

        if len(events) < 30:
            verdict = "INSUFFICIENT_EVENTS"
        elif lower > 0.0 and pvalue < 0.05:
            verdict = "DESCRIPTIVE_EDGE"
        elif upper <= 0.0:
            verdict = "NO_DESCRIPTIVE_EDGE"
        else:
            verdict = "INCONCLUSIVE"

        rows.append(
            {
                "signal": signal,
                "event_count": int(len(events)),
                "long_events": int((positions > 0.0).sum()),
                "short_events": int((positions < 0.0).sum()),
                "mean_net_signed_return": mean_value,
                "ci_95_lower": lower,
                "ci_95_upper": upper,
                "win_rate_after_cost": float(
                    np.mean(net_signed_return > 0.0)
                ),
                "matched_random_pvalue": pvalue,
                "stage_one_verdict": verdict,
            }
        )

    return pd.DataFrame(rows)


def stage_three_regime_summary(predictions: pd.DataFrame) -> pd.DataFrame:
    return (
        predictions.groupby(["signal", "latent_regime"], observed=True)
        .agg(
            observations=("incremental_net_edge", "size"),
            mean_incremental_log_loss=("incremental_log_loss", "mean"),
            mean_incremental_net_edge=("incremental_net_edge", "mean"),
            mean_signal_net_return=("signal_net_return", "mean"),
            mean_baseline_net_return=("baseline_net_return", "mean"),
            mean_filtered_probability=("latent_prob_range", "mean"),
        )
        .reset_index()
        .rename(columns={"latent_regime": "regime"})
    )


def _window_failure(
    frame: pd.DataFrame,
    bootstrap_samples: int,
    block_size: int,
) -> tuple[bool, dict]:
    edge_mean, edge_lower, edge_upper = moving_block_bootstrap_mean_ci(
        frame["incremental_net_edge"],
        samples=bootstrap_samples,
        block_size=min(block_size, len(frame)),
    )
    predictive_gain = float(frame["incremental_log_loss"].mean())
    failure = predictive_gain <= 0.0 and edge_upper <= 0.0
    return failure, {
        "mean_incremental_log_loss": predictive_gain,
        "mean_incremental_net_edge": edge_mean,
        "edge_ci_95_lower": edge_lower,
        "edge_ci_95_upper": edge_upper,
    }


def final_verdicts(
    stage_one: pd.DataFrame,
    folds: pd.DataFrame,
    predictions: pd.DataFrame,
    monitor_window: int,
    failure_windows: int,
    bootstrap_samples: int,
    block_size: int,
) -> dict[str, dict]:
    del failure_windows  # Retained in the public API for backward compatibility.

    results: dict[str, dict] = {}
    stage_one_by_signal = stage_one.set_index("signal")

    for signal in sorted(predictions["signal"].unique()):
        signal_folds = folds.loc[folds["signal"].eq(signal)].copy()
        signal_predictions = predictions.loc[
            predictions["signal"].eq(signal)
        ].sort_index()

        monitored = add_structural_change_monitor(
            signal_predictions,
            calibration_window=monitor_window,
        )

        overall_edge, overall_lower, overall_upper = (
            moving_block_bootstrap_mean_ci(
                monitored["incremental_net_edge"],
                samples=bootstrap_samples,
                block_size=min(block_size, len(monitored)),
            )
        )
        overall_predictive_gain = float(
            monitored["incremental_log_loss"].mean()
        )
        positive_folds = int(
            (signal_folds["incremental_log_loss"] > 0.0).sum()
        )
        required_positive_folds = max(
            1,
            math.ceil(0.60 * len(signal_folds)),
        )

        current_window = monitored.tail(
            min(monitor_window, len(monitored))
        )
        _, current = _window_failure(
            current_window,
            bootstrap_samples=bootstrap_samples,
            block_size=block_size,
        )

        established = (
            overall_predictive_gain > 0.0
            and overall_edge > 0.0
            and positive_folds >= required_positive_folds
        )
        structural_alarm = bool(
            current_window["structural_change_alarm"].iloc[-1]
        )

        if not established:
            status = "NOT_ESTABLISHED"
            explanation = (
                "The signal did not establish stable incremental value over "
                "the benchmark under chronological validation."
            )
        elif (
            structural_alarm
            and current["mean_incremental_log_loss"] <= 0.0
            and current["edge_ci_95_upper"] <= 0.0
        ):
            status = "SUSPENDED"
            explanation = (
                "A sequential deterioration alarm is active and the current "
                "window no longer shows predictive or economic contribution."
            )
        elif (
            not structural_alarm
            and current["mean_incremental_log_loss"] > 0.0
            and current["edge_ci_95_lower"] > 0.0
        ):
            status = "ACTIVE"
            explanation = (
                "The signal remains incrementally useful and no structural "
                "deterioration alarm is active."
            )
        else:
            status = "REDUCED"
            explanation = (
                "Historical value exists, but current evidence is uncertain "
                "or the structural-change monitor indicates deterioration."
            )

        regime_frame = stage_three_regime_summary(monitored)
        best_regime = None
        if not regime_frame.empty:
            best_regime = str(
                regime_frame.sort_values(
                    "mean_incremental_net_edge",
                    ascending=False,
                ).iloc[0]["regime"]
            )

        latest = monitored.iloc[-1]
        results[signal] = {
            "status": status,
            "explanation": explanation,
            "stage_one_verdict": str(
                stage_one_by_signal.loc[signal, "stage_one_verdict"]
            ),
            "event_count": int(
                stage_one_by_signal.loc[signal, "event_count"]
            ),
            "overall_mean_incremental_log_loss": overall_predictive_gain,
            "positive_log_loss_folds": positive_folds,
            "required_positive_folds": required_positive_folds,
            "overall_mean_incremental_net_edge": overall_edge,
            "overall_edge_ci_95_lower": overall_lower,
            "overall_edge_ci_95_upper": overall_upper,
            "current_window_observations": int(len(current_window)),
            "current_mean_incremental_log_loss": current[
                "mean_incremental_log_loss"
            ],
            "current_mean_incremental_net_edge": current[
                "mean_incremental_net_edge"
            ],
            "current_edge_ci_95_lower": current["edge_ci_95_lower"],
            "current_edge_ci_95_upper": current["edge_ci_95_upper"],
            "structural_change_alarm": structural_alarm,
            "structural_cusum": float(latest["structural_cusum"]),
            "current_regime": str(latest["latent_regime"]),
            "current_regime_probabilities": {
                "range": float(latest["latent_prob_range"]),
                "trend": float(latest["latent_prob_trend"]),
                "stress": float(latest["latent_prob_stress"]),
            },
            "best_historical_regime": best_regime,
            "latest_signal_probability": float(
                latest["signal_probability"]
            ),
        }

    return results
