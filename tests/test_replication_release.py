from __future__ import annotations

from pathlib import Path


def test_public_replication_release_files_exist() -> None:
    root = Path(__file__).parents[1]
    required = [
        "RESULTS.md",
        "PUBLISH_PUBLIC_REPLICATION.ps1",
        "REPLICATION_MANIFEST.json",
        "REPLICATION_CHECKSUMS.sha256",
        "PUBLIC_RELEASE_AUDIT.json",
        "docs/REPLICATION_PACKAGE.md",
        "docs/PUBLIC_RELEASE_POLICY.md",
        "scripts/build_replication_assets.py",
        "scripts/audit_public_release.py",
        "scripts/verify_replication.py",
        ".github/workflows/ci.yml",
    ]
    missing = [relative for relative in required if not (root / relative).exists()]
    assert not missing, missing


def test_gitignore_tracks_evidence_and_excludes_secrets() -> None:
    root = Path(__file__).parents[1]
    text = (root / ".gitignore").read_text(encoding="utf-8")
    assert "outputs/*" not in text
    assert "data/*" not in text
    assert ".env" in text
    assert "*.key" in text
