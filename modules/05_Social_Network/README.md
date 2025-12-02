# Module 05: Social Network & Clique Formation

**Version:** 1.0.0  
**Status:** Implementation Complete

## Overview

The Social Network module provides a graph-based representation of interpersonal relationships in small crews. It models tie strength dynamics, detects cliques, and computes structural metrics—all while maintaining strict separation from psychological or behavioral interpretation.

## Key Features

- **Graph Representation**: Weighted, undirected graph optimized for small crews (N ≤ 50)
- **Tie Dynamics**: Drift functions model tie strengthening, weakening, and stabilization
- **Passive Decay**: Relationships naturally evolve based on interaction patterns
- **Clique Detection**: Bron-Kerbosch algorithm for maximal clique enumeration
- **Structural Metrics**: Cohesion, density, fragmentation, clustering, centrality
- **Persistence Tracking**: Cliques tracked across time steps with stability indices

## Architecture

### Components

1. **GraphStore**: Adjacency matrix representation with O(1) edge lookup
2. **DriftEngine**: Processes interaction signals and applies weight updates
3. **CliqueDetector**: Identifies maximal cliques with persistence tracking
4. **MetricCalculator**: Computes cohesion, density, fragmentation, and centrality
5. **SocialNetworkModule**: Main interface coordinating all components

### Data Flow

```
Interaction Signals → Drift Engine → Graph Store
                                    ↓
                              Edge Pruning
                                    ↓
                           Clique Detector → Clique Snapshot
                                    ↓
                          Metric Calculator → Structural Metrics
```

## Installation

```powershell
# From module directory
pip install -e .
```

## Quick Start

```python
from social_network import (
    SocialNetworkModule,
    NodeDefinition,
    EdgeDefinition,
    InteractionSignal,
    NetworkConfiguration
)

# Define crew
nodes = [
    NodeDefinition("Alice"),
    NodeDefinition("Bob"),
    NodeDefinition("Charlie"),
]

# Initial relationships
edges = [
    EdgeDefinition("Alice", "Bob", 0.5),
    EdgeDefinition("Bob", "Charlie", 0.4),
]

# Create module
module = SocialNetworkModule(nodes, edges)

# Process interactions
signals = [
    InteractionSignal("Alice", "Bob", intensity=0.9, duration=1, timestamp=1)
]

module.update(signals, step_number=1)

# Query state
weight = module.query_edge_weight("Alice", "Bob")
metrics = module.get_structural_metrics()
cliques = module.get_clique_snapshot()
```

## Configuration

All parameters are tunable via `NetworkConfiguration`:

```python
config = NetworkConfiguration(
    drift_strengthening_rate=0.05,      # Tie strengthening coefficient
    drift_weakening_rate=0.02,          # Tie weakening coefficient
    passive_decay_coefficient=0.01,     # Decay rate for inactive edges
    edge_prune_threshold=0.05,          # Weight threshold for pruning
    clique_weight_threshold=0.5,        # Minimum weight for clique edges
    min_clique_size=2,                  # Minimum nodes in clique
    max_drift_delta=0.1,                # Maximum weight change per step
    stability_threshold=0.001,          # Edge stability detection threshold
)
```

## API Reference

### SocialNetworkModule

**`update(interaction_signals, step_number)`**
- Execute one time step update cycle
- Processes signals, applies decay, prunes edges, detects cliques, computes metrics

**`get_graph_snapshot()`**
- Returns complete graph state (nodes and edges)

**`get_clique_snapshot()`**
- Returns all detected cliques with stability indices

**`get_structural_metrics()`**
- Returns cohesion, density, fragmentation, clustering, centrality

**`query_edge_weight(source_id, target_id)`**
- Get current weight of edge between two nodes

**`query_clique_membership(node_id)`**
- Get list of clique IDs that node belongs to

**`query_node_centrality(node_id)`**
- Get degree and betweenness centrality for node

## Running Tests

```powershell
cd modules\05_Social_Network
python -m pytest tests/ -v
```

Or run tests directly:

```powershell
python tests\test_social_network.py
```

## Running Demo

```powershell
cd modules\05_Social_Network
python demo.py
```

The demo demonstrates:
- Basic network operations
- Tie strengthening and weakening
- Clique formation and detection
- Structural metric computation
- Network evolution over time

## Theory and Specification

This implementation is based on:

- **spec.md**: Engineering specification defining graph representation, drift mechanics, and clique detection
- **theory_basis.md**: Network science foundations and relevance to third-quarter research
- **data_contract.md**: Input/output interfaces and data schemas
- **implementation_notes.md**: Architectural guidance and design patterns

## Integration with 3QP System

### Inputs

- **Interaction Signals**: From BDI Cycle or other behavioral modules
- **Time Step Triggers**: From TQP Core orchestration
- **Configuration**: From system initialization

### Outputs

- **Graph Snapshots**: To Stressor Model, Intervention Engine
- **Clique Data**: To Stressor Model for social buffering
- **Structural Metrics**: To Logging System for analysis

### Dependencies

- Upstream: None (receives interaction signals from behavioral modules)
- Downstream: Stressor Model (07), Intervention Engine (08)

## Key Constraints

1. **Structural Focus**: Module models only relationship structure, not psychological meaning
2. **Semantic Neutrality**: No interpretation of why ties form or what they represent
3. **Small Crew Optimization**: Designed for N ≤ 50; larger crews may require algorithm adjustments
4. **Undirected Edges**: Symmetric relationships only
5. **Discrete Time**: Synchronous updates, no continuous time

## Performance Characteristics

- **Edge Lookup**: O(1) using adjacency matrix
- **Update Cycle**: O(N² + E) for N nodes, E edges
- **Clique Detection**: O(N³) worst case, efficient for small N
- **Metric Computation**: O(N² + E)

Typical performance for N=20 crew: <10ms per update cycle

## Limitations

- **Scalability**: Clique detection becomes expensive for N > 30
- **Betweenness Centrality**: Exact computation is O(N³); may need approximation for larger graphs
- **Static Topology**: Node set assumed constant within update cycles

## Future Extensions

Potential enhancements (not yet implemented):

- Approximate clique detection for larger graphs
- Higher-order network motifs (triangles, k-cores)
- Temporal evolution metrics (clique turnover rate)
- Incremental metric updates for efficiency

## Architectural Integrity

This module maintains strict architectural boundaries:

- **No psychological content**: Drift parameters are abstract coefficients, not emotional states
- **No behavioral dependencies**: Network state depends only on interaction signals, not outcomes
- **No scenario-specific logic**: All parameters are generic and configurable

## References

- Bron-Kerbosch Algorithm: Standard maximal clique enumeration
- Small Group Network Dynamics: Research on confined crews (submarines, polar stations, spaceflight)
- Graph Theory Foundations: Weighted, undirected graphs with structural metrics

## Contributing

When extending this module:

1. Maintain separation between structure and semantics
2. Preserve backward compatibility of interfaces
3. Add tests for new features
4. Update data_contract.md for interface changes
5. Document algorithmic complexity

## License

Part of the 3QP (Third-Quarter Phenomenon) research system.

---

**Module Status**: ✅ Implementation Complete  
**Test Coverage**: Core functionality tested  
**Integration Ready**: Yes  
**Documentation**: Complete
