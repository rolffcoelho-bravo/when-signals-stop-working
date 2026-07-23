from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from .data_contract import (
    CanonicalDataError,
    CanonicalMarketFrame,
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
    SCHEMA_VERSION,
    SourceManifest,
    ValidationReport,
    canonicalize_market_frame,
    file_sha256,
    stable_frame_hash,
    stable_mapping_hash,
)


class MarketDataAdapter(ABC):
    """Boundary between source-specific market data and Version 3 model code."""

    @abstractmethod
    def load(self, config: Mapping[str, Any]) -> CanonicalMarketFrame:
        raise NotImplementedError

    @abstractmethod
    def source_manifest(self) -> SourceManifest:
        raise NotImplementedError

    @abstractmethod
    def validate_source(self) -> ValidationReport:
        raise NotImplementedError


@dataclass
class FileMarketDataAdapter(MarketDataAdapter):
    adapter_id: str = "v3.file-market-data.v1"
    _manifest: SourceManifest | None = None
    _validation: ValidationReport | None = None

    def _read(
        self,
        path: Path,
        source_format: str,
        read_options: Mapping[str, Any],
    ) -> pd.DataFrame:
        if source_format == "csv":
            return pd.read_csv(path, **dict(read_options))
        if source_format == "parquet":
            try:
                return pd.read_parquet(path, **dict(read_options))
            except ImportError as exc:
                raise CanonicalDataError(
                    "Parquet input requires an installed pandas parquet engine."
                ) from exc
        raise CanonicalDataError(f"Unsupported file format: {source_format}")

    def load(self, config: Mapping[str, Any]) -> CanonicalMarketFrame:
        path = Path(str(config["path"])).expanduser().resolve()
        if not path.is_file():
            raise CanonicalDataError(f"Source file does not exist: {path}")

        source_format = str(config.get("format") or path.suffix.lstrip(".")).lower()
        raw = self._read(path, source_format, config.get("read_options", {}))
        mapped = self._map_columns(raw, config)
        canonical, validation = canonicalize_market_frame(
            mapped,
            timezone=str(config.get("timezone", "UTC")),
            timestamp_unit=config.get("timestamp_unit"),
        )
        data_hash = stable_frame_hash(canonical)
        manifest = SourceManifest(
            adapter_id=self.adapter_id,
            source_uri=path.as_uri(),
            source_format=source_format,
            source_sha256=file_sha256(path),
            config_sha256=stable_mapping_hash(dict(config)),
            schema_version=SCHEMA_VERSION,
            loaded_rows=int(len(canonical)),
            data_sha256=data_hash,
        )
        self._manifest = manifest
        self._validation = validation
        return CanonicalMarketFrame(canonical, validation, manifest)

    def _map_columns(
        self,
        raw: pd.DataFrame,
        config: Mapping[str, Any],
    ) -> pd.DataFrame:
        column_map = dict(config.get("column_map", {}))
        unknown_targets = [
            canonical
            for canonical in column_map
            if canonical not in REQUIRED_COLUMNS and canonical not in OPTIONAL_COLUMNS
        ]
        if unknown_targets:
            raise CanonicalDataError(
                f"Column map contains unregistered canonical fields: {unknown_targets}"
            )

        output = pd.DataFrame(index=raw.index)
        for canonical in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
            source = column_map.get(canonical)
            if source is not None:
                if source not in raw.columns:
                    raise CanonicalDataError(
                        f"Configured source column {source!r} for {canonical!r} is missing."
                    )
                output[canonical] = raw[source]
            elif canonical in raw.columns:
                output[canonical] = raw[canonical]

        constants = dict(config.get("constants", {}))
        for canonical, value in constants.items():
            if canonical not in REQUIRED_COLUMNS and canonical not in OPTIONAL_COLUMNS:
                raise CanonicalDataError(
                    f"Constant targets unregistered canonical field: {canonical}"
                )
            output[canonical] = value

        return output

    def source_manifest(self) -> SourceManifest:
        if self._manifest is None:
            raise RuntimeError("load() must be called before source_manifest().")
        return self._manifest

    def validate_source(self) -> ValidationReport:
        if self._validation is None:
            raise RuntimeError("load() must be called before validate_source().")
        return self._validation


@dataclass
class CcxtOHLCVAdapter(MarketDataAdapter):
    adapter_id: str = "v3.ccxt-ohlcv.v1"
    _manifest: SourceManifest | None = None
    _validation: ValidationReport | None = None

    def load(self, config: Mapping[str, Any]) -> CanonicalMarketFrame:
        from shockbridge_signal_validity.data import fetch_ccxt_ohlcv

        required = ("symbol", "timeframe", "start", "exchange")
        missing = [field for field in required if not config.get(field)]
        if missing:
            raise CanonicalDataError(f"Missing CCXT adapter configuration: {missing}")

        raw = fetch_ccxt_ohlcv(
            symbol=str(config["symbol"]),
            timeframe=str(config["timeframe"]),
            start=str(config["start"]),
            end=None if config.get("end") is None else str(config["end"]),
            exchange_id=str(config["exchange"]),
            limit=int(config.get("limit", 1000)),
        ).reset_index()
        raw.columns = [str(column).strip().lower() for column in raw.columns]
        timestamp_column = "timestamp" if "timestamp" in raw.columns else raw.columns[0]
        raw = raw.rename(columns={timestamp_column: "timestamp"})
        raw["asset"] = str(config.get("asset") or config["symbol"])
        raw["venue"] = str(config.get("venue") or config["exchange"])
        canonical, validation = canonicalize_market_frame(raw, timezone="UTC")
        data_hash = stable_frame_hash(canonical)
        source_uri = (
            f"ccxt://{config['exchange']}/{config['symbol']}"
            f"?timeframe={config['timeframe']}&start={config['start']}"
            f"&end={config.get('end', '')}"
        )
        manifest = SourceManifest(
            adapter_id=self.adapter_id,
            source_uri=source_uri,
            source_format="ccxt_ohlcv",
            source_sha256=data_hash,
            config_sha256=stable_mapping_hash(dict(config)),
            schema_version=SCHEMA_VERSION,
            loaded_rows=int(len(canonical)),
            data_sha256=data_hash,
        )
        self._manifest = manifest
        self._validation = validation
        return CanonicalMarketFrame(canonical, validation, manifest)

    def source_manifest(self) -> SourceManifest:
        if self._manifest is None:
            raise RuntimeError("load() must be called before source_manifest().")
        return self._manifest

    def validate_source(self) -> ValidationReport:
        if self._validation is None:
            raise RuntimeError("load() must be called before validate_source().")
        return self._validation


