"""Version 3 adaptive signal-validity framework."""

from .adapters import (
    CcxtOHLCVAdapter,
    FileMarketDataAdapter,
    MarketDataAdapter,
    OptionalFieldFileAdapter,
    build_adapter,
    merge_optional_fields,
)
from .data_contract import (
    CanonicalDataError,
    CanonicalMarketFrame,
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
    SCHEMA_VERSION,
    SourceManifest,
    ValidationIssue,
    ValidationReport,
    canonicalize_market_frame,
    stable_frame_hash,
)

__all__ = [
    "CanonicalDataError",
    "CanonicalMarketFrame",
    "CcxtOHLCVAdapter",
    "FileMarketDataAdapter",
    "MarketDataAdapter",
    "OPTIONAL_COLUMNS",
    "OptionalFieldFileAdapter",
    "REQUIRED_COLUMNS",
    "SCHEMA_VERSION",
    "SourceManifest",
    "ValidationIssue",
    "ValidationReport",
    "build_adapter",
    "canonicalize_market_frame",
    "merge_optional_fields",
    "stable_frame_hash",
]
