from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "v2" / "development"
OUTPUT = ROOT / "outputs" / "v2" / "development"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    required = [
        PROCESSED / "d2c_family_horizon_admission.csv",
        PROCESSED / "d2c_family_decisions.csv",
        PROCESSED / "d2c_component_selection_audit.csv",
        PROCESSED / "d2c_frozen_pipeline_registry.json",
        PROCESSED / "d2c_admission_manifest.json",
        OUTPUT / "d2c_holdout_authorization.json",
        OUTPUT / "d2c_admission_status.json",
    ]
    missing = [path.as_posix() for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Missing D2C assets: " + ", ".join(missing))

    status = json.loads((OUTPUT / "d2c_admission_status.json").read_text(encoding="utf-8"))
    if status["status"] != "PASS":
        raise RuntimeError("D2C status is not PASS.")
    if int(status["family_horizon_rows"]) != 8 or int(status["family_decision_rows"]) != 2:
        raise RuntimeError("D2C context counts are invalid.")
    if int(status["admitted_families"]) + int(status["rejected_families"]) != 2:
        raise RuntimeError("D2C family-decision counts are inconsistent.")
    if status["development_admission_evaluated"] is not True:
        raise RuntimeError("D2C did not report development admission.")
    if status["family_level_pipeline_freeze_completed"] is not True:
        raise RuntimeError("D2C did not report pipeline-freeze completion.")
    if status["predictive_model_fitting_performed"] is not False:
        raise RuntimeError("D2C incorrectly reports predictive fitting.")
    if status["economic_gate_evaluated"] is not False:
        raise RuntimeError("D2C incorrectly reports the economic gate.")
    if status["holdout_authorization_enabled"] is not False:
        raise RuntimeError("D2C incorrectly authorizes holdout access.")
    if status["holdout_performance_accessed"] is not False:
        raise RuntimeError("D2C incorrectly reports holdout access.")

    admission = pd.read_csv(PROCESSED / "d2c_family_horizon_admission.csv")
    if len(admission) != 8 or admission.duplicated(["signal_family", "horizon_candles"]).any():
        raise RuntimeError("D2C family-horizon admission rows are invalid.")
    if set(admission["signal_family"]) != {"rsi", "bollinger"}:
        raise RuntimeError("D2C confirmatory families are invalid.")
    if admission["economic_gate_evaluated"].astype(bool).any():
        raise RuntimeError("D2C admission rows incorrectly report economic evaluation.")
    if admission["holdout_evidence_used"].astype(bool).any():
        raise RuntimeError("D2C admission rows incorrectly report holdout evidence.")

    decisions = pd.read_csv(PROCESSED / "d2c_family_decisions.csv")
    if len(decisions) != 2 or set(decisions["signal_family"]) != {"rsi", "bollinger"}:
        raise RuntimeError("D2C family decisions are invalid.")
    allowed = {
        "NO_PIPELINE_ADMITTED",
        "PIPELINE_ADMITTED_FOR_METHODOLOGY_LOCKED_EVALUATION",
    }
    if not set(decisions["family_decision"]).issubset(allowed):
        raise RuntimeError("D2C contains an invalid family decision.")

    registry_path = PROCESSED / "d2c_frozen_pipeline_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    pipelines = registry["frozen_pipelines"]
    admitted = decisions["pipeline_admitted"].astype(bool)
    if len(pipelines) != int(admitted.sum()):
        raise RuntimeError("D2C frozen-pipeline count does not match admitted families.")
    if int(status["frozen_pipeline_count"]) != len(pipelines):
        raise RuntimeError("D2C status frozen-pipeline count is inconsistent.")
    hashes = []
    for pipeline in pipelines:
        value = str(pipeline.get("pipeline_hash", ""))
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise RuntimeError("D2C contains an invalid pipeline hash.")
        if pipeline["calibration_method"] not in {"none", "sigmoid"}:
            raise RuntimeError("D2C froze a diagnostic-only calibration method.")
        if pipeline["economic_gate_evaluated"] is not False or pipeline["holdout_performance_accessed"] is not False:
            raise RuntimeError("D2C pipeline governance flags are invalid.")
        hashes.append(value)
    if len(hashes) != len(set(hashes)):
        raise RuntimeError("D2C pipeline hashes are duplicated.")

    components = pd.read_csv(PROCESSED / "d2c_component_selection_audit.csv")
    expected_components = 4 * len(pipelines)
    if len(components) != expected_components:
        raise RuntimeError("D2C component-audit count is invalid.")
    if not components.empty and set(components["component"]) != {
        "SIGNAL_SPECIFICATION",
        "STRUCTURAL_PIPELINE",
        "CALIBRATION",
        "DECISION_POLICY",
    }:
        raise RuntimeError("D2C component-audit categories are invalid.")

    authorization = json.loads((OUTPUT / "d2c_holdout_authorization.json").read_text(encoding="utf-8"))
    if authorization["authorized"] is not False or authorization["holdout_performance_accessed"] is not False:
        raise RuntimeError("D2C holdout authorization is invalid.")

    manifest = json.loads((PROCESSED / "d2c_admission_manifest.json").read_text(encoding="utf-8"))
    if sha256(registry_path) != status["pipeline_registry_sha256"]:
        raise RuntimeError("D2C pipeline-registry checksum is invalid.")
    if sha256(PROCESSED / "d2c_admission_manifest.json") != status["manifest_sha256"]:
        raise RuntimeError("D2C manifest checksum is invalid.")
    for record in manifest["files"]:
        path = ROOT / record["path"]
        if not path.exists() or sha256(path) != record["sha256"]:
            raise RuntimeError(f"D2C generated-file checksum mismatch: {record['path']}")

    holdout_root = ROOT / "outputs" / "v2" / "holdout"
    holdout_files = [path for path in holdout_root.rglob("*") if path.is_file()] if holdout_root.exists() else []
    if holdout_files:
        raise RuntimeError("Unauthorized holdout files exist.")

    print("V2 D2C asset verification passed.")
    print(f"Family-horizon rows: {len(admission):,}")
    print(f"Admitted families: {int(admitted.sum()):,}")
    print(f"Frozen pipelines: {len(pipelines):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
