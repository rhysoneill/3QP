"""
Social Network Module - Main interface for TQP Core integration.

Manages social relationship graph with tie strength dynamics, clique detection,
and structural metrics.
"""

from typing import List, Optional
import logging
from .types import (
    InteractionSignal,
    NodeDefinition,
    EdgeDefinition,
    GraphSnapshot,
    CliqueSnapshot,
    StructuralMetrics,
    NetworkConfiguration,
)
from .graph_store import GraphStore
from .drift_engine import DriftEngine
from .clique_detector import CliqueDetector
from .metric_calculator import MetricCalculator


logger = logging.getLogger(__name__)


class SocialNetworkModule:
    """
    Social Network & Clique Formation Module.
    
    Manages graph-based representation of interpersonal relationships,
    including tie strength evolution, clique detection, and structural metrics.
    
    This module is stateful and maintains the network across time steps.
    """
    
    def __init__(
        self,
        nodes: List[NodeDefinition],
        edges: List[EdgeDefinition],
        config: Optional[NetworkConfiguration] = None
    ):
        """
        Initialize the social network module.
        
        Args:
            nodes: Initial node definitions
            edges: Initial edge definitions
            config: Network configuration (uses defaults if None)
        """
        self.config = config or NetworkConfiguration()
        
        # Initialize components
        self.graph = GraphStore(nodes, edges)
        self.drift_engine = DriftEngine(self.config)
        self.clique_detector = CliqueDetector(self.config)
        self.metric_calculator = MetricCalculator()
        
        # State tracking
        self.current_tick = 0
        self.last_snapshot: Optional[GraphSnapshot] = None
        self.last_cliques: Optional[CliqueSnapshot] = None
        self.last_metrics: Optional[StructuralMetrics] = None
        
        logger.info(
            f"SocialNetworkModule initialized with {len(nodes)} nodes "
            f"and {len(edges)} edges"
        )
    
    def update(
        self,
        interaction_signals: List[InteractionSignal],
        step_number: int
    ) -> None:
        """
        Execute one update cycle of the network.
        
        Sequence:
        1. Process interaction signals (drift updates)
        2. Apply passive decay to non-updated edges
        3. Prune weak edges
        4. Detect cliques
        5. Compute structural metrics
        6. Generate outputs
        
        Args:
            interaction_signals: Interactions to process this time step
            step_number: Current time step number
        """
        self.current_tick = step_number
        
        logger.debug(
            f"Step {step_number}: Processing {len(interaction_signals)} "
            f"interaction signals"
        )
        
        # 1. Process interaction signals
        updated_edges = self.drift_engine.apply_interaction_signals(
            self.graph,
            interaction_signals,
            self.current_tick
        )
        
        # Convert to set for efficient lookup
        updated_edge_set = set(updated_edges.keys())
        
        # 2. Apply passive decay
        decay_count = self.drift_engine.apply_passive_decay(
            self.graph,
            self.current_tick,
            updated_edge_set
        )
        
        logger.debug(
            f"Step {step_number}: Updated {len(updated_edges)} edges, "
            f"applied decay to {decay_count} edges"
        )
        
        # 3. Prune weak edges
        pruned_count = self.graph.prune_edges(
            self.config.edge_prune_threshold,
            self.current_tick
        )
        
        if pruned_count > 0:
            logger.debug(f"Step {step_number}: Pruned {pruned_count} weak edges")
        
        # 4. Detect cliques
        cliques = self.clique_detector.detect_cliques(
            self.graph,
            self.current_tick
        )
        
        logger.debug(f"Step {step_number}: Detected {len(cliques)} cliques")
        
        # 5. Compute metrics
        metrics = self.metric_calculator.compute_metrics(
            self.graph,
            cliques,
            self.current_tick
        )
        
        logger.debug(
            f"Step {step_number}: Metrics - "
            f"cohesion={metrics.global_cohesion:.3f}, "
            f"density={metrics.normalized_density:.3f}, "
            f"fragmentation={metrics.fragmentation_index:.3f}"
        )
        
        # 6. Store outputs
        self.last_snapshot = self._create_graph_snapshot()
        self.last_cliques = CliqueSnapshot(
            step_number=self.current_tick,
            cliques=cliques
        )
        self.last_metrics = metrics
        
        # Check for high volatility
        if len(updated_edges) > 0:
            edge_count = self.graph.get_edge_count(min_weight=0.0)
            if edge_count > 0:
                change_ratio = len(updated_edges) / edge_count
                if change_ratio > 0.5:
                    logger.warning(
                        f"Step {step_number}: High network volatility - "
                        f"{change_ratio*100:.1f}% of edges changed"
                    )
    
    def get_graph_snapshot(self) -> Optional[GraphSnapshot]:
        """
        Get the most recent graph snapshot.
        
        Returns:
            GraphSnapshot or None if no update has occurred
        """
        return self.last_snapshot
    
    def get_clique_snapshot(self) -> Optional[CliqueSnapshot]:
        """
        Get the most recent clique snapshot.
        
        Returns:
            CliqueSnapshot or None if no update has occurred
        """
        return self.last_cliques
    
    def get_structural_metrics(self) -> Optional[StructuralMetrics]:
        """
        Get the most recent structural metrics.
        
        Returns:
            StructuralMetrics or None if no update has occurred
        """
        return self.last_metrics
    
    def query_edge_weight(self, source_id: str, target_id: str) -> Optional[float]:
        """
        Query current weight of edge between two nodes.
        
        Args:
            source_id: First node ID
            target_id: Second node ID
            
        Returns:
            Edge weight or None if edge doesn't exist
        """
        return self.graph.get_edge_weight(source_id, target_id)
    
    def query_clique_membership(self, node_id: str) -> List[str]:
        """
        Query which cliques a node belongs to.
        
        Args:
            node_id: Node to check
            
        Returns:
            List of clique IDs
        """
        return self.clique_detector.get_clique_membership(node_id)
    
    def query_node_centrality(self, node_id: str) -> Optional[dict]:
        """
        Query centrality scores for a node.
        
        Args:
            node_id: Node to check
            
        Returns:
            Dictionary with centrality scores or None if no metrics available
        """
        if not self.last_metrics:
            return None
        
        scores = self.last_metrics.node_centralities.get(node_id)
        if not scores:
            return None
        
        return {
            'degree_centrality': scores.degree_centrality,
            'betweenness_centrality': scores.betweenness_centrality
        }
    
    def _create_graph_snapshot(self) -> GraphSnapshot:
        """
        Create a snapshot of current graph state.
        
        Returns:
            Complete GraphSnapshot
        """
        nodes = self.graph.get_all_nodes()
        edges = self.graph.get_all_edges(min_weight=0.0)
        
        return GraphSnapshot(
            step_number=self.current_tick,
            nodes=nodes,
            edges=edges,
            timestamp=self.current_tick
        )
    
    def get_summary(self) -> dict:
        """
        Get summary statistics for current network state.
        
        Returns:
            Dictionary with summary information
        """
        if not self.last_metrics:
            return {
                'initialized': True,
                'updates_run': 0,
                'node_count': self.graph.get_node_count(),
                'edge_count': self.graph.get_edge_count(min_weight=0.0)
            }
        
        return {
            'step_number': self.current_tick,
            'node_count': self.graph.get_node_count(),
            'edge_count': self.graph.get_edge_count(min_weight=0.0),
            'clique_count': len(self.last_cliques.cliques) if self.last_cliques else 0,
            'global_cohesion': self.last_metrics.global_cohesion,
            'normalized_density': self.last_metrics.normalized_density,
            'fragmentation_index': self.last_metrics.fragmentation_index,
            'clustering_coefficient': self.last_metrics.global_clustering_coefficient,
            'clique_coverage': self.last_metrics.clique_coverage,
            'component_count': self.last_metrics.component_count
        }
