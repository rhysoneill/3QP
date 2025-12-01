# Module 05: Social Network & Clique Formation — Engineering Specification

## 1. Graph Representation

### 1.1 Structural Model

The social network is represented as a **weighted, undirected graph** G = (V, E, W) where:

- **V**: Set of nodes, each representing a crew member
- **E**: Set of edges, each representing a bidirectional interpersonal tie
- **W**: Weight function W: E → [0, 1] assigning tie strength to each edge

### 1.2 Node Definition

Each node `v ∈ V` contains:

- `node_id`: Unique identifier (immutable)
- `metadata`: Optional key-value store for extensibility (must not contain behavioral or psychological data)
- `active_status`: Boolean indicating whether node participates in current update cycle

### 1.3 Edge Definition

Each edge `e ∈ E` is defined by:

- `source_node_id`: Identifier of first node
- `target_node_id`: Identifier of second node
- `weight`: Real value in [0, 1] representing tie strength
- `last_modified_tick`: Timestamp of most recent weight update
- `drift_velocity`: Rate of change in weight (real value, may be positive, negative, or zero)

### 1.4 Adjacency Representation

The graph may be stored using:

- **Adjacency matrix**: N×N matrix where N = |V|, with entry (i,j) storing weight of edge between nodes i and j
- **Edge list**: Collection of edge objects with explicit source, target, and weight
- **Adjacency list**: Map from node_id to collection of (neighbor_id, weight) pairs

Choice of representation is implementation-dependent; specification requires support for:

- O(1) or O(log N) edge weight lookup
- O(N) or better traversal of all edges incident to a node
- O(N²) or better full graph traversal

## 2. Tie-Update Mechanisms

### 2.1 Interaction Signal Processing

At each time step `t`, the module receives a set of **interaction signals** of the form:

```
interaction_signal = {
  source_node_id: identifier,
  target_node_id: identifier,
  intensity: real ∈ [0, 1],
  duration: integer ≥ 0
}
```

These signals are abstract inputs from upstream modules. The Social Network module does not interpret their semantic meaning.

### 2.2 Weight Update Function

For each interaction signal, the weight of the corresponding edge is updated according to:

```
W_new(e) = clamp(W_old(e) + Δ(intensity, duration, W_old(e)), 0, 1)
```

Where:

- `Δ` is a **drift function** mapping (intensity, duration, current_weight) → real
- `clamp(x, min, max)` constrains x to [min, max]

### 2.3 Drift Function Specification

The drift function must satisfy:

- **Boundedness**: |Δ(...)| ≤ δ_max for some configurable δ_max > 0
- **Continuity**: Small changes in inputs produce small changes in output
- **Saturation behavior**: As W approaches 0 or 1, sensitivity to further change decreases

Example parametric form (implementation may vary):

```
Δ(intensity, duration, W) = α · intensity · duration · (1 - W) - β · (1 - intensity) · W
```

Where:

- `α` controls strengthening rate
- `β` controls weakening rate
- Positive intensity strengthens ties; low intensity weakens them

### 2.4 Passive Decay

Edges not receiving interaction signals during time step `t` undergo **passive drift**:

```
W_new(e) = W_old(e) + γ · drift_velocity(e)
```

Where:

- `γ` is a global decay/stabilization coefficient
- `drift_velocity(e)` reflects recent trend in weight changes

If drift velocity is near zero, weight remains stable. If velocity is negative, weight decays toward zero.

### 2.5 Edge Pruning

Edges with weights below threshold `ε` (configurable, typically 0.01 ≤ ε ≤ 0.1) are removed from the graph to prevent accumulation of negligible ties.

## 3. Drift Processes

### 3.1 Strengthening

A tie strengthens when:

- Frequent interaction signals with high intensity are received
- Current weight is below saturation threshold
- Drift velocity is positive and sustained

### 3.2 Weakening

A tie weakens when:

- Interaction signals cease or have low intensity
- Passive decay dominates
- Drift velocity is negative

### 3.3 Stabilization

A tie stabilizes when:

- Drift velocity approaches zero
- Weight change per time step falls below threshold σ (typically σ ≈ 0.001)
- Interaction patterns become consistent

## 4. Clique Detection

### 4.1 Clique Definition

A **clique** C ⊆ V is a subset of nodes such that:

- All pairs of nodes in C are connected by edges
- All edges within C have weights ≥ threshold `τ` (typically τ ≈ 0.5)
- |C| ≥ minimum clique size (typically 2 or 3)

### 4.2 Maximal Clique Identification

The module identifies **maximal cliques**: cliques that cannot be extended by adding any additional node while maintaining clique properties.

Algorithm requirements:

- Enumerate all maximal cliques in the graph
- Handle overlapping cliques (a node may belong to multiple cliques)
- Execute within O(N³) time or better for small N (typical crew sizes ≤ 20)

### 4.3 Clique Persistence

Each identified clique is tracked across time steps:

- `clique_id`: Unique identifier
- `member_set`: Set of node_ids currently in clique
- `formation_tick`: Time step when clique first met criteria
- `stability_index`: Measure of membership consistency over recent time window

### 4.4 Clique Evolution

Cliques may:

- **Form**: New maximal clique emerges when sufficient ties strengthen
- **Dissolve**: Existing clique falls below threshold criteria
- **Merge**: Two cliques combine as edges between them strengthen
- **Split**: Single clique fragments as internal ties weaken

