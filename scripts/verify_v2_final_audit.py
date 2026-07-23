from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "V2_FINAL_RELEASE_AUDIT.json"

V1_TAG = "v1.2.0"
EXPECTED_V1_COMMIT = "748d1720da9131ebd6eb7b0606913fd43fc6e5e8"
V1_CHECKSUMS = "REPLICATION_CHECKSUMS.sha256"

D5_TAG = "v2-d5-robustness-publication-20260723"
EXPECTED_D5_COMMIT = "74866b920e2b19543686d84e0208f8b12b496090"
EXPECTED_D5_LOCK = "v2-d5-f9233e24526fa5b2"
EXPECTED_RELEASE_VERSION = "2.0.0"
EXPECTED_RELEASE_DATE = "2026-07-23"
EXPECTED_FROZEN_PACKAGE_VERSION = "2.0.0.dev8"

CHECKPOINTS = (
    (
        "protocol",
        "v2-protocol-freeze-20260722",
        "3f4871e",
        "V2_PROTOCOL_LOCK.json",
        "v2-protocol-068f03ca1452c5ef",
        "files",
    ),
    (
        "D0",
        "v2-implementation-d0-20260722",
        "e196282",
        "V2_D0_IMPLEMENTATION_LOCK.json",
        "v2-d0-0e1cca99b90e5a50",
        "protected_files",
    ),
    (
        "D1",
        "v2-d1-causal-engine-20260722",
        "50b5ef7",
        "V2_D1_ENGINE_LOCK.json",
        "v2-d1-53c53a61a3011a65",
        "protected_files",
    ),
    (
        "D2A",
        "v2-d2a-screening-20260722",
        "81e2b8c",
        "V2_D2A_SELECTION_LOCK.json",
        "v2-d2a-43b7dcb8379cc9c7",
        "protected_files",
    ),
    (
        "D2B",
        "v2-d2b-selection-20260722",
        "93ecb7e",
        "V2_D2B_SELECTION_LOCK.json",
        "v2-d2b-f88a98fce021cb1d",
        "protected_files",
    ),
    (
        "D2C",
        "v2-d2c-admission-20260722",
        "5153f2e",
        "V2_D2C_ADMISSION_LOCK.json",
        "v2-d2c-190392a1d97827b2",
        "protected_files",
    ),
    (
        "D3",
        "v2-d3-locked-evaluation-20260723",
        "d0872b9",
        "V2_D3_EVALUATION_LOCK.json",
        "v2-d3-e2d92bf8786bdb8f",
        "protected_files",
    ),
    (
        "D4",
        "v2-d4-confirmatory-inference-20260723",
        "69f1c40",
        "V2_D4_INFERENCE_LOCK.json",
        "v2-d4-ec8d9850edbcb622",
        "protected_files",
    ),
    (
        "D5",
        D5_TAG,
        "74866b9",
        "V2_D5_ROBUSTNESS_LOCK.json",
        EXPECTED_D5_LOCK,
        "protected_files",
    ),
)

RELEASE_FILES = {
    ".github/workflows/ci.yml",
    "CITATION.cff",
    "RELEASE_NOTES_V2_0_0.md",
    "RUN_REPLICATION.ps1",
    "RUN_REPLICATION.sh",
    "V2_FINAL_RELEASE_CHECKPOINT.md",
    "V2_RELEASE_METADATA.json",
    "scripts/verify_v2_final_audit.py",
    "tests/test_v2_final_audit.py",
}
ALLOWED_POST_D5 = RELEASE_FILES | {"V2_FINAL_RELEASE_AUDIT.json"}