@dataclass
class OptionalFieldFileAdapter:
    """Load keyed supplemental fields without allowing hidden imputation."""

    adapter_id: str = "v3.optional-field-file.v1"

    def load(self, config: Mapping[str, Any]) -> pd.DataFrame:
        path = Path(str(config["path"])).expanduser().resolve()
        source_format = str(config.get("format") or path.suffix.lstrip(".")).lower()
        if source_format == "csv":
            raw = pd.read_csv(path, **dict(config.get("read_options", {})))
        elif source_format == "parquet":
            try:
                raw = pd.read_parquet(path, **dict(config.get("read_options", {})))
            except ImportError as exc:
                raise CanonicalDataError(
                    "Parquet input requires an installed pandas parquet engine."
                ) from exc
        else:
            raise CanonicalDataError(
                f"Unsupported optional-field format: {source_format}"
            )

        column_map = dict(config.get("column_map", {}))
        fields = tuple(config.get("fields", ()))
        if not fields:
            raise CanonicalDataError("At least one governed optional field is required.")
        unknown = [field for field in fields if field not in OPTIONAL_COLUMNS]
        if unknown:
            raise CanonicalDataError(f"Unregistered optional fields: {unknown}")

        output = pd.DataFrame(index=raw.index)
        for canonical in ("timestamp", "asset", "venue") + fields:
            source = column_map.get(canonical, canonical)
            if source not in raw.columns:
                raise CanonicalDataError(
                    f"Missing supplemental source column {source!r} for {canonical!r}."
                )
            output[canonical] = raw[source]

        output["timestamp"] = pd.to_datetime(
            output["timestamp"],
            unit=config.get("timestamp_unit"),
            utc=True,
            errors="coerce",
        )
        output["asset"] = output["asset"].astype("string").str.strip()
        output["venue"] = output["venue"].astype("string").str.strip()
        for field in fields:
            output[field] = pd.to_numeric(output[field], errors="coerce")
        if output[["timestamp", "asset", "venue"]].isna().any().any():
            raise CanonicalDataError("Supplemental data contain missing canonical keys.")
        if output.duplicated(["timestamp", "asset", "venue"]).any():
            raise CanonicalDataError(
                "Supplemental data contain duplicate canonical keys."
            )
        return output.sort_values(
            ["timestamp", "asset", "venue"]
        ).reset_index(drop=True)


def merge_optional_fields(
    base: CanonicalMarketFrame,
    supplement: pd.DataFrame,
) -> CanonicalMarketFrame:
    fields = [
        column
        for column in supplement.columns
        if column not in ("timestamp", "asset", "venue")
    ]
    unknown = [field for field in fields if field not in OPTIONAL_COLUMNS]
    if unknown:
        raise CanonicalDataError(f"Unregistered supplemental fields: {unknown}")
    collisions = [field for field in fields if field in base.frame.columns]
    if collisions:
        raise CanonicalDataError(
            f"Supplemental fields already exist in the canonical frame: {collisions}"
        )
    merged = base.frame.merge(
        supplement,
        how="left",
        on=["timestamp", "asset", "venue"],
        validate="one_to_one",
        sort=False,
    )
    canonical, validation = canonicalize_market_frame(merged, timezone="UTC")
    data_hash = stable_frame_hash(canonical)
    manifest = SourceManifest(
        adapter_id=f"{base.manifest.adapter_id}+v3.optional-field-merge.v1",
        source_uri=base.manifest.source_uri,
        source_format=base.manifest.source_format,
        source_sha256=base.manifest.source_sha256,
        config_sha256=stable_mapping_hash(
            {
                "base_manifest": base.manifest.manifest_sha256,
                "supplement_fields": fields,
                "supplement_hash": stable_frame_hash(supplement),
            }
        ),
        schema_version=SCHEMA_VERSION,
        loaded_rows=int(len(canonical)),
        data_sha256=data_hash,
    )
    return CanonicalMarketFrame(canonical, validation, manifest)


def build_adapter(adapter_type: str) -> MarketDataAdapter:
    normalized = adapter_type.strip().lower()
    if normalized in {"file", "csv", "parquet"}:
        return FileMarketDataAdapter()
    if normalized in {"ccxt", "exchange"}:
        return CcxtOHLCVAdapter()
    raise CanonicalDataError(f"Unknown Version 3 adapter type: {adapter_type}")
