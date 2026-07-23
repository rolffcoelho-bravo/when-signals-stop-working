from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from .data_contract import CanonicalDataError, canonicalize_market_frame
from .spectral import (
    CausalFeatureConfig,
    PanelSpec,
    SpectralFeatureFrame,
    compute_spectral_feature_frame,
)


def _read_canonical_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError("Canonical input must be CSV or Parquet.")


def build_panel_spec(config: Mapping[str, Any]) -> PanelSpec:
    members = config.get("members")
    if not isinstance(members, (list, tuple)):
        raise ValueError("Spectral configuration requires explicit panel.members.")
    return PanelSpec(
        members=tuple(str(value) for value in members),
        dependence_windows=tuple(
            int(value) for value in config.get("dependence_windows", (30, 60, 120))
        ),
        minimum_complete_observations=int(
            config.get("minimum_complete_observations", 20)
        ),
        minimum_window_coverage=float(config.get("minimum_window_coverage", 0.80)),
        estimator=str(config.get("estimator", "sample")),
        ewma_decay=float(config.get("ewma_decay", 0.94)),
        shrinkage_alpha=float(config.get("shrinkage_alpha", 0.10)),
        network_threshold=float(config.get("network_threshold", 0.50)),
    )


def build_causal_feature_config(
    config: Mapping[str, Any] | None,
) -> CausalFeatureConfig:
    values = config or {}
    return CausalFeatureConfig(
        volatility_windows=tuple(
            int(value) for value in values.get("volatility_windows", (6, 18, 42))
        ),
        stress_window=int(values.get("stress_window", 42)),
        volume_window=int(values.get("volume_window", 42)),
    )


def run_spectral_features(
    config: Mapping[str, Any],
    output_directory: str | Path,
) -> SpectralFeatureFrame:
    input_value = str(config.get("input_path", "")).strip()
    if not input_value:
        raise ValueError("Configuration requires input_path.")
    input_path = Path(input_value)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    panel_config = config.get("panel")
    if not isinstance(panel_config, Mapping):
        raise ValueError("Configuration requires a panel mapping.")
    feature_config = config.get("causal_features")
    if feature_config is not None and not isinstance(feature_config, Mapping):
        raise ValueError("causal_features must be a mapping.")

    source = _read_canonical_file(input_path)
    canonical, validation = canonicalize_market_frame(
        source,
        timezone=str(config.get("timezone", "UTC")),
        timestamp_unit=config.get("timestamp_unit"),
    )
    if not validation.valid:
        critical = "; ".join(
            f"{issue.code}: {issue.message}"
            for issue in validation.issues
            if issue.severity == "CRITICAL"
        )
        raise CanonicalDataError(critical or "Canonical input validation failed.")

    result = compute_spectral_feature_frame(
        canonical,
        build_panel_spec(panel_config),
        build_causal_feature_config(feature_config),
    )
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    result.frame.to_csv(output / "spectral_market_structure.csv", index=False)
    result.series_features.to_csv(output / "causal_series_features.csv", index=False)
    (output / "spectral_manifest.json").write_text(
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
    (output / "spectral_diagnostics.json").write_text(
        json.dumps(result.diagnostics, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    (output / "canonical_validation_report.json").write_text(
        json.dumps(validation.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result