def git(*arguments: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if binary:
        return completed.stdout
    return completed.stdout.decode("utf-8").strip()


def fail(message: str) -> None:
    raise RuntimeError(message)


def object_id(reference: str, path: str) -> str:
    return str(git("rev-parse", f"{reference}:{path}"))


def file_bytes(reference: str, path: str) -> bytes:
    return git("show", f"{reference}:{path}", binary=True)


def verify_annotated_tag(
    tag: str,
    expected_commit: str,
    *,
    allow_prefix: bool = False,
) -> str:
    if str(git("cat-file", "-t", tag)) != "tag":
        fail(f"Checkpoint is not an annotated tag: {tag}")

    commit = str(git("rev-parse", f"{tag}^{{commit}}"))
    matches = commit.startswith(expected_commit) if allow_prefix else commit == expected_commit
    if not matches:
        fail(f"Checkpoint tag moved: {tag} -> {commit}")

    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        fail(f"Checkpoint is not an ancestor of HEAD: {tag}")

    return commit


def verify_v1_replication_objects() -> int:
    verify_annotated_tag(V1_TAG, EXPECTED_V1_COMMIT)

    if object_id("HEAD", V1_CHECKSUMS) != object_id(V1_TAG, V1_CHECKSUMS):
        fail("Version 1 checksum inventory changed.")

    checksum_text = file_bytes(V1_TAG, V1_CHECKSUMS).decode("utf-8")
    paths: list[str] = []

    for line in checksum_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        parts = line.split("  ", 1)
        if len(parts) != 2 or not parts[1].strip():
            fail(f"Invalid Version 1 checksum row: {line!r}")
        paths.append(parts[1].strip())

    if not paths:
        fail("Version 1 replication inventory is empty.")

    for path in paths:
        try:
            frozen = object_id(V1_TAG, path)
            current = object_id("HEAD", path)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(
                f"Version 1 replication object is missing: {path}"
            ) from error

        if current != frozen:
            fail(f"Version 1 replication object changed: {path}")

    return len(paths)


def verify_v2_checkpoint_objects() -> int:
    protected_count = 0

    for (
        name,
        tag,
        commit_prefix,
        lock_path,
        expected_lock_id,
        protected_key,
    ) in CHECKPOINTS:
        verify_annotated_tag(tag, commit_prefix, allow_prefix=True)

        if object_id("HEAD", lock_path) != object_id(tag, lock_path):
            fail(f"{name} lock object changed: {lock_path}")

        payload = json.loads(file_bytes(tag, lock_path).decode("utf-8"))
        if payload.get("lock_id") != expected_lock_id:
            fail(f"{name} lock identifier is invalid.")

        protected = payload.get(protected_key)
        if not isinstance(protected, dict) or not protected:
            fail(f"{name} protected-file inventory is missing.")

        for relative in protected:
            path = str(relative)
            try:
                frozen = object_id(tag, path)
                current = object_id("HEAD", path)
            except subprocess.CalledProcessError as error:
                raise RuntimeError(
                    f"{name} protected Git object is missing: {path}"
                ) from error

            if current != frozen:
                fail(f"{name} protected Git object changed: {path}")

            protected_count += 1

    return protected_count


def verify_release_diff() -> None:
    changed = {
        line
        for line in str(git("diff", "--name-only", f"{D5_TAG}..HEAD")).splitlines()
        if line
    }

    unexpected = changed - ALLOWED_POST_D5
    missing = RELEASE_FILES - changed

    if unexpected:
        fail(f"Unexpected post-D5 paths: {sorted(unexpected)}")
    if missing:
        fail(f"Required release-control paths are missing: {sorted(missing)}")


def verify_audit_manifest(audit: dict[str, object]) -> None:
    expected_fields = {
        "audit_id": "v2-final-release-audit-20260723",
        "status": "PASS",
        "release_readiness": "READY_FOR_PULL_REQUEST",
        "release_version": EXPECTED_RELEASE_VERSION,
        "release_date": EXPECTED_RELEASE_DATE,
        "source_d5_tag": D5_TAG,
        "source_d5_commit": EXPECTED_D5_COMMIT,
        "source_d5_lock_id": EXPECTED_D5_LOCK,
        "final_evidence_grade": "NO_INCREMENTAL_EVIDENCE",
        "primary_case_established": False,
        "pipeline_retuning_performed": False,
        "v2_1_extension_used": False,
        "d5_protected_files_changed": False,
        "lock_verification_mode":
            "GIT_OBJECT_IDENTITY_ACROSS_ANNOTATED_CHECKPOINT_TAGS",
    }

    for field, expected in expected_fields.items():
        if audit.get(field) != expected:
            fail(f"Final audit field {field!r} is invalid.")

    for field in ("preparation_commit", "ci_erratum_commit"):
        value = str(audit.get(field, ""))
        if not re.fullmatch(r"[0-9a-f]{40}", value):
            fail(f"Final audit field {field!r} is not a full commit SHA.")

        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", value, "HEAD"],
            cwd=ROOT,
            check=False,
        )
        if ancestor.returncode != 0:
            fail(f"Final audit commit is not an ancestor of HEAD: {field}")

    records = audit.get("files")
    if not isinstance(records, list):
        fail("Final audit file inventory is missing.")

    observed: set[str] = set()

    for record in records:
        if not isinstance(record, dict):
            fail("Final audit contains an invalid file record.")

        path = str(record.get("path", ""))
        if path not in RELEASE_FILES:
            fail(f"Unexpected release-control file in audit: {path}")

        payload = file_bytes("HEAD", path)
        expected_bytes = int(record.get("bytes", -1))
        expected_hash = str(record.get("sha256", ""))

        if len(payload) != expected_bytes:
            fail(f"Release-control byte count changed: {path}")
        if hashlib.sha256(payload).hexdigest() != expected_hash:
            fail(f"Release-control SHA-256 changed: {path}")

        observed.add(path)

    if observed != RELEASE_FILES:
        fail(
            "Final audit file inventory mismatch. "
            f"Missing={sorted(RELEASE_FILES - observed)}, "
            f"extra={sorted(observed - RELEASE_FILES)}"
        )


