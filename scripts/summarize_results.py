from __future__ import annotations

import argparse
import json
from pathlib import Path


DISPLAY = {
    "bollinger": "Bollinger Bands",
    "rsi": "RSI",
    "combined": "Combined RSI + Bollinger",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print the direct RSI and Bollinger conclusions."
    )
    parser.add_argument(
        "--verdicts",
        type=Path,
        default=Path("outputs/final_verdicts.json"),
    )
    return parser.parse_args()


def direct_answer(signal_name: str, result: dict) -> str:
    label = DISPLAY[signal_name]

    if result["status"] == "NOT_ESTABLISHED":
        return (
            f"Under the frozen specification, {label} did not establish "
            "reliable incremental predictive and economic value over the "
            "non-indicator benchmark. The correct conclusion is not that it "
            "stopped working; its edge was not established by this test."
        )

    if result["status"] == "ACTIVE":
        return (
            f"{label} established benchmark-relative value and remains active "
            "under the current filtered regime and monitoring rule. It has not "
            "currently stopped working, although its usefulness is conditional "
            "and must continue to be monitored."
        )

    if result["status"] == "REDUCED":
        return (
            f"{label} showed some historical incremental value, but its current "
            "contribution is uncertain, weakening, or concentrated in specific "
            "regimes. It should be treated as reduced rather than as a stable "
            "unconditional signal."
        )

    return (
        f"{label} previously established incremental value, but the online "
        "structural-change alarm and current predictive and economic gates now "
        "indicate failure. Under the declared model contract, it has stopped "
        "working sufficiently to be classified as suspended."
    )


def print_model_details(signal: str, result: dict) -> None:
    print(f"\n{DISPLAY[signal]}")
    print("-" * len(DISPLAY[signal]))
    print(f"Status: {result['status']}")
    print(result["explanation"])
    print(f"Current filtered regime: {result['current_regime']}")
    print(
        "Regime probabilities: "
        f"range={result['current_regime_probabilities']['range']:.3f}, "
        f"trend={result['current_regime_probabilities']['trend']:.3f}, "
        f"stress={result['current_regime_probabilities']['stress']:.3f}"
    )
    print(f"Structural-change alarm: {result['structural_change_alarm']}")


def main() -> int:
    args = parse_args()
    verdicts = json.loads(args.verdicts.read_text(encoding="utf-8"))

    print("\nWHEN SIGNALS STOP WORKING")
    print("=" * 25)

    for signal in ("rsi", "bollinger", "combined"):
        print_model_details(signal, verdicts[signal])

    print("\nDIRECT ANSWER TO THE ORIGINAL RSI QUESTION")
    print("-" * 42)
    print(direct_answer("rsi", verdicts["rsi"]))

    print("\nDIRECT ANSWER TO THE CORRECTED BOLLINGER QUESTION")
    print("-" * 49)
    print(direct_answer("bollinger", verdicts["bollinger"]))

    print("\nRELATION BETWEEN THE TWO")
    print("-" * 24)
    print(
        "RSI and Bollinger Bands are evaluated separately because they measure "
        "different market structures. The combined model is only a secondary "
        "test of complementary information and does not replace either direct "
        "conclusion."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
