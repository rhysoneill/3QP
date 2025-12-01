# Module 05: Social Network & Clique Formation — Implementation Notes

## 1. Purpose of This Document

This document provides guidance for implementing the Social Network module based on the specifications defined in `spec.md` and the data contracts in `data_contract.md`. It addresses architectural concerns, design patterns, data structure choices, and strategies for maintaining system integrity during development and evolution.

**This document does NOT contain code.** It describes how to construct the subsystem in conceptual and structural terms.

## 2. Architectural Overview

### 2.1 Subsystem Decomposition

The Social Network module can be decomposed into the following logical components:

1. **Graph Store**: Maintains the current state of nodes, edges, and weights
2. **Drift Engine**: Processes interaction signals and applies weight update functions
3. **Decay Processor**: Applies passive drift to edges not receiving interaction signals
4. **Edge Maintenance**: Handles pruning of weak edges and normalization
5. **Clique Detector**: Identifies maximal cliques satisfying weight and size criteria
6. **Metric Calculator**: Computes structural metrics from graph state
7. **Query Handler**: Responds to synchronous queries from other modules
8. **Output Generator**: Packages graph state, cliques, and metrics for export

### 2.2 Component Interactions

```
[External Trigger] → [Drift Engine] → [Graph Store]
                                     ↓
[Decay Processor] → [Graph Store] → [Edge Maintenance]
                                     ↓
[Graph Store] → [Clique Detector] → [Clique Store]
                                     ↓
[Graph Store] + [Clique Store] → [Metric Calculator] → [Output Generator]
                                                       ↓
                                                   [Downstream Modules]
```

Each component operates on well-defined interfaces, enabling isolated testing and modular evolution.

## 3. Data Structure Selection

### 3.1 Graph Representation

**Choice 1: Adjacency Matrix**

- **Structure**: N×N matrix where entry (i,j) stores weight of edge between nodes i and j
- **Advantages**: O(1) lookup, simple to implement, cache-friendly for dense graphs
- **Disadvantages**: O(N²) space regardless of edge count, inefficient for sparse graphs
- **Recommended for**: Small crews (N ≤ 20), dense networks

**Choice 2: Adjacency List**

- **Structure**: Map from node_id to list of (neighbor_id, weight) pairs
- **Advantages**: O(E) space where E = edge count, efficient for sparse graphs
- **Disadvantages**: O(degree) lookup time, more complex iteration patterns
- **Recommended for**: Larger crews (N > 20), sparse networks

**Choice 3: Edge List with Index**

- **Structure**: List of edge objects, indexed by (source, target) pairs
- **Advantages**: Flexible, easy to add/remove edges, supports rich edge metadata
- **Disadvantages**: Requires indexing for efficient lookup
- **Recommended for**: General-purpose implementation with extensibility needs

**Recommendation**: Use adjacency matrix for initial implementation targeting small crews, with option to swap in edge list representation if scalability becomes an issue.

### 3.2 Node Storage

Store nodes in a **map** (dictionary) keyed by `node_id`. Each node entry contains:

- `node_id`: Unique identifier
- `active_status`: Boolean
- `metadata`: Extensible key-value store

This allows O(1) node lookup and flexible metadata attachment.

### 3.3 Clique Storage

Store cliques as:

```
Clique {
  clique_id: unique identifier,
  member_set: set of node_ids,
  formation_tick: integer,
  stability_history: fixed-size buffer of recent membership snapshots
}
```

Use a **map** keyed by `clique_id` for O(1) clique lookup. Maintain a **secondary index** mapping node_id to list of clique_ids for efficient membership queries.

### 3.4 Metric Cache

Store computed metrics in a **cache structure** updated after each time step:

```
MetricCache {
  step_number: integer,
  global_metrics: map<metric_name, value>,
  node_metrics: map<node_id, map<metric_name, value>>
}
```

This avoids recomputation during queries.

## 4. Drift Engine Implementation

### 4.1 Signal Aggregation

When multiple interaction signals target the same edge within a single time step, aggregate them:

**Option 1: Summation**
```
total_effect = Σ Δ(intensity_i, duration_i, W_old)
```

**Option 2: Maximum**
```
total_effect = max(Δ(intensity_i, duration_i, W_old))
```

**Option 3: Weighted Average**
```
total_effect = (Σ duration_i · Δ(...)) / (Σ duration_i)
```

**Recommendation**: Use **summation** with per-step clamping to ensure bounded changes.

### 4.2 Drift Function Parameterization

Define drift function as:

