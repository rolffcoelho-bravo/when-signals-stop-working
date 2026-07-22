from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from shockbridge_signal_validity.v2.contracts import ProtocolViolation
from shockbridge_signal_validity.v2.filtered_states import CausalFilteredStateEngine


def _state_frame(rows: int = 900) -> pd.DataFrame:
    index = pd.date_range("2022-01-01", periods=rows, freq="4h", tz="UTC")
    rng = np.random.default_rng(31)
    state = np.repeat([0, 1, 2], rows // 3)
    if len(state) < rows:
        state = np.r_[state, np.full(rows - len(state), 2)]
    ret = rng.normal(0.0, np.choose(state, [0.004, 0.009, 0.025]))
    trend = rng.normal(np.choose(state, [0.0002, 0.006, 0.001]), 0.002)
    vol = np.choose(state, [0.015, 0.025, 0.09]) + rng.normal(0.0, 0.002, rows)
    return pd.DataFrame({"sol_ret_1": ret, "vol_20": vol, "trend_12": trend}, index=index)


def test_filtered_state_probabilities_are_normalized_and_forward_only() -> None:
    frame = _state_frame()
    engine = CausalFilteredStateEngine().fit(frame.iloc[:650])
    output = engine.filter_forward(frame.iloc[650:])
    sums = output[["state_p_range", "state_p_trend", "state_p_stress"]].sum(axis=1)
    assert np.allclose(sums.to_numpy(), 1.0)
    assert set(output["state_label"]).issubset({"range", "trend", "stress"})


def test_filtered_state_forward_probabilities_are_prefix_invariant() -> None:
    frame = _state_frame()
    engine = CausalFilteredStateEngine().fit(frame.iloc[:650])
    full = engine.filter_forward(frame.iloc[650:])
    prefix = engine.filter_forward(frame.iloc[650:760])
    pd.testing.assert_frame_equal(full.loc[prefix.index], prefix)


def test_filtered_state_engine_rejects_overlapping_evaluation() -> None:
    frame = _state_frame()
    engine = CausalFilteredStateEngine().fit(frame.iloc[:650])
    with pytest.raises(ProtocolViolation):
        engine.filter_forward(frame.iloc[640:700])


def test_filtered_state_parameters_are_positive_definite() -> None:
    frame = _state_frame()
    record = CausalFilteredStateEngine().fit(frame.iloc[:650]).parameter_record()
    eigenvalues = np.asarray(record["covariance_eigenvalues"], dtype=float)
    transitions = np.asarray(record["transition_matrix"], dtype=float)
    assert eigenvalues.min() > 0.0
    assert np.allclose(transitions.sum(axis=1), 1.0)
    assert set(record["state_names"].values()) == {"range", "trend", "stress"}
