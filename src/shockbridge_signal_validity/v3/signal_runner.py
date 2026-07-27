from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from .data_contract import CanonicalDataError, canonicalize_market_frame
from .signal_engine import SignalFeatureFrame, compute_signal_feature_frame
from .signal_registry import load_registry


def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError("Signal-engine input must be CSV or Parquet.")


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, default=str, ensure_ascii=True)
        + "\n"
    ).encode("utf-8")


def run_signal_engine(
    config: Mapping[str, Any],
    output_directory: str | Path,
) -> SignalFeatureFrame:
    input_value = str(config.get("input_path", "")).strip()
    if not input_value:
        raise ValueError("Signal-engine configuration requires input_path.")
    input_path = Path(input_value)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    registry_value = str(config.get("registry_path", "")).strip()
    if not registry_value:
        raise ValueError("Signal-engine configuration requires registry_path.")
    registry_path = Path(registry_value)
    if not registry_path.exists():
        raise FileNotFoundError(registry_path)

    source = _read_table(input_path)
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

    context_frame = None
    context_value = str(config.get("context_path", "")).strip()
    if context_value:
        context_path = Path(context_value)
        if not context_path.exists():
            raise FileNotFoundError(context_path)
        context_frame = _read_table(context_path)

    parameters = config.get("training_only_parameters", {})
    if not isinstance(parameters, Mapping):
        raise ValueError("training_only_parameters must be a mapping.")

    registry = load_registry(registry_path)
    result = compute_signal_feature_frame(
        canonical,
        registry,
        training_only_parameters=parameters,
        context_frame=context_frame,
    )

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    csv_payload = result.frame.to_csv(index=False, lineterminator="\n").encode("utf-8")
    (output / "signal_features.csv").write_bytes(csv_payload)
    (output / "signal_registry_manifest.json").write_bytes(
        _json_bytes(result.registry_manifest)
    )
    (output / "signal_feature_manifest.json").write_bytes(
        _json_bytes(result.feature_manifest)
    )
    (output / "signal_coverage_report.json").write_bytes(
        _json_bytes(result.coverage_report)
    )
    (output / "signal_validation_report.json").write_bytes(
        _json_bytes(result.validation_report)
    )
    (output / "canonical_validation_report.json").write_bytes(
        _json_bytes(validation.to_dict())
    )
    return result