def verify_metadata() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)

    if project["project"]["version"] != EXPECTED_FROZEN_PACKAGE_VERSION:
        fail("D5-protected package metadata version changed.")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if "## Unreleased - Version 2 methodological design freeze" not in changelog:
        fail("D5-protected changelog changed.")

    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    if 'version: "2.0.0"' not in citation:
        fail("CITATION.cff release version is invalid.")
    if 'date-released: "2026-07-23"' not in citation:
        fail("CITATION.cff release date is invalid.")

    metadata = json.loads(
        (ROOT / "V2_RELEASE_METADATA.json").read_text(encoding="utf-8")
    )
    expected = {
        "release_version": EXPECTED_RELEASE_VERSION,
        "release_date": EXPECTED_RELEASE_DATE,
        "source_d5_lock_id": EXPECTED_D5_LOCK,
        "package_metadata_version": EXPECTED_FROZEN_PACKAGE_VERSION,
        "package_metadata_frozen_by_d5_lock": True,
        "changelog_frozen_by_d5_lock": True,
        "final_evidence_grade": "NO_INCREMENTAL_EVIDENCE",
        "primary_case_established": False,
        "pipeline_retuning_performed": False,
        "v2_1_extension_used": False,
    }

    for field, value in expected.items():
        if metadata.get(field) != value:
            fail(f"Release metadata field {field!r} is invalid.")

    notes = (ROOT / "RELEASE_NOTES_V2_0_0.md").read_text(encoding="utf-8")
    for phrase in (
        "NO_PIPELINE_ADMITTED",
        "NO_INCREMENTAL_EVIDENCE",
        "Frozen-metadata boundary",
        "not an indicator-rescue exercise",
    ):
        if phrase not in notes:
            fail(f"Release notes are missing: {phrase}")


