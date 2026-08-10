from __future__ import annotations
from typing import Any, Mapping

import numpy as np
import pandas as pd

from .signal_math import binary
from .signal_registry import SignalSpec

def compute_spectral_feature(
    context: pd.DataFrame,
    spec: SignalSpec,
    parameters: Mapping[str, Any],
) -> pd.Series:
    """
    Computes a standalone spectral signal based on market structure context.
    """
    name = spec.interpretation
    threshold = float(parameters.get("threshold", 0.5))

    if name == "SPECTRAL_DOMINANT_EIGENVALUE_SPIKE":
        if "dominant_eigenvalue_share" not in context.columns:
            return pd.Series(np.nan, index=context.index, dtype=float)
        feature = context["dominant_eigenvalue_share"]
        return binary(feature > threshold, feature.notna())

    if name == "SPECTRAL_PARTICIPATION_DROP":
        if "participation_ratio" not in context.columns:
            return pd.Series(np.nan, index=context.index, dtype=float)
        feature = context["participation_ratio"]
        return binary(feature < threshold, feature.notna())

    if name == "SPECTRAL_EIGENVECTOR_DIVERGENCE":
        if "normalized_eigenvalue_gap" not in context.columns:
            return pd.Series(np.nan, index=context.index, dtype=float)
        feature = context["normalized_eigenvalue_gap"]
        return binary(feature > threshold, feature.notna())

    return pd.Series(np.nan, index=context.index, dtype=float)
