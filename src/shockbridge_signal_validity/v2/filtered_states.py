from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from .causal_features import STATE_INPUT_FEATURES
from .contracts import ProtocolViolation


def _logsumexp(values: np.ndarray) -> float:
    maximum = float(np.max(values))
    return maximum + float(np.log(np.exp(values - maximum).sum()))


def _validate_frame(frame: pd.DataFrame, minimum_rows: int = 1) -> pd.DataFrame:
    missing = [column for column in STATE_INPUT_FEATURES if column not in frame]
    if missing:
        raise ProtocolViolation("Filtered-state inputs are missing: " + ", ".join(missing))
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise ProtocolViolation("Filtered-state inputs require timezone-aware timestamps.")
    data = frame.loc[:, STATE_INPUT_FEATURES].apply(pd.to_numeric, errors="coerce")
    if data.isna().any().any():
        raise ProtocolViolation("Filtered-state inputs must be complete within each fold.")
    if not data.index.is_monotonic_increasing or data.index.has_duplicates:
        raise ProtocolViolation("Filtered-state timestamps must be unique and chronological.")
    if len(data) < minimum_rows:
        raise ProtocolViolation(
            f"Filtered-state estimation requires at least {minimum_rows} observations."
        )
    return data.astype(float)


@dataclass(frozen=True)
class FilteredStateConfig:
    states: int = 3
    random_state: int = 42
    covariance_floor: float = 1e-5
    transition_smoothing: float = 1.0
    kmeans_n_init: int = 10
    minimum_training_rows: int = 120


