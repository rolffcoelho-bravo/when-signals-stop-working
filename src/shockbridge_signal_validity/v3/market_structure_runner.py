from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from .data_contract import CanonicalDataError, canonicalize_market_frame
from .market_structure import (
    MarketStructureFeatureFrame,
    NetworkSpec,
    compute_market_structure_feature_frame,
)
from .spectral_runner import build_causal_feature_config, build_panel_spec


def _read_canonical_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError("Canonical input must be CSV or Parquet.")


def build_network_spec(config: Mapping[str, Any] | None) -> NetworkSpec:
    values = config or {}
    return NetworkSpec(
        threshold=float(values.get("threshold", 0.50)),
        use_absolute_threshold=bool(values.get("use_absolute_threshold", True)),
        community_resolution=float(values.get("community_resolution", 1.0)),
        dynamic_window=int(values.get("dynamic_window", 5)),
    )


def run_market_structure(
    config: Mapping[str, Any],
    output_directory: str | Path,
) -> MarketStructureFeatureFrame:
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
    network_config = config.get("network")
    if network_config is not None and not isinstance(network_config, Mapping):
        raise ValueError("network must be a mapping.")

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

    result = compute_market_structure_feature_frame(
        canonical,
        build_panel_spec(panel_config),
        build_causal_feature_config(feature_config),
        build_network_spec(network_config),
    )
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    result.frame.to_csv(output / "market_structure_features.csv", index=False)
    result.series_features.to_csv(output / "causal_series_features.csv", index=False)
    (output / "market_structure_manifest.json").write_text(
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
    (output / "market_structure_diagnostics.json").write_text(
        json.dumps(result.diagnostics, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    (output / "canonical_validation_report.json").write_text(
        json.dumps(validation.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result
