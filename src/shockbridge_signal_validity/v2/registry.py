from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .contracts import ProtocolViolation


_REQUIRED_TOP_LEVEL = {
    "registry_version",
    "freeze_status",
    "parent_release",
    "development_branch",
    "confirmatory_hypotheses",
    "data",
    "horizons_candles",
    "signal_grids",
    "model_families",
    "window_schemes",
    "validation",
    "calibration",
    "abstention",
    "v2_namespaces",
}


@dataclass(frozen=True)
class V2Registry:
    path: Path
    payload: dict[str, Any]
    sha256: str

    @property
    def protocol_version(self) -> str:
        return str(self.payload["registry_version"])

    @property
    def development_start(self) -> pd.Timestamp:
        return pd.Timestamp(self.payload["data"]["development"]["start_utc"])

    @property
    def development_end(self) -> pd.Timestamp:
        return pd.Timestamp(self.payload["data"]["development"]["end_utc"])

    @property
    def holdout_start(self) -> pd.Timestamp:
        return pd.Timestamp(
            self.payload["data"]["locked_evaluation"]["start_utc"]
        )

    @property
    def holdout_end(self) -> pd.Timestamp:
        return pd.Timestamp(self.payload["data"]["locked_evaluation"]["end_utc"])

    @property
    def horizons(self) -> tuple[int, ...]:
        return tuple(int(value) for value in self.payload["horizons_candles"])

    @property
    def outer_folds(self) -> int:
        return int(self.payload["validation"]["outer_development_folds"])

    @property
    def inner_folds(self) -> int:
        return int(self.payload["validation"]["inner_selection_folds"])

    @property
    def development_namespace(self) -> str:
        expected = "outputs/v2/development"
        namespaces = set(self.payload["v2_namespaces"])
        if expected not in namespaces:
            raise ProtocolViolation(
                f"Frozen registry does not declare {expected}."
            )
        return expected

    def require_frozen(self) -> None:
        if self.payload["freeze_status"] != "FROZEN_BEFORE_IMPLEMENTATION":
            raise ProtocolViolation(
                "Version 2 registry is not in the frozen pre-implementation state."
            )
        parent = self.payload["parent_release"]
        if parent.get("tag") != "v1.2.0":
            raise ProtocolViolation("Unexpected Version 1 parent release tag.")
        if not str(parent.get("commit", "")).startswith("748d172"):
            raise ProtocolViolation("Unexpected Version 1 parent commit.")
        if self.development_end >= self.holdout_start:
            raise ProtocolViolation(
                "Development and locked-evaluation partitions overlap."
            )


def load_v2_registry(
    path: Path | str = Path("configs/v2_experiment_registry.json"),
) -> V2Registry:
    registry_path = Path(path)
    raw = registry_path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolViolation(f"Invalid Version 2 registry: {registry_path}") from exc

    missing = sorted(_REQUIRED_TOP_LEVEL.difference(payload))
    if missing:
        raise ProtocolViolation(
            "Version 2 registry is missing required fields: " + ", ".join(missing)
        )

    registry = V2Registry(
        path=registry_path,
        payload=payload,
        sha256=hashlib.sha256(raw).hexdigest(),
    )
    registry.require_frozen()
    return registry
