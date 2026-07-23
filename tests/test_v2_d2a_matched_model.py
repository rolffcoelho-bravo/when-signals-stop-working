from __future__ import annotations

import numpy as np
import pandas as pd

from shockbridge_signal_validity.v2.causal_features import BASELINE_FEATURES
from shockbridge_signal_validity.v2.predictive_screening import matched_logistic_fold


def test_matched_logistic_fold_returns_aligned_probabilities() -> None:
    rng = np.random.default_rng(42)
    index = pd.date_range("2022-01-01", periods=420, freq="4h", tz="UTC")
    baseline = pd.DataFrame(rng.normal(size=(len(index), len(BASELINE_FEATURES))), index=index, columns=BASELINE_FEATURES)
    states = pd.DataFrame(
        np.tile([0.6, 0.3, 0.1], (len(index), 1)),
        index=index,
        columns=["state_p_range", "state_p_trend", "state_p_stress"],
    )
    signal = pd.DataFrame({"rsi_feature": rng.normal(size=len(index)), "signal_x_range": rng.normal(size=len(index)), "signal_x_trend": rng.normal(size=len(index)), "signal_x_stress": rng.normal(size=len(index))}, index=index)
    target = pd.Series((rng.normal(size=len(index)) > 0).astype(int), index=index)
    result = matched_logistic_fold(
        baseline_features=baseline,
        signal_features=signal,
        train_states=states.iloc[:300],
        test_states=states.iloc[300:],
        target=target,
        train_start=index[0],
        train_end=index[299],
        test_start=index[300],
        test_end=index[-1],
    )
    assert result.test_rows == 120
    assert len(result.candidate_probability) == 120
    assert np.isfinite(result.incremental_log_loss)
