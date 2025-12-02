"""
Structural metrics calculator for the Social Network module.

Computes cohesion, fragmentation, clustering, and centrality metrics.
"""

from typing import Dict, List, Set, Tuple
import numpy as np
from collections import deque
import logging
from .types import StructuralMetrics, CentralityScores, CliqueDescriptor
from .graph_store import GraphStore


logger = logging.getLogger(__name__)


class MetricCalculator:
    """
    Computes structural metrics from graph state.
    
    Implements cohesion, density, fragmentation, clustering, and centrality.
    """
    
    def __init__(self):
        """Initialize metric calculator."""
        pass
    
    def compute_metrics(
        self,
        graph: GraphStore,
        cliques: List[CliqueDescriptor],
        current_tick: int
    ) -> StructuralMetrics:
        """
        Compute all structural metrics.
        
        Args:
            graph: Graph store to analyze
            cliques: List of detected cliques
            current_tick: Current time step
            
        Returns:
            Complete structural metrics
        """
        # Compute global metrics
        cohesion = self._compute_cohesion(graph)
        density = self._compute_density(graph)
        fragmentation, component_count = self._compute_fragmentation(graph)
        clustering = self._compute_clustering_coefficient(graph)
        clique_coverage = self._compute_clique_coverage(graph, cliques)
        
        # Compute node-level centrality
        node_centralities = self._compute_all_centralities(graph)
        
        return StructuralMetrics(
            step_number=current_tick,
            global_cohesion=cohesion,
            normalized_density=density,
            fragmentation_index=fragmentation,
            global_clustering_coefficient=clustering,
            component_count=component_count,
            clique_coverage=clique_coverage,
            node_centralities=node_centralities
        )
    
    def _compute_cohesion(self, graph: GraphStore) -> float:
        """
        Compute global cohesion: average edge weight.
        
        cohesion(G) = (Σ W(e)) / |E|
        """
        edges = graph.get_all_edges(min_weight=0.0)
        
        if not edges:
            return 0.0
        
        total_weight = sum(edge.weight for edge in edges)
        return total_weight / len(edges)
    
    def _compute_density(self, graph: GraphStore) -> float:
        """
        Compute normalized density: proportion of possible edges present.
        
        density(G) = (2 · |E|) / (|V| · (|V| - 1))
        
        Only counts edges with non-zero weight.
        """
        n = graph.get_node_count()
        
        if n <= 1:
            return 0.0
        
        max_edges = n * (n - 1) / 2
        actual_edges = graph.get_edge_count(min_weight=0.0)
        
        return actual_edges / max_edges
    
    def _compute_fragmentation(self, graph: GraphStore) -> Tuple[float, int]:
        """
        Compute fragmentation index and component count.
        
        Uses BFS to find connected components.
        
        fragmentation = 1 - (size_of_largest_component / |V|)
        
        Returns:
            Tuple of (fragmentation_index, component_count)
        """
        node_ids = graph.get_node_ids()
        
        if not node_ids:
            return 0.0, 0
        
        # Find connected components using BFS
        visited = set()
        components = []
        
        for node_id in node_ids:
            if node_id in visited:
                continue
            
            # BFS from this node
            component = self._bfs_component(graph, node_id)
            components.append(component)
            visited.update(component)
        
        component_count = len(components)
        largest_component_size = max(len(c) for c in components)
        
        fragmentation = 1.0 - (largest_component_size / len(node_ids))
        
        return fragmentation, component_count
    
    def _bfs_component(self, graph: GraphStore, start_node: str) -> Set[str]:
        """
        Find connected component containing start_node using BFS.
        
        Considers edges with weight > 0 as connections.
        """
        component = set()
        queue = deque([start_node])
        visited = {start_node}
        
        while queue:
            node = queue.popleft()
            component.add(node)
            
            # Get neighbors with non-zero edge weight
            neighbors = graph.get_neighbors(node, min_weight=0.0)
            
            for neighbor_id, weight in neighbors:
                if weight > 0.0 and neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append(neighbor_id)
        
        return component
    
    def _compute_clustering_coefficient(self, graph: GraphStore) -> float:
        """
        Compute global clustering coefficient.
        
        For each node v:
        C(v) = (edges among neighbors) / (possible edges among neighbors)
        
        Global C(G) = average C(v)
        """
        node_ids = graph.get_node_ids()
        
        if not node_ids:
            return 0.0
        
        clustering_values = []
        
        for node_id in node_ids:
            c_v = self._compute_node_clustering(graph, node_id)
            clustering_values.append(c_v)
        
        return sum(clustering_values) / len(clustering_values)
    
    def _compute_node_clustering(self, graph: GraphStore, node_id: str) -> float:
        """
        Compute clustering coefficient for a single node.
        """
        neighbors = graph.get_neighbors(node_id, min_weight=0.0)
        neighbor_ids = [n_id for n_id, _ in neighbors]
        
        k = len(neighbor_ids)
        
        if k < 2:
            return 0.0  # Need at least 2 neighbors to form triangle
        
        # Count edges among neighbors
        edges_among_neighbors = 0
        
        for i in range(len(neighbor_ids)):
            for j in range(i + 1, len(neighbor_ids)):
                weight = graph.get_edge_weight(neighbor_ids[i], neighbor_ids[j])
                if weight and weight > 0.0:
                    edges_among_neighbors += 1
        
        # Maximum possible edges among k neighbors
        max_edges = k * (k - 1) / 2
        
        return edges_among_neighbors / max_edges
    
    def _compute_clique_coverage(
        self,
        graph: GraphStore,
        cliques: List[CliqueDescriptor]
    ) -> float:
        """
        Compute clique coverage: proportion of nodes in at least one clique.
        
        clique_coverage = (nodes in cliques) / |V|
        """
        node_ids = graph.get_node_ids()
        
        if not node_ids:
            return 0.0
        
        nodes_in_cliques = set()
        for clique in cliques:
            nodes_in_cliques.update(clique.member_node_ids)
        
        return len(nodes_in_cliques) / len(node_ids)
    
    def _compute_all_centralities(
        self,
        graph: GraphStore
    ) -> Dict[str, CentralityScores]:
        """
        Compute centrality scores for all nodes.
        
        Returns:
            Dictionary mapping node_id -> CentralityScores
        """
        node_ids = graph.get_node_ids()
        centralities = {}
        
        for node_id in node_ids:
            degree = self._compute_degree_centrality(graph, node_id)
            betweenness = self._compute_betweenness_centrality(graph, node_id)
            
            centralities[node_id] = CentralityScores(
                degree_centrality=degree,
                betweenness_centrality=betweenness
            )
        
        return centralities
    
    def _compute_degree_centrality(self, graph: GraphStore, node_id: str) -> float:
        """
        Compute degree centrality: sum of incident edge weights.
        
        degree(v) = Σ W(edge(v, u)) for all neighbors u
        """
        neighbors = graph.get_neighbors(node_id, min_weight=0.0)
        return sum(weight for _, weight in neighbors)
    
    def _compute_betweenness_centrality(
        self,
        graph: GraphStore,
        node_id: str
    ) -> float:
        """
        Compute betweenness centrality: fraction of shortest paths through node.
        
        Note: Full betweenness is O(N³). This is a simplified approximation
        for small graphs.
        
        Returns approximate betweenness normalized to [0, 1].
        """
        # For small crews, we can compute exact betweenness
        # For larger graphs, this should be replaced with approximation
        
        node_ids = graph.get_node_ids()
        n = len(node_ids)
        
        if n <= 2:
            return 0.0
        
        # Count shortest paths passing through node_id
        paths_through_node = 0
        total_paths = 0
        
        for source in node_ids:
            if source == node_id:
                continue
            
            # Run BFS from source to find shortest paths
            distances, predecessors = self._bfs_shortest_paths(graph, source)
            
            for target in node_ids:
                if target == node_id or target == source:
                    continue
                
                if target not in distances:
                    continue  # No path
                
                # Check if shortest path passes through node_id
                if self._path_passes_through(
                    source, target, node_id, predecessors
                ):
                    paths_through_node += 1
                
                total_paths += 1
        
        if total_paths == 0:
            return 0.0
        
        # Normalize
        return paths_through_node / total_paths
    
    def _bfs_shortest_paths(
        self,
        graph: GraphStore,
        source: str
    ) -> Tuple[Dict[str, int], Dict[str, List[str]]]:
        """
        Find shortest paths from source using BFS.
        
        Returns:
            Tuple of (distances, predecessors)
            - distances: node_id -> distance from source
            - predecessors: node_id -> list of predecessor nodes
        """
        distances = {source: 0}
        predecessors = {source: []}
        queue = deque([source])
        
        while queue:
            current = queue.popleft()
            current_dist = distances[current]
            
            neighbors = graph.get_neighbors(current, min_weight=0.0)
            
            for neighbor_id, weight in neighbors:
                if weight <= 0.0:
                    continue
                
                if neighbor_id not in distances:
                    distances[neighbor_id] = current_dist + 1
                    predecessors[neighbor_id] = [current]
                    queue.append(neighbor_id)
                elif distances[neighbor_id] == current_dist + 1:
                    # Another shortest path found
                    predecessors[neighbor_id].append(current)
        
        return distances, predecessors
    
    def _path_passes_through(
        self,
        source: str,
        target: str,
        intermediate: str,
        predecessors: Dict[str, List[str]]
    ) -> bool:
        """
        Check if any shortest path from source to target passes through intermediate.
        
        Uses backtracking through predecessor graph.
        """
        if target not in predecessors:
            return False
        
        # Backtrack from target to source
        visited = set()
        queue = deque([target])
        
        while queue:
            current = queue.popleft()
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current == intermediate:
                return True
            
            if current == source:
                continue
            
            # Add predecessors to queue
            for pred in predecessors.get(current, []):
                if pred not in visited:
                    queue.append(pred)
        
        return False
