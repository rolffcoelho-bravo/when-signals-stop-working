from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shockbridge_signal_validity.v3.forecast_benchmark import (  # noqa: E402
    BASE_BENCHMARK_FEATURES,
    build_continuity_benchmark,
)
from shockbridge_signal_validity.v3.forecast_contract import (  # noqa: E402
    ForecastContract,
    ReservedSegmentAccessError,
)
from shockbridge_signal_validity.v3.forecast_inventory import (  # noqa: E402
    build_candidate_inventory,
    load_signal_registry_manifest,
)
from shockbridge_signal_validity.v3.forecast_matching import (  # noqa: E402
    build_matched_pair,
    matched_pair_manifest,
)
from shockbridge_signal_validity.v3.forecast_splits import build_nested_fold_plan  # noqa: E402
from shockbridge_signal_validity.v3.forecast_targets import (  # noqa: E402
    build_development_targets,
    target_manifest,
)

CONTRACT_PATH = ROOT / "configs" / "v3_g5_forecast_contract.json"
VALIDATION_PATH = ROOT / "V3_G5_CONTRACT_VALIDATION.json"
REGISTRY_MANIFEST_PATH = (
    ROOT / "evidence" / "v3" / "g4_signal_lock" / "signal_registry_manifest.json"
)


def synthetic_market(rows: int = 3000) -> tuple[pd.DataFrame, pd.Series]:
    index = pd.date_range("2021-01-01", periods=rows, freq="4h", tz="UTC")
    phase = np.linspace(0.0, 40.0, rows)
    sol_close = 30.0 * np.exp(0.0002 * np.arange(rows) + 0.02 * np.sin(phase))
    btc_close = 29000.0 * np.exp(0.0001 * np.arange(rows) + 0.01 * np.cos(phase))
    market = pd.DataFrame(
        {
            "high": sol_close * 1.01,
            "low": sol_close * 0.99,
            "close": sol_close,
            "volume": 1000.0 + 50.0 * np.sin(phase) ** 2,
        },
        index=index,
    )
    return market, pd.Series(btc_close, index=index, name="btc_close")


def main() -> int:
    validation = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
    if validation.get("status") != "CONTRACT_AUTHORITATIVELY_VALIDATED":
        raise RuntimeError("Gate V3-5 contract validation record is not authoritative.")
    if validation.get("validated_contract_commit") != (
        "013d91abc0c3c74a28784aed486edb4c95efc6d7"
    ):
        raise RuntimeError("Gate V3-5 validated contract commit changed.")
    if validation.get("access_state") != {
        "target_accessed": False,
        "development_model_fitting_started": False,
        "signal_establishment_segment_accessed": False,
        "final_framework_reserve_accessed": False,
    }:
        raise RuntimeError("Gate V3-5 validation access state changed.")

    contract = ForecastContract.from_path(CONTRACT_PATH)
    market, btc = synthetic_market()
    targets = build_development_targets(market["close"], contract)
    target_evidence = target_manifest(targets, contract)
    if target_evidence["rows"] != len(targets):
        raise RuntimeError("Target-manifest row identity failed.")
    if target_evidence["maximum_target_timestamp_utc"] > contract.development_end.isoformat():
        raise RuntimeError("Development targets crossed the frozen boundary.")

    folds = build_nested_fold_plan(targets, contract)
    if len(folds) != 120:
        raise RuntimeError(f"Expected 120 nested fold records, observed {len(folds)}.")
    if set(folds["purge_rows"].astype(int)) != set(contract.horizons):
        raise RuntimeError("Fold purge gaps do not match registered horizons.")

    benchmark = build_continuity_benchmark(market, btc, contract)
    if tuple(benchmark.columns[: len(BASE_BENCHMARK_FEATURES)]) != BASE_BENCHMARK_FEATURES:
        raise RuntimeError("Continuity benchmark feature identity changed.")

    registry_manifest = load_signal_registry_manifest(REGISTRY_MANIFEST_PATH)
    candidates = build_candidate_inventory(registry_manifest)
    if len(candidates) != 57:
        raise RuntimeError("Candidate inventory does not contain 57 bounded candidates.")
    if int((candidates["candidate_kind"] == "SINGLE_SIGNAL").sum()) != 48:
        raise RuntimeError("Candidate inventory lost locked single-signal candidates.")

    horizon_targets = targets.loc[targets["horizon_candles"] == 1].copy()
    horizon_targets = horizon_targets.set_index("timestamp")["direction"].astype(float)
    signal = pd.DataFrame(
        {"synthetic_registered_signal": np.sin(np.arange(len(market)) / 13.0)},
        index=market.index,
    )
    first_candidate = str(candidates.iloc[0]["candidate_id"])
    pair = build_matched_pair(
        benchmark_features=benchmark,
        candidate_features=signal,
        target=horizon_targets,
        candidate_id=first_candidate,
        horizon_candles=1,
        contract=contract,
    )
    manifest = matched_pair_manifest(pair)
    if pair.rows <= 0 or manifest["matched_rows"] != pair.rows:
        raise RuntimeError("Matched row contract produced no valid rows.")
    if not pair.benchmark.index.equals(pair.candidate.index):
        raise RuntimeError("Benchmark and candidate matched rows differ.")

    try:
        contract.assert_development_only(
            pd.date_range("2026-01-01", periods=2, freq="4h", tz="UTC")
        )
    except ReservedSegmentAccessError as error:
        if str(error) != "PROTOCOL_VIOLATION_FINAL_RESERVE_ACCESSED":
            raise
    else:
        raise RuntimeError("Final-framework reserve access did not fail closed.")

    print("Gate V3-5 forecast foundation verified.")
    print("Contract authoritatively validated: True")
    print("Registered horizons: 4h/8h/12h/24h/48h/72h")
    print("Nested fold records: 120")
    print("Locked single-signal candidates preserved: 48")
    print("Bounded candidate inventory: 57")
    print("Matched benchmark/candidate rows identical: True")
    print("Signal-establishment segment accessed: False")
    print("V3-9 final-framework reserve accessed: False")
    print("Model fitting performed: False")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"Gate V3-5 foundation verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
