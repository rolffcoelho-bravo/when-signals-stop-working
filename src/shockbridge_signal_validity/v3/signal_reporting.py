from __future__ import annotations
from hashlib import sha256
import json
from typing import Any, Mapping
import pandas as pd
from .data_contract import REQUIRED_COLUMNS, stable_frame_hash
from .signal_registry import SignalSpec, build_registry_manifest, registry_sha256


def stable_mapping_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return sha256(payload).hexdigest()


def build_reports(data: pd.DataFrame, output: pd.DataFrame, registry: Mapping[str, Any],
                  specs: tuple[SignalSpec, ...], statuses: Mapping[str, pd.Series],
                  context_columns: tuple[str, ...], parameter_count: int):
    coverage = {}
    for spec in specs:
        counts = statuses[spec.signal_id].value_counts(dropna=False).sort_index()
        eligible = int(counts.get("ELIGIBLE", 0))
        coverage[spec.signal_id] = {
            "signal_family": spec.signal_family,
            "interpretation": spec.interpretation,
            "parameter_policy": spec.parameter_policy,
            "regime_interaction_policy": spec.regime_interaction_policy,
            "rows": len(data), "eligible_rows": eligible,
            "eligible_share": float(eligible / len(data)) if len(data) else 0.0,
            "status_counts": {str(k): int(v) for k, v in counts.items()},
        }
    registry_manifest = build_registry_manifest(registry)
    feature_manifest = {
        "schema_version": "v3.signal-feature-manifest.v1",
        "feature_schema_version": "v3.signal-features.v1",
        "input_sha256": stable_frame_hash(data[list(REQUIRED_COLUMNS)]),
        "registry_sha256": registry_sha256(registry),
        "output_sha256": stable_frame_hash(output),
        "rows": len(output), "source_rows": len(data),
        "timestamps": int(data["timestamp"].nunique()),
        "assets": sorted(map(str, data["asset"].unique())),
        "venues": sorted(map(str, data["venue"].unique())),
        "signal_count": len(specs),
        "context_columns_available": list(context_columns),
        "training_only_parameter_sets_supplied": parameter_count,
        "automatic_selection_performed": False, "target_accessed": False,
        "chronology_accessed": False, "predictive_claims_produced": False,
        "economic_claims_produced": False, "deterioration_claims_produced": False,
        "failure_claims_produced": False,
        "frozen_v1_v2_determinations_modified": False,
    }
    feature_manifest["manifest_sha256"] = stable_mapping_hash(feature_manifest)
    coverage_report = {
        "schema_version": "v3.signal-coverage.v1", "source_rows": len(data),
        "signal_count": len(specs), "signals": coverage,
        "automatic_candidate_deletion_performed": False,
    }
    coverage_report["report_sha256"] = stable_mapping_hash(coverage_report)
    validation = {
        "schema_version": "v3.signal-validation.v1", "valid": True, "gate": "V3-4",
        "required_columns_verified": list(REQUIRED_COLUMNS),
        "input_columns_accessed": list(REQUIRED_COLUMNS), "target_columns_accessed": [],
        "target_accessed": False, "chronology_accessed": False,
        "automatic_signal_selection_performed": False,
        "automatic_threshold_selection_performed": False,
        "adaptive_parameters_estimated_by_engine": False,
        "interaction_components_preserved": True, "future_information_accessed": False,
        "predictive_claims_produced": False, "economic_claims_produced": False,
        "deterioration_claims_produced": False, "failure_claims_produced": False,
        "next_gate": "V3-5",
        "richard_question_advanced_by": "DEFINES_SIGNAL_INFORMATION_TO_BE_TESTED",
    }
    validation["report_sha256"] = stable_mapping_hash(validation)
    return registry_manifest, feature_manifest, coverage_report, validation
