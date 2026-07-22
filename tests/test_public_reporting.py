from __future__ import annotations

from pathlib import Path

from shockbridge_signal_validity.features import FeatureConfig
from shockbridge_signal_validity.framework import ValidationConfig, run_framework

from test_indicators import make_prices


def test_public_report_and_svg_suite(tmp_path: Path) -> None:
    result = run_framework(
        sol=make_prices(51, 1250),
        btc=make_prices(52, 1250),
        config=ValidationConfig(
            feature=FeatureConfig(),
            splits=3,
            bootstrap_samples=80,
            monitor_window=90,
            failure_windows=2,
        ),
        output_directory=tmp_path,
    )

    assert result["primary_signal"] == "bollinger"
    report = (tmp_path / "research_report.md").read_text(encoding="utf-8")
    assert "Executive determination" in report
    assert "Sources, methodology, and reproducibility" in report
    assert "NOT_ESTABLISHED" in report or "ACTIVE" in report or "REDUCED" in report or "SUSPENDED" in report
    assert (tmp_path / "run_manifest.json").exists()

    expected = {
        "figure_01_market_signal_anatomy.svg",
        "figure_02_validation_evidence.svg",
        "figure_03_probability_calibration.svg",
        "figure_04_regime_evidence_matrix.svg",
        "monitoring_rsi.svg",
        "monitoring_bollinger.svg",
        "monitoring_combined.svg",
    }
    assert expected.issubset({item.name for item in (tmp_path / "figures").iterdir()})
