# Module 05: Social Network & Clique Formation

## Purpose

This module defines the structural and computational subsystem responsible for modeling interpersonal ties, relationship strengths, clique formation dynamics, and social drift patterns within small crews. It operates as a pure graph-theoretic mechanism, independent of psychological interpretation, emotional content, or behavioral semantics.

## Scope

The Social Network module provides:

- **Graph representation** of crew members as nodes and interpersonal ties as weighted edges
- **Tie evolution rules** governing how connection strengths change over time
- **Clique detection algorithms** identifying cohesive subgroups within the network
- **Drift mechanisms** modeling gradual strengthening, weakening, or stabilization of ties
- **Structural metrics** quantifying cohesion, fragmentation, clustering, and centrality
- **Time-stepped update protocols** ensuring deterministic graph state transitions

## Boundaries

This module does NOT:

- Interpret ties in psychological or emotional terms
- Generate behavioral outcomes or decisions
- Define stressor sources or intervention strategies
- Model cognitive states or affective processes
- Create narrative content or mission scenarios

All functionality is strictly structural and mechanistic.

## High-Level Flow

1. **Initialization**: Network graph is constructed with nodes representing crew members and edges representing initial tie configurations
2. **Update Cycle**: At each discrete time step, the module receives abstract interaction signals and applies drift functions to modify edge weights
3. **Clique Identification**: Algorithmic detection of subgraph clusters meeting cohesion criteria
4. **Metric Computation**: Calculation of structural indicators (density, fragmentation indices, centrality measures)
5. **State Output**: Updated graph structure and derived metrics are exported for consumption by other 3QP modules

## Integration with 3QP

The Social Network module operates as a self-contained subsystem within the broader 3QP architecture. It receives abstract interaction intensity signals from upstream modules and produces structural outputs consumed downstream. The module maintains no awareness of:

- Why ties change (psychological causation)
- What behaviors result from network structure (performance effects)
- How interventions should respond to network states (strategic logic)

These concerns are handled by other modules according to their respective domains.

## Output to Rest of 3QP

The module provides:

- **Graph State**: Current adjacency structure, edge weights, and node metadata
- **Clique Indicators**: Identification of cohesive subgroups and membership vectors
- **Structural Metrics**: Quantitative measures of network properties (cohesion, fragmentation, centrality distributions)
- **Change Deltas**: Information about tie evolution rates and directionality

These outputs serve as input to modules responsible for stressor modeling, intervention logic, and performance tracking, but this module does not interpret or prescribe their usage.

## Engineering Characteristics

- **Deterministic**: Given identical inputs and initial conditions, produces identical outputs
- **Modular**: No dependencies on psychological or behavioral interpretation layers
- **Scalable**: Design accommodates variable crew sizes within small-group constraints
- **Versioned**: Maintains clear separation between structural specification and implementation details

## Document Structure

This module is documented across five files:

- `README.md` (this file): Overview and purpose
- `spec.md`: Complete engineering specification
- `theory_basis.md`: Network-science foundations
- `data_contract.md`: Input/output interface definitions
- `implementation_notes.md`: Construction and maintenance guidance
