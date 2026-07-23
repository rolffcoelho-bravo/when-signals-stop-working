from __future__ import annotations

from hashlib import sha1
import json
from pathlib import Path

import numpy as np
import pandas as pd

from shockbridge_signal_validity.v3 import (
    PanelSpec,
    SPECTRAL_SCHEMA_VERSION,
    compute_spectral_feature_frame,
    spectral_metrics_from_correlation,
)

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "V3_G2_SPECTRAL_ENGINE_LOCK.json"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return sha1(header + data).hexdigest()


def verify_locked_files(lock: dict[str, object]) -> None:
    protected = lock.get("protected_files")
    if not isinstance(protected, dict):
        raise RuntimeError("Gate V3-2 lock has no protected_files mapping.")
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
        raise RuntimeError("Gate V3-2 lock verification failed:\n" + "\n".join(failures))


def synthetic_panel(periods: int = 50) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01", periods=periods, freq="4h", tz="UTC")
    rows: list[dict[str, object]] = []
    common = np.sin(np.linspace(0.0, 5.0, periods)) * 0.003
    for index, asset in enumerate(("SOL", "BTC", "ETH")):
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


def verify_analytical_contract() -> None:
    identity = spectral_metrics_from_correlation(np.eye(4))
    if not np.isclose(identity["dominant_eigenvalue_share"], 0.25):
        raise RuntimeError("Identity-matrix dominant share is incorrect.")
    if not np.isclose(identity["participation_ratio"], 4.0):
        raise RuntimeError("Identity-matrix participation ratio is incorrect.")
    if not np.isclose(identity["spectral_entropy"], 1.0):
        raise RuntimeError("Identity-matrix spectral entropy is incorrect.")

    common = spectral_metrics_from_correlation(np.ones((4, 4)))
    if not np.isclose(common["dominant_eigenvalue_share"], 1.0):
        raise RuntimeError("Common-mode dominant share is incorrect.")
    if not np.isclose(common["participation_ratio"], 1.0):
        raise RuntimeError("Common-mode participation ratio is incorrect.")


def verify_causal_contract() -> None:
    frame = synthetic_panel()
    panel = PanelSpec(
        members=("SOL@fixture", "BTC@fixture", "ETH@fixture"),
        dependence_windows=(20,),
        minimum_complete_observations=15,
        minimum_window_coverage=0.80,
    )
    baseline = compute_spectral_feature_frame(frame, panel).frame
    cutoff = pd.Timestamp("2026-01-06T00:00:00Z")
    mutated = frame.copy()
    future = mutated["timestamp"] > cutoff
    mutated.loc[future, "close"] *= np.linspace(1.0, 1.8, int(future.sum()))
    changed = compute_spectral_feature_frame(mutated, panel).frame
    columns = [
        "timestamp",
        "window",
        "eligibility_status",
        "dominant_eigenvalue_share",
        "spectral_entropy",
        "average_correlation",
    ]
    left = baseline.loc[baseline["timestamp"] <= cutoff, columns].reset_index(drop=True)
    right = changed.loc[changed["timestamp"] <= cutoff, columns].reset_index(drop=True)
    try:
        pd.testing.assert_frame_equal(left, right)
    except AssertionError as exc:
        raise RuntimeError("Future observations changed prior spectral outputs.") from exc


def main() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("gate") != "V3-2":
        raise RuntimeError("Unexpected gate identifier in Version 3 spectral lock.")
    if lock.get("schema_version") != SPECTRAL_SCHEMA_VERSION:
        raise RuntimeError("Gate lock and spectral schema versions differ.")
    verify_locked_files(lock)
    verify_analytical_contract()
    verify_causal_contract()
    print("Gate V3-2 causal spectral engine lock verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
