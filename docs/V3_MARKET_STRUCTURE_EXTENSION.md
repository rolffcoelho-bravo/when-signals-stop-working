# Version 3 Market Structure Extension

## Purpose

Gate V3-2B extends the locked Gate V3-2 spectral engine without modifying its protected files. It adds deterministic network topology, minimum-spanning-tree structure, community diagnostics, centrality concentration, path-based contagion descriptors, and causal dynamics.

The layer remains descriptive. It does not label investor panic, select a favourable panel or threshold, or evaluate RSI and Bollinger predictive power.

## Inputs

The runner consumes canonical Version 3 market data and the fixed-panel `asset@venue` contract already established by Gates V3-1 and V3-2.

Configuration sections:

- `panel`: fixed members, rolling windows, estimator and coverage controls;
- `causal_features`: return, volatility, downside, volume and optional stress-feature settings;
- `network`: fixed threshold, absolute-versus-positive dependence treatment, modularity resolution and dynamic-feature window.

All settings are declared before execution. The extension performs no automatic threshold, panel or rolling-window selection.

## Network construction

For each eligible causal dependence window, the extension creates a weighted threshold network from the registered correlation matrix. It also creates the correlation-distance matrix

\[
d_{ij,t}=\sqrt{2\left(1-\rho_{ij,t}\right)}
\]

and a deterministic minimum spanning tree using stable panel order to resolve equal-weight ties.

## Output variables

### Threshold network

- edge count and density;
- mean edge weight;
- degree dispersion and concentration;
- weighted-degree concentration;
- average clustering coefficient;
- connected-component count;
- largest-component and pair-connectivity shares;
- average shortest path, diameter and radius;
- `contagion_radius`;
- betweenness-centrality concentration;
- eigenvector-centrality concentration.

### Communities

- deterministic greedy weighted-modularity partition;
- modularity value;
- community count;
- stable community labels and member lists.

### Minimum spanning tree

- total and mean correlation distance;
- diameter and average path length;
- leaf fraction;
- degree concentration;
- serialized stable edge list.

### Dynamic descriptors

For dominant-eigenvalue share, spectral entropy, average correlation, network density, modularity and MST total distance, the extension produces:

- first difference (`*_velocity`);
- second difference (`*_acceleration`);
- causal rolling volatility (`*_rolling_volatility`).

It also produces sign-invariant eigenvector instability and a transparent `market_mode_strength` descriptor equal to the dominant-eigenvalue share. No composite panic score is created at this gate.

## Fail-closed controls

A window is unavailable when the fixed panel lacks the registered coverage or complete observations. The engine reports `INSUFFICIENT_PANEL_COVERAGE` or `INELIGIBLE_MARKET_STRUCTURE_WINDOW`; it never silently shrinks the panel or imputes a missing member.

Future observations cannot alter earlier outputs. Dynamic quantities are calculated separately inside each registered dependence window and only from eligible prior and current observations.

## Execution

PowerShell:

```powershell
.\RUN_V3_G2B_MARKET_STRUCTURE.ps1
```

Shell:

```bash
./RUN_V3_G2B_MARKET_STRUCTURE.sh
```

Direct Python:

```bash
python scripts/run_v3_market_structure.py \
  --config configs/v3_market_structure_example.json \
  --output-directory outputs/v3/market_structure
```

## Evidence package

The runner writes:

```text
market_structure_features.csv
causal_series_features.csv
market_structure_manifest.json
market_structure_diagnostics.json
canonical_validation_report.json
```

The output and configuration identities are deterministic. Gate V3-3 may consume this layer only after the V3-2B checkpoint and lock pass.
