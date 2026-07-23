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
D5_TAG = "v2-d5-robustness-publication-20260723"
EXPECTED_D5_COMMIT = "74866b920e2b19543686d84e0208f8b12b496090"
EXPECTED_D5_LOCK = "v2-d5-f9233e24526fa5b2"
EXPECTED_RELEASE_VERSION = "2.0.0"
EXPECTED_RELEASE_DATE = "2026-07-23"
EXPECTED_FROZEN_PACKAGE_VERSION = "2.0.0.dev8"

CHECKPOINT_OBJECT_LOCKS = (
    {
        "name": "protocol",
        "tag": "v2-protocol-freeze-20260722",
        "commit_prefix": "3f4871e",
        "lock_path": "V2_PROTOCOL_LOCK.json",
        "lock_id": "v2-protocol-068f03ca1452c5ef",
        "protected_key": "files",
    },
    {
        "name": "D0",
        "tag": "v2-implementation-d0-20260722",
        "commit_prefix": "e196282",
        "lock_path": "V2_D0_IMPLEMENTATION_LOCK.json",
        "lock_id": "v2-d0-0e1cca99b90e5a50",
        "protected_key": "protected_files",
    },
    {
        "name": "D1",
        "tag": "v2-d1-causal-engine-20260722",
        "commit_prefix": "50b5ef7",
        "lock_path": "V2_D1_ENGINE_LOCK.json",
        "lock_id": "v2-d1-53c53a61a3011a65",
        "protected_key": "protected_files",
    },
    {
        "name": "D2A",
        "tag": "v2-d2a-screening-20260722",
        "commit_prefix": "81e2b8c",
        "lock_path": "V2_D2A_SELECTION_LOCK.json",
        "lock_id": "v2-d2a-43b7dcb8379cc9c7",
        "protected_key": "protected_files",
    },
    {
        "name": "D2B",
        "tag": "v2-d2b-selection-20260722",
        "commit_prefix": "93ecb7e",
        "lock_path": "V2_D2B_SELECTION_LOCK.json",
        "lock_id": "v2-d2b-f88a98fce021cb1d",
        "protected_key": "protected_files",
    },
    {
        "name": "D2C",
        "tag": "v2-d2c-admission-20260722",
        "commit_prefix": "5153f2e",
        "lock_path": "V2_D2C_ADMISSION_LOCK.json",
        "lock_id": "v2-d2c-190392a1d97827b2",
        "protected_key": "protected_files",
    },
    {
        "name": "D3",
        "tag": "v2-d3-locked-evaluation-20260723",
        "commit_prefix": "d0872b9",
        "lock_path": "V2_D3_EVALUATION_LOCK.json",
        "lock_id": "v2-d3-e2d92bf8786bdb8f",
        "protected_key": "protected_files",
    },
    {
        "name": "D4",
        "tag": "v2-d4-confirmatory-inference-20260723",
        "commit_prefix": "69f1c40",
        "lock_path": "V2_D4_INFERENCE_LOCK.json",
        "lock_id": "v2-d4-ec8d9850edbcb622",
        "protected_key": "protected_files",
    },
    {
        "name": "D5",
        "tag": D5_TAG,
        "commit_prefix": "74866b9",
        "lock_path": "V2_D5_ROBUSTNESS_LOCK.json",
        "lock_id": EXPECTED_D5_LOCK,
        "protected_key": "protected_files",
    },
)

