"""
Data types and structures for the Social Network module.

These types implement the data contract defined in data_contract.md.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional


@dataclass
class InteractionSignal:
    """
    Signal representing an interaction between two nodes.
    
    Attributes:
        source_node_id: Identifier of first node
        target_node_id: Identifier of second node
        intensity: Interaction strength in [0.0, 1.0]
        duration: Interaction duration in time step units (non-negative)
        timestamp: Time step when interaction occurred
    """
    source_node_id: str
    target_node_id: str
    intensity: float
    duration: int
    timestamp: int
    
    def __post_init__(self):
        """Validate signal constraints."""
        if not 0.0 <= self.intensity <= 1.0:
            self.intensity = max(0.0, min(1.0, self.intensity))
        if self.duration < 0:
            self.duration = 0
        if self.source_node_id == self.target_node_id:
            raise ValueError("source_node_id and target_node_id must differ")


@dataclass
class NodeDefinition:
    """
    Initial definition of a network node.
    
    Attributes:
        node_id: Unique identifier (immutable)
        metadata: Optional key-value store for extensibility
    """
    node_id: str
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class EdgeDefinition:
    """
    Initial definition of a network edge.
    
    Attributes:
        source_node_id: Identifier of first node
        target_node_id: Identifier of second node
        initial_weight: Starting edge weight in [0.0, 1.0]
    """
    source_node_id: str
    target_node_id: str
    initial_weight: float
    
    def __post_init__(self):
        """Validate edge constraints."""
        if not 0.0 <= self.initial_weight <= 1.0:
            raise ValueError(f"initial_weight must be in [0.0, 1.0], got {self.initial_weight}")
        if self.source_node_id == self.target_node_id:
            raise ValueError("Cannot create self-loop edge")


@dataclass
class NodeState:
    """
    Current state of a network node.
    
    Attributes:
        node_id: Unique identifier
        active_status: Whether node participates in current update cycle
        metadata: Optional key-value store
    """
    node_id: str
    active_status: bool = True
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class EdgeState:
    """
    Current state of a network edge.
    
    Attributes:
        source_node_id: Identifier of first node
        target_node_id: Identifier of second node
        weight: Current tie strength in [0.0, 1.0]
        drift_velocity: Rate of weight change (may be positive, negative, or zero)
        last_modified_tick: Timestamp of most recent weight update
    """
    source_node_id: str
    target_node_id: str
    weight: float
    drift_velocity: float = 0.0
    last_modified_tick: int = 0


@dataclass
class GraphSnapshot:
    """
    Complete network state at a specific time step.
    
    Attributes:
        step_number: Current time step
        nodes: List of all node states
        edges: List of all edge states
        timestamp: Time step identifier
    """
    step_number: int
    nodes: List[NodeState]
    edges: List[EdgeState]
    timestamp: int


@dataclass
class CliqueDescriptor:
    """
    Description of a detected clique.
    
    Attributes:
        clique_id: Unique identifier for this clique
        member_node_ids: Set of node IDs in the clique
        formation_tick: Time step when clique first formed
        stability_index: Measure of membership consistency in [0.0, 1.0]
    """
    clique_id: str
    member_node_ids: Set[str]
    formation_tick: int
    stability_index: float = 1.0


@dataclass
class CliqueSnapshot:
    """
    All detected cliques at a specific time step.
    
    Attributes:
        step_number: Current time step
        cliques: List of all detected cliques
    """
    step_number: int
    cliques: List[CliqueDescriptor]


@dataclass
class CentralityScores:
    """
    Centrality metrics for a single node.
    
    Attributes:
        degree_centrality: Sum of incident edge weights
        betweenness_centrality: Fraction of shortest paths through node
    """
    degree_centrality: float = 0.0
    betweenness_centrality: float = 0.0


@dataclass
class StructuralMetrics:
    """
    Structural metrics for the entire network.
    
    Attributes:
        step_number: Current time step
        global_cohesion: Average edge weight across all edges
        normalized_density: Proportion of possible edges that exist
        fragmentation_index: Degree of network fragmentation (0 = connected, 1 = fragmented)
        global_clustering_coefficient: Average clustering coefficient
        component_count: Number of connected components
        clique_coverage: Proportion of nodes in at least one clique
        node_centralities: Centrality scores for each node
    """
    step_number: int
    global_cohesion: float = 0.0
    normalized_density: float = 0.0
    fragmentation_index: float = 0.0
    global_clustering_coefficient: float = 0.0
    component_count: int = 0
    clique_coverage: float = 0.0
    node_centralities: Dict[str, CentralityScores] = field(default_factory=dict)


@dataclass
class NetworkConfiguration:
    """
    Configuration parameters for network dynamics.
    
    Attributes:
        drift_strengthening_rate: Coefficient for tie strengthening (alpha)
        drift_weakening_rate: Coefficient for tie weakening (gamma)
        passive_decay_coefficient: Global decay/stabilization coefficient
        edge_prune_threshold: Weight below which edges are removed
        clique_weight_threshold: Minimum weight for edges within cliques
        min_clique_size: Minimum number of nodes in a clique
        max_drift_delta: Maximum absolute weight change per time step
        stability_threshold: Threshold for detecting stable edges
        saturation_exponent_strengthen: Saturation exponent for strengthening
        saturation_exponent_weaken: Saturation exponent for weakening
        velocity_smoothing_factor: Exponential smoothing coefficient for velocity
    """
    drift_strengthening_rate: float = 0.05
    drift_weakening_rate: float = 0.02
    passive_decay_coefficient: float = 0.01
    edge_prune_threshold: float = 0.05
    clique_weight_threshold: float = 0.5
    min_clique_size: int = 2
    max_drift_delta: float = 0.1
    stability_threshold: float = 0.001
    saturation_exponent_strengthen: float = 1.5
    saturation_exponent_weaken: float = 1.0
    velocity_smoothing_factor: float = 0.5
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.drift_strengthening_rate <= 0:
            raise ValueError("drift_strengthening_rate must be positive")
        if self.drift_weakening_rate <= 0:
            raise ValueError("drift_weakening_rate must be positive")
        if not 0.0 <= self.edge_prune_threshold <= 0.2:
            raise ValueError("edge_prune_threshold should be in [0.0, 0.2]")
        if not 0.0 <= self.clique_weight_threshold <= 1.0:
            raise ValueError("clique_weight_threshold must be in [0.0, 1.0]")
        if self.min_clique_size < 2:
            raise ValueError("min_clique_size must be at least 2")
