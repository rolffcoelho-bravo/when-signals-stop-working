from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .forecast_contract import ForecastContract, ForecastProtocolViolation, require_utc_index


@dataclass(frozen=True)
class PurgedFold:
    fold: int
    train_indices: np.ndarray
    purge_indices: np.ndarray
    test_indices: np.ndarray

    @property
    def train_rows(self) -> int:
        return int(len(self.train_indices))

    @property
    def purge_rows(self) -> int:
        return int(len(self.purge_indices))

    @property
    def test_rows(self) -> int:
        return int(len(self.test_indices))


def purged_expanding_folds(
    n_samples: int,
    n_splits: int,
    purge_gap: int,
) -> list[PurgedFold]:
    if int(n_samples) < 1:
        raise ForecastProtocolViolation("Chronological folds require observations.")
    if int(n_splits) < 2:
        raise ForecastProtocolViolation("At least two chronological folds are required.")
    if int(purge_gap) < 0:
        raise ForecastProtocolViolation("Purge gap cannot be negative.")

    test_size = int(n_samples) // (int(n_splits) + 1)
    initial_train = int(n_samples) - int(n_splits) * test_size
    if test_size < 1 or initial_train <= int(purge_gap):
        raise ForecastProtocolViolation("Insufficient observations for the fold plan.")

    folds: list[PurgedFold] = []
    for fold_number in range(1, int(n_splits) + 1):
        test_start = initial_train + (fold_number - 1) * test_size
        test_end = int(n_samples) if fold_number == int(n_splits) else test_start + test_size
        train_end = test_start - int(purge_gap)
        if train_end <= 0:
            raise ForecastProtocolViolation("Purge gap removed all training observations.")
        folds.append(
            PurgedFold(
                fold=fold_number,
                train_indices=np.arange(0, train_end, dtype=int),
                purge_indices=np.arange(train_end, test_start, dtype=int),
                test_indices=np.arange(test_start, test_end, dtype=int),
            )
        )
    return folds


def _fold_record(
    *,
    level: str,
    horizon: int,
    fold: PurgedFold,
    index: pd.DatetimeIndex,
    target_timestamps: pd.DatetimeIndex,
    outer_fold: int | None = None,
) -> dict[str, object]:
    return {
        "level": level,
        "horizon_candles": int(horizon),
        "horizon_hours": int(horizon * 4),
        "outer_fold": int(outer_fold if outer_fold is not None else fold.fold),
        "inner_fold": int(fold.fold) if outer_fold is not None else None,
        "train_rows": fold.train_rows,
        "purge_rows": fold.purge_rows,
        "test_rows": fold.test_rows,
        "train_start_utc": index[fold.train_indices[0]].isoformat(),
        "train_end_utc": index[fold.train_indices[-1]].isoformat(),
        "test_start_utc": index[fold.test_indices[0]].isoformat(),
        "test_end_utc": index[fold.test_indices[-1]].isoformat(),
        "maximum_train_target_timestamp_utc": target_timestamps[
            fold.train_indices
        ].max().isoformat(),
        "minimum_test_target_timestamp_utc": target_timestamps[
            fold.test_indices
        ].min().isoformat(),
        "shuffle": False,
    }


def build_nested_fold_plan(
    targets: pd.DataFrame,
    contract: ForecastContract,
) -> pd.DataFrame:
    required = {
        "timestamp",
        "target_timestamp",
        "horizon_candles",
        "future_log_return",
        "direction",
        "segment",
    }
    missing = sorted(required.difference(targets.columns))
    if missing:
        raise ForecastProtocolViolation(
            "Fold-plan target input is missing: " + ", ".join(missing)
        )
    if set(targets["segment"].astype(str)) != {"DEVELOPMENT"}:
        raise ForecastProtocolViolation("Fold plans may use development targets only.")

    records: list[dict[str, object]] = []
    observed_horizons = tuple(sorted(int(value) for value in targets["horizon_candles"].unique()))
    if any(horizon not in contract.horizons for horizon in observed_horizons):
        raise ForecastProtocolViolation("Fold plan contains an unregistered horizon.")

    for horizon in observed_horizons:
        horizon_frame = targets.loc[targets["horizon_candles"] == horizon].copy()
        horizon_frame["timestamp"] = pd.to_datetime(horizon_frame["timestamp"], utc=True)
        horizon_frame["target_timestamp"] = pd.to_datetime(
            horizon_frame["target_timestamp"], utc=True
        )
        horizon_frame = horizon_frame.sort_values("timestamp", kind="mergesort")
        index = require_utc_index(
            pd.DatetimeIndex(horizon_frame["timestamp"]),
            f"horizon {horizon} fold timestamps",
        )
        contract.assert_development_only(index)
        target_timestamps = require_utc_index(
            pd.DatetimeIndex(horizon_frame["target_timestamp"]),
            f"horizon {horizon} target timestamps",
        )
        if target_timestamps.max() > contract.development_end:
            raise ForecastProtocolViolation("Fold target timestamps cross development end.")

        outer_folds = purged_expanding_folds(
            n_samples=len(index),
            n_splits=contract.outer_folds,
            purge_gap=horizon,
        )
        for outer in outer_folds:
            if target_timestamps[outer.train_indices].max() >= index[outer.test_indices[0]]:
                raise ForecastProtocolViolation(
                    "Outer training targets overlap the outer test origin."
                )
            records.append(
                _fold_record(
                    level="outer",
                    horizon=horizon,
                    fold=outer,
                    index=index,
                    target_timestamps=target_timestamps,
                )
            )
            inner_index = index[outer.train_indices]
            inner_targets = target_timestamps[outer.train_indices]
            inner_folds = purged_expanding_folds(
                n_samples=len(inner_index),
                n_splits=contract.inner_folds,
                purge_gap=horizon,
            )
            for inner in inner_folds:
                if inner_targets[inner.train_indices].max() >= inner_index[inner.test_indices[0]]:
                    raise ForecastProtocolViolation(
                        "Inner training targets overlap the inner test origin."
                    )
                records.append(
                    _fold_record(
                        level="inner",
                        horizon=horizon,
                        fold=inner,
                        index=inner_index,
                        target_timestamps=inner_targets,
                        outer_fold=outer.fold,
                    )
                )

    plan = pd.DataFrame.from_records(records)
    expected_rows = len(observed_horizons) * contract.outer_folds * (
        1 + contract.inner_folds
    )
    if len(plan) != expected_rows:
        raise ForecastProtocolViolation(
            f"Fold-plan identity failed: expected {expected_rows}, observed {len(plan)}."
        )
    return plan.sort_values(
        ["horizon_candles", "outer_fold", "level", "inner_fold"],
        kind="mergesort",
        na_position="first",
    ).reset_index(drop=True)
