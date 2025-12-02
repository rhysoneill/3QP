"""
Graph storage and representation for the Social Network module.

Implements adjacency matrix representation optimized for small crews.
"""

from typing import Dict, List, Optional, Set, Tuple
import numpy as np
from .types import NodeDefinition, EdgeDefinition, NodeState, EdgeState


class GraphStore:
    """
    Manages the graph structure using adjacency matrix representation.
    
    Optimized for small crews (N ≤ 50) with O(1) edge lookup.
    """
    
    def __init__(self, nodes: List[NodeDefinition], edges: List[EdgeDefinition]):
        """
        Initialize graph with nodes and edges.
        
        Args:
            nodes: Initial node definitions
            edges: Initial edge definitions
        """
        # Node management
        self._nodes: Dict[str, NodeState] = {}
        self._node_id_to_index: Dict[str, int] = {}
        self._index_to_node_id: Dict[int, str] = {}
        
        # Initialize nodes
        for i, node_def in enumerate(nodes):
            self._nodes[node_def.node_id] = NodeState(
                node_id=node_def.node_id,
                active_status=True,
                metadata=node_def.metadata.copy()
            )
            self._node_id_to_index[node_def.node_id] = i
            self._index_to_node_id[i] = node_def.node_id
        
        n = len(nodes)
        
        # Adjacency matrix: weights[i][j] stores edge weight
        # Initialize to zeros - no edges exist initially
        self._weights = np.zeros((n, n), dtype=np.float64)
        
        # Drift velocity matrix
        self._velocities = np.zeros((n, n), dtype=np.float64)
        
        # Last modified tick matrix
        self._last_modified = np.zeros((n, n), dtype=np.int64)
        
        # Initialize only the specified edges (not a complete graph)
        for edge_def in edges:
            self.set_edge_weight(
                edge_def.source_node_id,
                edge_def.target_node_id,
                edge_def.initial_weight,
                tick=0
            )
    
    def node_exists(self, node_id: str) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self._nodes
    
    def get_node(self, node_id: str) -> Optional[NodeState]:
        """Get node state by ID."""
        return self._nodes.get(node_id)
    
    def get_all_nodes(self) -> List[NodeState]:
        """Get all node states."""
        return list(self._nodes.values())
    
    def get_edge_weight(self, source_id: str, target_id: str) -> Optional[float]:
        """
        Get weight of edge between two nodes.
        
        Returns None if either node doesn't exist.
        Graph is undirected, so order doesn't matter.
        """
        if source_id not in self._node_id_to_index or target_id not in self._node_id_to_index:
            return None
        
        i = self._node_id_to_index[source_id]
        j = self._node_id_to_index[target_id]
        
        return float(self._weights[i, j])
    
    def set_edge_weight(
        self,
        source_id: str,
        target_id: str,
        weight: float,
        tick: int,
        velocity: float = 0.0
    ) -> bool:
        """
        Set weight of edge between two nodes.
        
        Graph is undirected, so sets both (i,j) and (j,i).
        
        Args:
            source_id: First node ID
            target_id: Second node ID
            weight: New weight value (clamped to [0.0, 1.0])
            tick: Current time step
            velocity: Drift velocity (optional)
            
        Returns:
            True if successful, False if nodes don't exist
        """
        if source_id not in self._node_id_to_index or target_id not in self._node_id_to_index:
            return False
        
        if source_id == target_id:
            return False  # No self-loops
        
        i = self._node_id_to_index[source_id]
        j = self._node_id_to_index[target_id]
        
        # Clamp weight to [0, 1]
        weight = max(0.0, min(1.0, weight))
        
        # Set symmetric edges
        self._weights[i, j] = weight
        self._weights[j, i] = weight
        
        self._velocities[i, j] = velocity
        self._velocities[j, i] = velocity
        
        self._last_modified[i, j] = tick
        self._last_modified[j, i] = tick
        
        return True
    
    def get_edge_state(self, source_id: str, target_id: str) -> Optional[EdgeState]:
        """
        Get complete edge state.
        
        Returns None if edge doesn't exist or nodes invalid.
        """
        if source_id not in self._node_id_to_index or target_id not in self._node_id_to_index:
            return None
        
        i = self._node_id_to_index[source_id]
        j = self._node_id_to_index[target_id]
        
        weight = float(self._weights[i, j])
        
        if weight == 0.0:
            return None  # Edge doesn't exist
        
        return EdgeState(
            source_node_id=source_id,
            target_node_id=target_id,
            weight=weight,
            drift_velocity=float(self._velocities[i, j]),
            last_modified_tick=int(self._last_modified[i, j])
        )
    
    def get_all_edges(self, min_weight: float = 0.0) -> List[EdgeState]:
        """
        Get all edges with weight > min_weight (or >= min_weight if min_weight > 0).
        
        Returns only upper triangle to avoid duplicates (undirected graph).
        """
        edges = []
        n = len(self._nodes)
        
        for i in range(n):
            for j in range(i + 1, n):  # Only upper triangle
                weight = float(self._weights[i, j])
                # For min_weight=0.0, only include edges with weight > 0
                # For min_weight > 0, include edges with weight >= min_weight
                include_edge = False
                if min_weight == 0.0:
                    include_edge = weight > 0.0
                else:
                    include_edge = weight >= min_weight
                
                if include_edge:
                    source_id = self._index_to_node_id[i]
                    target_id = self._index_to_node_id[j]
                    
                    edges.append(EdgeState(
                        source_node_id=source_id,
                        target_node_id=target_id,
                        weight=weight,
                        drift_velocity=float(self._velocities[i, j]),
                        last_modified_tick=int(self._last_modified[i, j])
                    ))
        
        return edges
    
    def get_neighbors(self, node_id: str, min_weight: float = 0.0) -> List[Tuple[str, float]]:
        """
        Get all neighbors of a node with edge weight > min_weight (or >= min_weight if min_weight > 0).
        
        Returns:
            List of (neighbor_id, edge_weight) tuples
        """
        if node_id not in self._node_id_to_index:
            return []
        
        i = self._node_id_to_index[node_id]
        neighbors = []
        
        for j, weight in enumerate(self._weights[i]):
            # For min_weight=0.0, only include neighbors with weight > 0
            # For min_weight > 0, include neighbors with weight >= min_weight
            include_neighbor = False
            if min_weight == 0.0:
                include_neighbor = weight > 0.0 and i != j
            else:
                include_neighbor = weight >= min_weight and i != j
            
            if include_neighbor:
                neighbor_id = self._index_to_node_id[j]
                neighbors.append((neighbor_id, float(weight)))
        
        return neighbors
    
    def prune_edges(self, threshold: float, current_tick: int) -> int:
        """
        Remove edges with weight below threshold.
        
        Args:
            threshold: Minimum weight to keep edge
            current_tick: Current time step (for logging)
            
        Returns:
            Number of edges removed
        """
        n = len(self._nodes)
        removed_count = 0
        
        for i in range(n):
            for j in range(i + 1, n):  # Only check upper triangle
                if 0.0 < self._weights[i, j] < threshold:
                    self._weights[i, j] = 0.0
                    self._weights[j, i] = 0.0
                    self._velocities[i, j] = 0.0
                    self._velocities[j, i] = 0.0
                    removed_count += 1
        
        return removed_count
    
    def get_edge_count(self, min_weight: float = 0.0) -> int:
        """Count edges with weight > min_weight (or >= min_weight if min_weight > 0)."""
        count = 0
        n = len(self._nodes)
        
        for i in range(n):
            for j in range(i + 1, n):
                # For min_weight=0.0, only count edges with weight > 0
                # For min_weight > 0, count edges with weight >= min_weight
                if min_weight == 0.0:
                    if self._weights[i, j] > 0.0:
                        count += 1
                else:
                    if self._weights[i, j] >= min_weight:
                        count += 1
        
        return count
    
    def get_node_count(self) -> int:
        """Get total number of nodes."""
        return len(self._nodes)
    
    def get_adjacency_matrix(self) -> np.ndarray:
        """
        Get read-only view of adjacency matrix.
        
        Returns:
            N×N numpy array of edge weights
        """
        return self._weights.copy()
    
    def get_node_ids(self) -> List[str]:
        """Get list of all node IDs."""
        return list(self._nodes.keys())
