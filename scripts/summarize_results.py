from __future__ import annotations

import argparse
import json
from pathlib import Path


DISPLAY = {
    "bollinger": "Bollinger Bands",
    "rsi": "RSI",
    "combined": "Combined RSI and Bollinger specification",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print the institutional Version 1 signal determinations."
    )
    parser.add_argument(
        "--verdicts",
        type=Path,
        default=Path("outputs/final_verdicts.json"),
    )
    return parser.parse_args()


def institutional_determination(signal_name: str, result: dict) -> str:
    label = DISPLAY[signal_name]
    status = result["status"]

    if status == "NOT_ESTABLISHED":
        return (
            f"Under the frozen Version 1 specification, {label} did not "
            "demonstrate stable incremental predictive and economic "
            "contribution over the common non-indicator benchmark. The "
            "appropriate operational status is NOT_ESTABLISHED."
        )

    if status == "ACTIVE":
        return (
            f"{label} satisfied the historical establishment requirement and "
            "remains ACTIVE under the current market-state and monitoring "
            "evidence."
        )

    if status == "REDUCED":
        return (
            f"{label} satisfied the historical establishment requirement, but "
            "the current evidence is uncertain, regime-concentrated, or "
            "deteriorating. The appropriate status is REDUCED."
        )

    return (
        f"{label} previously satisfied the establishment requirement. The "
        "structural-deterioration condition and recent predictive and economic "
        "evidence support a SUSPENDED status under the model contract."
    )


def print_model_details(signal: str, result: dict) -> None:
    print(f"\n{DISPLAY[signal]}")
    print("-" * len(DISPLAY[signal]))
    print(f"Operational status: {result['status']}")
    print(f"Current filtered market state: {result['current_regime']}")
    print(
        "Filtered probabilities: "
        f"range={result['current_regime_probabilities']['range']:.3f}, "
        f"trend={result['current_regime_probabilities']['trend']:.3f}, "
        f"stress={result['current_regime_probabilities']['stress']:.3f}"
    )
    print(f"Structural-deterioration alarm: {result['structural_change_alarm']}")


def main() -> int:
    args = parse_args()
    verdicts = json.loads(args.verdicts.read_text(encoding="utf-8"))

    print("\nTECHNICAL SIGNAL VALIDITY - VERSION 1")
    print("=" * 37)

    for signal in ("rsi", "bollinger", "combined"):
        print_model_details(signal, verdicts[signal])

    print("\nINSTITUTIONAL DETERMINATIONS")
    print("-" * 28)
    print(institutional_determination("rsi", verdicts["rsi"]))
    print(institutional_determination("bollinger", verdicts["bollinger"]))

    print("\nCROSS-SPECIFICATION ASSESSMENT")
    print("-" * 30)
    print(
        "RSI and Bollinger Bands are assessed independently because they "
        "represent different information families. The combined specification "
        "is secondary and does not replace either standalone determination."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
