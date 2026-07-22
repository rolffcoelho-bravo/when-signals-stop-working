from __future__ import annotations

from pathlib import Path

from shockbridge_signal_validity.features import FeatureConfig
from shockbridge_signal_validity.framework import ValidationConfig, run_framework

from test_indicators import make_prices


def test_three_stage_framework_smoke(tmp_path: Path) -> None:
    result = run_framework(
        sol=make_prices(3, 1200),
        btc=make_prices(4, 1200),
        config=ValidationConfig(
            feature=FeatureConfig(),
            splits=3,
            bootstrap_samples=100,
            monitor_window=90,
            failure_windows=2,
        ),
        output_directory=tmp_path,
    )

    assert result["primary_signal"] == "bollinger"
    assert set(result["verdicts"]) == {"rsi", "bollinger", "combined"}
    assert result["primary_verdict"]["status"] in {
        "ACTIVE",
        "REDUCED",
        "SUSPENDED",
        "NOT_ESTABLISHED",
    }

    expected = {
        "stage_1_event_study.csv",
        "stage_2_fold_results.csv",
        "stage_2_oos_predictions.csv",
        "stage_3_regime_summary.csv",
        "final_verdicts.json",
        "research_report.md",
    }
    assert expected.issubset({path.name for path in tmp_path.iterdir()})
