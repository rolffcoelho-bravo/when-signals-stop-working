from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shockbridge_signal_validity.v3.forecast_materialization import (
    materialize_real_development_foundation,
    write_materialized_foundation,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Materialize the Gate V3-5 real development-only forecast foundation."
    )
    value.add_argument(
        "--contract",
        default="configs/v3_g5_forecast_contract.json",
    )
    value.add_argument("--sol", default="data/raw/sol_usdt_4h.csv")
    value.add_argument("--btc", default="data/raw/btc_usdt_4h.csv")
    value.add_argument(
        "--signal-features",
        default="outputs/v3/signal_engine/signal_features.csv",
    )
    value.add_argument(
        "--signal-registry-manifest",
        default="evidence/v3/g4_signal_lock/signal_registry_manifest.json",
    )
    value.add_argument(
        "--output-dir",
        default="outputs/v3/forecast_foundation",
    )
    return value


def main() -> int:
    arguments = parser().parse_args()
    os.chdir(ROOT)
    foundation = materialize_real_development_foundation(
        contract_path=arguments.contract,
        sol_path=arguments.sol,
        btc_path=arguments.btc,
        signal_features_path=arguments.signal_features,
        signal_registry_manifest_path=arguments.signal_registry_manifest,
    )
    manifest = write_materialized_foundation(
        foundation,
        arguments.output_dir,
    )
    print("Gate V3-5 real development foundation materialized.")
    print(f"Development rows: {manifest['development_rows']}")
    print(f"Target rows: {manifest['target_rows']}")
    print(f"Nested fold rows: {manifest['fold_rows']}")
    print(f"Bounded candidates: {manifest['candidate_count']}")
    print(f"Candidate-horizon coverage rows: {manifest['matched_coverage_rows']}")
    print("Large-move labels materialized: False")
    print("Model fitting performed: False")
    print("Signal-establishment segment accessed: False")
    print("V3-9 final-framework reserve accessed: False")
    print(f"Outputs: {(ROOT / arguments.output_dir).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
