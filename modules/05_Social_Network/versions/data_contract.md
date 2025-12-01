# Module 05: Social Network & Clique Formation — Data Contract

## 1. Overview

This document defines the input and output interfaces for the Social Network module. All data exchanged with other 3QP modules is specified here in abstract, implementation-neutral terms.

## 2. Inputs

### 2.1 Interaction Signals

**Source**: Upstream modules (e.g., TQP Core, BDI Cycle, or other behavioral subsystems)

**Format**:
```
InteractionSignal {
  source_node_id: Identifier,
  target_node_id: Identifier,
  intensity: Real,
  duration: Integer,
  timestamp: Integer
}
```

**Field Constraints**:
- `source_node_id`: Must reference an existing node in the graph
- `target_node_id`: Must reference an existing node in the graph; must differ from `source_node_id`
- `intensity`: Value in [0.0, 1.0]; represents abstract interaction strength
- `duration`: Non-negative integer; represents abstract interaction duration in time step units
- `timestamp`: Time step at which interaction occurred

**Semantics**:
- Intensity = 0.0: Minimal interaction effect
- Intensity = 1.0: Maximal interaction effect
- Duration = 0: Instantaneous signal (may be ignored or handled with minimum duration)
- Duration > 0: Sustained interaction over multiple sub-steps

**Delivery**:
- Signals may arrive individually or in batches per time step
- Order of signal processing within a time step is deterministic (e.g., sorted by timestamp, then by node_id)
- Signals referencing invalid nodes are logged and discarded

### 2.2 Time Step Trigger

**Source**: TQP Core or orchestration layer

**Format**:
```
TimeStepTrigger {
  step_number: Integer,
  delta_time: Real
}
```

**Field Constraints**:
- `step_number`: Monotonically increasing integer starting from 0
- `delta_time`: Real value > 0; may represent abstract or real time units

**Semantics**:
- Signals the module to execute its update cycle for step `step_number`
- `delta_time` may be used to scale drift rates if needed

### 2.3 Configuration Parameters

**Source**: Configuration system or TQP Core initialization

**Format**:
```
NetworkConfiguration {
  drift_strengthening_rate: Real,
  drift_weakening_rate: Real,
  passive_decay_coefficient: Real,
  edge_prune_threshold: Real,
  clique_weight_threshold: Real,
  min_clique_size: Integer,
  max_drift_delta: Real,
  stability_threshold: Real
}
```

**Field Constraints**:
- All `Real` parameters > 0
- `edge_prune_threshold`: Typically in [0.01, 0.1]
- `clique_weight_threshold`: Typically in [0.3, 0.7]
- `min_clique_size`: Typically 2 or 3
- `max_drift_delta`: Typically in [0.05, 0.2]
- `stability_threshold`: Typically in [0.0001, 0.01]

**Semantics**:
- These parameters control drift function behavior, clique detection criteria, and graph maintenance thresholds
- Parameters are set during initialization and may be updated between time steps if needed

### 2.4 Initial Graph State

**Source**: Configuration or initialization module

**Format**:
```
InitialGraphState {
  nodes: List<NodeDefinition>,
  edges: List<EdgeDefinition>
}

NodeDefinition {
  node_id: Identifier,
  metadata: KeyValueMap
}

EdgeDefinition {
  source_node_id: Identifier,
  target_node_id: Identifier,
  initial_weight: Real
}
```

**Field Constraints**:
- `initial_weight`: Value in [0.0, 1.0]
- All `node_id` references in edges must correspond to defined nodes
- No duplicate edges (a pair of nodes may have at most one edge)

**Semantics**:
- Defines the starting state of the social network
- Metadata is optional and extensible (no behavioral data permitted)

## 3. Outputs

### 3.1 Graph State Snapshot

**Destination**: Stressor Model, Intervention Engine, Logging System, or other downstream consumers

**Format**:
```
GraphSnapshot {
  step_number: Integer,
  nodes: List<NodeState>,
  edges: List<EdgeState>,
  timestamp: Integer
}

NodeState {
  node_id: Identifier,
  active_status: Boolean,
  metadata: KeyValueMap
}

EdgeState {
  source_node_id: Identifier,
  target_node_id: Identifier,
  weight: Real,
  drift_velocity: Real,
  last_modified_tick: Integer
}
```

**Field Constraints**:
- `weight`: Value in [0.0, 1.0]
- `drift_velocity`: Real value; may be positive, negative, or zero
- `last_modified_tick`: Integer ≤ current `step_number`

**Semantics**:
- Represents the complete network state at the end of time step `step_number`
- Consumers may extract edge weights, check connectivity, or compute additional metrics

**Frequency**: Generated once per time step after all updates complete

### 3.2 Clique Data

**Destination**: Stressor Model, Intervention Engine, or analytical modules

**Format**:
```
CliqueSnapshot {
  step_number: Integer,
  cliques: List<CliqueDescriptor>
}

CliqueDescriptor {
  clique_id: Identifier,
  member_node_ids: Set<Identifier>,
  formation_tick: Integer,
  stability_index: Real
}
```

**Field Constraints**:
- `member_node_ids`: Set of at least `min_clique_size` node IDs
- `stability_index`: Real value in [0.0, 1.0]; 1.0 = maximally stable, 0.0 = highly volatile
- `formation_tick`: Integer ≤ current `step_number`

**Semantics**:
- Lists all maximal cliques detected at end of time step
- Cliques are identified by unique ID; IDs persist across time steps if clique membership is sufficiently consistent
- A node may appear in multiple cliques

