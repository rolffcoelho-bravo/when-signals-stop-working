from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from shockbridge_signal_validity.v2.causal_features import BASELINE_FEATURES
from shockbridge_signal_validity.v2.pipeline_selection import (
    MatchedPipelineFoldResult,
    StructuralPipelineSpecification,
    directional_policy_metrics,
    matched_pipeline_fold,
)


def registry_payload() -> dict:
    return json.loads(Path("configs/v2_experiment_registry.json").read_text(encoding="utf-8"))


def synthetic_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    rng = np.random.default_rng(42)
    index = pd.date_range("2022-01-01", periods=700, freq="4h", tz="UTC")
    baseline = pd.DataFrame(
        rng.normal(size=(len(index), len(BASELINE_FEATURES))),
        index=index,
        columns=BASELINE_FEATURES,
    )
    state_raw = rng.dirichlet([5.0, 3.0, 2.0], size=len(index))
    states = pd.DataFrame(
        state_raw,
        index=index,
        columns=["state_p_range", "state_p_trend", "state_p_stress"],
    )
    score = pd.Series(rng.normal(size=len(index)), index=index)
    signal = pd.DataFrame(
        {
            "rsi_rsi_signal_score": score,
            "rsi_rsi_signal_event": (score.abs() > 1.0).astype(float),
            "rsi_rsi_extreme": score.abs(),
            "rsi_rsi_event_persistence": score.rolling(3, min_periods=1).mean(),
            "signal_x_range": score * states["state_p_range"],
            "signal_x_trend": score * states["state_p_trend"],
            "signal_x_stress": score * states["state_p_stress"],
        },
        index=index,
    )
    latent = 0.25 * baseline["sol_ret_1"] + 0.35 * score + rng.normal(scale=0.8, size=len(index))
    target = (latent > 0.0).astype(int)
    future_return = pd.Series(0.002 * np.sign(latent) + rng.normal(scale=0.01, size=len(index)), index=index)
    return baseline, states, signal, target, future_return


def test_matched_pipeline_fold_supports_training_only_sigmoid_calibration() -> None:
    baseline, states, signal, target, future_return = synthetic_inputs()
    index = baseline.index
    specification = StructuralPipelineSpecification(
        pipeline_id="regularized-test",
        model_family="regularized_linear",
        window_scheme="expanding",
        regime_conditioned=True,
        parameters={"C": 1.0},
        complexity_rank=1,
    )
    result = matched_pipeline_fold(
        baseline_features=baseline,
        states=states,
        signal_features=signal,
        target=target,
        future_return=future_return,
        train_start=index[0],
        train_end=index[549],
        test_start=index[550],
        test_end=index[-1],
        specification=specification,
        registry_payload=registry_payload(),
        calibration_method="sigmoid",
        horizon_candles=1,
        minimum_fit_rows=120,
        minimum_calibration_rows=60,
    )
    assert isinstance(result, MatchedPipelineFoldResult)
    assert result.test_rows == 150
    assert result.calibration_rows >= 60
    assert len(result.candidate_probability) == 150
    assert np.all((result.candidate_probability > 0.0) & (result.candidate_probability < 1.0))
    assert np.isfinite(result.incremental_log_loss)


def test_directional_policy_metrics_reports_abstention_coverage() -> None:
    metrics = directional_policy_metrics(
        probability=[0.51, 0.60, 0.40, 0.49],
        future_return=[0.01, 0.02, -0.01, -0.02],
        threshold=0.05,
        one_way_cost_bps=10.0,
    )
    assert metrics["nonzero_decisions"] == 2
    assert metrics["coverage"] == 0.5
    assert np.isfinite(metrics["mean_net_edge"])
