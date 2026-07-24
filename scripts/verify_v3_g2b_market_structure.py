from __future__ import annotations

from hashlib import sha1
import json
from pathlib import Path

import numpy as np
import pandas as pd

from shockbridge_signal_validity.v3.market_structure import (
    MARKET_STRUCTURE_SCHEMA_VERSION,
    NetworkSpec,
    compute_market_structure_feature_frame,
    network_metrics_from_correlation,
)
from shockbridge_signal_validity.v3.spectral import PanelSpec

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "V3_G2B_MARKET_STRUCTURE_LOCK.json"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return sha1(header + data).hexdigest()


def verify_locked_files(lock: dict[str, object]) -> None:
    protected = lock.get("protected_files")
    if not isinstance(protected, dict):
        raise RuntimeError("Gate V3-2B lock has no protected_files mapping.")
    failures: list[str] = []
    for relative_path, expected_sha in protected.items():
        path = ROOT / str(relative_path)
        if not path.is_file():
            failures.append(f"missing: {relative_path}")
            continue
        actual_sha = git_blob_sha(path)
        if actual_sha != expected_sha:
            failures.append(
                f"hash mismatch: {relative_path} expected={expected_sha} actual={actual_sha}"
            )
    if failures:
        raise RuntimeError("Gate V3-2B lock verification failed:\n" + "\n".join(failures))


def synthetic_panel(periods: int = 60) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01", periods=periods, freq="4h", tz="UTC")
    rows: list[dict[str, object]] = []
    common = np.sin(np.linspace(0.0, 7.0, periods)) * 0.003
    for index, asset in enumerate(("SOL", "BTC", "ETH", "BNB")):
        returns = common + np.cos(
            np.linspace(0.0, 4.0 + index, periods)
        ) * (0.0005 + index * 0.0001)
        closes = (100.0 + index * 10.0) * np.exp(np.cumsum(returns))
        for timestamp, close in zip(timestamps, closes):
            rows.append(
                {
                    "timestamp": timestamp,
                    "asset": asset,
                    "venue": "fixture",
                    "open": close * 0.999,
                    "high": close * 1.002,
                    "low": close * 0.998,
                    "close": close,
                    "volume": 1000.0 + index,
                }
            )
    return pd.DataFrame(rows)


def panel_spec() -> PanelSpec:
    return PanelSpec(
        members=(
            "SOL@fixture",
            "BTC@fixture",
            "ETH@fixture",
            "BNB@fixture",
        ),
        dependence_windows=(20,),
        minimum_complete_observations=15,
        minimum_window_coverage=0.80,
        estimator="sample",
        network_threshold=0.50,
    )


def verify_analytical_contract() -> None:
    identity = network_metrics_from_correlation(
        np.eye(4), ("A", "B", "C", "D"), NetworkSpec(threshold=0.50)
    )
    if identity["network_density"] != 0.0:
        raise RuntimeError("Identity network density is incorrect.")
    if identity["network_community_count"] != 4:
        raise RuntimeError("Identity network community count is incorrect.")
    if not np.isclose(identity["mst_total_distance"], 3.0 * np.sqrt(2.0)):
        raise RuntimeError("Identity-network MST length is incorrect.")

    common = network_metrics_from_correlation(
        np.ones((4, 4)), ("A", "B", "C", "D"), NetworkSpec(threshold=0.50)
    )
    if common["network_density"] != 1.0:
        raise RuntimeError("Common-mode network density is incorrect.")
    if common["network_community_count"] != 1:
        raise RuntimeError("Common-mode community count is incorrect.")

    blocks = np.array(
        [
            [1.0, 0.90, 0.10, 0.10],
            [0.90, 1.0, 0.10, 0.10],
            [0.10, 0.10, 1.0, 0.85],
            [0.10, 0.10, 0.85, 1.0],
        ]
    )
    block_metrics = network_metrics_from_correlation(
        blocks, ("A", "B", "C", "D"), NetworkSpec(threshold=0.50)
    )
    if block_metrics["network_community_count"] != 2:
        raise RuntimeError("Block-network community recovery is incorrect.")
    if block_metrics["network_modularity"] <= 0.0:
        raise RuntimeError("Block-network modularity must be positive.")


def verify_causal_contract() -> None:
    frame = synthetic_panel()
    spec = panel_spec()
    network = NetworkSpec(threshold=0.50, dynamic_window=3)
    baseline = compute_market_structure_feature_frame(
        frame, spec, network_spec=network
    ).frame
    cutoff = pd.Timestamp("2026-01-07T00:00:00Z")
    changed = frame.copy()
    future = changed["timestamp"] > cutoff
    changed.loc[future, "close"] *= np.linspace(1.0, 2.0, int(future.sum()))
    mutated = compute_market_structure_feature_frame(
        changed, spec, network_spec=network
    ).frame
    columns = [
        "timestamp",
        "window",
        "eligibility_status",
        "dominant_eigenvalue_share",
        "network_density",
        "network_modularity",
        "mst_total_distance",
    ]
    left = baseline.loc[baseline["timestamp"] <= cutoff, columns].reset_index(drop=True)
    right = mutated.loc[mutated["timestamp"] <= cutoff, columns].reset_index(drop=True)
    try:
        pd.testing.assert_frame_equal(left, right)
    except AssertionError as exc:
        raise RuntimeError("Future observations changed prior market-structure outputs.") from exc


def main() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("gate") != "V3-2B":
        raise RuntimeError("Unexpected gate identifier in V3-2B lock.")
    if lock.get("schema_version") != MARKET_STRUCTURE_SCHEMA_VERSION:
        raise RuntimeError("Gate lock and market-structure schema versions differ.")
    verify_locked_files(lock)
    verify_analytical_contract()
    verify_causal_contract()
    print("Gate V3-2B market-structure extension lock verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
