"""
Drift engine for updating edge weights based on interaction signals.

Implements the drift function and decay mechanics defined in spec.md.
"""

from typing import List, Dict, Tuple
import logging
from .types import InteractionSignal, NetworkConfiguration
from .graph_store import GraphStore


logger = logging.getLogger(__name__)


class DriftEngine:
    """
    Processes interaction signals and applies weight updates.
    
    Implements strengthening, weakening, and saturation behaviors.
    """
    
    def __init__(self, config: NetworkConfiguration):
        """
        Initialize drift engine with configuration.
        
        Args:
            config: Network configuration parameters
        """
        self.config = config
        
        # Parameters for drift function
        self.alpha = config.drift_strengthening_rate
        self.beta = config.saturation_exponent_strengthen
        self.gamma = config.drift_weakening_rate
        self.delta = config.saturation_exponent_weaken
        self.max_delta = config.max_drift_delta
        self.lambda_smooth = config.velocity_smoothing_factor
    
    def compute_drift(
        self,
        intensity: float,
        duration: int,
        current_weight: float
    ) -> float:
        """
        Compute weight change (delta) for a single interaction.
        
        Uses drift function:
        Δ(intensity, duration, W) = 
          α · intensity · duration · (1 - W)^β - γ · (1 - intensity) · W^δ
        
        Args:
            intensity: Interaction strength [0.0, 1.0]
            duration: Interaction duration (time step units)
            current_weight: Current edge weight [0.0, 1.0]
            
        Returns:
            Weight change (may be positive or negative)
        """
        # Strengthening term: positive intensity strengthens ties
        strengthen = (
            self.alpha * intensity * duration * 
            ((1.0 - current_weight) ** self.beta)
        )
        
        # Weakening term: low intensity weakens ties
        weaken = (
            self.gamma * (1.0 - intensity) * 
            (current_weight ** self.delta)
        )
        
        drift = strengthen - weaken
        
        # Clamp to max delta to ensure bounded changes
        drift = max(-self.max_delta, min(self.max_delta, drift))
        
        return drift
    
    def apply_interaction_signals(
        self,
        graph: GraphStore,
        signals: List[InteractionSignal],
        current_tick: int
    ) -> Dict[Tuple[str, str], float]:
        """
        Apply all interaction signals to graph.
        
        Aggregates multiple signals to same edge by summation.
        
        Args:
            graph: Graph store to update
            signals: List of interaction signals
            current_tick: Current time step
            
        Returns:
            Dictionary mapping (source, target) -> total_drift applied
        """
        # Aggregate signals by edge
        edge_drifts: Dict[Tuple[str, str], float] = {}
        
        for signal in signals:
            # Validate nodes exist
            if not graph.node_exists(signal.source_node_id):
                logger.warning(
                    f"Interaction signal references non-existent node: "
                    f"{signal.source_node_id}"
                )
                continue
            
            if not graph.node_exists(signal.target_node_id):
                logger.warning(
                    f"Interaction signal references non-existent node: "
                    f"{signal.target_node_id}"
                )
                continue
            
            # Get current weight (or 0 if edge doesn't exist)
            current_weight = graph.get_edge_weight(
                signal.source_node_id,
                signal.target_node_id
            )
            if current_weight is None:
                current_weight = 0.0
            
            # Compute drift
            drift = self.compute_drift(
                signal.intensity,
                signal.duration,
                current_weight
            )
            
            # Aggregate (use canonical edge ordering)
            edge_key = self._canonical_edge_key(
                signal.source_node_id,
                signal.target_node_id
            )
            
            if edge_key in edge_drifts:
                edge_drifts[edge_key] += drift
            else:
                edge_drifts[edge_key] = drift
        
        # Apply aggregated drifts to graph
        for (source_id, target_id), total_drift in edge_drifts.items():
            current_weight = graph.get_edge_weight(source_id, target_id)
            if current_weight is None:
                current_weight = 0.0
            
            # Clamp total drift to max delta
            total_drift = max(-self.max_delta, min(self.max_delta, total_drift))
            
            new_weight = current_weight + total_drift
            new_weight = max(0.0, min(1.0, new_weight))  # Clamp to [0, 1]
            
            # Compute new velocity (smoothed)
            old_velocity = 0.0
            edge_state = graph.get_edge_state(source_id, target_id)
            if edge_state:
                old_velocity = edge_state.drift_velocity
            
            new_velocity = self._smooth_velocity(total_drift, old_velocity)
            
            # Update edge
            graph.set_edge_weight(
                source_id,
                target_id,
                new_weight,
                current_tick,
                new_velocity
            )
        
        return edge_drifts
    
    def apply_passive_decay(
        self,
        graph: GraphStore,
        current_tick: int,
        updated_edges: set
    ) -> int:
        """
        Apply passive drift to edges not receiving interaction signals.
        
        Uses drift velocity to continue recent trends.
        
        Args:
            graph: Graph store to update
            current_tick: Current time step
            updated_edges: Set of (source, target) tuples already updated
            
        Returns:
            Number of edges affected by passive decay
        """
        decay_count = 0
        all_edges = graph.get_all_edges(min_weight=0.0)
        
        for edge in all_edges:
            edge_key = self._canonical_edge_key(
                edge.source_node_id,
                edge.target_node_id
            )
            
            # Skip edges that received interaction signals
            if edge_key in updated_edges:
                continue
            
            # Apply passive drift based on velocity
            drift = self.config.passive_decay_coefficient * edge.drift_velocity
            
            new_weight = edge.weight + drift
            new_weight = max(0.0, min(1.0, new_weight))
            
            # Smooth velocity (decaying toward zero)
            new_velocity = self._smooth_velocity(drift, edge.drift_velocity)
            
            # Update edge
            graph.set_edge_weight(
                edge.source_node_id,
                edge.target_node_id,
                new_weight,
                current_tick,
                new_velocity
            )
            
            decay_count += 1
        
        return decay_count
    
    def _canonical_edge_key(self, node_a: str, node_b: str) -> Tuple[str, str]:
        """
        Create canonical edge key (undirected).
        
        Always returns (smaller_id, larger_id) to ensure consistency.
        """
        if node_a < node_b:
            return (node_a, node_b)
        else:
            return (node_b, node_a)
    
    def _smooth_velocity(self, new_drift: float, old_velocity: float) -> float:
        """
        Apply exponential smoothing to velocity.
        
        velocity_smoothed = λ · new_drift + (1 - λ) · old_velocity
        """
        return (
            self.lambda_smooth * new_drift + 
            (1.0 - self.lambda_smooth) * old_velocity
        )