class CausalFilteredStateEngine:
    """Training-scoped Gaussian Markov filter with forward-only evaluation."""

    def __init__(self, config: FilteredStateConfig | None = None) -> None:
        self.config = config or FilteredStateConfig()
        if self.config.states != 3:
            raise ProtocolViolation("Version 2 state governance requires exactly three states.")

    def fit(self, training_frame: pd.DataFrame) -> "CausalFilteredStateEngine":
        data = _validate_frame(training_frame, self.config.minimum_training_rows)
        x = data.to_numpy(dtype=float)
        self.location_ = x.mean(axis=0)
        self.scale_ = x.std(axis=0, ddof=0)
        self.scale_[self.scale_ == 0.0] = 1.0
        z = (x - self.location_) / self.scale_

        clusters = KMeans(
            n_clusters=3,
            n_init=self.config.kmeans_n_init,
            random_state=self.config.random_state,
        ).fit_predict(z)
        if len(np.unique(clusters)) != 3:
            raise ProtocolViolation("State initialization did not produce three populated states.")

        self.means_ = np.vstack([z[clusters == state].mean(axis=0) for state in range(3)])
        self.covariances_ = np.stack(
            [self._regularized_covariance(z[clusters == state]) for state in range(3)]
        )
        counts = np.bincount(clusters, minlength=3).astype(float)
        self.initial_probabilities_ = (counts + 1.0) / (counts.sum() + 3.0)

        transitions = np.full((3, 3), self.config.transition_smoothing, dtype=float)
        for previous, current in zip(clusters[:-1], clusters[1:]):
            transitions[previous, current] += 1.0
        self.transition_matrix_ = transitions / transitions.sum(axis=1, keepdims=True)
        self.state_names_ = self._semantic_state_names(data, clusters)
        probabilities = self._filter_standardized(z, self.initial_probabilities_)
        self.training_probabilities_ = self._probability_frame(data.index, probabilities)
        self.last_train_probabilities_ = probabilities[-1].copy()
        self.fit_start_ = data.index.min()
        self.fit_end_ = data.index.max()
        self.training_rows_ = len(data)
        return self

    def filter_forward(self, evaluation_frame: pd.DataFrame) -> pd.DataFrame:
        self._require_fitted()
        data = _validate_frame(evaluation_frame)
        if len(data) and data.index.min() <= self.fit_end_:
            raise ProtocolViolation(
                "Forward state evaluation must begin strictly after the training endpoint."
            )
        z = (data.to_numpy(dtype=float) - self.location_) / self.scale_
        probabilities = self._filter_standardized(z, self.last_train_probabilities_)
        return self._probability_frame(data.index, probabilities)

    def parameter_record(self) -> dict[str, Any]:
        self._require_fitted()
        covariance_eigenvalues = [
            np.linalg.eigvalsh(covariance).tolist() for covariance in self.covariances_
        ]
        return {
            "state_inputs": list(STATE_INPUT_FEATURES),
            "fit_start_utc": self.fit_start_.isoformat(),
            "fit_end_utc": self.fit_end_.isoformat(),
            "training_rows": int(self.training_rows_),
            "location": self.location_.tolist(),
            "scale": self.scale_.tolist(),
            "means": self.means_.tolist(),
            "covariances": self.covariances_.tolist(),
            "covariance_eigenvalues": covariance_eigenvalues,
            "initial_probabilities": self.initial_probabilities_.tolist(),
            "last_train_probabilities": self.last_train_probabilities_.tolist(),
            "transition_matrix": self.transition_matrix_.tolist(),
            "state_names": {str(key): value for key, value in self.state_names_.items()},
            "configuration": {
                "random_state": self.config.random_state,
                "covariance_floor": self.config.covariance_floor,
                "transition_smoothing": self.config.transition_smoothing,
                "kmeans_n_init": self.config.kmeans_n_init,
                "minimum_training_rows": self.config.minimum_training_rows,
            },
        }

    def _require_fitted(self) -> None:
        if not hasattr(self, "last_train_probabilities_"):
            raise ProtocolViolation("Filtered-state engine has not been fitted.")

    def _regularized_covariance(self, values: np.ndarray) -> np.ndarray:
        if len(values) < 2:
            covariance = np.eye(len(STATE_INPUT_FEATURES), dtype=float)
        else:
            covariance = np.cov(values, rowvar=False, ddof=1)
        covariance = np.atleast_2d(covariance).astype(float)
        covariance += np.eye(covariance.shape[0]) * self.config.covariance_floor
        return covariance

    def _semantic_state_names(self, frame: pd.DataFrame, clusters: np.ndarray) -> dict[int, str]:
        summaries: list[dict[str, float | int]] = []
        for state in range(3):
            subset = frame.iloc[np.flatnonzero(clusters == state)]
            summaries.append(
                {
                    "state": state,
                    "volatility": float(subset["vol_20"].mean()),
                    "trend": float(subset["trend_12"].abs().mean()),
                }
            )
        stress_state = int(max(summaries, key=lambda item: float(item["volatility"]))["state"])
        remaining = [item for item in summaries if int(item["state"]) != stress_state]
        trend_state = int(max(remaining, key=lambda item: float(item["trend"]))["state"])
        range_state = int(next(item["state"] for item in remaining if int(item["state"]) != trend_state))
        return {range_state: "range", trend_state: "trend", stress_state: "stress"}

    def _probability_frame(self, index: pd.DatetimeIndex, probabilities: np.ndarray) -> pd.DataFrame:
        output = pd.DataFrame(index=index)
        for state_id, state_name in self.state_names_.items():
            output[f"state_p_{state_name}"] = probabilities[:, state_id]
        required = ["state_p_range", "state_p_trend", "state_p_stress"]
        output = output[required]
        output["state_label"] = output[required].idxmax(axis=1).str.replace("state_p_", "", regex=False)
        return output

    def _filter_standardized(self, z: np.ndarray, previous_probabilities: np.ndarray) -> np.ndarray:
        filtered = np.empty((len(z), 3), dtype=float)
        previous = np.asarray(previous_probabilities, dtype=float)
        emissions = self._emission_log_probabilities(z)
        for index in range(len(z)):
            predicted = previous @ self.transition_matrix_
            log_weights = np.log(np.clip(predicted, 1e-15, None)) + emissions[index]
            current = np.exp(log_weights - _logsumexp(log_weights))
            filtered[index] = current
            previous = current
        return filtered

    def _emission_log_probabilities(self, z: np.ndarray) -> np.ndarray:
        emissions = np.empty((len(z), 3), dtype=float)
        dimension = z.shape[1]
        constant = dimension * np.log(2.0 * np.pi)
        for state in range(3):
            covariance = self.covariances_[state]
            sign, log_determinant = np.linalg.slogdet(covariance)
            if sign <= 0:
                raise ProtocolViolation("State covariance must be positive definite.")
            inverse = np.linalg.inv(covariance)
            difference = z - self.means_[state]
            quadratic = np.einsum("ij,jk,ik->i", difference, inverse, difference)
            emissions[:, state] = -0.5 * (constant + log_determinant + quadratic)
        return emissions
