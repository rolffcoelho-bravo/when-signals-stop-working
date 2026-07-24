from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from .data_contract import KEY_COLUMNS, OPTIONAL_COLUMNS, REQUIRED_COLUMNS, stable_frame_hash
from .spectral import (
    CausalFeatureConfig,
    PanelSpec,
    SpectralFeatureError,
    build_causal_series_features,
    build_return_panel,
    estimate_correlation,
    spectral_metrics_from_correlation,
)

MARKET_STRUCTURE_SCHEMA_VERSION = "v3.market-structure-extension.v1"


class MarketStructureError(ValueError):
    """Raised when Gate V3-2B cannot satisfy its market-structure contract."""


@dataclass(frozen=True)
class NetworkSpec:
    threshold: float = 0.50
    use_absolute_threshold: bool = True
    community_resolution: float = 1.0
    dynamic_window: int = 5

    def __post_init__(self) -> None:
        if not 0.0 <= self.threshold <= 1.0:
            raise MarketStructureError("threshold must be in [0, 1].")
        if self.community_resolution <= 0.0:
            raise MarketStructureError("community_resolution must be positive.")
        if self.dynamic_window < 2:
            raise MarketStructureError("dynamic_window must be >= 2.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarketStructureManifest:
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
class MarketStructureFeatureFrame:
    frame: pd.DataFrame
    series_features: pd.DataFrame
    manifest: MarketStructureManifest
    diagnostics: Mapping[str, Any] = field(default_factory=dict)


def _stable_mapping_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def _validate_correlation(correlation: np.ndarray) -> np.ndarray:
    matrix = np.asarray(correlation, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] < 2:
        raise MarketStructureError("Correlation matrix must be square with size >= 2.")
    if not np.isfinite(matrix).all():
        raise MarketStructureError("Correlation matrix contains non-finite values.")
    if not np.allclose(matrix, matrix.T, atol=1e-10):
        raise MarketStructureError("Correlation matrix must be symmetric.")
    if not np.allclose(np.diag(matrix), 1.0, atol=1e-8):
        raise MarketStructureError("Correlation matrix diagonal must equal one.")
    return np.clip((matrix + matrix.T) / 2.0, -1.0, 1.0)


def correlation_to_adjacency(
    correlation: np.ndarray,
    spec: NetworkSpec | None = None,
) -> np.ndarray:
    spec = spec or NetworkSpec()
    matrix = _validate_correlation(correlation)
    weights = np.abs(matrix) if spec.use_absolute_threshold else np.clip(matrix, 0.0, None)
    adjacency = np.where(weights >= spec.threshold, weights, 0.0)
    np.fill_diagonal(adjacency, 0.0)
    return adjacency


def correlation_distance(correlation: np.ndarray) -> np.ndarray:
    matrix = _validate_correlation(correlation)
    distance = np.sqrt(np.clip(2.0 * (1.0 - matrix), 0.0, None))
    np.fill_diagonal(distance, 0.0)
    return distance


class _DisjointSet:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> bool:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return False
        if self.rank[root_left] < self.rank[root_right]:
            root_left, root_right = root_right, root_left
        self.parent[root_right] = root_left
        if self.rank[root_left] == self.rank[root_right]:
            self.rank[root_left] += 1
        return True


def minimum_spanning_tree(
    distance: np.ndarray,
) -> tuple[np.ndarray, tuple[tuple[int, int, float], ...]]:
    matrix = np.asarray(distance, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] < 2:
        raise MarketStructureError("Distance matrix must be square with size >= 2.")
    if not np.isfinite(matrix).all() or np.any(matrix < 0.0):
        raise MarketStructureError("Distance matrix must contain finite non-negative values.")
    if not np.allclose(matrix, matrix.T, atol=1e-10):
        raise MarketStructureError("Distance matrix must be symmetric.")
    size = matrix.shape[0]
    candidates = [
        (float(matrix[left, right]), left, right)
        for left in range(size)
        for right in range(left + 1, size)
    ]
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    tree = np.zeros_like(matrix)
    selected: list[tuple[int, int, float]] = []
    sets = _DisjointSet(size)
    for weight, left, right in candidates:
        if sets.union(left, right):
            tree[left, right] = tree[right, left] = weight
            selected.append((left, right, weight))
            if len(selected) == size - 1:
                break
    if len(selected) != size - 1:
        raise MarketStructureError("Unable to construct a connected minimum spanning tree.")
    return tree, tuple(selected)


def _binary_adjacency(adjacency: np.ndarray) -> np.ndarray:
    binary = (np.asarray(adjacency, dtype=float) > 0.0).astype(int)
    np.fill_diagonal(binary, 0)
    return binary


def _connected_components(binary: np.ndarray) -> list[list[int]]:
    size = binary.shape[0]
    unseen = set(range(size))
    components: list[list[int]] = []
    while unseen:
        root = min(unseen)
        stack = [root]
        unseen.remove(root)
        component: list[int] = []
        while stack:
            node = stack.pop()
            component.append(node)
            neighbors = [int(value) for value in np.flatnonzero(binary[node])]
            for neighbor in sorted(neighbors, reverse=True):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
        components.append(sorted(component))
    return sorted(components, key=lambda value: (value[0], len(value)))


def _average_clustering(binary: np.ndarray) -> float:
    coefficients: list[float] = []
    for node in range(binary.shape[0]):
        neighbors = np.flatnonzero(binary[node])
        degree = len(neighbors)
        if degree < 2:
            coefficients.append(0.0)
            continue
        subgraph = binary[np.ix_(neighbors, neighbors)]
        edges = float(subgraph.sum() / 2.0)
        coefficients.append((2.0 * edges) / (degree * (degree - 1)))
    return float(np.mean(coefficients)) if coefficients else 0.0


def _brandes_betweenness(binary: np.ndarray) -> np.ndarray:
    size = binary.shape[0]
    centrality = np.zeros(size, dtype=float)
    for source in range(size):
        stack: list[int] = []
        predecessors: list[list[int]] = [[] for _ in range(size)]
        sigma = np.zeros(size, dtype=float)
        sigma[source] = 1.0
        distance = np.full(size, -1, dtype=int)
        distance[source] = 0
        queue = [source]
        head = 0
        while head < len(queue):
            vertex = queue[head]
            head += 1
            stack.append(vertex)
            for neighbor in np.flatnonzero(binary[vertex]):
                neighbor = int(neighbor)
                if distance[neighbor] < 0:
                    queue.append(neighbor)
                    distance[neighbor] = distance[vertex] + 1
                if distance[neighbor] == distance[vertex] + 1:
                    sigma[neighbor] += sigma[vertex]
                    predecessors[neighbor].append(vertex)
        dependency = np.zeros(size, dtype=float)
        while stack:
            target = stack.pop()
            if sigma[target] > 0.0:
                factor = (1.0 + dependency[target]) / sigma[target]
                for predecessor in predecessors[target]:
                    dependency[predecessor] += sigma[predecessor] * factor
            if target != source:
                centrality[target] += dependency[target]
    centrality /= 2.0
    if size > 2:
        centrality /= ((size - 1) * (size - 2) / 2.0)
    return centrality


def _eigenvector_centrality(adjacency: np.ndarray) -> np.ndarray:
    matrix = np.asarray(adjacency, dtype=float)
    if np.allclose(matrix, 0.0):
        return np.zeros(matrix.shape[0], dtype=float)
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    vector = np.abs(eigenvectors[:, int(np.argmax(eigenvalues))])
    total = float(vector.sum())
    return vector / total if total > 0.0 else np.zeros_like(vector)


def _floyd_warshall(weighted_graph: np.ndarray) -> np.ndarray:
    graph = np.asarray(weighted_graph, dtype=float)
    size = graph.shape[0]
    distances = np.full((size, size), np.inf, dtype=float)
    np.fill_diagonal(distances, 0.0)
    mask = graph > 0.0
    distances[mask] = graph[mask]
    for intermediate in range(size):
        distances = np.minimum(
            distances,
            distances[:, intermediate, None] + distances[None, intermediate, :],
        )
    return distances


def _partition_modularity(
    adjacency: np.ndarray,
    communities: Sequence[Sequence[int]],
    resolution: float,
) -> float:
    matrix = np.asarray(adjacency, dtype=float)
    total_weight = float(matrix.sum() / 2.0)
    if total_weight <= 0.0:
        return 0.0
    degree = matrix.sum(axis=1)
    modularity = 0.0
    for community in communities:
        members = np.asarray(list(community), dtype=int)
        internal_weight = float(matrix[np.ix_(members, members)].sum() / 2.0)
        degree_sum = float(degree[members].sum())
        modularity += internal_weight / total_weight
        modularity -= resolution * (degree_sum / (2.0 * total_weight)) ** 2
    return float(modularity)


def greedy_modularity_communities(
    adjacency: np.ndarray,
    resolution: float = 1.0,
) -> tuple[tuple[int, ...], ...]:
    matrix = np.asarray(adjacency, dtype=float)
    size = matrix.shape[0]
    if size == 0:
        return ()
    communities: list[tuple[int, ...]] = [(index,) for index in range(size)]
    current = _partition_modularity(matrix, communities, resolution)
    tolerance = 1e-12
    while len(communities) > 1:
        best_gain = tolerance
        best_pair: tuple[int, int] | None = None
        best_partition: list[tuple[int, ...]] | None = None
        best_value = current
        for left in range(len(communities)):
            for right in range(left + 1, len(communities)):
                merged = tuple(sorted(communities[left] + communities[right]))
                candidate = [
                    community
                    for index, community in enumerate(communities)
                    if index not in {left, right}
                ] + [merged]
                candidate = sorted(candidate, key=lambda value: (value[0], len(value), value))
                value = _partition_modularity(matrix, candidate, resolution)
                gain = value - current
                pair_key = (communities[left][0], communities[right][0])
                if gain > best_gain or (
                    np.isclose(gain, best_gain, atol=tolerance)
                    and best_pair is not None
                    and pair_key < best_pair
                ):
                    best_gain = gain
                    best_pair = pair_key
                    best_partition = candidate
                    best_value = value
        if best_partition is None:
            break
        communities = best_partition
        current = best_value
    return tuple(communities)


def _concentration(values: np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    total = float(np.abs(array).sum())
    if total <= 0.0:
        return 0.0
    shares = np.abs(array) / total
    return float(np.sum(shares**2))


def network_metrics_from_correlation(
    correlation: np.ndarray,
    members: Sequence[str],
    spec: NetworkSpec | None = None,
) -> dict[str, Any]:
    spec = spec or NetworkSpec()
    matrix = _validate_correlation(correlation)
    if len(members) != matrix.shape[0]:
        raise MarketStructureError("members do not match the correlation matrix size.")
    adjacency = correlation_to_adjacency(matrix, spec)
    binary = _binary_adjacency(adjacency)
    size = matrix.shape[0]
    possible_edges = size * (size - 1) / 2.0
    edge_count = float(binary.sum() / 2.0)
    degree = binary.sum(axis=1).astype(float)
    weighted_degree = adjacency.sum(axis=1)
    components = _connected_components(binary)
    largest = max(components, key=lambda value: (len(value), -value[0]))
    raw_graph_distance = correlation_distance(matrix)
    graph_distance = np.where(binary > 0, np.maximum(raw_graph_distance, 1e-12), 0.0)
    shortest = _floyd_warshall(graph_distance)
    finite_pairs = shortest[np.triu_indices(size, 1)]
    finite_pairs = finite_pairs[np.isfinite(finite_pairs)]
    connectivity_share = (
        float(len(finite_pairs) / possible_edges) if possible_edges > 0.0 else 1.0
    )
    if len(largest) > 1:
        largest_distances = shortest[np.ix_(largest, largest)]
        largest_pairs = largest_distances[np.triu_indices(len(largest), 1)]
        average_shortest_path = float(np.mean(largest_pairs))
        eccentricity = np.max(largest_distances, axis=1)
        network_diameter = float(np.max(eccentricity))
        network_radius = float(np.min(eccentricity))
    else:
        average_shortest_path = 0.0
        network_diameter = 0.0
        network_radius = 0.0

    betweenness = _brandes_betweenness(binary)
    eigenvector = _eigenvector_centrality(adjacency)
    communities = greedy_modularity_communities(
        adjacency, resolution=spec.community_resolution
    )
    modularity = _partition_modularity(
        adjacency, communities, spec.community_resolution
    )

    distance = correlation_distance(matrix)
    tree, tree_edges = minimum_spanning_tree(distance)
    tree_binary = np.zeros_like(tree, dtype=int)
    for left, right, _ in tree_edges:
        tree_binary[left, right] = tree_binary[right, left] = 1
    tree_degree = tree_binary.sum(axis=1).astype(float)
    tree_for_paths = np.where(tree_binary > 0, np.maximum(tree, 1e-12), 0.0)
    tree_shortest = _floyd_warshall(tree_for_paths)
    tree_pairs = tree_shortest[np.triu_indices(size, 1)]
    tree_eccentricity = np.max(tree_shortest, axis=1)

    community_labels = np.empty(size, dtype=int)
    community_payload: list[list[str]] = []
    for label, community in enumerate(communities):
        community_payload.append([str(members[index]) for index in community])
        for index in community:
            community_labels[index] = label

    upper = adjacency[np.triu_indices(size, 1)]
    positive_upper = upper[upper > 0.0]
    return {
        "network_edge_count": int(edge_count),
        "network_density": float(edge_count / possible_edges) if possible_edges else 0.0,
        "network_mean_weight": (
            float(positive_upper.mean()) if positive_upper.size else 0.0
        ),
        "network_average_degree": float(degree.mean()),
        "network_degree_dispersion": float(degree.std(ddof=0)),
        "network_degree_concentration": _concentration(degree),
        "network_weighted_degree_concentration": _concentration(weighted_degree),
        "network_average_clustering": _average_clustering(binary),
        "network_component_count": int(len(components)),
        "network_largest_component_share": float(len(largest) / size),
        "network_connectivity_share": connectivity_share,
        "network_average_shortest_path": average_shortest_path,
        "network_diameter": network_diameter,
        "network_radius": network_radius,
        "contagion_radius": network_radius,
        "betweenness_centrality_concentration": _concentration(betweenness),
        "eigenvector_centrality_concentration": _concentration(eigenvector),
        "network_modularity": float(modularity),
        "network_community_count": int(len(communities)),
        "network_communities": json.dumps(community_payload, separators=(",", ":")),
        "network_degree_distribution": json.dumps(
            [int(value) for value in degree], separators=(",", ":")
        ),
        "mst_total_distance": float(sum(edge[2] for edge in tree_edges)),
        "mst_mean_distance": float(np.mean([edge[2] for edge in tree_edges])),
        "mst_diameter": float(np.max(tree_eccentricity)),
        "mst_average_path_length": float(np.mean(tree_pairs)),
        "mst_leaf_fraction": float(np.mean(tree_degree == 1.0)),
        "mst_degree_concentration": _concentration(tree_degree),
        "mst_edges": json.dumps(
            [
                [str(members[left]), str(members[right]), float(weight)]
                for left, right, weight in tree_edges
            ],
            separators=(",", ":"),
        ),
        "community_labels": json.dumps(
            [int(value) for value in community_labels], separators=(",", ":")
        ),
    }


def _add_dynamic_features(frame: pd.DataFrame, dynamic_window: int) -> pd.DataFrame:
    output = frame.copy()
    eligible = output["eligibility_status"] == "ELIGIBLE"
    dynamic_columns = (
        "dominant_eigenvalue_share",
        "spectral_entropy",
        "average_correlation",
        "network_density",
        "network_modularity",
        "mst_total_distance",
    )
    for _, indices in output.groupby("window", sort=True).groups.items():
        ordered = output.loc[indices].sort_values("timestamp", kind="mergesort")
        eligible_ordered = ordered.loc[eligible.loc[ordered.index]]
        for column in dynamic_columns:
            if column not in eligible_ordered:
                continue
            values = eligible_ordered[column].astype(float)
            velocity = values.diff()
            output.loc[eligible_ordered.index, f"{column}_velocity"] = velocity
            output.loc[eligible_ordered.index, f"{column}_acceleration"] = velocity.diff()
            output.loc[
                eligible_ordered.index, f"{column}_rolling_volatility"
            ] = values.rolling(
                dynamic_window, min_periods=dynamic_window
            ).std(ddof=1)
    if "eigenvector_stability" in output:
        output["eigenvector_instability"] = 1.0 - output["eigenvector_stability"]
    output["market_mode_strength"] = output.get("dominant_eigenvalue_share", np.nan)
    return output


def summarize_market_structure(frame: pd.DataFrame) -> dict[str, Any]:
    if "eligibility_status" not in frame or "window" not in frame:
        raise MarketStructureError("Market-structure frame lacks gate status columns.")
    summaries: dict[str, Any] = {}
    for window, group in frame.groupby("window", sort=True):
        eligible = group.loc[group["eligibility_status"] == "ELIGIBLE"]
        summaries[str(int(window))] = {
            "rows": int(len(group)),
            "eligible_rows": int(len(eligible)),
            "eligible_share": float(len(eligible) / len(group)) if len(group) else 0.0,
            "mean_network_density": (
                None if eligible.empty else float(eligible["network_density"].mean())
            ),
            "mean_network_modularity": (
                None if eligible.empty else float(eligible["network_modularity"].mean())
            ),
            "mean_mst_total_distance": (
                None if eligible.empty else float(eligible["mst_total_distance"].mean())
            ),
            "mean_contagion_radius": (
                None if eligible.empty else float(eligible["contagion_radius"].mean())
            ),
        }
    return {
        "windows": summaries,
        "automatic_structure_selection_performed": False,
    }


def compute_market_structure_feature_frame(
    frame: pd.DataFrame,
    panel: PanelSpec,
    feature_config: CausalFeatureConfig | None = None,
    network_spec: NetworkSpec | None = None,
) -> MarketStructureFeatureFrame:
    feature_config = feature_config or CausalFeatureConfig()
    network_spec = network_spec or NetworkSpec(threshold=panel.network_threshold)
    try:
        returns = build_return_panel(frame, panel)
        series_features = build_causal_series_features(frame, panel, feature_config)
    except SpectralFeatureError as exc:
        raise MarketStructureError(str(exc)) from exc

    rows: list[dict[str, Any]] = []
    previous_vectors: dict[int, np.ndarray] = {}
    for window in panel.dependence_windows:
        for end_position, timestamp in enumerate(returns.index):
            start_position = max(0, end_position - window + 1)
            window_frame = returns.iloc[start_position : end_position + 1]
            expected_cells = int(window * len(panel.members))
            observed_cells = int(window_frame.notna().sum().sum())
            coverage = observed_cells / expected_cells if expected_cells else 0.0
            complete = window_frame.dropna(axis=0, how="any")
            row: dict[str, Any] = {
                "timestamp": timestamp,
                "window": int(window),
                "estimator": panel.estimator,
                "panel_members": "|".join(panel.members),
                "panel_size": len(panel.members),
                "window_rows": int(len(window_frame)),
                "complete_observations": int(len(complete)),
                "window_coverage": float(coverage),
                "eligibility_status": "ELIGIBLE",
            }
            if (
                len(window_frame) < window
                or coverage < panel.minimum_window_coverage
                or len(complete) < panel.minimum_complete_observations
            ):
                row["eligibility_status"] = "INSUFFICIENT_PANEL_COVERAGE"
                rows.append(row)
                continue
            try:
                correlation = estimate_correlation(complete.to_numpy(dtype=float), panel)
                spectral = spectral_metrics_from_correlation(
                    correlation, network_threshold=panel.network_threshold
                )
                first_vector = np.asarray(
                    spectral.pop("first_eigenvector"), dtype=float
                )
                eigenvalues = np.asarray(spectral.pop("eigenvalues"), dtype=float)
                network = network_metrics_from_correlation(
                    correlation, panel.members, network_spec
                )
            except (SpectralFeatureError, MarketStructureError) as exc:
                row["eligibility_status"] = "INELIGIBLE_MARKET_STRUCTURE_WINDOW"
                row["ineligibility_reason"] = str(exc)
                rows.append(row)
                continue
            previous = previous_vectors.get(window)
            row.update(spectral)
            row.update(network)
            row["eigenvector_stability"] = (
                np.nan
                if previous is None
                else float(abs(np.dot(previous, first_vector)))
            )
            row["eigenvalue_spectrum"] = json.dumps(
                [float(value) for value in eigenvalues], separators=(",", ":")
            )
            previous_vectors[window] = first_vector
            rows.append(row)

    output = pd.DataFrame(rows).sort_values(
        ["timestamp", "window"], kind="mergesort"
    ).reset_index(drop=True)
    output = _add_dynamic_features(output, network_spec.dynamic_window)
    input_columns = [
        column
        for column in REQUIRED_COLUMNS + OPTIONAL_COLUMNS
        if column in frame.columns
    ]
    canonical_input = frame[input_columns].sort_values(
        list(KEY_COLUMNS)
    ).reset_index(drop=True)
    configuration = {
        "panel": panel.to_dict(),
        "causal_features": feature_config.to_dict(),
        "network": network_spec.to_dict(),
    }
    manifest = MarketStructureManifest(
        schema_version=MARKET_STRUCTURE_SCHEMA_VERSION,
        input_sha256=stable_frame_hash(canonical_input),
        config_sha256=_stable_mapping_hash(configuration),
        output_sha256=stable_frame_hash(output),
        panel_members=panel.members,
        rows=int(len(output)),
        timestamps=int(output["timestamp"].nunique()) if not output.empty else 0,
        estimator=panel.estimator,
    )
    diagnostics = {
        "eligibility_counts": output["eligibility_status"]
        .value_counts()
        .sort_index()
        .to_dict(),
        "panel_members": list(panel.members),
        "dependence_windows": list(panel.dependence_windows),
        "estimator": panel.estimator,
        "network_spec": network_spec.to_dict(),
        "market_structure_summary": summarize_market_structure(output),
        "automatic_panel_selection_performed": False,
        "automatic_window_selection_performed": False,
        "automatic_network_threshold_selection_performed": False,
    }
    return MarketStructureFeatureFrame(
        frame=output,
        series_features=series_features,
        manifest=manifest,
        diagnostics=diagnostics,
    )