def verify_stage_semantics() -> None:
    expected_pipeline = (
        "2f85b54f8f178ec59c2bfb8a06cd8dedb3e053e2bec4da40cb446d380def2851"
    )

    d3 = json.loads(
        (ROOT / "outputs/v2/holdout/d3_locked_evaluation_status.json")
        .read_text(encoding="utf-8")
    )
    d3_expected = {
        "status": "PASS",
        "signal_family": "bollinger",
        "frozen_pipeline_count": 1,
        "pipeline_hash": expected_pipeline,
        "prediction_rows": 2318,
        "methodology_locked_evaluation_executed": True,
        "holdout_authorization_consumed": True,
        "holdout_performance_accessed": True,
        "pipeline_retuning_performed": False,
        "rsi_reentry_performed": False,
        "statistical_gate_evaluated": False,
        "economic_gate_evaluated": False,
        "robustness_gate_evaluated": False,
        "multiplicity_adjustment_applied": False,
    }
    for field, expected in d3_expected.items():
        if d3.get(field) != expected:
            fail(f"D3 semantic field {field!r} is invalid.")

    d4_grade = json.loads(
        (ROOT / "outputs/v2/holdout/d4_final_evidence_grade.json")
        .read_text(encoding="utf-8")
    )
    if d4_grade.get("evidence_grade") != "NO_INCREMENTAL_EVIDENCE":
        fail("D4 evidence grade changed.")
    if d4_grade.get("primary_case_established") is not False:
        fail("D4 primary-case determination changed.")
    if d4_grade.get("rsi_status") != "NO_PIPELINE_ADMITTED":
        fail("D4 RSI decision changed.")
    if d4_grade.get("pipeline_hash") != expected_pipeline:
        fail("D4 pipeline hash changed.")

    d4_gates = json.loads(
        (ROOT / "outputs/v2/holdout/d4_gate_results.json")
        .read_text(encoding="utf-8")
    )
    if d4_gates.get("pipeline_retuning_performed") is not False:
        fail("D4 incorrectly reports pipeline retuning.")
    if d4_gates.get("rsi_reentry_performed") is not False:
        fail("D4 incorrectly reports RSI re-entry.")
    if d4_gates.get("panic_state_extension_used") is not False:
        fail("D4 incorrectly includes the V2.1 extension.")
    if d4_gates.get("predictive_gate", {}).get("passed") is not False:
        fail("D4 predictive gate changed.")
    if d4_gates.get("economic_gate", {}).get("passed") is not False:
        fail("D4 economic gate changed.")

    d5 = json.loads(
        (ROOT / "outputs/v2/publication/d5_publication_status.json")
        .read_text(encoding="utf-8")
    )
    d5_expected = {
        "status": "PASS",
        "pipeline_hash": expected_pipeline,
        "prediction_rows": 2318,
        "robustness_diagnostics_completed": True,
        "publication_evidence_completed": True,
        "robustness_determination": "FAVOURABLE_MEANS_NOT_CONFIDENCE_ROBUST",
        "fragility_class": "UNCERTAINTY_AND_PARAMETER_SPECIFICATION_SENSITIVE",
        "final_evidence_grade": "NO_INCREMENTAL_EVIDENCE",
        "primary_case_established": False,
        "external_replication_triggered": False,
        "pipeline_retuning_performed": False,
        "rsi_reentry_performed": False,
        "panic_state_extension_used": False,
    }
    for field, expected in d5_expected.items():
        if d5.get(field) != expected:
            fail(f"D5 semantic field {field!r} is invalid.")


def verify_ci_contract() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    required = (
        "runs-on: windows-latest",
        "fail-fast: false",
        "fetch-depth: 0",
        "fetch-tags: true",
        "python scripts/verify_v2_final_audit.py",
        "python scripts/audit_public_release.py",
        "python -m pytest -q",
        "--ignore=tests/test_v2_d0_lock.py",
        "--ignore=tests/test_v2_d3_assets.py",
        "-k \"not test_v2_protocol_lock_hashes\"",
    )

    missing = [fragment for fragment in required if fragment not in workflow]
    if missing:
        fail(f"CI release contract is incomplete: {missing}")

    prohibited = [
        "python scripts/verify_replication.py",
        *[
            f"python scripts/verify_v2_{stage}_{kind}.py"
            for stage in ("d0", "d1", "d2a", "d2b", "d2c", "d3", "d4", "d5")
            for kind in ("lock", "assets")
        ],
    ]
    active = [command for command in prohibited if command in workflow]
    if active:
        fail(f"CI invokes non-portable working-tree hash checks: {active}")


