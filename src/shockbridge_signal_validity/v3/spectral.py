from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from .data_contract import KEY_COLUMNS, OPTIONAL_COLUMNS, REQUIRED_COLUMNS, stable_frame_hash


class SpectralFeatureError(ValueError):
    """Raised when Gate V3-2 cannot satisfy its fixed-panel causal contract."""


SPECTRAL_SCHEMA_VERSION = "v3.market-structure.v1"


@dataclass(frozen=True)
class PanelSpec:
    members: tuple[str, ...]
    dependence_windows: tuple[int, ...] = (30, 60, 120)
    minimum_complete_observations: int = 20
    minimum_window_coverage: float = 0.80
    estimator: str = "sample"
    ewma_decay: float = 0.94
    shrinkage_alpha: float = 0.10
    network_threshold: float = 0.50

    def __post_init__(self) -> None:
        members = tuple(str(member).strip() for member in self.members)
        if len(members) < 2:
            raise SpectralFeatureError("PanelSpec requires at least two explicit members.")
        if len(set(members)) != len(members):
            raise SpectralFeatureError("PanelSpec members must be unique.")
        if any("@" not in member for member in members):
            raise SpectralFeatureError(
                "Panel members must use the stable 'asset@venue' identifier."
            )
        if not self.dependence_windows or any(
            int(window) < 3 for window in self.dependence_windows
        ):
            raise SpectralFeatureError("Dependence windows must contain integers >= 3.")
        if self.minimum_complete_observations < 3:
            raise SpectralFeatureError("minimum_complete_observations must be >= 3.")
        if not 0.0 < self.minimum_window_coverage <= 1.0:
            raise SpectralFeatureError("minimum_window_coverage must be in (0, 1].")
        if self.estimator not in {"sample", "ewma", "shrinkage"}:
            raise SpectralFeatureError(
                "estimator must be one of: sample, ewma, shrinkage."
            )
        if not 0.0 < self.ewma_decay < 1.0:
            raise SpectralFeatureError("ewma_decay must be in (0, 1).")
        if not 0.0 <= self.shrinkage_alpha <= 1.0:
            raise SpectralFeatureError("shrinkage_alpha must be in [0, 1].")
        if not 0.0 <= self.network_threshold <= 1.0:
            raise SpectralFeatureError("network_threshold must be in [0, 1].")
        object.__setattr__(self, "members", members)
        object.__setattr__(
            self,
            "dependence_windows",
            tuple(sorted(set(int(window) for window in self.dependence_windows))),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CausalFeatureConfig:
    volatility_windows: tuple[int, ...] = (6, 18, 42)
    stress_window: int = 42
    volume_window: int = 42

    def __post_init__(self) -> None:
        if not self.volatility_windows or any(
            int(window) < 2 for window in self.volatility_windows
        ):
            raise SpectralFeatureError(
                "volatility_windows must contain integers >= 2."
            )
        if self.stress_window < 2 or self.volume_window < 2:
            raise SpectralFeatureError(
                "stress_window and volume_window must be >= 2."
            )
        object.__setattr__(
            self,
            "volatility_windows",
            tuple(sorted(set(int(window) for window in self.volatility_windows))),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SpectralRunManifest:
    schema_version: str
    input_sha256: str
    config_sha256: str
    output_sha256: str
    panel_members: tuple[str, ...]
    rows: int
    timestamps: int
    estimator: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def manifest_sha256(self) -> str:
        payload = json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")
        return sha256(payload).hexdigest()


@dataclass(frozen=True)
class SpectralFeatureFrame:
    frame: pd.DataFrame
    series_features: pd.DataFrame
    manifest: SpectralRunManifest
    diagnostics: Mapping[str, Any] = field(default_factory=dict)


def _stable_mapping_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def _series_id(asset: pd.Series, venue: pd.Series) -> pd.Series:
    return asset.astype("string").str.strip() + "@" + venue.astype("string").str.strip()


def _validate_canonical_input(frame: pd.DataFrame, panel: PanelSpec) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise SpectralFeatureError(f"Missing canonical columns: {missing}")
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    if data["timestamp"].isna().any():
        raise SpectralFeatureError("Canonical timestamps must be valid UTC values.")
    if data.duplicated(list(KEY_COLUMNS)).any():
        raise SpectralFeatureError("Duplicate canonical keys are prohibited.")
    data["series_id"] = _series_id(data["asset"], data["venue"])
    observed = set(data["series_id"].unique())
    absent = sorted(set(panel.members).difference(observed))
    if absent:
        raise SpectralFeatureError(
            "Explicit panel members are absent from the dataset: " + ", ".join(absent)
        )
    data = data.loc[data["series_id"].isin(panel.members)].copy()
    data["series_id"] = pd.Categorical(
        data["series_id"], categories=list(panel.members), ordered=True
    )
    return data.sort_values(
        ["timestamp", "series_id"], kind="mergesort"
    ).reset_index(drop=True)


def build_close_panel(frame: pd.DataFrame, panel: PanelSpec) -> pd.DataFrame:
    data = _validate_canonical_input(frame, panel)
    close = data.pivot(index="timestamp", columns="series_id", values="close")
    close = close.reindex(columns=list(panel.members)).sort_index()
    close.columns = pd.Index([str(column) for column in close.columns], name="series_id")
    return close.astype(float)


def build_return_panel(frame: pd.DataFrame, panel: PanelSpec) -> pd.DataFrame:
    close = build_close_panel(frame, panel)
    with np.errstate(divide="ignore", invalid="ignore"):
        returns = np.log(close).diff()
    returns.columns = close.columns
    return returns.replace([np.inf, -np.inf], np.nan)


def _safe_rolling_zscore(values: pd.Series, window: int) -> pd.Series:
    mean = values.rolling(window, min_periods=window).mean()
    std = values.rolling(window, min_periods=window).std(ddof=1)
    return (values - mean) / std.replace(0.0, np.nan)


def build_causal_series_features(
    frame: pd.DataFrame,
    panel: PanelSpec,
    config: CausalFeatureConfig | None = None,
) -> pd.DataFrame:
    config = config or CausalFeatureConfig()
    data = _validate_canonical_input(frame, panel)
    output: list[pd.DataFrame] = []

    for member, group in data.groupby("series_id", observed=True, sort=False):
        group = group.sort_values("timestamp", kind="mergesort").copy()
        close = group["close"].astype(float)
        log_close = np.log(close)
        returns = log_close.diff()
        features = group[["timestamp", "asset", "venue"]].copy()
        features["series_id"] = str(member)
        features["log_return_1"] = returns
        features["drawdown"] = log_close - log_close.cummax()
        features["drawdown_velocity"] = features["drawdown"].diff()
        features["downside_semivariance"] = returns.clip(upper=0.0).pow(2).rolling(
            config.stress_window, min_periods=config.stress_window
        ).mean()
        features["downside_return_acceleration"] = returns.diff()
        for window in config.volatility_windows:
            features[f"realised_volatility_{window}"] = returns.rolling(
                window, min_periods=window
            ).std(ddof=1)
        volume = group["volume"].astype(float)
        features["volume_log_change"] = np.log1p(volume).diff()
        features["abnormal_volume_z"] = _safe_rolling_zscore(
            np.log1p(volume), config.volume_window
        )

        if "bid_ask_spread" in group:
            features["bid_ask_spread"] = group["bid_ask_spread"].astype(float)
            features["bid_ask_spread_z"] = _safe_rolling_zscore(
                features["bid_ask_spread"], config.stress_window
            )
        if "order_book_depth" in group:
            depth = group["order_book_depth"].astype(float)
            features["order_book_depth_log_change"] = np.log1p(depth).diff()
        if "order_book_imbalance" in group:
            features["order_book_imbalance"] = group["order_book_imbalance"].astype(float)
        if "open_interest" in group:
            open_interest = group["open_interest"].astype(float)
            features["open_interest_log_change"] = np.log1p(open_interest).diff()
        if "funding_rate" in group:
            funding = group["funding_rate"].astype(float)
            features["funding_rate"] = funding
            features["funding_stress_z"] = _safe_rolling_zscore(
                funding.abs(), config.stress_window
            )
        if "long_liquidations" in group or "short_liquidations" in group:
            long_liq = (
                group["long_liquidations"].astype(float)
                if "long_liquidations" in group
                else pd.Series(0.0, index=group.index)
            )
            short_liq = (
                group["short_liquidations"].astype(float)
                if "short_liquidations" in group
                else pd.Series(0.0, index=group.index)
            )
            total_liq = long_liq.fillna(0.0) + short_liq.fillna(0.0)
            features["liquidation_intensity"] = total_liq / volume.replace(0.0, np.nan)
            features["net_liquidation_pressure"] = (
                long_liq.fillna(0.0) - short_liq.fillna(0.0)
            ) / volume.replace(0.0, np.nan)
        if "cross_venue_price_dispersion" in group:
            features["cross_venue_price_dispersion"] = group[
                "cross_venue_price_dispersion"
            ].astype(float)
        if "exchange_inflows" in group or "exchange_outflows" in group:
            inflow = (
                group["exchange_inflows"].astype(float)
                if "exchange_inflows" in group
                else pd.Series(np.nan, index=group.index)
            )
            outflow = (
                group["exchange_outflows"].astype(float)
                if "exchange_outflows" in group
                else pd.Series(np.nan, index=group.index)
            )
            features["net_exchange_flow"] = inflow - outflow
        output.append(features)

    result = pd.concat(output, ignore_index=True)
    result["series_id"] = pd.Categorical(
        result["series_id"], categories=list(panel.members), ordered=True
    )
    return result.sort_values(
        ["timestamp", "series_id"], kind="mergesort"
    ).reset_index(drop=True)


def _weighted_covariance(values: np.ndarray, decay: float) -> np.ndarray:
    rows = values.shape[0]
    weights = np.power(decay, np.arange(rows - 1, -1, -1, dtype=float))
    weights /= weights.sum()
    mean = np.sum(values * weights[:, None], axis=0)
    centered = values - mean
    covariance = (centered * weights[:, None]).T @ centered
    correction = 1.0 - float(np.sum(weights**2))
    if correction <= 0.0:
        raise SpectralFeatureError("EWMA window has insufficient effective observations.")
    return covariance / correction


def _covariance_to_correlation(covariance: np.ndarray) -> np.ndarray:
    variances = np.diag(covariance)
    if np.any(~np.isfinite(variances)) or np.any(variances <= 0.0):
        raise SpectralFeatureError(
            "Dependence window contains a zero-variance or invalid panel member."
        )
    scale = np.sqrt(variances)
    correlation = covariance / np.outer(scale, scale)
    correlation = (correlation + correlation.T) / 2.0
    np.fill_diagonal(correlation, 1.0)
    return np.clip(correlation, -1.0, 1.0)


def estimate_correlation(values: np.ndarray, panel: PanelSpec) -> np.ndarray:
    if values.ndim != 2 or values.shape[1] != len(panel.members):
        raise SpectralFeatureError("Dependence values do not match the fixed panel.")
    if values.shape[0] < panel.minimum_complete_observations:
        raise SpectralFeatureError("Insufficient complete observations.")
    if not np.isfinite(values).all():
        raise SpectralFeatureError("Dependence values must be finite complete cases.")

    if panel.estimator == "ewma":
        covariance = _weighted_covariance(values, panel.ewma_decay)
    else:
        covariance = np.cov(values, rowvar=False, ddof=1)
        if panel.estimator == "shrinkage":
            diagonal = np.diag(np.diag(covariance))
            covariance = (
                (1.0 - panel.shrinkage_alpha) * covariance
                + panel.shrinkage_alpha * diagonal
            )
    return _covariance_to_correlation(np.asarray(covariance, dtype=float))


def spectral_metrics_from_correlation(
    correlation: np.ndarray,
    *,
    network_threshold: float = 0.50,
) -> dict[str, Any]:
    matrix = np.asarray(correlation, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] < 2:
        raise SpectralFeatureError("Correlation matrix must be square with size >= 2.")
    if not np.isfinite(matrix).all():
        raise SpectralFeatureError("Correlation matrix contains non-finite values.")
    if not np.allclose(matrix, matrix.T, atol=1e-10):
        raise SpectralFeatureError("Correlation matrix must be symmetric.")
    if not np.allclose(np.diag(matrix), 1.0, atol=1e-8):
        raise SpectralFeatureError("Correlation matrix diagonal must equal one.")

    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = np.clip(eigenvalues[order], 0.0, None)
    eigenvectors = eigenvectors[:, order]
    total = float(eigenvalues.sum())
    if total <= 0.0:
        raise SpectralFeatureError("Correlation matrix has no positive spectral mass.")
    shares = eigenvalues / total
    positive = shares[shares > 0.0]
    n_assets = matrix.shape[0]
    entropy = -float(np.sum(positive * np.log(positive)))
    normalized_entropy = entropy / np.log(n_assets) if n_assets > 1 else 0.0
    participation = total**2 / float(np.sum(eigenvalues**2))
    first_vector = eigenvectors[:, 0]
    offdiag = matrix[np.triu_indices(n_assets, 1)]
    adjacency = np.abs(matrix) >= network_threshold
    np.fill_diagonal(adjacency, False)
    possible_edges = n_assets * (n_assets - 1)
    network_density = float(adjacency.sum() / possible_edges)
    degrees = adjacency.sum(axis=1).astype(float)
    degree_total = float(degrees.sum())
    degree_concentration = (
        float(np.sum((degrees / degree_total) ** 2)) if degree_total > 0.0 else 0.0
    )
    return {
        "n_assets": int(n_assets),
        "dominant_eigenvalue": float(eigenvalues[0]),
        "dominant_eigenvalue_share": float(shares[0]),
        "eigenvalue_gap": float((eigenvalues[0] - eigenvalues[1]) / total),
        "participation_ratio": float(participation),
        "effective_dimension": float(participation),
        "spectral_entropy": float(normalized_entropy),
        "first_eigenvector_concentration": float(np.sum(first_vector**4)),
        "average_correlation": float(offdiag.mean()),
        "correlation_dispersion": float(offdiag.std(ddof=0)),
        "network_density": network_density,
        "network_degree_concentration": degree_concentration,
        "first_eigenvector": first_vector,
        "eigenvalues": eigenvalues,
    }


def summarize_window_sensitivity(spectral_frame: pd.DataFrame) -> dict[str, Any]:
    required = {
        "timestamp",
        "window",
        "eligibility_status",
        "dominant_eigenvalue_share",
        "spectral_entropy",
        "average_correlation",
    }
    missing = sorted(required.difference(spectral_frame.columns))
    if missing:
        raise SpectralFeatureError(
            "Window-sensitivity input is missing columns: " + ", ".join(missing)
        )
    eligible = spectral_frame.loc[
        spectral_frame["eligibility_status"] == "ELIGIBLE"
    ].copy()
    summaries: dict[str, Any] = {}
    for window, group in spectral_frame.groupby("window", sort=True):
        eligible_group = group.loc[group["eligibility_status"] == "ELIGIBLE"]
        summaries[str(int(window))] = {
            "rows": int(len(group)),
            "eligible_rows": int(len(eligible_group)),
            "eligible_share": float(len(eligible_group) / len(group)) if len(group) else 0.0,
            "mean_dominant_eigenvalue_share": (
                None
                if eligible_group.empty
                else float(eligible_group["dominant_eigenvalue_share"].mean())
            ),
            "mean_spectral_entropy": (
                None
                if eligible_group.empty
                else float(eligible_group["spectral_entropy"].mean())
            ),
            "mean_average_correlation": (
                None
                if eligible_group.empty
                else float(eligible_group["average_correlation"].mean())
            ),
        }
    correlation: dict[str, float | None] = {}
    if not eligible.empty and eligible["window"].nunique() > 1:
        pivot = eligible.pivot(
            index="timestamp",
            columns="window",
            values="dominant_eigenvalue_share",
        )
        matrix = pivot.corr(min_periods=3)
        windows = sorted(int(value) for value in matrix.columns)
        for left_index, left in enumerate(windows):
            for right in windows[left_index + 1 :]:
                value = matrix.loc[left, right]
                correlation[f"{left}:{right}"] = (
                    None if pd.isna(value) else float(value)
                )
    return {
        "windows": summaries,
        "dominant_share_cross_window_correlation": correlation,
        "selection_performed": False,
    }


def compare_registered_panels(
    frame: pd.DataFrame,
    panel_specs: Sequence[PanelSpec],
    feature_config: CausalFeatureConfig | None = None,
) -> pd.DataFrame:
    if not panel_specs:
        raise SpectralFeatureError("At least one registered panel is required.")
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for panel in panel_specs:
        panel_id = _stable_mapping_hash(panel.to_dict())
        if panel_id in seen:
            raise SpectralFeatureError("Duplicate registered panel specification.")
        seen.add(panel_id)
        result = compute_spectral_feature_frame(frame, panel, feature_config)
        eligible = result.frame.loc[
            result.frame["eligibility_status"] == "ELIGIBLE"
        ]
        records.append(
            {
                "panel_id": panel_id,
                "members": "|".join(panel.members),
                "panel_size": len(panel.members),
                "estimator": panel.estimator,
                "registered_windows": "|".join(
                    str(value) for value in panel.dependence_windows
                ),
                "rows": int(len(result.frame)),
                "eligible_rows": int(len(eligible)),
                "eligible_share": (
                    float(len(eligible) / len(result.frame))
                    if len(result.frame)
                    else 0.0
                ),
                "mean_dominant_eigenvalue_share": (
                    np.nan
                    if eligible.empty
                    else float(eligible["dominant_eigenvalue_share"].mean())
                ),
                "mean_spectral_entropy": (
                    np.nan
                    if eligible.empty
                    else float(eligible["spectral_entropy"].mean())
                ),
                "mean_average_correlation": (
                    np.nan
                    if eligible.empty
                    else float(eligible["average_correlation"].mean())
                ),
                "selection_performed": False,
            }
        )
    return pd.DataFrame(records).sort_values("panel_id").reset_index(drop=True)


def compute_spectral_feature_frame(
    frame: pd.DataFrame,
    panel: PanelSpec,
    feature_config: CausalFeatureConfig | None = None,
) -> SpectralFeatureFrame:
    data = _validate_canonical_input(frame, panel)
    returns = build_return_panel(data, panel)
    series_features = build_causal_series_features(data, panel, feature_config)
    rows: list[dict[str, Any]] = []
    previous_vectors: dict[int, np.ndarray] = {}
    previous_shares: dict[int, float] = {}

    for window in panel.dependence_windows:
        for end_position, timestamp in enumerate(returns.index):
            start_position = max(0, end_position - window + 1)
            window_frame = returns.iloc[start_position : end_position + 1]
            expected_cells = int(window * len(panel.members))
            observed_cells = int(window_frame.notna().sum().sum())
            window_coverage = observed_cells / expected_cells if expected_cells else 0.0
            complete = window_frame.dropna(axis=0, how="any")
            complete_observations = int(len(complete))
            row: dict[str, Any] = {
                "timestamp": timestamp,
                "window": int(window),
                "estimator": panel.estimator,
                "panel_members": "|".join(panel.members),
                "panel_size": len(panel.members),
                "window_rows": int(len(window_frame)),
                "complete_observations": complete_observations,
                "window_coverage": float(window_coverage),
                "eligibility_status": "ELIGIBLE",
            }
            if (
                len(window_frame) < window
                or window_coverage < panel.minimum_window_coverage
                or complete_observations < panel.minimum_complete_observations
            ):
                row["eligibility_status"] = "INSUFFICIENT_PANEL_COVERAGE"
                rows.append(row)
                continue
            try:
                correlation = estimate_correlation(complete.to_numpy(dtype=float), panel)
                metrics = spectral_metrics_from_correlation(
                    correlation, network_threshold=panel.network_threshold
                )
            except SpectralFeatureError as exc:
                row["eligibility_status"] = "INELIGIBLE_DEPENDENCE_WINDOW"
                row["ineligibility_reason"] = str(exc)
                rows.append(row)
                continue

            current_vector = metrics.pop("first_eigenvector")
            eigenvalues = metrics.pop("eigenvalues")
            previous_vector = previous_vectors.get(window)
            previous_share = previous_shares.get(window)
            row.update(metrics)
            row["eigenvector_stability"] = (
                np.nan
                if previous_vector is None
                else float(abs(np.dot(previous_vector, current_vector)))
            )
            row["dominant_eigenvalue_share_change"] = (
                np.nan
                if previous_share is None
                else float(row["dominant_eigenvalue_share"] - previous_share)
            )
            row["eigenvalue_spectrum"] = json.dumps(
                [float(value) for value in eigenvalues],
                separators=(",", ":"),
            )
            previous_vectors[window] = current_vector
            previous_shares[window] = float(row["dominant_eigenvalue_share"])
            rows.append(row)

    spectral = pd.DataFrame(rows)
    spectral = spectral.sort_values(["timestamp", "window"], kind="mergesort").reset_index(
        drop=True
    )
    configuration = {
        "panel": panel.to_dict(),
        "features": (feature_config or CausalFeatureConfig()).to_dict(),
    }
    input_columns = [
        column for column in REQUIRED_COLUMNS + OPTIONAL_COLUMNS if column in data.columns
    ]
    input_hash = stable_frame_hash(
        data[input_columns].sort_values(list(KEY_COLUMNS)).reset_index(drop=True)
    )
    output_hash = stable_frame_hash(spectral)
    manifest = SpectralRunManifest(
        schema_version=SPECTRAL_SCHEMA_VERSION,
        input_sha256=input_hash,
        config_sha256=_stable_mapping_hash(configuration),
        output_sha256=output_hash,
        panel_members=panel.members,
        rows=int(len(spectral)),
        timestamps=int(spectral["timestamp"].nunique()) if not spectral.empty else 0,
        estimator=panel.estimator,
    )
    diagnostics = {
        "eligibility_counts": spectral["eligibility_status"]
        .value_counts()
        .sort_index()
        .to_dict(),
        "panel_members": list(panel.members),
        "dependence_windows": list(panel.dependence_windows),
        "estimator": panel.estimator,
        "window_sensitivity": summarize_window_sensitivity(spectral),
        "panel_selection_performed": False,
    }
    return SpectralFeatureFrame(
        frame=spectral,
        series_features=series_features,
        manifest=manifest,
        diagnostics=diagnostics,
    )