**Frequency**: Generated once per time step after clique detection completes

### 3.3 Structural Metrics

**Destination**: TQP Core, Stressor Model, Logging System, or analytical modules

**Format**:
```
StructuralMetrics {
  step_number: Integer,
  global_cohesion: Real,
  normalized_density: Real,
  fragmentation_index: Real,
  global_clustering_coefficient: Real,
  component_count: Integer,
  clique_coverage: Real,
  node_centralities: Map<Identifier, CentralityScores>
}

CentralityScores {
  degree_centrality: Real,
  betweenness_centrality: Real
}
```

**Field Constraints**:
- All `Real` metrics are non-negative
- `global_cohesion`, `normalized_density`, `fragmentation_index`, `global_clustering_coefficient`, `clique_coverage`: Values in [0.0, 1.0]
- `component_count`: Positive integer ≤ |V|

**Semantics**:
- Quantitative summary of network structural properties
- Node-level centrality scores provided for all active nodes

**Frequency**: Generated once per time step after metric computation completes

### 3.4 Change Log (Optional)

**Destination**: Logging System, debugging tools, or analytical modules

**Format**:
```
ChangeLog {
  step_number: Integer,
  edge_changes: List<EdgeChange>
}

EdgeChange {
  source_node_id: Identifier,
  target_node_id: Identifier,
  old_weight: Real,
  new_weight: Real,
  change_magnitude: Real
}
```

**Field Constraints**:
- `change_magnitude`: |new_weight - old_weight|

**Semantics**:
- Lists all edges whose weights changed during the time step
- Useful for tracking network volatility and debugging drift functions

**Frequency**: Generated once per time step if logging is enabled

## 4. Query Interface

### 4.1 Edge Weight Query

**Input**:
```
EdgeWeightQuery {
  source_node_id: Identifier,
  target_node_id: Identifier
}
```

**Output**:
```
EdgeWeightResponse {
  weight: Real | null,
  exists: Boolean
}
```

**Semantics**:
- Returns current weight of edge between specified nodes
- If edge does not exist, `exists = false` and `weight = null`

### 4.2 Clique Membership Query

**Input**:
```
CliqueMembershipQuery {
  node_id: Identifier
}
```

**Output**:
```
CliqueMembershipResponse {
  clique_ids: List<Identifier>
}
```

**Semantics**:
- Returns list of all cliques to which the node currently belongs
- Empty list if node is not in any clique

### 4.3 Node Centrality Query

**Input**:
```
NodeCentralityQuery {
  node_id: Identifier
}
```

**Output**:
```
NodeCentralityResponse {
  degree_centrality: Real,
  betweenness_centrality: Real
}
```

**Semantics**:
- Returns current centrality scores for specified node
- If node does not exist, returns zeros or error code

### 4.4 Global Metric Query

**Input**:
```
GlobalMetricQuery {
  metric_name: String
}
```

**Output**:
```
GlobalMetricResponse {
  value: Real | Integer | null
}
```

**Semantics**:
- Returns current value of named global metric (e.g., "global_cohesion", "fragmentation_index")
- If metric name is invalid, returns null

## 5. Timing and Synchronization

### 5.1 Update Sequence

1. **T0**: Time step trigger received
2. **T1**: All interaction signals for this step collected
3. **T2**: Weight updates applied
4. **T3**: Passive decay applied
5. **T4**: Edge pruning performed
6. **T5**: Clique detection executed
7. **T6**: Metrics computed
8. **T7**: Outputs generated and made available
9. **T8**: Ready for queries until next time step trigger

### 5.2 Output Availability

All outputs for step `N` are guaranteed available before step `N+1` begins. Queries return data from the most recently completed step.

### 5.3 Granularity

Time steps are treated as atomic units. Sub-step events (e.g., multiple interactions within a single step) are aggregated during update processing. No intra-step state is exposed.

## 6. Data Validity Rules

### 6.1 Input Validation

The module must reject or sanitize:

- Interaction signals with intensity outside [0.0, 1.0] → clamp to bounds
- Interaction signals with negative duration → set to zero
- Interaction signals referencing non-existent nodes → discard and log error
- Configuration parameters outside reasonable bounds → reject initialization

### 6.2 Output Guarantees

All outputs satisfy:

- Edge weights in [0.0, 1.0]
- Clique members are valid node IDs
- Metrics are well-defined (no NaN, no infinite values)
- Timestamps and step numbers are consistent and monotonically increasing

### 6.3 Consistency

At all times:

- Undirected edges: if weight(A, B) = w, then weight(B, A) = w
- No self-loops: no edge (A, A) exists
- Pruning: no edge with weight < prune threshold remains in graph
- Clique definitions: all cliques satisfy weight and size criteria

## 7. Extensibility

### 7.1 Adding New Inputs

Future versions may accept:

- External perturbation signals (e.g., crew rotation events)
- Context tags on interaction signals (task type, location) — metadata only, no interpretation

New input types must not break existing processing logic.

### 7.2 Adding New Outputs

Future versions may produce:

- Higher-order network motifs (triangles, k-cores)
- Temporal evolution metrics (rate of clique turnover)
- Subgraph embeddings for machine learning consumers

New outputs are additive; existing outputs remain available.

### 7.3 Schema Versioning

All inputs and outputs include implicit or explicit version identifiers. Breaking changes to data structures require major version increments and migration paths.

---

**End of Data Contract**
