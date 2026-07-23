import pandas as pd

from shockbridge_signal_validity.v2.development_admission import (
    pipeline_hash,
    select_final_calibration,
    select_final_policy,
    select_final_signal_specification,
    select_final_structural_pipeline,
)


def inner_rows(kind: str) -> pd.DataFrame:
    rows = []
    for outer in range(1, 6):
        for inner in range(1, 4):
            base = {
                "signal_family": "rsi",
                "horizon_candles": 1,
                "outer_fold": outer,
                "inner_fold": inner,
                "incremental_log_loss": 0.01,
                "candidate_brier": 0.249,
                "benchmark_brier": 0.25,
                "candidate_ece": 0.041,
                "benchmark_ece": 0.04,
            }
            if kind == "signal":
                rows.append({"status": "EVALUATED", "signal_spec_id": "rsi-p14-l30-u70-continuous", **base})
            elif kind == "structural":
                rows.append(
                    {
                        "status": "EVALUATED",
                        "pipeline_id": "linear",
                        "model_family": "regularized_linear",
                        "window_scheme": "expanding",
                        "regime_conditioned": False,
                        "parameters_json": '{"C":1.0}',
                        "complexity_rank": 1,
                        **base,
                    }
                )
            elif kind == "calibration":
                rows.extend(
                    [
                        {"calibration_method": "none", "eligible_for_selection": True, **base},
                        {"calibration_method": "sigmoid", "eligible_for_selection": True, **{**base, "incremental_log_loss": 0.009}},
                        {"calibration_method": "isotonic", "eligible_for_selection": False, **{**base, "incremental_log_loss": 0.5}},
                    ]
                )
            elif kind == "policy":
                for threshold in (0.0, 0.02, 0.05, 0.1):
                    rows.append(
                        {
                            "threshold": threshold,
                            "coverage": 0.5,
                            "nonzero_decisions": 20,
                            "mean_net_edge": 0.001 - threshold,
                            **{key: value for key, value in base.items() if key not in {"incremental_log_loss", "candidate_brier", "benchmark_brier", "candidate_ece", "benchmark_ece"}},
                        }
                    )
    return pd.DataFrame(rows)


def test_final_component_selection_is_complete_and_confirmatory() -> None:
    signal = select_final_signal_specification(inner_rows("signal"), "rsi", 1, 15, 0.0025)
    structural = select_final_structural_pipeline(inner_rows("structural"), "rsi", 1, 15, 0.0025, 0.01)
    calibration = select_final_calibration(inner_rows("calibration"), "rsi", 1, 15)
    policy = select_final_policy(inner_rows("policy"), "rsi", 1, 15, 0.1, 100)
    assert signal["signal_spec_id"].startswith("rsi-")
    assert structural["pipeline_id"] == "linear"
    assert calibration["calibration_method"] == "none"
    assert policy["threshold"] == 0.0


def test_pipeline_hash_is_deterministic() -> None:
    first = pipeline_hash({"b": 2, "a": 1})
    second = pipeline_hash({"a": 1, "b": 2})
    assert first == second
    assert len(first) == 64
