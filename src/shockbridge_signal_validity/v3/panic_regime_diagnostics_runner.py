from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data_contract import stable_mapping_hash
from .panic_regime_diagnostics import compute_panic_regime_governance
from .panic_regime_governance_base import (
    FAMILY_ORDER,
    PanicRegimeDiagnosticsConfig,
    PanicRegimeDiagnosticsResult,
)


def _read_frame(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported diagnostics input format: {path}")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON input must contain an object: {path}")
    return value


def build_diagnostics_config(config: Mapping[str, Any]) -> PanicRegimeDiagnosticsConfig:
    threshold_values = config.get(
        "threshold_sensitivity",
        [[0.20, 0.45, 0.70], [0.25, 0.50, 0.75], [0.30, 0.55, 0.80]],
    )
    ewma_values = config.get("ewma_alpha_sensitivity", [0.20, 0.35, 0.50])
    return PanicRegimeDiagnosticsConfig(
        bootstrap_replications=int(config.get("bootstrap_replications", 250)),
        minimum_valid_bootstrap_replications=int(
            config.get("minimum_valid_bootstrap_replications", 200)
        ),
        minimum_interval_history=int(config.get("minimum_interval_history", 30)),
        bootstrap_history_window=int(config.get("bootstrap_history_window", 500)),
        interval_coverage=float(config.get("interval_coverage", 0.95)),
        innovation_location_alpha=float(
            config.get("innovation_location_alpha", 0.20)
        ),
        transition_dirichlet_alpha=float(
            config.get("transition_dirichlet_alpha", 1.0)
        ),
        state_confirmation_observations=int(
            config.get("state_confirmation_observations", 2)
        ),
        minimum_episode_observations=int(
            config.get("minimum_episode_observations", 2)
        ),
        minimum_state_occupancy_fraction=float(
            config.get("minimum_state_occupancy_fraction", 0.05)
        ),
        minimum_state_occupancy_count=int(
            config.get("minimum_state_occupancy_count", 20)
        ),
        monotone_logistic_slope=float(
            config.get("monotone_logistic_slope", 6.0)
        ),
        central_monotone_ewma_alpha=float(
            config.get("central_monotone_ewma_alpha", 0.35)
        ),
        ewma_alpha_sensitivity=tuple(float(value) for value in ewma_values),
        threshold_sensitivity=tuple(
            tuple(float(value) for value in row) for row in threshold_values
        ),
        disagreement_moderate_threshold=float(
            config.get("disagreement_moderate_threshold", 0.15)
        ),
        disagreement_high_threshold=float(
            config.get("disagreement_high_threshold", 0.30)
        ),
        contribution_minimum_history=int(
            config.get("contribution_minimum_history", 60)
        ),
        contribution_refit_interval=int(
            config.get("contribution_refit_interval", 30)
        ),
        contribution_ridge_penalty=float(
            config.get("contribution_ridge_penalty", 1.0)
        ),
        scaling_refit_interval=int(config.get("scaling_refit_interval", 30)),
        scaling_minimum_prior_observations=int(
            config.get("scaling_minimum_prior_observations", 250)
        ),
        random_seed=int(config.get("random_seed", 1729)),
    )


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _coverage_heatmap(coverage: pd.DataFrame, output_path: Path) -> None:
    admitted = coverage.loc[~coverage["governed_exclusion"].astype(bool)].copy()
    grouped = (
        admitted.groupby(["timestamp", "family"], sort=True)["available"]
        .mean()
        .unstack("family")
        .reindex(columns=list(FAMILY_ORDER))
    )
    if grouped.empty:
        raise ValueError("Coverage heatmap requires admitted coverage rows.")
    maximum_columns = 500
    if len(grouped) > maximum_columns:
        bins = np.floor(
            np.arange(len(grouped)) * maximum_columns / len(grouped)
        ).astype(int)
        grouped = grouped.groupby(bins, sort=True).mean()
    matrix = grouped.to_numpy(dtype=float).T
    matplotlib.rcParams["svg.hashsalt"] = "wssw-v3-g3c"
    figure, axis = plt.subplots(figsize=(12, 4.5))
    image = axis.imshow(matrix, aspect="auto", vmin=0.0, vmax=1.0)
    axis.set_yticks(np.arange(len(FAMILY_ORDER)))
    axis.set_yticklabels(FAMILY_ORDER)
    axis.set_xlabel("Causal time bins")
    axis.set_ylabel("Mechanism family")
    axis.set_title("Mechanism Evidence Coverage")
    figure.colorbar(image, ax=axis, label="Available share")
    figure.tight_layout()
    figure.savefig(
        output_path,
        format="svg",
        metadata={"Date": None, "Creator": "ShockBridge Pulse Research"},
    )
    plt.close(figure)


