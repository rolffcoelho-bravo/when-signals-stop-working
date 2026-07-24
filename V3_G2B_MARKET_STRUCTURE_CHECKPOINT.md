# Gate V3-2B — Market Structure Extension Checkpoint

## Status

> `IMPLEMENTATION_COMPLETE_AND_LOCKED`

Gate V3-2B extends the protected Gate V3-2 spectral layer with causal network topology and dynamic market-structure evidence. It was added as a separate governed extension because the original V3-2 checkpoint was already locked before the richer network scope was approved.

## Baseline and parent preservation

- frozen baseline: `v2.0.0`;
- baseline commit: `5a07299367b80c3940e652e7bbdd208ce86ba5ef`;
- Version 3 branch: `research/v3-adaptive-signal-validity`;
- parent gate: `V3-2`;
- parent lock: `V3_G2_SPECTRAL_ENGINE_LOCK.json`;
- V3-2B locked implementation boundary: `33c447c2793b3ba2f2e2c3bd99ede3a5395046a0`;
- protected V3-2 files modified: none;
- Version 2 files modified: none.

## Delivered components

### Threshold-network layer

- registered absolute or positive-correlation threshold treatment;
- edge count, density and mean weight;
- degree dispersion and concentration;
- weighted-degree concentration;
- average clustering coefficient;
- connected-component count;
- largest-component and pair-connectivity shares;
- average shortest path, diameter, radius and `contagion_radius`;
- betweenness- and eigenvector-centrality concentration.

### Community layer

- deterministic greedy weighted-modularity partition;
- modularity and community count;
- stable community labels and member lists;
- no automatic threshold or community-resolution tuning.

### Minimum-spanning-tree layer

- causal correlation distance;
- deterministic Kruskal construction with stable tie handling;
- total and mean tree distance;
- diameter and average path length;
- leaf fraction and degree concentration;
- serialized stable edge evidence;
- explicit handling of zero-distance edges under perfect common-mode dependence.

### Dynamic market-structure layer

For dominant-eigenvalue share, spectral entropy, average correlation, network density, modularity and MST total distance:

- causal first differences;
- causal second differences;
- causal rolling volatility;
- sign-invariant eigenvector instability;
- transparent market-mode strength descriptor.

### Reusable execution layer

- `src/shockbridge_signal_validity/v3/market_structure.py`;
- `src/shockbridge_signal_validity/v3/market_structure_runner.py`;
- `scripts/run_v3_market_structure.py`;
- JSON configuration template;
- PowerShell and shell workflows;
- documentation, tests, implementation lock and portable verifier.

## Output contract

```text
market_structure_features.csv
causal_series_features.csv
market_structure_manifest.json
market_structure_diagnostics.json
canonical_validation_report.json
```

Primary new downstream variables include:

```text
network_average_clustering
network_component_count
network_largest_component_share
network_connectivity_share
network_average_shortest_path
network_diameter
network_radius
contagion_radius
betweenness_centrality_concentration
eigenvector_centrality_concentration
network_modularity
network_community_count
mst_total_distance
mst_mean_distance
mst_diameter
mst_average_path_length
mst_leaf_fraction
mst_degree_concentration
```

Dynamic variables use the suffixes:

```text
*_velocity
*_acceleration
*_rolling_volatility
```

## Acceptance evidence

The isolated analytical and integration suite completed with:

```text
10 passed
```

The suite establishes that:

1. identity dependence produces a sparse threshold network and deterministic equal-distance MST;
2. perfect common-mode dependence produces a complete network and one community;
3. a two-block dependence fixture recovers two communities with positive modularity;
4. every MST contains exactly `N - 1` edges;
5. future data mutation cannot alter earlier market-structure outputs;
6. insufficient fixed-panel coverage fails closed;
7. dynamic descriptors are generated only from causal eligible histories;
8. shuffled input order produces identical evidence and manifest identity;
9. the runner emits the complete machine-readable evidence package;
10. an identified zero-distance MST path edge case was corrected before lock.

The recorded result is the isolated V3-2B suite. Full repository and Python 3.11–3.13 CI validation remains a later audit obligation and is not represented as completed.

## Gate boundary

Gate V3-2B remains descriptive. It does not:

- label investor panic;
- estimate `PANIC_CONSISTENT_REGIME`;
- select a favourable panel, window or network threshold;
- evaluate RSI or Bollinger predictive power;
- estimate signal-failure probability;
- issue a trading or permitted-use decision.

## Next gate

> `V3-3 — PANIC-CONSISTENT PROBABILISTIC REGIME ENGINE`

Gate V3-3 will combine the locked V3-2 and V3-2B evidence with downside acceleration, volatility and semivariance jumps, abnormal volume, liquidity and order-book deterioration, leverage, funding, liquidation and cross-venue stress where available.

Its output will be a forward-filtered probability of `PANIC_CONSISTENT_REGIME`, explicit transition risk, occupancy and duration evidence, and an `INSUFFICIENT_MECHANISM_EVIDENCE` state when the available data cannot support the richer classification.
