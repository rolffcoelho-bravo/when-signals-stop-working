from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

from shockbridge_signal_validity.v3.lock_lineage import audit_lock_lineage


ROOT = Path(__file__).resolve().parents[1]
TEST_FILES = (
    "tests/test_v3_panic_regime_contract.py",
    "tests/test_v3_panic_regime.py",
    "tests/test_v3_panic_regime_diagnostics.py",
    "tests/test_v3_lock_lineage.py",
    "tests/test_v3_g3_final_acceptance.py",
)
VERIFIERS = (
    "scripts/verify_v3_g3a_identification.py",
    "scripts/verify_v3_g3b_probabilistic_engine.py",
    "scripts/verify_v3_g3c_governance.py",
)
EXPECTED_TEST_COUNT = 46
EXPECTED_BRANCH = "research/v3-adaptive-signal-validity"


def _run(arguments: list[str]) -> None:
    completed = subprocess.run(arguments, cwd=ROOT)
    if completed.returncode != 0:
        raise RuntimeError("Command failed: " + " ".join(arguments))


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _load_json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _verify_chronology_governance(
    acceptance_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    validation_complete = acceptance_evidence.get(
        "external_chronology_validation_complete"
    )
    deferred = acceptance_evidence.get(
        "external_chronology_deferred_to_later_robustness"
    )
    explicitly_used = acceptance_evidence.get("external_chronology_used", False)

    if validation_complete is not False:
        raise RuntimeError(
            "External chronology validation must remain incomplete before the robustness gate."
        )
    if deferred is not True:
        raise RuntimeError(
            "External chronology must remain explicitly deferred to the later robustness gate."
        )
    if explicitly_used is not False:
        raise RuntimeError("External chronology was used before the robustness gate.")

    return {
        "external_chronology_validation_complete": False,
        "external_chronology_deferred_to_later_robustness": True,
        "external_chronology_used": False,
    }


def _verify_static_governance() -> dict[str, Any]:
    registry = _load_json("configs/v3_panic_regime_model_registry.json")
    identification = _load_json("configs/v3_panic_regime_identification.json")
    g3b = _load_json("V3_G3B_PROBABILISTIC_ENGINE_LOCK.json")
    g3c = _load_json("V3_G3C_GOVERNANCE_LOCK.json")

    if registry.get("automatic_model_selection") is not False:
        raise RuntimeError("Model registry permits automatic model selection.")
    if registry.get("automatic_ensemble") is not False:
        raise RuntimeError("Model registry permits an automatic ensemble.")
    if registry.get("reporting_policy", {}).get("consensus_probability_prohibited") is not True:
        raise RuntimeError("Consensus-probability prohibition is missing.")
    if g3b.get("acceptance_evidence", {}).get("automatic_model_selection_performed") is not False:
        raise RuntimeError("V3-3B lock records automatic model selection.")

    g3c_evidence = g3c.get("acceptance_evidence")
    if not isinstance(g3c_evidence, Mapping):
        raise RuntimeError("V3-3C lock has no acceptance_evidence mapping.")
    if g3c_evidence.get("automatic_model_selection_performed") is not False:
        raise RuntimeError("V3-3C lock records automatic model selection.")
    chronology = _verify_chronology_governance(g3c_evidence)

    required_outputs = set(identification.get("required_final_gate_outputs", []))
    expected_outputs = {
        "panic_regime_probability.csv",
        "transition_matrix.json",
        "state_duration.csv",
        "occupancy_statistics.json",
        "mechanism_contributions.csv",
        "probability_diagnostics.json",
        "regime_manifest.json",
        "regime_validation_report.json",
    }
    if required_outputs != expected_outputs:
        raise RuntimeError("Required final Gate V3-3 output contract changed.")

    return {
        "automatic_model_selection_performed": False,
        "automatic_ensemble_performed": False,
        "consensus_probability_produced": False,
        **chronology,
        "required_output_contract_verified": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute Gate V3-3D final acceptance without creating the final lock."
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("outputs/v3/g3_final_acceptance/final_acceptance_report.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    branch = _git("branch", "--show-current")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"Expected branch {EXPECTED_BRANCH}, observed {branch}.")
    if _git("diff", "--name-only") or _git("diff", "--cached", "--name-only"):
        raise RuntimeError("Tracked working-tree changes are prohibited during final acceptance.")

    print("1. AUDITING HISTORICAL LOCK LINEAGE")
    lineage = audit_lock_lineage(ROOT)
    print(f"Historical protected objects verified: {lineage.historical_objects_verified}")
    print(f"Current latest-owner objects verified: {lineage.current_objects_verified}")
    print(f"Governed superseded paths: {len(lineage.superseded_paths)}")
    print("Lock finalization anchors verified: True")

    print("2. VERIFYING STATIC GOVERNANCE AND OUTPUT CONTRACTS")
    static = _verify_static_governance()

    print("3. RUNNING INTEGRATED GATE V3-3 ACCEPTANCE SUITE")
    _run([sys.executable, "-m", "pytest", "-q", *TEST_FILES])

    print("4. VERIFYING V3-3 SUBGATE LOCKS")
    for verifier in VERIFIERS:
        _run([sys.executable, verifier])

    report = {
        "schema_version": "v3.g3-final-acceptance-report.v3",
        "status": "FINAL_LOCK_AUTHORIZATION_EVIDENCE_COMPLETE",
        "branch": branch,
        "commit": _git("rev-parse", "HEAD"),
        "integrated_tests_passed": EXPECTED_TEST_COUNT,
        "test_files": list(TEST_FILES),
        "subgate_verifiers_passed": list(VERIFIERS),
        "historical_protected_objects_verified": lineage.historical_objects_verified,
        "current_latest_owner_objects_verified": lineage.current_objects_verified,
        "superseded_paths": {
            path: list(locks) for path, locks in lineage.superseded_paths.items()
        },
        "lock_creation_commits": dict(lineage.lock_creation_commits),
        "lock_finalization_commits": dict(lineage.lock_finalization_commits),
        "authoritative_lock_blobs": dict(lineage.authoritative_lock_blobs),
        "lock_anchor_sources": dict(lineage.lock_anchor_sources),
        "lock_finalization_anchors_verified": True,
        **static,
        "version_1_and_version_2_determinations_modified": False,
        "final_lock_created_by_this_script": False,
        "next_action": "Create V3_G3_PANIC_REGIME_LOCK.json and V3_G3_PANIC_REGIME_CHECKPOINT.md from this evidence.",
    }
    report_path = args.report
    if not report_path.is_absolute():
        report_path = ROOT / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("5. FINAL ACCEPTANCE EVIDENCE COMPLETE")
    print(f"Integrated tests passed: {EXPECTED_TEST_COUNT}")
    print("Automatic model selection performed: False")
    print("External chronology validation complete: False")
    print("External chronology deferred: True")
    print("External chronology used: False")
    print("Final lock created: False")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        KeyError,
        OSError,
        RuntimeError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"Gate V3-3D final acceptance failed: {error}", file=sys.stderr)
        raise SystemExit(1)