def run_panic_regime_diagnostics(
    config: Mapping[str, Any],
    output_directory: str | Path,
) -> PanicRegimeDiagnosticsResult:
    engine_output_value = str(config.get("engine_output_directory", "")).strip()
    market_value = str(config.get("market_structure_path", "")).strip()
    series_value = str(config.get("causal_series_path", "")).strip()
    if not engine_output_value or not market_value or not series_value:
        raise ValueError(
            "Configuration requires engine_output_directory, market_structure_path, "
            "and causal_series_path."
        )
    engine_output = Path(engine_output_value)
    market_path = Path(market_value)
    series_path = Path(series_value)
    required_engine_files = {
        "panic_regime_probability.csv",
        "mechanism_family_scores.csv",
        "regime_manifest.json",
        "probability_engine_diagnostics.json",
    }
    missing = sorted(
        name for name in required_engine_files if not (engine_output / name).exists()
    )
    if missing:
        raise FileNotFoundError(
            "V3-3B engine output is incomplete: " + ", ".join(missing)
        )
    if not market_path.exists():
        raise FileNotFoundError(market_path)
    if not series_path.exists():
        raise FileNotFoundError(series_path)

    diagnostics_config_value = config.get("diagnostics")
    if not isinstance(diagnostics_config_value, Mapping):
        raise ValueError("Configuration requires a diagnostics mapping.")
    diagnostics_config = build_diagnostics_config(diagnostics_config_value)
    parent_manifest = _read_json(engine_output / "regime_manifest.json")
    engine_config_value = config.get("engine")
    if isinstance(engine_config_value, Mapping):
        expected_hash = str(parent_manifest.get("configuration_sha256", ""))
        observed_hash = stable_mapping_hash(dict(engine_config_value))
        if expected_hash and expected_hash != observed_hash:
            raise ValueError(
                "Embedded engine configuration does not match the locked V3-3B manifest."
            )

    result = compute_panic_regime_governance(
        _read_frame(engine_output / "panic_regime_probability.csv"),
        _read_frame(engine_output / "mechanism_family_scores.csv"),
        _read_frame(market_path),
        _read_frame(series_path),
        _read_json(engine_output / "probability_engine_diagnostics.json"),
        parent_manifest,
        diagnostics_config,
    )

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    result.probabilities.to_csv(output / "panic_regime_probability.csv", index=False)
    result.state_duration.to_csv(output / "state_duration.csv", index=False)
    result.mechanism_contributions.to_csv(
        output / "mechanism_contributions.csv", index=False
    )
    result.disagreement.to_csv(
        output / "cross_model_disagreement.csv", index=False
    )
    result.coverage.to_csv(output / "mechanism_coverage.csv", index=False)
    _write_json(output / "transition_matrix.json", result.transition_matrix)
    _write_json(output / "occupancy_statistics.json", result.occupancy_statistics)
    _write_json(
        output / "mechanism_coverage_summary.json", result.coverage_summary
    )
    _write_json(output / "sensitivity_diagnostics.json", result.sensitivity)
    _write_json(output / "probability_diagnostics.json", result.diagnostics)
    _write_json(
        output / "regime_validation_report.json", result.validation_report
    )
    _coverage_heatmap(
        result.coverage, output / "mechanism_coverage_heatmap.svg"
    )
    _write_json(
        output / "regime_manifest.json",
        {
            **result.manifest.to_dict(),
            "manifest_sha256": result.manifest.manifest_sha256,
            "visual_outputs": ["mechanism_coverage_heatmap.svg"],
        },
    )
    return result
