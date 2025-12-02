"""
Clique detection for the Social Network module.

Implements Bron-Kerbosch algorithm for maximal clique enumeration.
"""

from typing import List, Set, Dict
import logging
from .types import CliqueDescriptor, NetworkConfiguration
from .graph_store import GraphStore


logger = logging.getLogger(__name__)


class CliqueDetector:
    """
    Detects maximal cliques in the social network.
    
    Uses Bron-Kerbosch algorithm for exhaustive clique enumeration.
    Tracks clique persistence across time steps.
    """
    
    def __init__(self, config: NetworkConfiguration):
        """
        Initialize clique detector with configuration.
        
        Args:
            config: Network configuration parameters
        """
        self.config = config
        self.weight_threshold = config.clique_weight_threshold
        self.min_size = config.min_clique_size
        
        # Track cliques across time steps for persistence
        self._clique_history: Dict[str, CliqueDescriptor] = {}
        self._next_clique_id = 0
    
    def detect_cliques(
        self,
        graph: GraphStore,
        current_tick: int
    ) -> List[CliqueDescriptor]:
        """
        Detect all maximal cliques in the graph.
        
        Args:
            graph: Graph store to analyze
            current_tick: Current time step
            
        Returns:
            List of detected cliques with persistence tracking
        """
        # Get all nodes
        all_nodes = set(graph.get_node_ids())
        
        # Find maximal cliques using Bron-Kerbosch
        cliques_as_sets = []
        self._bron_kerbosch(
            graph,
            current=set(),
            candidates=all_nodes,
            excluded=set(),
            cliques=cliques_as_sets
        )
        
        # Filter by minimum size
        cliques_as_sets = [
            clique for clique in cliques_as_sets
            if len(clique) >= self.min_size
        ]
        
        # Match with historical cliques for persistence tracking
        clique_descriptors = self._match_and_track_cliques(
            cliques_as_sets,
            current_tick
        )
        
        return clique_descriptors
    
    def _bron_kerbosch(
        self,
        graph: GraphStore,
        current: Set[str],
        candidates: Set[str],
        excluded: Set[str],
        cliques: List[Set[str]]
    ):
        """
        Bron-Kerbosch algorithm for maximal clique enumeration.
        
        Recursive algorithm that finds all maximal cliques.
        
        Args:
            graph: Graph to analyze
            current: Current clique being built
            candidates: Candidate nodes that could extend current clique
            excluded: Nodes already processed
            cliques: Output list to append found cliques
        """
        # Base case: no candidates or excluded nodes
        if not candidates and not excluded:
            if len(current) >= self.min_size:
                cliques.append(current.copy())
            return
        
        # Process each candidate
        # Make a copy to avoid modifying during iteration
        candidates_copy = candidates.copy()
        
        for node in candidates_copy:
            # Get neighbors of node with sufficient weight
            neighbors = set(
                neighbor_id
                for neighbor_id, weight in graph.get_neighbors(
                    node,
                    min_weight=self.weight_threshold
                )
            )
            
            # Recurse with node added to current clique
            self._bron_kerbosch(
                graph,
                current=current | {node},
                candidates=candidates & neighbors,
                excluded=excluded & neighbors,
                cliques=cliques
            )
            
            # Move node from candidates to excluded
            candidates.remove(node)
            excluded.add(node)
    
    def _match_and_track_cliques(
        self,
        new_cliques: List[Set[str]],
        current_tick: int
    ) -> List[CliqueDescriptor]:
        """
        Match new cliques with historical cliques for persistence tracking.
        
        Uses Jaccard similarity to identify continuing cliques.
        
        Args:
            new_cliques: List of newly detected cliques
            current_tick: Current time step
            
        Returns:
            List of clique descriptors with IDs and stability indices
        """
        descriptors = []
        matched_historical = set()
        
        for new_clique in new_cliques:
            # Try to match with existing clique
            best_match_id = None
            best_similarity = 0.0
            
            for clique_id, historical_clique in self._clique_history.items():
                if clique_id in matched_historical:
                    continue
                
                # Compute Jaccard similarity
                similarity = self._jaccard_similarity(
                    new_clique,
                    historical_clique.member_node_ids
                )
                
                # Match if similarity exceeds threshold (0.6)
                if similarity > best_similarity and similarity >= 0.6:
                    best_similarity = similarity
                    best_match_id = clique_id
            
            if best_match_id:
                # Continue existing clique
                matched_historical.add(best_match_id)
                historical = self._clique_history[best_match_id]
                
                # Update stability index based on similarity
                new_stability = (
                    0.8 * historical.stability_index + 
                    0.2 * best_similarity
                )
                
                descriptor = CliqueDescriptor(
                    clique_id=best_match_id,
                    member_node_ids=new_clique.copy(),
                    formation_tick=historical.formation_tick,
                    stability_index=new_stability
                )
            else:
                # New clique
                clique_id = f"clique_{self._next_clique_id}"
                self._next_clique_id += 1
                
                descriptor = CliqueDescriptor(
                    clique_id=clique_id,
                    member_node_ids=new_clique.copy(),
                    formation_tick=current_tick,
                    stability_index=1.0
                )
            
            descriptors.append(descriptor)
        
        # Update clique history
        self._clique_history = {
            desc.clique_id: desc
            for desc in descriptors
        }
        
        return descriptors
    
    def _jaccard_similarity(self, set_a: Set[str], set_b: Set[str]) -> float:
        """
        Compute Jaccard similarity between two sets.
        
        similarity = |A ∩ B| / |A ∪ B|
        
        Args:
            set_a: First set
            set_b: Second set
            
        Returns:
            Similarity value in [0.0, 1.0]
        """
        if not set_a and not set_b:
            return 1.0
        
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def get_clique_membership(self, node_id: str) -> List[str]:
        """
        Get list of clique IDs that a node belongs to.
        
        Args:
            node_id: Node to check
            
        Returns:
            List of clique IDs
        """
        return [
            clique_id
            for clique_id, clique in self._clique_history.items()
            if node_id in clique.member_node_ids
        ]