RELEASE_CONTROL_FILES = {
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
ALLOWED_RELEASE_DIFF = RELEASE_CONTROL_FILES | {"V2_FINAL_RELEASE_AUDIT.json"}


def run_git(*arguments: str, binary: bool = False) -> bytes | str:
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


def git_file_bytes(reference: str, path: str) -> bytes:
    return run_git("show", f"{reference}:{path}", binary=True)


def git_object_id(reference: str, path: str) -> str:
    return str(run_git("rev-parse", f"{reference}:{path}"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verify_repository_object_locks() -> None:
    for checkpoint in CHECKPOINT_OBJECT_LOCKS:
        name = str(checkpoint["name"])
        tag = str(checkpoint["tag"])
        lock_path = str(checkpoint["lock_path"])
        expected_lock_id = str(checkpoint["lock_id"])
        protected_key = str(checkpoint["protected_key"])
        expected_prefix = str(checkpoint["commit_prefix"])

        if str(run_git("cat-file", "-t", tag)) != "tag":
            fail(f"{name} checkpoint is not an annotated tag: {tag}")

        tag_commit = str(run_git("rev-parse", f"{tag}^{{commit}}"))
        if not tag_commit.startswith(expected_prefix):
            fail(f"{name} checkpoint tag moved: {tag_commit}")

        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", tag_commit, "HEAD"],
            cwd=ROOT,
            check=False,
        )
        if ancestor.returncode != 0:
            fail(f"{name} checkpoint is not an ancestor of HEAD.")

        if git_object_id("HEAD", lock_path) != git_object_id(tag, lock_path):
            fail(f"{name} lock file changed after its checkpoint: {lock_path}")

        payload = json.loads(git_file_bytes("HEAD", lock_path).decode("utf-8"))
        if payload.get("lock_id") != expected_lock_id:
            fail(f"{name} lock identifier is invalid.")

        protected = payload.get(protected_key)
        if not isinstance(protected, dict) or not protected:
            fail(f"{name} protected-file inventory is missing.")

        for relative in protected:
            path = str(relative)
            try:
                current_object = git_object_id("HEAD", path)
                frozen_object = git_object_id(tag, path)
            except subprocess.CalledProcessError as error:
                fail(f"{name} protected object is missing: {path}") from error
            if current_object != frozen_object:
                fail(f"{name} protected Git object changed: {path}")


def verify_file_hashes(audit: dict[str, object]) -> None:
    records = audit.get("files")
    if not isinstance(records, list):
        fail("Final audit file records are missing.")

    observed_paths: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            fail("Final audit contains an invalid file record.")

        path = str(record.get("path", ""))
        expected_hash = str(record.get("sha256", ""))
        expected_bytes = int(record.get("bytes", -1))

        if path not in RELEASE_CONTROL_FILES:
            fail(f"Final audit contains an unexpected release file: {path}")

        payload = git_file_bytes("HEAD", path)
        actual_hash = sha256_bytes(payload)

        if actual_hash != expected_hash:
            fail(f"Release-control hash mismatch: {path}")
        if len(payload) != expected_bytes:
            fail(f"Release-control byte-count mismatch: {path}")

        observed_paths.add(path)

    if observed_paths != RELEASE_CONTROL_FILES:
        missing = sorted(RELEASE_CONTROL_FILES - observed_paths)
        extra = sorted(observed_paths - RELEASE_CONTROL_FILES)
        fail(f"Final audit file inventory mismatch. Missing={missing}, extra={extra}")


def verify_release_diff() -> None:
    changed_text = run_git("diff", "--name-only", f"{D5_TAG}..HEAD")
    changed = {line for line in str(changed_text).splitlines() if line}

    unexpected = changed - ALLOWED_RELEASE_DIFF
    missing = RELEASE_CONTROL_FILES - changed

    if unexpected:
        fail(f"Unexpected post-D5 release changes: {sorted(unexpected)}")
    if missing:
        fail(f"Required release-control changes are missing: {sorted(missing)}")


def verify_metadata() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)
    if pyproject["project"]["version"] != EXPECTED_FROZEN_PACKAGE_VERSION:
        fail("D5-protected package metadata version changed.")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if "## Unreleased - Version 2 methodological design freeze" not in changelog:
        fail("D5-protected changelog content changed.")

    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    if 'version: "2.0.0"' not in citation:
        fail("CITATION.cff is not Version 2.0.0.")
    if 'date-released: "2026-07-23"' not in citation:
        fail("CITATION.cff release date is missing or incorrect.")

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
    required_notes = {
        "NO_PIPELINE_ADMITTED",
        "NO_INCREMENTAL_EVIDENCE",
        "Frozen-metadata boundary",
        "not an indicator-rescue exercise",
    }
    missing_notes = sorted(value for value in required_notes if value not in notes)
    if missing_notes:
        fail(f"Release notes are incomplete: {missing_notes}")


def verify_ci() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    required_fragments = {
        "runs-on: windows-latest",
        "fetch-depth: 0",
        "fetch-tags: true",
        "fail-fast: false",
        "python scripts/verify_v2_final_audit.py",
        "python scripts/verify_v2_d3_assets.py",
        "python scripts/verify_v2_d4_assets.py",
        "python scripts/verify_v2_d5_assets.py",
    }
    missing = sorted(fragment for fragment in required_fragments if fragment not in workflow)
    if missing:
        fail(f"Continuous integration is missing release controls: {missing}")

    prohibited = {
        "python scripts/verify_v2_d0_lock.py",
        "python scripts/verify_v2_d1_lock.py",
        "python scripts/verify_v2_d2a_lock.py",
        "python scripts/verify_v2_d2b_lock.py",
        "python scripts/verify_v2_d2c_lock.py",
        "python scripts/verify_v2_d3_lock.py",
        "python scripts/verify_v2_d4_lock.py",
        "python scripts/verify_v2_d5_lock.py",
    }
    present = sorted(command for command in prohibited if command in workflow)
    if present:
        fail(f"CI still invokes non-portable working-tree lock checks: {present}")


def verify_replication_preservation() -> None:
    powershell = (ROOT / "RUN_REPLICATION.ps1").read_text(encoding="utf-8")
    if '@(".gitkeep", "README.md", "v2")' not in powershell:
        fail("Windows replication does not explicitly preserve outputs/v2.")

    shell = (ROOT / "RUN_REPLICATION.sh").read_text(encoding="utf-8")
    if "! -name v2" not in shell:
        fail("macOS/Linux replication does not explicitly preserve outputs/v2.")
    if "Version 2 evidence preserved: outputs/v2" not in shell:
        fail("macOS/Linux replication preservation is not reported.")


def verify_frozen_verdict() -> None:
    verdict = json.loads(
        (ROOT / "outputs" / "v2" / "publication" / "v2_final_evidence_grade.json")
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
        fail("README no longer states the V2.1 non-rescue boundary.")

    public_audit = json.loads(
        (ROOT / "PUBLIC_RELEASE_AUDIT.json").read_text(encoding="utf-8")
    )
    if public_audit.get("status") != "PASS" or public_audit.get("problems") != []:
        fail("Public release sensitive-information audit is not PASS.")


def main() -> int:
    if not AUDIT_PATH.exists():
        fail("V2_FINAL_RELEASE_AUDIT.json is missing.")

    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))

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
    }
    for field, expected in expected_fields.items():
        if audit.get(field) != expected:
            fail(f"Final audit field {field!r} is invalid.")

    preparation_commit = str(audit.get("preparation_commit", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", preparation_commit):
        fail("Final audit preparation commit is invalid.")

    d5_commit = str(run_git("rev-parse", f"{D5_TAG}^{{commit}}"))
    if d5_commit != EXPECTED_D5_COMMIT:
        fail("D5 checkpoint tag moved.")

    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", preparation_commit, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        fail("Release-preparation commit is not an ancestor of HEAD.")

    verify_repository_object_locks()
    verify_release_diff()
    verify_file_hashes(audit)
    verify_metadata()
    verify_ci()
    verify_replication_preservation()
    verify_frozen_verdict()
    verify_public_boundaries()

    print("Version 2 final release audit verification passed.")
    print(f"Release version: {EXPECTED_RELEASE_VERSION}")
    print("Frozen package metadata version: 2.0.0.dev8")
    print("Release readiness: READY_FOR_PULL_REQUEST")
    print("Final evidence grade: NO_INCREMENTAL_EVIDENCE")
    print(f"Repository object locks verified: {len(CHECKPOINT_OBJECT_LOCKS)}")
    print("D5 protected files changed: False")
    print("V2.1 extension used: False")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Version 2 final release audit verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
