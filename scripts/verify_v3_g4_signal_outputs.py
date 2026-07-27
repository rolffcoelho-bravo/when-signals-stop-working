from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any


REQUIRED_OUTPUTS = (
    "signal_features.csv",
    "signal_registry_manifest.json",
    "signal_feature_manifest.json",
    "signal_coverage_report.json",
    "signal_validation_report.json",
    "canonical_validation_report.json",
)


class SignalOutputVerificationError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SignalOutputVerificationError(f"Expected JSON object: {path}")
    return value


def _csv_data_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None:
            raise SignalOutputVerificationError("signal_features.csv is empty")
        required = {
            "timestamp",
            "asset",
            "venue",
            "signal_id",
            "signal_family",
            "feature_value",
            "eligibility_status",
        }
        missing = required.difference(header)
        if missing:
            raise SignalOutputVerificationError(
                f"signal_features.csv is missing columns: {sorted(missing)}"
            )
        return sum(1 for _ in reader)


def verify(output_directory: str | Path) -> dict[str, Any]:
    output = Path(output_directory)
    if not output.is_dir():
        raise SignalOutputVerificationError(
            f"Gate V3-4 output directory does not exist: {output}"
        )

    missing = [name for name in REQUIRED_OUTPUTS if not (output / name).is_file()]
    if missing:
        raise SignalOutputVerificationError(
            f"Gate V3-4 evidence package is incomplete: {missing}"
        )

    manifest = _load_json(output / "signal_feature_manifest.json")
    validation = _load_json(output / "signal_validation_report.json")
    registry = _load_json(output / "signal_registry_manifest.json")
    canonical = _load_json(output / "canonical_validation_report.json")

    signal_count = int(manifest.get("signal_count", -1))
    source_rows = int(manifest.get("source_rows", -1))
    observed_rows = int(manifest.get("rows", -1))
    expected_rows = source_rows * signal_count

    if signal_count != 48:
        raise SignalOutputVerificationError(
            f"Unexpected registered signal count: {signal_count}"
        )
    if source_rows <= 0:
        raise SignalOutputVerificationError(
            f"Canonical source row count is invalid: {source_rows}"
        )
    if int(manifest.get("expected_rows", -1)) != expected_rows:
        raise SignalOutputVerificationError(
            "Manifest expected-row value does not match source_rows × signal_count"
        )
    if observed_rows != expected_rows:
        raise SignalOutputVerificationError(
            f"Feature-row identity failed: observed={observed_rows}, expected={expected_rows}"
        )
    if manifest.get("row_count_identity_verified") is not True:
        raise SignalOutputVerificationError(
            "Manifest does not confirm the feature-row identity"
        )

    actual_csv_rows = _csv_data_rows(output / "signal_features.csv")
    if actual_csv_rows != observed_rows:
        raise SignalOutputVerificationError(
            f"CSV row count differs from manifest: csv={actual_csv_rows}, manifest={observed_rows}"
        )

    if int(registry.get("signal_count", -1)) != 48:
        raise SignalOutputVerificationError(
            "Registry manifest does not contain 48 specifications"
        )
    definitions = registry.get("signal_definitions")
    if not isinstance(definitions, list) or len(definitions) != 48:
        raise SignalOutputVerificationError(
            "Registry manifest does not contain 48 complete signal definitions"
        )

    prohibited_false = (
        "automatic_selection_performed",
        "target_accessed",
        "chronology_accessed",
        "predictive_claims_produced",
        "economic_claims_produced",
        "deterioration_claims_produced",
        "failure_claims_produced",
    )
    for field in prohibited_false:
        if manifest.get(field) is not False:
            raise SignalOutputVerificationError(
                f"Gate V3-4 prohibited field is not false: {field}"
            )

    if validation.get("valid") is not True:
        raise SignalOutputVerificationError("Signal validation report is not valid")
    if validation.get("row_count_identity_verified") is not True:
        raise SignalOutputVerificationError(
            "Signal validation report does not confirm row identity"
        )
    if validation.get("next_gate") != "V3-5":
        raise SignalOutputVerificationError(
            f"Unexpected next gate: {validation.get('next_gate')}"
        )
    if canonical.get("valid") is not True:
        raise SignalOutputVerificationError(
            "Canonical input validation report is not valid"
        )

    result = {
        "source_rows": source_rows,
        "registered_signals": signal_count,
        "expected_feature_rows": expected_rows,
        "observed_feature_rows": observed_rows,
        "row_count_identity_verified": True,
        "automatic_selection_performed": False,
        "target_accessed": False,
        "chronology_accessed": False,
        "predictive_claims_produced": False,
        "economic_claims_produced": False,
        "deterioration_claims_produced": False,
        "failure_claims_produced": False,
        "next_gate": "V3-5",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the complete Gate V3-4 signal-engine evidence package."
    )
    parser.add_argument(
        "--output-directory",
        default="outputs/v3/signal_engine",
        help="Directory containing Gate V3-4 evidence outputs.",
    )
    arguments = parser.parse_args()
    result = verify(arguments.output_directory)
    print("Gate V3-4 output evidence verified.")
    for key, value in result.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, SignalOutputVerificationError) as error:
        print(f"Gate V3-4 output verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