```
Δ(intensity, duration, W) = 
  α · intensity · duration · (1 - W)^β - γ · (1 - intensity) · W^δ
```

Where:

- `α`: Strengthening coefficient (typical range: 0.01–0.1)
- `β`: Saturation exponent for strengthening (typical value: 1.0–2.0)
- `γ`: Weakening coefficient (typical range: 0.005–0.05)
- `δ`: Saturation exponent for weakening (typical value: 1.0)

These parameters should be tunable via configuration.

### 4.3 Numerical Stability

- Clamp all weight values to [0.0, 1.0] after every update
- Use bounded arithmetic to prevent overflow
- Represent weights as double-precision floating point (64-bit) to maintain precision
- Implement epsilon-comparisons for weight thresholds to avoid floating-point errors

## 5. Decay Processor Implementation

### 5.1 Passive Drift

For edges not receiving interaction signals:

```
W_new = W_old + γ_decay · velocity(e)
```

Where `velocity(e)` is computed as:

```
velocity(e) = (W_current - W_previous) / Δt
```

This models inertia: edges continue their recent trend unless acted upon by interaction signals.

### 5.2 Velocity Smoothing

To avoid oscillations, apply exponential smoothing:

```
velocity_smoothed(e) = λ · velocity_raw(e) + (1 - λ) · velocity_previous(e)
```

Where `λ` is a smoothing coefficient (typical value: 0.3–0.7).

### 5.3 Stabilization Detection

Mark an edge as "stable" if:

```
|velocity_smoothed(e)| < σ  AND  |W_new - W_old| < ε
```

For configurable thresholds σ and ε. Stable edges may bypass certain drift computations for efficiency.

## 6. Edge Maintenance Implementation

### 6.1 Pruning

After each time step:

1. Iterate over all edges
2. Remove edges where W < prune_threshold
3. Update adjacency structures to reflect removed edges

**Optimization**: Maintain a "weak edge watchlist" of edges approaching the prune threshold to avoid scanning the entire graph.

### 6.2 Normalization (Optional)

If total edge weight grows unboundedly, apply global normalization:

```
W_normalized(e) = W(e) / max(W_total / target_total, 1.0)
```

Where `W_total = Σ W(e)` and `target_total` is a configurable reference value.

**Caution**: Normalization can distort temporal dynamics. Use sparingly.

## 7. Clique Detection Implementation

### 7.1 Algorithm Selection

**Option 1: Bron-Kerbosch Algorithm**

- Exhaustive maximal clique enumeration
- Worst-case exponential, but efficient for small graphs
- Standard algorithm in network science

**Option 2: Threshold-Based Subgraph Extraction**

- Extract subgraph where all edges have weight ≥ τ
- Find connected components in subgraph
- Enumerate cliques within each component

**Recommendation**: Use Bron-Kerbosch with pruning for small crews (N ≤ 20). For larger crews, implement threshold-based heuristic.

### 7.2 Clique Persistence Tracking

To track clique identity across time steps:

1. Compute **Jaccard similarity** between clique at step t and all cliques at step t-1
2. If similarity > threshold (e.g., 0.6), assign same clique_id
3. Otherwise, generate new clique_id

This maintains stable identifiers for slowly-evolving cliques.

### 7.3 Stability Index Calculation

```
stability_index = (number of time steps with consistent membership) / (window_size)
```

Where "consistent membership" means Jaccard similarity > 0.8 across consecutive steps. Use a rolling window of 10–20 steps.

## 8. Metric Calculator Implementation

### 8.1 Cohesion Metrics

**Global Cohesion**:
```
cohesion = (Σ W(e) for e in E) / |E|
```

Efficient: O(E) iteration.

**Normalized Density**:
```
density = |E| / (|V| · (|V| - 1) / 2)
```

Consider only edges with W > prune_threshold.

### 8.2 Fragmentation Metrics

Use **union-find** or **breadth-first search** to identify connected components. For weighted graphs, consider edges with W > ε as "present."

**Fragmentation Index**:
```
fragmentation = 1 - (size_of_largest_component / |V|)
```

### 8.3 Clustering Coefficient

For each node v:

```
C(v) = (number of edges among neighbors of v) / (|neighbors(v)| · (|neighbors(v)| - 1) / 2)
```

Global clustering coefficient is the average of C(v) over all nodes.

**Optimization**: Precompute neighbor sets during graph update; reuse for metric computation.

### 8.4 Centrality Measures

**Degree Centrality**:
```
degree(v) = Σ W(edge(v, u)) for all neighbors u of v
```

**Betweenness Centrality**:
- Compute shortest paths between all pairs of nodes (weighted by 1/W)
- Count number of shortest paths passing through v
- Normalize by total number of paths

