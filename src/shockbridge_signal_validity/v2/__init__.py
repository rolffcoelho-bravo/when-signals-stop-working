"""Governed Version 2 development infrastructure.

The package exposes protocol-aware utilities for development-only data
partitioning, target construction, chronological fold planning, candidate
inventory generation, and holdout-access control. It intentionally contains
no fitted Version 2 model and creates no holdout performance evidence.
"""

from .contracts import HoldoutAccessError, ProtocolViolation
from .inventory import build_candidate_inventory
from .partitions import DevelopmentPartition, build_development_partition
from .registry import V2Registry, load_v2_registry
from .splits import PurgedFold, build_nested_fold_plan, purged_expanding_folds
from .targets import build_development_targets

__all__ = [
    "DevelopmentPartition",
    "HoldoutAccessError",
    "ProtocolViolation",
    "PurgedFold",
    "V2Registry",
    "build_candidate_inventory",
    "build_development_partition",
    "build_development_targets",
    "build_nested_fold_plan",
    "load_v2_registry",
    "purged_expanding_folds",
]
