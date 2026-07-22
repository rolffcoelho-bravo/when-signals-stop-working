from __future__ import annotations

import numpy as np
import pandas as pd


def add_structural_change_monitor(
    frame: pd.DataFrame,
    calibration_window: int = 180,
    allowance: float = 0.10,
    threshold: float = 8.0,
) -> pd.DataFrame:
    """
    Add a one-sided online CUSUM for deterioration in signal quality.

    Quality combines benchmark-relative log-loss improvement and net edge.
    The calibration statistics use only the initial out-of-sample segment.
    """
    data = frame.sort_index().copy()
    calibration_window = min(
        max(60, calibration_window),
        max(60, len(data) // 3),
    )
    calibration = data.iloc[:calibration_window]

    quality_parts = []
    for column in ("incremental_log_loss", "incremental_net_edge"):
        median = float(calibration[column].median())
        mad = float(
            np.median(np.abs(calibration[column].to_numpy() - median))
        )
        standard_deviation = float(calibration[column].std(ddof=0))
        robust_scale = max(1.4826 * mad, 0.10 * standard_deviation, 1e-6)
        standardized = (data[column] - median) / robust_scale
        quality_parts.append(standardized.clip(-6.0, 6.0))

    data["signal_quality_score"] = 0.5 * (
        quality_parts[0] + quality_parts[1]
    )

    cusum_values = np.zeros(len(data), dtype=float)
    alarms = np.zeros(len(data), dtype=bool)
    cusum = 0.0

    for index, quality in enumerate(data["signal_quality_score"].to_numpy()):
        if index < calibration_window:
            continue
        cusum = min(0.0, cusum + float(quality) + allowance)
        cusum_values[index] = cusum
        alarms[index] = cusum <= -threshold

    data["structural_cusum"] = cusum_values
    data["structural_deterioration_index"] = np.log1p(
        np.maximum(0.0, -cusum_values) / threshold
    )
    data["structural_change_alarm"] = alarms
    return data
