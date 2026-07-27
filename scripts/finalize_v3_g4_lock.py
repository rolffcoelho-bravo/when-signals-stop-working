from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATED_IMPLEMENTATION_COMMIT = "ff2e7ecba3fa69f22e0b109437d23b52d30fba2b"
LOCK_PATH = ROOT / "V3_G4_SIGNAL_ENGINE_LOCK.json"
EVIDENCE_DIRECTORY = ROOT / "evidence" / "v3" / "g4_signal_lock"

PROTECTED_FILES = (
    "configs/v3_adapter_frozen_sol.json",
    "configs/v3_signal_engine_example.json",
    "configs/v3_signal_interpretation_registry.json",
    "src/shockbridge_signal_validity/v3/signal_math.py",
    "src/shockbridge_signal_validity/v3/signal_rsi.py",
    "src/shockbridge_signal_validity/v3/signal_bollinger.py",
    "src/shockbridge_signal_validity/v3/signal_registry.py",
    "src/shockbridge_signal_validity/v3/signal_reporting.py",
    "src/shockbridge_signal_validity/v3/signal_engine.py",
    "src/shockbridge_signal_validity/v3/signal_runner.py",
    "scripts/run_v3_signal_engine.py",
    "scripts/verify_v3_g1_data_adapter.py",
    "scripts/verify_v3_g4_signal_outputs.py",
    "tests/test_v3_signal_registry.py",
    "tests/test_v3_signal_engine.py",
    "tests/test_v3_signal_runner.py",
    "RUN_V3_G4_SIGNAL_ENGINE.ps1",
    "RUN_V3_G4_SIGNAL_ENGINE.sh",
)

RUNTIME_FILES = {
    "canonical_market_data": ROOT / "outputs/v3/data_adapter/canonical_market_data.csv",
    "canonical_source_manifest": ROOT / "outputs/v3/data_adapter/source_manifest.json",
    "canonical_validation_report": ROOT / "outputs/v3/data_adapter/validation_report.json",
    "signal_features": ROOT / "outputs/v3/signal_engine/signal_features.csv",
    "signal_registry_manifest": ROOT / "outputs/v3/signal_engine/signal_registry_manifest.json",
    "signal_feature_manifest": ROOT / "outputs/v3/signal_engine/signal_feature_manifest.json",
    "signal_coverage_report": ROOT / "outputs/v3/signal_engine/signal_coverage_report.json",
    "signal_validation_report": ROOT / "outputs/v3/signal_engine/signal_validation_report.json",
    "signal_canonical_validation_report": ROOT / "outputs/v3/signal_engine/canonical_validation_report.json",
}

CURATED_FILES = {
    "canonical_source_manifest": "canonical_source_manifest.json",
    "canonical_validation_report": "canonical_validation_report.json",
    "signal_registry_manifest": "signal_registry_manifest.json",
    "signal_feature_manifest": "signal_feature_manifest.json",
    "signal_coverage_report": "signal_coverage_report.json",
    "signal_validation_report": "signal_validation_report.json",
    "signal_canonical_validation_report": "signal_canonical_validation_report.json",
}


def run(command: list[str], *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=capture,
        text=True,
    )


def require_success(command: list[str], label: str) -> subprocess.CompletedProcess[str]:
    completed = run(command)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"{label} failed: {detail}")
    return completed


def git_object_sha(commit: str, relative_path: str) -> str:
    completed = require_success(
        ["git", "rev-parse", f"{commit}:{relative_path}"],
        f"Resolve Git object {relative_path}",
    )
    return completed.stdout.strip()


def current_head() -> str:
    return require_success(["git", "rev-parse", "HEAD"], "Resolve HEAD").stdout.strip()


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_clean_tracked_worktree() -> None:
    completed = run(["git", "diff", "--quiet", "--"])
    if completed.returncode != 0:
        raise RuntimeError(
            "Tracked working tree is not clean. Commit or restore tracked changes before lock finalization."
        )


def require_validated_boundary() -> None:
    require_success(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            VALIDATED_IMPLEMENTATION_COMMIT,
            "HEAD",
        ],
        "Validated V3-4 boundary ancestry",
    )
    drift: list[str] = []
    for relative in PROTECTED_FILES:
        validated_sha = git_object_sha(VALIDATED_IMPLEMENTATION_COMMIT, relative)
        current_sha = git_object_sha("HEAD", relative)
        if current_sha != validated_sha:
            drift.append(
                f"{relative}: validated={validated_sha} current={current_sha}"
            )
    if drift:
        raise RuntimeError(
            "Protected V3-4 implementation drifted after authoritative validation:\n"
            + "\n".join(drift)
        )


