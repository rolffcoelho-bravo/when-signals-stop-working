from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_d5_publication_boundaries_are_explicit() -> None:
    boundaries = (ROOT / "docs/V2_FINAL_MODEL_BOUNDARIES.md").read_text(
        encoding="utf-8"
    )
    assert "NO_PIPELINE_ADMITTED" in boundaries
    assert "NO_INCREMENTAL_EVIDENCE" in boundaries
    assert "Operational deployment: not supported" in boundaries
    assert "V2.1 boundary" in boundaries


def test_checkpoint_names_final_audit_as_next_phase() -> None:
    checkpoint = (ROOT / "V2_D5_ROBUSTNESS_CHECKPOINT.md").read_text(
        encoding="utf-8"
    )
    assert "Final Version 2 audit" in checkpoint
    assert "cannot reopen model selection" in checkpoint
