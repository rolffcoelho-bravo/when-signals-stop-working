from pathlib import Path


def test_public_package_integrity() -> None:
    root = Path(__file__).parents[1]
    required = [
        "README.md",
        "RESULTS.md",
        "RESEARCH_SCOPE.md",
        "ROADMAP.md",
        "CITATION.cff",
        ".gitattributes",
        "docs/REFERENCES.md",
        "docs/FIGURE_CATALOG.md",
        "src/shockbridge_signal_validity/visualization.py",
    ]
    for relative in required:
        assert (root / relative).exists(), relative

    runner = (root / "RUN_REPLICATION.ps1").read_text(encoding="utf-8")
    assert runner.startswith("param("), "Institutional PowerShell runner must begin with param()."
    assert "Invoke-NativeStep" in runner
    assert "outputs\\run_manifest.json" in runner