def require_runtime_files() -> None:
    missing = [str(path.relative_to(ROOT)) for path in RUNTIME_FILES.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Required authoritative V3-4 runtime evidence is missing:\n" + "\n".join(missing)
        )


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def validate_evidence() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    require_success(
        [
            sys.executable,
            "scripts/verify_v3_g4_signal_outputs.py",
            "--output-directory",
            "outputs/v3/signal_engine",
        ],
        "Gate V3-4 output verifier",
    )

    feature = read_json(RUNTIME_FILES["signal_feature_manifest"])
    registry = read_json(RUNTIME_FILES["signal_registry_manifest"])
    validation = read_json(RUNTIME_FILES["signal_validation_report"])
    canonical = read_json(RUNTIME_FILES["canonical_validation_report"])

    expected_rows = int(feature["source_rows"]) * int(feature["signal_count"])
    if int(feature["source_rows"]) != 12171:
        raise RuntimeError("Unexpected frozen SOL source-row count.")
    if int(feature["signal_count"]) != 48:
        raise RuntimeError("Unexpected registered signal count.")
    if int(feature["rows"]) != 584208 or int(feature["rows"]) != expected_rows:
        raise RuntimeError("Gate V3-4 feature-row identity changed.")
    if feature.get("row_count_identity_verified") is not True:
        raise RuntimeError("Gate V3-4 row-count identity is not verified.")
    if int(registry.get("signal_count", -1)) != 48:
        raise RuntimeError("Registry manifest does not contain 48 signals.")
    definitions = registry.get("signal_definitions")
    if not isinstance(definitions, list) or len(definitions) != 48:
        raise RuntimeError("Registry manifest does not contain 48 definitions.")
    if canonical.get("valid") is not True:
        raise RuntimeError("Canonical validation report is not valid.")
    if validation.get("next_gate") != "V3-5":
        raise RuntimeError("Signal validation report does not advance to V3-5.")

    for field in (
        "automatic_selection_performed",
        "target_accessed",
        "chronology_accessed",
        "predictive_claims_produced",
        "economic_claims_produced",
        "deterioration_claims_produced",
        "failure_claims_produced",
    ):
        if feature.get(field) is not False:
            raise RuntimeError(f"Prohibited Gate V3-4 action changed: {field}")

    return feature, registry, validation


def curate_evidence() -> dict[str, str]:
    if EVIDENCE_DIRECTORY.exists():
        shutil.rmtree(EVIDENCE_DIRECTORY)
    EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    for key, output_name in CURATED_FILES.items():
        source = RUNTIME_FILES[key]
        destination = EVIDENCE_DIRECTORY / output_name
        destination.write_bytes(source.read_bytes())
        hashes[str(destination.relative_to(ROOT))] = sha256_file(destination)
    return hashes


def build_lock(
    feature: dict[str, Any],
    registry: dict[str, Any],
    validation: dict[str, Any],
    curated_hashes: dict[str, str],
) -> dict[str, Any]:
    protected = {
        relative: git_object_sha(VALIDATED_IMPLEMENTATION_COMMIT, relative)
        for relative in PROTECTED_FILES
    }
    runtime_hashes = {
        key: {
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_file(path),
        }
        for key, path in RUNTIME_FILES.items()
    }
    return {
        "gate": "V3-4",
        "schema_version": "v3.signal-engine-lock.v1",
        "status": "LOCK_CANDIDATE_AWAITING_REPOSITORY_REVIEW",
        "branch": "research/v3-adaptive-signal-validity",
        "baseline_release": "v2.0.0",
        "baseline_commit": "5a07299367b80c3940e652e7bbdd208ce86ba5ef",
        "parent_gate": "V3-1",
        "parent_lock": "V3_G1_DATA_ADAPTER_LOCK.json",
        "parent_historical_boundary_commit": "7a7a5c55184aadfb436774ff1e497ce873a96b6e",
        "validated_implementation_commit": VALIDATED_IMPLEMENTATION_COMMIT,
        "lock_preparation_commit": current_head(),
        "protected_files": protected,
        "runtime_evidence": runtime_hashes,
        "curated_evidence_sha256": curated_hashes,
        "acceptance_evidence": {
            "repository_realignment_tests_passed": 7,
            "exact_hardened_signal_tests_passed": 19,
            "canonical_source_rows": int(feature["source_rows"]),
            "registered_signal_count": int(feature["signal_count"]),
            "expected_feature_rows": int(feature["expected_rows"]),
            "observed_feature_rows": int(feature["rows"]),
            "row_count_identity_verified": feature["row_count_identity_verified"],
            "registry_definition_count": len(registry["signal_definitions"]),
            "canonical_data_sha256": "3c49bfcab5fdf3aba9ada614873fa424e97c1f66e2690b790204fc29fdb5109c",
            "automatic_selection_performed": feature["automatic_selection_performed"],
            "target_accessed": feature["target_accessed"],
            "chronology_accessed": feature["chronology_accessed"],
            "predictive_claims_produced": feature["predictive_claims_produced"],
            "economic_claims_produced": feature["economic_claims_produced"],
            "deterioration_claims_produced": feature["deterioration_claims_produced"],
            "failure_claims_produced": feature["failure_claims_produced"],
            "next_gate": validation["next_gate"],
            "tracked_worktree_mutation": False,
        },
        "large_runtime_artifact_policy": {
            "signal_features_csv_tracked": False,
            "signal_features_csv_bound_by_sha256": True,
            "small_manifests_curated_for_repository_review": True,
        },
        "next_gate": {
            "gate": "V3-5",
            "title": "Matched Benchmark-versus-Signal Forecast Selection",
            "approval": "APPROVED",
            "implementation_started": False,
            "may_start_after_final_lock_promotion": True,
        },
    }


def main() -> int:
    require_clean_tracked_worktree()
    require_validated_boundary()
    require_runtime_files()
    feature, registry, validation = validate_evidence()
    curated_hashes = curate_evidence()
    lock = build_lock(feature, registry, validation, curated_hashes)
    LOCK_PATH.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("Gate V3-4 lock candidate generated.")
    print(f"validated_implementation_commit: {VALIDATED_IMPLEMENTATION_COMMIT}")
    print(f"source_rows: {feature['source_rows']}")
    print(f"registered_signals: {feature['signal_count']}")
    print(f"feature_rows: {feature['rows']}")
    print(f"lock_path: {LOCK_PATH.relative_to(ROOT)}")
    print(f"curated_evidence_directory: {EVIDENCE_DIRECTORY.relative_to(ROOT)}")
    print("Large signal_features.csv remains untracked and is bound by SHA-256.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"Gate V3-4 lock finalization failed: {error}", file=sys.stderr)
        raise SystemExit(1)
