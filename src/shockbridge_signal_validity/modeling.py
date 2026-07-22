from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .regimes import FilteredRegimeModel

from .features import (
    BASELINE_FEATURES,
    BOLLINGER_FEATURES,
    COMBINED_FEATURES,
    RSI_FEATURES,
)


MODEL_FEATURES: Mapping[str, list[str]] = {
    "rsi": RSI_FEATURES,
    "bollinger": BOLLINGER_FEATURES,
    "combined": COMBINED_FEATURES,
}


@dataclass
class FoldResult:
    signal: str
    fold: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    n_train: int
    n_test: int
    baseline_log_loss: float
    signal_log_loss: float
    incremental_log_loss: float
    baseline_brier: float
    signal_brier: float
    incremental_brier: float
    baseline_auc: float | None
    signal_auc: float | None
    baseline_accuracy: float
    signal_accuracy: float
    baseline_mean_net_return: float
    signal_mean_net_return: float
    incremental_mean_net_edge: float


def make_model() -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    C=1.0,
                    solver="lbfgs",
                    max_iter=3000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def safe_auc(y_true: pd.Series, probability: np.ndarray) -> float | None:
    if y_true.nunique() < 2:
        return None
    return float(roc_auc_score(y_true, probability))


def probability_positions(
    probability: np.ndarray,
    lower_probability: float,
    upper_probability: float,
) -> np.ndarray:
    if not 0.0 < lower_probability < upper_probability < 1.0:
        raise ValueError("Require 0 < lower_probability < upper_probability < 1.")

    return np.where(
        probability >= upper_probability,
        1.0,
        np.where(probability <= lower_probability, -1.0, 0.0),
    )


def strategy_returns(
    probability: np.ndarray,
    future_return: np.ndarray,
    cost_bps: float,
    lower_probability: float,
    upper_probability: float,
) -> tuple[np.ndarray, np.ndarray]:
    position = probability_positions(
        probability,
        lower_probability=lower_probability,
        upper_probability=upper_probability,
    )
    previous_position = np.r_[0.0, position[:-1]]
    turnover = np.abs(position - previous_position)
    net_return = (
        position * future_return
        - turnover * (cost_bps / 10_000.0)
    )
    return net_return, position


def per_observation_log_loss(
    target: np.ndarray,
    probability: np.ndarray,
) -> np.ndarray:
    probability = np.clip(probability, 1e-10, 1.0 - 1e-10)
    return -(
        target * np.log(probability)
        + (1.0 - target) * np.log(1.0 - probability)
    )


def evaluate_incremental_models(
    data: pd.DataFrame,
    signals: list[str],
    splits: int,
    horizon: int,
    cost_bps: float,
    lower_probability: float,
    upper_probability: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    unknown = sorted(set(signals) - set(MODEL_FEATURES))
    if unknown:
        raise ValueError(f"Unknown signals: {unknown}")

    splitter = TimeSeriesSplit(n_splits=splits, gap=horizon)
    fold_results: list[FoldResult] = []
    prediction_frames: list[pd.DataFrame] = []

    for fold, (train_index, test_index) in enumerate(splitter.split(data), start=1):
        train = data.iloc[train_index]
        test = data.iloc[test_index]
        y_train = train["target_up"]
        y_test = test["target_up"]

        if y_train.nunique() < 2:
            raise RuntimeError(f"Fold {fold} training target contains one class.")

        regime_model = FilteredRegimeModel().fit(train)
        filtered_regimes = regime_model.filter(test)

        baseline_model = make_model()
        baseline_model.fit(train[BASELINE_FEATURES], y_train)
        baseline_probability = baseline_model.predict_proba(
            test[BASELINE_FEATURES]
        )[:, 1]

        baseline_net, baseline_position = strategy_returns(
            baseline_probability,
            test["future_return"].to_numpy(),
            cost_bps,
            lower_probability,
            upper_probability,
        )
        baseline_loss_vector = per_observation_log_loss(
            y_test.to_numpy(),
            baseline_probability,
        )

        for signal in signals:
            features = MODEL_FEATURES[signal]
            signal_model = make_model()
            signal_model.fit(train[features], y_train)
            signal_probability = signal_model.predict_proba(test[features])[:, 1]

            signal_net, signal_position = strategy_returns(
                signal_probability,
                test["future_return"].to_numpy(),
                cost_bps,
                lower_probability,
                upper_probability,
            )
            signal_loss_vector = per_observation_log_loss(
                y_test.to_numpy(),
                signal_probability,
            )

            baseline_log_loss = float(log_loss(y_test, baseline_probability))
            signal_log_loss = float(log_loss(y_test, signal_probability))
            baseline_brier = float(
                brier_score_loss(y_test, baseline_probability)
            )
            signal_brier = float(brier_score_loss(y_test, signal_probability))

            fold_results.append(
                FoldResult(
                    signal=signal,
                    fold=fold,
                    train_start=str(train.index.min()),
                    train_end=str(train.index.max()),
                    test_start=str(test.index.min()),
                    test_end=str(test.index.max()),
                    n_train=len(train),
                    n_test=len(test),
                    baseline_log_loss=baseline_log_loss,
                    signal_log_loss=signal_log_loss,
                    incremental_log_loss=baseline_log_loss - signal_log_loss,
                    baseline_brier=baseline_brier,
                    signal_brier=signal_brier,
                    incremental_brier=baseline_brier - signal_brier,
                    baseline_auc=safe_auc(y_test, baseline_probability),
                    signal_auc=safe_auc(y_test, signal_probability),
                    baseline_accuracy=float(
                        accuracy_score(y_test, baseline_probability >= 0.5)
                    ),
                    signal_accuracy=float(
                        accuracy_score(y_test, signal_probability >= 0.5)
                    ),
                    baseline_mean_net_return=float(np.mean(baseline_net)),
                    signal_mean_net_return=float(np.mean(signal_net)),
                    incremental_mean_net_edge=float(
                        np.mean(signal_net - baseline_net)
                    ),
                )
            )

            prediction_frames.append(
                pd.DataFrame(
                    {
                        "signal": signal,
                        "fold": fold,
                        "target_up": y_test.to_numpy(),
                        "future_return": test["future_return"].to_numpy(),
                        "baseline_probability": baseline_probability,
                        "signal_probability": signal_probability,
                        "baseline_position": baseline_position,
                        "signal_position": signal_position,
                        "baseline_net_return": baseline_net,
                        "signal_net_return": signal_net,
                        "incremental_net_edge": signal_net - baseline_net,
                        "incremental_log_loss": (
                            baseline_loss_vector - signal_loss_vector
                        ),
                        "latent_prob_range": filtered_regimes[
                            "latent_prob_range"
                        ].to_numpy(),
                        "latent_prob_trend": filtered_regimes[
                            "latent_prob_trend"
                        ].to_numpy(),
                        "latent_prob_stress": filtered_regimes[
                            "latent_prob_stress"
                        ].to_numpy(),
                        "latent_regime": filtered_regimes[
                            "latent_regime"
                        ].to_numpy(),
                    },
                    index=test.index,
                )
            )

    return (
        pd.DataFrame([asdict(result) for result in fold_results]),
        pd.concat(prediction_frames).sort_index(),
    )
