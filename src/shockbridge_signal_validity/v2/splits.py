from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from .contracts import ProtocolViolation


@dataclass(frozen=True)
class PurgedFold:
    fold: int
    train_indices: np.ndarray
    test_indices: np.ndarray
    purge_indices: np.ndarray

    @property
    def train_rows(self) -> int:
        return int(len(self.train_indices))

    @property
    def test_rows(self) -> int:
        return int(len(self.test_indices))


def purged_expanding_folds(
    n_samples: int,
    n_splits: int,
    purge_gap: int,
) -> list[PurgedFold]:
    if n_samples < 1:
        raise ProtocolViolation("Chronological folds require observations.")
    if n_splits < 2:
        raise ProtocolViolation("At least two chronological folds are required.")
    if purge_gap < 0:
        raise ProtocolViolation("Purge gap cannot be negative.")

    test_size = n_samples // (n_splits + 1)
    initial_train = n_samples - n_splits * test_size
    if test_size < 1 or initial_train <= purge_gap:
        raise ProtocolViolation("Insufficient observations for the requested fold plan.")

    folds: list[PurgedFold] = []
    for fold_number in range(1, n_splits + 1):
        test_start = initial_train + (fold_number - 1) * test_size
        test_end = n_samples if fold_number == n_splits else test_start + test_size
        train_end = test_start - purge_gap
        if train_end <= 0:
            raise ProtocolViolation("Purge gap removed the complete training partition.")
        train_indices = np.arange(0, train_end, dtype=int)
        purge_indices = np.arange(train_end, test_start, dtype=int)
        test_indices = np.arange(test_start, test_end, dtype=int)
        folds.append(
            PurgedFold(
                fold=fold_number,
                train_indices=train_indices,
                test_indices=test_indices,
                purge_indices=purge_indices,
            )
        )
    return folds


def _fold_record(
    level: str,
    horizon: int,
    fold: PurgedFold,
    index: pd.DatetimeIndex,
    parent_outer_fold: int | None = None,
) -> dict[str, object]:
    return {
        "level": level,
        "horizon_candles": int(horizon),
        "horizon_hours": int(horizon * 4),
        "outer_fold": parent_outer_fold if parent_outer_fold is not None else fold.fold,
        "inner_fold": fold.fold if parent_outer_fold is not None else None,
        "train_rows": fold.train_rows,
        "purge_rows": int(len(fold.purge_indices)),
        "test_rows": fold.test_rows,
        "train_start_utc": index[fold.train_indices[0]].isoformat(),
        "train_end_utc": index[fold.train_indices[-1]].isoformat(),
        "test_start_utc": index[fold.test_indices[0]].isoformat(),
        "test_end_utc": index[fold.test_indices[-1]].isoformat(),
    }


def build_nested_fold_plan(
    index: pd.DatetimeIndex,
    horizons: Iterable[int],
    outer_splits: int,
    inner_splits: int,
) -> pd.DataFrame:
    if not isinstance(index, pd.DatetimeIndex) or index.tz is None:
        raise ProtocolViolation("Fold plans require timezone-aware timestamps.")
    if not index.is_monotonic_increasing or index.has_duplicates:
        raise ProtocolViolation("Fold-plan timestamps must be unique and chronological.")

    records: list[dict[str, object]] = []
    for horizon in sorted({int(value) for value in horizons}):
        outer_folds = purged_expanding_folds(
            n_samples=len(index),
            n_splits=outer_splits,
            purge_gap=horizon,
        )
        for outer in outer_folds:
            records.append(_fold_record("outer", horizon, outer, index))
            inner_index = index[outer.train_indices]
            inner_folds = purged_expanding_folds(
                n_samples=len(inner_index),
                n_splits=inner_splits,
                purge_gap=horizon,
            )
            for inner in inner_folds:
                records.append(
                    _fold_record(
                        "inner",
                        horizon,
                        inner,
                        inner_index,
                        parent_outer_fold=outer.fold,
                    )
                )
    return pd.DataFrame.from_records(records)
