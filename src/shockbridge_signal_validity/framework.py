from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .evaluation import (
    final_verdicts,
    stage_one_event_study,
    stage_three_regime_summary,
)
from .features import FeatureConfig, build_feature_frame
from .modeling import evaluate_incremental_models
from .reporting import save_outputs


@dataclass(frozen=True)
class ValidationConfig:
    feature: FeatureConfig = FeatureConfig()
    signals: tuple[str, ...] = ("rsi", "bollinger", "combined")
    primary_signal: str = "bollinger"
    splits: int = 5
    lower_probability: float = 0.45
    upper_probability: float = 0.55
    bootstrap_samples: int = 2000
    block_size: int = 10
    monitor_window: int = 180
    failure_windows: int = 3


def run_framework(
    sol: pd.DataFrame,
    btc: pd.DataFrame,
    config: ValidationConfig,
    output_directory: Path,
) -> dict:
    signals = list(config.signals)
    if config.primary_signal not in signals:
        raise ValueError("The primary signal must be included in signals.")

    data = build_feature_frame(sol, btc, config.feature)
    if len(data) < 500:
        raise RuntimeError(
            f"Only {len(data)} usable observations. Use a longer sample."
        )

    stage_one = stage_one_event_study(
        data=data,
        signals=signals,
        cost_bps=config.feature.cost_bps,
        bootstrap_samples=config.bootstrap_samples,
        block_size=config.block_size,
    )

    folds, predictions = evaluate_incremental_models(
        data=data,
        signals=signals,
        splits=config.splits,
        horizon=config.feature.horizon,
        cost_bps=config.feature.cost_bps,
        lower_probability=config.lower_probability,
        upper_probability=config.upper_probability,
    )

    regimes = stage_three_regime_summary(predictions)
    verdicts = final_verdicts(
        stage_one=stage_one,
        folds=folds,
        predictions=predictions,
        monitor_window=config.monitor_window,
        failure_windows=config.failure_windows,
        bootstrap_samples=config.bootstrap_samples,
        block_size=config.block_size,
    )

    save_outputs(
        output_directory=output_directory,
        stage_one=stage_one,
        folds=folds,
        predictions=predictions,
        regimes=regimes,
        verdicts=verdicts,
        primary_signal=config.primary_signal,
    )

    return {
        "observations": len(data),
        "primary_signal": config.primary_signal,
        "primary_verdict": verdicts[config.primary_signal],
        "verdicts": verdicts,
    }
