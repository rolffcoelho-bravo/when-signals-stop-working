from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from .panic_regime import (
    PanicRegimeConfig,
    PanicRegimeFeatureFrame,
    compute_panic_regime_probabilities,
)


def _read_feature_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError("Regime-engine input must be CSV or Parquet.")


def build_panic_regime_config(config: Mapping[str, Any]) -> PanicRegimeConfig:
    return PanicRegimeConfig(
        dependence_window=int(config["dependence_window"]),
        reference_series_id=str(config["reference_series_id"]),
        minimum_prior_observations=int(
            config.get("minimum_prior_observations", 250)
        ),
        scaling_refit_interval=int(config.get("scaling_refit_interval", 30)),
        minimum_available_mechanism_families=int(
            config.get("minimum_available_mechanism_families", 4)
        ),
        minimum_valid_feature_fraction=float(
            config.get("minimum_valid_feature_fraction", 0.50)
        ),
        minimum_features_per_family=int(
            config.get("minimum_features_per_family", 2)
        ),
        monotone_logistic_slope=float(
            config.get("monotone_logistic_slope", 6.0)
        ),
        monotone_ewma_alpha=float(config.get("monotone_ewma_alpha", 0.35)),
        challenger_minimum_history=int(
            config.get("challenger_minimum_history", 250)
        ),
        hmm_minimum_history=int(config.get("hmm_minimum_history", 500)),
        hmm_refit_interval=int(config.get("hmm_refit_interval", 30)),
        hmm_max_iter=int(config.get("hmm_max_iter", 20)),
        hmm_tolerance=float(config.get("hmm_tolerance", 1e-6)),
        covariance_floor=float(config.get("covariance_floor", 1e-4)),
        transition_smoothing=float(config.get("transition_smoothing", 1.0)),
        minimum_state_occupancy_fraction=float(
            config.get("minimum_state_occupancy_fraction", 0.05)
        ),
        minimum_state_occupancy_count=int(
            config.get("minimum_state_occupancy_count", 20)
        ),
        random_seed=int(config.get("random_seed", 1729)),
    )


def run_panic_regime_engine(
    config: Mapping[str, Any],
    output_directory: str | Path,
) -> PanicRegimeFeatureFrame:
    market_value = str(config.get("market_structure_path", "")).strip()
    series_value = str(config.get("causal_series_path", "")).strip()
    if not market_value or not series_value:
        raise ValueError(
            "Configuration requires market_structure_path and causal_series_path."
        )
    market_path = Path(market_value)
    series_path = Path(series_value)
    if not market_path.exists():
        raise FileNotFoundError(market_path)
    if not series_path.exists():
        raise FileNotFoundError(series_path)

    engine_config = config.get("engine")
    if not isinstance(engine_config, Mapping):
        raise ValueError("Configuration requires an engine mapping.")

    result = compute_panic_regime_probabilities(
        _read_feature_file(market_path),
        _read_feature_file(series_path),
        build_panic_regime_config(engine_config),
    )
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)

    result.probabilities.to_csv(
        output / "panic_regime_probability.csv",
        index=False,
    )
    result.mechanism_scores.to_csv(
        output / "mechanism_family_scores.csv",
        index=False,
    )
    (output / "regime_manifest.json").write_text(
        json.dumps(
            {
                **result.manifest.to_dict(),
                "manifest_sha256": result.manifest.manifest_sha256,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output / "regime_validation_report.json").write_text(
        json.dumps(
            {
                "schema_version": result.manifest.schema_version,
                "status": "IMPLEMENTATION_COMPLETE_UNCERTAINTY_AND_GOVERNANCE_PENDING",
                "probability_rows": int(len(result.probabilities)),
                "timestamps": int(result.probabilities["timestamp"].nunique()),
                "registered_models": list(result.manifest.model_ids),
                "automatic_model_selection_performed": False,
                "automatic_ensemble_performed": False,
                "uncertainty_intervals_complete": False,
                "transition_diagnostics_complete": False,
                "duration_and_occupancy_outputs_complete": False,
                "mechanism_contribution_decomposition_complete": False,
                "final_v3_3_lock_permitted": False,
                "next_subgate": "V3-3C — Governance and Diagnostics",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output / "probability_engine_diagnostics.json").write_text(
        json.dumps(
            result.diagnostics,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    return result
