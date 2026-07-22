from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


REGIME_FEATURES = ["sol_ret_1", "vol_20", "trend_12"]


def _logsumexp(values: np.ndarray) -> float:
    maximum = float(np.max(values))
    return maximum + float(np.log(np.exp(values - maximum).sum()))


@dataclass
class FilteredRegimeModel:
    """Three-state Gaussian Markov filter fitted only on the training sample."""

    random_state: int = 42
    covariance_floor: float = 1e-5
    transition_smoothing: float = 1.0

    def fit(self, frame: pd.DataFrame) -> "FilteredRegimeModel":
        x = frame[REGIME_FEATURES].to_numpy(dtype=float)
        self.location_ = x.mean(axis=0)
        self.scale_ = x.std(axis=0)
        self.scale_[self.scale_ == 0.0] = 1.0
        z = (x - self.location_) / self.scale_

        clusters = KMeans(
            n_clusters=3,
            n_init=20,
            random_state=self.random_state,
        ).fit_predict(z)

        self.means_ = np.vstack([z[clusters == state].mean(axis=0) for state in range(3)])
        self.covariances_ = np.stack(
            [
                self._regularized_covariance(z[clusters == state])
                for state in range(3)
            ]
        )

        counts = np.bincount(clusters, minlength=3).astype(float)
        self.initial_probabilities_ = (counts + 1.0) / (counts.sum() + 3.0)

        transitions = np.full((3, 3), self.transition_smoothing, dtype=float)
        for previous, current in zip(clusters[:-1], clusters[1:]):
            transitions[previous, current] += 1.0
        self.transition_matrix_ = transitions / transitions.sum(axis=1, keepdims=True)

        self.state_names_ = self._semantic_state_names(frame, clusters)
        train_probabilities = self._filter_standardized(z, self.initial_probabilities_)
        self.last_train_probabilities_ = train_probabilities[-1]
        return self

    def filter(self, frame: pd.DataFrame) -> pd.DataFrame:
        x = frame[REGIME_FEATURES].to_numpy(dtype=float)
        z = (x - self.location_) / self.scale_
        probabilities = self._filter_standardized(
            z,
            self.last_train_probabilities_,
        )

        output = pd.DataFrame(index=frame.index)
        for state_id, state_name in self.state_names_.items():
            output[f"latent_prob_{state_name}"] = probabilities[:, state_id]

        output["latent_regime"] = [
            self.state_names_[int(state)]
            for state in probabilities.argmax(axis=1)
        ]
        return output

    def _regularized_covariance(self, values: np.ndarray) -> np.ndarray:
        if len(values) < 2:
            covariance = np.eye(len(REGIME_FEATURES))
        else:
            covariance = np.cov(values, rowvar=False)
        covariance = np.atleast_2d(covariance)
        return covariance + np.eye(covariance.shape[0]) * self.covariance_floor

    def _semantic_state_names(
        self,
        frame: pd.DataFrame,
        clusters: np.ndarray,
    ) -> dict[int, str]:
        summaries = []
        for state in range(3):
            subset = frame.iloc[np.flatnonzero(clusters == state)]
            summaries.append(
                {
                    "state": state,
                    "volatility": float(subset["vol_20"].mean()),
                    "trend": float(subset["trend_12"].abs().mean()),
                }
            )

        stress_state = max(summaries, key=lambda item: item["volatility"])["state"]
        remaining = [item for item in summaries if item["state"] != stress_state]
        trend_state = max(remaining, key=lambda item: item["trend"])["state"]
        range_state = next(
            item["state"]
            for item in remaining
            if item["state"] != trend_state
        )
        return {
            int(range_state): "range",
            int(trend_state): "trend",
            int(stress_state): "stress",
        }

    def _filter_standardized(
        self,
        z: np.ndarray,
        previous_probabilities: np.ndarray,
    ) -> np.ndarray:
        filtered = np.empty((len(z), 3), dtype=float)
        previous = np.asarray(previous_probabilities, dtype=float)

        for index, observation in enumerate(z):
            predicted = previous @ self.transition_matrix_
            log_weights = np.log(np.clip(predicted, 1e-15, None))

            for state in range(3):
                log_weights[state] += self._gaussian_log_density(
                    observation,
                    self.means_[state],
                    self.covariances_[state],
                )

            normalizer = _logsumexp(log_weights)
            current = np.exp(log_weights - normalizer)
            filtered[index] = current
            previous = current

        return filtered

    @staticmethod
    def _gaussian_log_density(
        observation: np.ndarray,
        mean: np.ndarray,
        covariance: np.ndarray,
    ) -> float:
        difference = observation - mean
        sign, log_determinant = np.linalg.slogdet(covariance)
        if sign <= 0:
            raise RuntimeError("Regime covariance must be positive definite.")
        quadratic = float(difference.T @ np.linalg.solve(covariance, difference))
        dimension = len(observation)
        return -0.5 * (
            dimension * np.log(2.0 * np.pi)
            + log_determinant
            + quadratic
        )