## 5. Structural Metrics

### 5.1 Cohesion Metrics

**Global Cohesion**:

```
cohesion(G) = (Σ_{e ∈ E} W(e)) / |E|
```

Average weight across all edges.

**Normalized Density**:

```
density(G) = (2 · |E|) / (|V| · (|V| - 1))
```

Proportion of possible edges that exist.

### 5.2 Fragmentation Metrics

**Component Count**: Number of connected components in the graph (treating edges with weight > ε as present).

**Fragmentation Index**:

```
fragmentation(G) = 1 - (size of largest component / |V|)
```

Ranges from 0 (fully connected) to 1 (maximally fragmented).

### 5.3 Clustering Coefficient

For each node `v`:

```
C(v) = (number of edges among neighbors of v) / (number of possible edges among neighbors of v)
```

Global clustering coefficient:

```
C(G) = average C(v) over all v ∈ V
```

### 5.4 Centrality Measures

**Degree Centrality** for node `v`:

```
degree(v) = Σ_{u ∈ neighbors(v)} W(edge(v,u))
```

**Betweenness Centrality**: Fraction of shortest paths passing through node `v` (weighted by edge weights).

### 5.5 Clique Coverage

```
clique_coverage(G) = (number of nodes in at least one clique) / |V|
```

Indicates proportion of network embedded in cohesive subgroups.

## 6. Update Cycle Sequencing

### 6.1 Time Step Structure

Each discrete time step `t` consists of:

1. **Signal Reception**: Collect all interaction signals for current step
2. **Weight Updates**: Apply drift functions to all affected edges
3. **Passive Decay**: Apply decay/stabilization to non-updated edges
4. **Edge Pruning**: Remove edges below weight threshold
5. **Clique Detection**: Re-identify maximal cliques
6. **Metric Computation**: Calculate all structural metrics
7. **State Export**: Package graph state and metrics for output

### 6.2 Timing Constraints

- All operations within a time step must complete before step `t+1` begins
- No state from future time steps may influence current step (strict causality)
- Update order within a step must be deterministic (reproducibility requirement)

### 6.3 Granularity

Time step duration is defined by upstream modules. This module treats time as discrete ticks with no assumption about real-time correspondence.

## 7. Integration Hooks with TQP Core

### 7.1 Input Interface

The module receives:

- **Interaction signals**: As defined in section 2.1
- **Time step trigger**: Signal to begin update cycle
- **Configuration parameters**: Drift coefficients, thresholds, clique criteria

### 7.2 Output Interface

The module produces:

- **Graph snapshot**: Complete adjacency structure at end of time step
- **Clique data**: List of identified cliques with member sets and stability indices
- **Structural metrics**: All computed cohesion, fragmentation, and centrality measures
- **Change log**: Optional record of edges modified during step

### 7.3 State Queries

Other modules may query:

- Edge weight between specific nodes
- Clique membership for specific node
- Centrality score for specific node
- Global cohesion/fragmentation values

Queries return current state; no historical data is guaranteed unless explicitly logged.

## 8. Error Handling

### 8.1 Invalid Interaction Signals

If an interaction signal references:

- Non-existent node_id: Log error, discard signal
- Intensity outside [0,1]: Clamp to bounds, log warning
- Negative duration: Set to zero, log warning

### 8.2 Graph Instability

If update cycle produces:

- More than 50% edge weight changes > 0.2: Flag as high volatility
- Disconnected graph when connectivity was required: Log fragmentation event
- Clique count exceeding node count (impossible under correct logic): Halt and report internal error

### 8.3 Numerical Stability

All weight computations must:

- Avoid floating-point overflow/underflow
- Maintain precision to at least 3 decimal places
- Handle degenerate cases (zero-node graph, complete graph, etc.)

## 9. Constraints and Assumptions

### 9.1 Scalability

- Design targets crew sizes 2 ≤ N ≤ 50
- Clique detection complexity acceptable for N ≤ 20 with careful algorithm choice
- Larger crews may require approximate clique methods

### 9.2 Graph Properties

- Undirected edges only (symmetric relationships)
- No self-loops (a node cannot have a tie to itself)
- Simple graph (at most one edge between any pair of nodes)

### 9.3 Weight Semantics

- Weight = 0: No tie (edge may be absent or pruned)
- Weight = 1: Maximal tie strength
- Intermediate values represent partial connection strength
- Weights do not encode behavioral, emotional, or psychological meaning

### 9.4 Time Model

- Discrete time steps (no continuous time)
- Synchronous updates (all changes within a step occur "simultaneously")
- No retroactive modifications (past states are immutable)

## 10. Versioning and Extensibility

### 10.1 Parameter Configuration

All thresholds, coefficients, and algorithmic choices must be externally configurable to support:

- Different crew size regimes
- Varied mission contexts (without introducing mission-specific logic)
- Experimental tuning

### 10.2 Metric Extensions

New structural metrics may be added without modifying core graph update logic. Metric computation is isolated from drift and clique detection.

### 10.3 Algorithm Substitution

Clique detection, centrality calculation, and drift functions are modular. Alternative algorithms satisfying the same interface may be swapped in.

### 10.4 Schema Evolution

Node and edge metadata fields allow for extensibility. Future versions may add fields but must not remove or reinterpret existing fields in ways that break downstream consumers.

---

**End of Engineering Specification**