def verify_replication_preservation() -> None:
    powershell = (ROOT / "RUN_REPLICATION.ps1").read_text(encoding="utf-8")
    if '@(".gitkeep", "README.md", "v2")' not in powershell:
        fail("Windows V1 replication does not preserve outputs/v2.")

    shell = (ROOT / "RUN_REPLICATION.sh").read_text(encoding="utf-8")
    if "! -name v2" not in shell:
        fail("Unix V1 replication does not preserve outputs/v2.")
    if "Version 2 evidence preserved: outputs/v2" not in shell:
        fail("Unix V1 replication does not report outputs/v2 preservation.")


def verify_verdict() -> None:
    verdict = json.loads(
        (ROOT / "outputs/v2/publication/v2_final_evidence_grade.json")
        .read_text(encoding="utf-8")
    )

    if verdict["rsi"]["status"] != "NO_PIPELINE_ADMITTED":
        fail("Frozen RSI decision changed.")
    if verdict["bollinger"]["status"] != "NO_INCREMENTAL_EVIDENCE":
        fail("Frozen Bollinger decision changed.")
    if verdict["evidence_grade"] != "NO_INCREMENTAL_EVIDENCE":
        fail("Frozen Version 2 evidence grade changed.")
    if verdict["primary_case_established"] is not False:
        fail("Frozen primary-case determination changed.")
    if verdict["pipeline_retuning_performed"] is not False:
        fail("Version 2 incorrectly reports pipeline retuning.")
    if verdict["panic_state_extension_used"] is not False:
        fail("Version 2 incorrectly includes the V2.1 extension.")


def verify_public_boundaries() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    license_index = readme.find("## License and data notice")
    citation_index = readme.find("## Citation")
    bibtex_index = readme.find("## BibTeX")

    if not (0 <= license_index < citation_index < bibtex_index):
        fail("README citation placement changed.")
    if "not an indicator-rescue exercise" not in readme:
        fail("README V2.1 non-rescue boundary changed.")

    public_audit = json.loads(
        (ROOT / "PUBLIC_RELEASE_AUDIT.json").read_text(encoding="utf-8")
    )
    if public_audit.get("status") != "PASS":
        fail("Public release audit is not PASS.")
    if public_audit.get("problems") != []:
        fail("Public release audit contains problems.")


def main() -> int:
    if not AUDIT_PATH.exists():
        fail("V2_FINAL_RELEASE_AUDIT.json is missing.")

    if str(git("rev-parse", f"{D5_TAG}^{{commit}}")) != EXPECTED_D5_COMMIT:
        fail("D5 checkpoint tag moved.")

    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    v1_count = verify_v1_replication_objects()
    v2_count = verify_v2_checkpoint_objects()
    verify_release_diff()
    verify_audit_manifest(audit)
    verify_metadata()
    verify_stage_semantics()
    verify_ci_contract()
    verify_replication_preservation()
    verify_verdict()
    verify_public_boundaries()

    print("Version 2 final release audit verification passed.")
    print(f"Release version: {EXPECTED_RELEASE_VERSION}")
    print("Frozen package metadata version: 2.0.0.dev8")
    print("Release readiness: READY_FOR_PULL_REQUEST")
    print("Final evidence grade: NO_INCREMENTAL_EVIDENCE")
    print(f"Version 1 replication objects verified: {v1_count}")
    print(f"Annotated Version 2 checkpoint tags verified: {len(CHECKPOINTS)}")
    print(f"Version 2 protected Git objects verified: {v2_count}")
    print("D5 protected files changed: False")
    print("V2.1 extension used: False")
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
        print(
            f"Version 2 final release audit verification failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
