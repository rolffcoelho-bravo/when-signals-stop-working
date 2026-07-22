from __future__ import annotations

from itertools import product

import pandas as pd

from .registry import V2Registry


def _model_variants(registry: V2Registry) -> list[str]:
    return sorted(str(name) for name in registry.payload["model_families"])


def _window_variants(registry: V2Registry) -> list[str]:
    return sorted(str(name) for name in registry.payload["window_schemes"])


def _calibration_variants(registry: V2Registry) -> list[str]:
    return [str(value) for value in registry.payload["calibration"]["confirmatory_candidates"]]


def build_candidate_inventory(registry: V2Registry) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    common = product(
        registry.horizons,
        _model_variants(registry),
        _window_variants(registry),
        _calibration_variants(registry),
    )
    common_values = list(common)

    rsi = registry.payload["signal_grids"]["rsi"]
    for period, thresholds, interpretation, common_value in product(
        rsi["periods"],
        rsi["threshold_pairs"],
        rsi["interpretations"],
        common_values,
    ):
        horizon, model_family, window, calibration = common_value
        lower, upper = thresholds
        records.append(
            {
                "signal_family": "rsi",
                "horizon_candles": int(horizon),
                "horizon_hours": int(horizon) * 4,
                "interpretation": interpretation,
                "period": int(period),
                "lower_threshold": float(lower),
                "upper_threshold": float(upper),
                "standard_deviations": None,
                "model_family": model_family,
                "window_scheme": window,
                "calibration": calibration,
                "confirmatory_eligible": True,
            }
        )

    bollinger = registry.payload["signal_grids"]["bollinger"]
    for period, standard_deviations, interpretation, common_value in product(
        bollinger["periods"],
        bollinger["standard_deviations"],
        bollinger["interpretations"],
        common_values,
    ):
        horizon, model_family, window, calibration = common_value
        records.append(
            {
                "signal_family": "bollinger",
                "horizon_candles": int(horizon),
                "horizon_hours": int(horizon) * 4,
                "interpretation": interpretation,
                "period": int(period),
                "lower_threshold": None,
                "upper_threshold": None,
                "standard_deviations": float(standard_deviations),
                "model_family": model_family,
                "window_scheme": window,
                "calibration": calibration,
                "confirmatory_eligible": True,
            }
        )

    frame = pd.DataFrame.from_records(records)
    frame.insert(0, "candidate_id", [f"v2-candidate-{i:05d}" for i in range(1, len(frame) + 1)])
    return frame


def build_decision_policy_inventory(registry: V2Registry) -> pd.DataFrame:
    thresholds = registry.payload["abstention"][
        "direction_probability_distance_thresholds"
    ]
    records = [{"policy_id": "always_on", "probability_distance": 0.0}]
    records.extend(
        {
            "policy_id": f"abstain_{str(value).replace('.', '_')}",
            "probability_distance": float(value),
        }
        for value in thresholds
    )
    return pd.DataFrame.from_records(records)