**Caution**: Betweenness is O(N³) for dense graphs. Consider approximation methods for N > 30.

## 9. Query Handler Implementation

### 9.1 Synchronous Queries

Implement queries as **blocking function calls** that return immediately using cached data:

- Edge weight query: O(1) or O(log N) depending on representation
- Clique membership query: O(k) where k = number of cliques node belongs to
- Centrality query: O(1) using metric cache

No queries trigger recomputation; all return data from most recent completed time step.

### 9.2 Thread Safety (If Applicable)

If the module runs in a concurrent environment:

- Use **read-write locks** to allow concurrent queries during non-update phases
- Acquire write lock during update cycle to prevent inconsistent reads
- Ensure metric cache is updated atomically

## 10. Output Generator Implementation

### 10.1 Serialization

Package outputs in structured format (e.g., JSON, Protocol Buffers, or custom binary format). Ensure:

- All node and edge identifiers are consistent
- Floating-point values are rounded to reasonable precision (e.g., 4 decimal places)
- Timestamps and step numbers are explicitly included

### 10.2 Incremental Outputs

To reduce bandwidth, optionally generate **delta outputs**:

- Only include edges whose weights changed beyond threshold δ
- Only include nodes affected by edge changes
- Include full snapshot periodically (e.g., every 10 steps)

Downstream consumers must support delta reconstruction.

### 10.3 Validation

Before emitting outputs, validate:

- All weights in [0, 1]
- All cliques satisfy size and weight criteria
- All node references are valid
- No NaN or infinite values in metrics

Log validation failures; do not emit malformed data.

## 11. Versioning and Extension Strategies

### 11.1 Configuration Versioning

Store configuration parameters in versioned schema:

```
NetworkConfigV1 {
  version: 1,
  drift_params: {...},
  clique_params: {...},
  metric_params: {...}
}
```

When introducing new parameters, increment version and provide backward-compatible defaults.

### 11.2 Algorithm Swapping

Encapsulate algorithms (drift function, clique detection) behind **interface abstractions**:

```
Interface DriftFunction {
  compute_delta(intensity, duration, current_weight) → real
}

Interface CliqueDetector {
  find_cliques(graph, threshold) → list<clique>
}
```

Implementations can be swapped without changing surrounding logic.

### 11.3 Metric Extensibility

Allow registration of custom metric calculators:

```
register_metric("custom_cohesion", CustomCohesionCalculator)
```

Metric calculator interface:

```
Interface MetricCalculator {
  compute(graph, cliques) → map<metric_name, value>
}
```

This enables experimentation with new metrics without modifying core module.

### 11.4 Schema Evolution

When adding fields to node or edge structures:

- Use optional fields with default values
- Maintain backward-compatible parsers
- Provide migration scripts for existing data

When removing fields:

- Deprecate first (warn if field is present but unused)
- Remove in major version increment only

## 12. Testing and Validation Strategies

### 12.1 Unit Testing

Test each component in isolation:

- **Drift Engine**: Given specific interaction signals and initial weights, verify output weights
- **Clique Detector**: Given hand-constructed graphs, verify correct clique identification
- **Metric Calculator**: Given known graph structures, verify metric values match analytical solutions

### 12.2 Integration Testing

Test full update cycle:

- Initialize graph with known state
- Apply sequence of interaction signals
- Verify final graph state, cliques, and metrics match expected results

### 12.3 Property-Based Testing

Verify invariants:

- All weights remain in [0, 1]
- Graph remains undirected (symmetric weights)
- Cliques satisfy definition (all pairs connected with sufficient weight)
- Metrics satisfy bounds (e.g., density in [0, 1])

Use randomized inputs to explore edge cases.

### 12.4 Regression Testing

Maintain suite of reference scenarios:

- Small stable network (no drift)
- Growing network (ties strengthen over time)
- Fragmenting network (ties weaken, cliques dissolve)
- Dynamic network (cliques form and split)

Ensure outputs remain consistent across implementation changes.

## 13. Performance Optimization

### 13.1 Incremental Computation

Where possible, update metrics incrementally rather than recomputing from scratch:

- When an edge weight changes, update only affected node centralities
- When cliques change, update only clique-related metrics

This reduces complexity from O(N²) or O(N³) to O(affected_nodes).

### 13.2 Lazy Evaluation

Compute expensive metrics (e.g., betweenness centrality) only when queried or when changes exceed threshold.

### 13.3 Parallelization

For larger graphs:

- Parallelize metric computation across nodes (degree, clustering)
- Parallelize clique detection across subgraphs

Ensure thread-safe access to graph state.

### 13.4 Profiling

Identify bottlenecks using profiling tools:

- If clique detection dominates: consider approximate methods
- If metric computation dominates: implement incremental updates
- If drift computation dominates: optimize drift function

Optimize most expensive operations first.

## 14. Error Handling and Robustness

### 14.1 Input Validation

Reject or sanitize invalid inputs:

- Out-of-range intensity: clamp to [0, 1]
- Invalid node references: log error, discard signal
- Negative duration: set to zero

Do not crash on bad input; log and continue.

### 14.2 Numerical Robustness

Handle edge cases:

- Division by zero (e.g., density of empty graph): return 0 or NaN with appropriate handling
- Extremely small weights: treat as zero if below machine epsilon
- Floating-point underflow: use epsilon-comparisons

### 14.3 State Consistency

After each update, verify:

- Graph structure is valid (no dangling references)
- Weights are in bounds
- Cliques satisfy criteria

If inconsistencies detected, log error and attempt recovery (e.g., recompute cliques from scratch).

### 14.4 Graceful Degradation

If computational budget is exceeded (e.g., clique detection takes too long):

- Return approximate results with warning
- Skip less critical metrics
- Reduce clique detection thoroughness

Do not block system on pathological cases.

## 15. Integration with Other 3QP Modules

### 15.1 TQP Core

- Receives time step triggers from TQP Core
- Exports graph snapshots and metrics to TQP Core for distribution
- Does not interpret TQP Core's orchestration logic

### 15.2 Stressor Model

- Provides structural metrics as inputs to stressor calculations
- Does not know how stressors are computed or what they represent

### 15.3 Intervention Engine

- Provides clique indicators and fragmentation metrics for intervention targeting
- Does not define or execute interventions

### 15.4 BDI Cycle

- May receive interaction signals derived from BDI agent interactions
- Does not model beliefs, desires, or intentions

### 15.5 Logging System

- Exports change logs, graph snapshots, and metrics for historical analysis
- Does not interpret logged data

## 16. Risks to Architectural Integrity

### 16.1 Psychological Content Creep

**Risk**: Drift functions or metadata begin encoding psychological states (e.g., "this tie is hostile").

**Mitigation**: Enforce strict code review; reject any interpretation-laden labels or parameters.

### 16.2 Behavioral Outcome Dependencies

**Risk**: Module logic starts checking downstream behavioral outcomes to adjust network state (circular reasoning).

**Mitigation**: Maintain unidirectional data flow; network state depends only on interaction signals, not on performance or behavior.

### 16.3 Scenario-Specific Tuning

**Risk**: Parameters are tuned for specific mission narratives, reducing generalizability.

**Mitigation**: Use parameter sets labeled by abstract conditions (e.g., "high interaction frequency" vs. "Mars transit mission").

### 16.4 Scope Expansion

**Risk**: Module accumulates logic for stressor detection, intervention, or other concerns outside its domain.

**Mitigation**: Regularly audit module boundaries; reject feature requests that belong in other modules.

## 17. Maintenance and Evolution

### 17.1 Documentation

Maintain:

- **Specification documents**: Up-to-date with implementation
- **API documentation**: For all input/output interfaces and query methods
- **Change log**: Record of parameter changes, algorithm updates, and bug fixes

### 17.2 Backward Compatibility

When evolving the module:

- Preserve existing interfaces unless major version increment is warranted
- Provide migration tools for configuration and data format changes
- Notify downstream consumers of breaking changes with sufficient lead time

### 17.3 Experimental Features

Implement experimental metrics or algorithms as **optional extensions**:

- Flag as "experimental" in documentation
- Do not expose to production consumers unless validated
- Provide mechanism to enable/disable via configuration

### 17.4 Community and Peer Review

For research use cases:

- Share specifications and validation data with domain experts
- Solicit feedback on drift functions and clique criteria
- Publish anonymized case studies demonstrating module behavior

## 18. Conclusion

This implementation guide provides a comprehensive roadmap for constructing the Social Network module in accordance with the architectural principles of the 3QP project. By adhering to the strategies outlined here—modular design, rigorous validation, careful boundary management—developers can build a robust, maintainable, and scientifically defensible subsystem that serves as a cornerstone of the broader 3QP architecture.

The module's success depends on maintaining its **structural focus** and **semantic neutrality**. Avoid the temptation to interpret or explain network changes in psychological terms. Let the graph speak for itself, and let other modules handle interpretation.

---

**End of Implementation Notes**
