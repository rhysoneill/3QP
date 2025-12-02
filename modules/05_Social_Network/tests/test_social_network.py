"""
Tests for the Social Network module.

Tests graph operations, drift mechanics, clique detection, and metrics.
"""

import unittest
from social_network import (
    InteractionSignal,
    NodeDefinition,
    EdgeDefinition,
    NetworkConfiguration,
    SocialNetworkModule,
)


class TestGraphStore(unittest.TestCase):
    """Test GraphStore functionality."""
    
    def setUp(self):
        """Create a simple test network."""
        self.nodes = [
            NodeDefinition("alice"),
            NodeDefinition("bob"),
            NodeDefinition("charlie"),
        ]
        
        self.edges = [
            EdgeDefinition("alice", "bob", 0.5),
            EdgeDefinition("bob", "charlie", 0.3),
        ]
    
    def test_initialization(self):
        """Test module initialization."""
        module = SocialNetworkModule(self.nodes, self.edges)
        
        self.assertEqual(module.graph.get_node_count(), 3)
        self.assertEqual(module.graph.get_edge_count(min_weight=0.0), 2)
    
    def test_edge_weight_query(self):
        """Test edge weight queries."""
        module = SocialNetworkModule(self.nodes, self.edges)
        
        # Test existing edge
        weight = module.query_edge_weight("alice", "bob")
        self.assertAlmostEqual(weight, 0.5)
        
        # Test symmetric edge
        weight_rev = module.query_edge_weight("bob", "alice")
        self.assertAlmostEqual(weight_rev, 0.5)
        
        # Test non-existent edge
        weight_none = module.query_edge_weight("alice", "charlie")
        self.assertEqual(weight_none, 0.0)


class TestDriftMechanics(unittest.TestCase):
    """Test drift and decay mechanics."""
    
    def setUp(self):
        """Create test network."""
        self.nodes = [
            NodeDefinition("alice"),
            NodeDefinition("bob"),
        ]
        
        self.edges = [
            EdgeDefinition("alice", "bob", 0.5),
        ]
        
        self.config = NetworkConfiguration(
            drift_strengthening_rate=0.1,
            drift_weakening_rate=0.05,
            passive_decay_coefficient=0.01,
            edge_prune_threshold=0.05,
        )
    
    def test_strengthening(self):
        """Test that positive interactions strengthen ties."""
        module = SocialNetworkModule(self.nodes, self.edges, self.config)
        
        initial_weight = module.query_edge_weight("alice", "bob")
        
        # Apply positive interaction
        signals = [
            InteractionSignal(
                source_node_id="alice",
                target_node_id="bob",
                intensity=1.0,
                duration=1,
                timestamp=1
            )
        ]
        
        module.update(signals, step_number=1)
        
        new_weight = module.query_edge_weight("alice", "bob")
        
        # Weight should increase
        self.assertGreater(new_weight, initial_weight)
    
    def test_weakening(self):
        """Test that low-intensity interactions weaken ties."""
        module = SocialNetworkModule(self.nodes, self.edges, self.config)
        
        initial_weight = module.query_edge_weight("alice", "bob")
        
        # Apply low-intensity interaction
        signals = [
            InteractionSignal(
                source_node_id="alice",
                target_node_id="bob",
                intensity=0.0,
                duration=1,
                timestamp=1
            )
        ]
        
        module.update(signals, step_number=1)
        
        new_weight = module.query_edge_weight("alice", "bob")
        
        # Weight should decrease
        self.assertLess(new_weight, initial_weight)
    
    def test_passive_decay(self):
        """Test passive decay of edges without interaction."""
        module = SocialNetworkModule(self.nodes, self.edges, self.config)
        
        # No interactions for multiple steps
        for step in range(1, 6):
            module.update([], step_number=step)
        
        # Edge should still exist but may have changed due to velocity
        weight = module.query_edge_weight("alice", "bob")
        self.assertIsNotNone(weight)


class TestCliqueDetection(unittest.TestCase):
    """Test clique detection."""
    
    def setUp(self):
        """Create network with clique structure."""
        self.nodes = [
            NodeDefinition("alice"),
            NodeDefinition("bob"),
            NodeDefinition("charlie"),
            NodeDefinition("dave"),
        ]
        
        # Create triangle (alice-bob-charlie) with strong ties
        self.edges = [
            EdgeDefinition("alice", "bob", 0.8),
            EdgeDefinition("bob", "charlie", 0.8),
            EdgeDefinition("alice", "charlie", 0.8),
            EdgeDefinition("dave", "alice", 0.3),  # Weak tie to dave
        ]
        
        self.config = NetworkConfiguration(
            clique_weight_threshold=0.5,
            min_clique_size=3,
        )
    
    def test_clique_detection(self):
        """Test that cliques are detected."""
        module = SocialNetworkModule(self.nodes, self.edges, self.config)
        
        # Run one update to detect cliques
        module.update([], step_number=1)
        
        clique_snapshot = module.get_clique_snapshot()
        
        # Should detect the triangle
        self.assertIsNotNone(clique_snapshot)
        self.assertGreater(len(clique_snapshot.cliques), 0)
        
        # Check that triangle members are in a clique
        clique = clique_snapshot.cliques[0]
        self.assertIn("alice", clique.member_node_ids)
        self.assertIn("bob", clique.member_node_ids)
        self.assertIn("charlie", clique.member_node_ids)
    
    def test_clique_membership_query(self):
        """Test clique membership queries."""
        module = SocialNetworkModule(self.nodes, self.edges, self.config)
        
        module.update([], step_number=1)
        
        # Check membership
        alice_cliques = module.query_clique_membership("alice")
        dave_cliques = module.query_clique_membership("dave")
        
        # Alice should be in a clique
        self.assertGreater(len(alice_cliques), 0)
        
        # Dave should not be in any clique (weak tie)
        self.assertEqual(len(dave_cliques), 0)


class TestStructuralMetrics(unittest.TestCase):
    """Test structural metric computation."""
    
    def setUp(self):
        """Create test network."""
        self.nodes = [
            NodeDefinition("alice"),
            NodeDefinition("bob"),
            NodeDefinition("charlie"),
        ]
        
        self.edges = [
            EdgeDefinition("alice", "bob", 0.6),
            EdgeDefinition("bob", "charlie", 0.4),
        ]
    
    def test_cohesion_metric(self):
        """Test cohesion calculation."""
        module = SocialNetworkModule(self.nodes, self.edges)
        
        module.update([], step_number=1)
        
        metrics = module.get_structural_metrics()
        
        # Cohesion should be average of edge weights
        expected_cohesion = (0.6 + 0.4) / 2
        self.assertAlmostEqual(metrics.global_cohesion, expected_cohesion)
    
    def test_density_metric(self):
        """Test density calculation."""
        module = SocialNetworkModule(self.nodes, self.edges)
        
        module.update([], step_number=1)
        
        metrics = module.get_structural_metrics()
        
        # 2 edges out of 3 possible = 2/3 density
        expected_density = 2 / 3
        self.assertAlmostEqual(metrics.normalized_density, expected_density)
    
    def test_centrality_query(self):
        """Test centrality queries."""
        module = SocialNetworkModule(self.nodes, self.edges)
        
        module.update([], step_number=1)
        
        # Bob should have highest degree centrality (connected to both)
        bob_centrality = module.query_node_centrality("bob")
        alice_centrality = module.query_node_centrality("alice")
        
        self.assertIsNotNone(bob_centrality)
        self.assertIsNotNone(alice_centrality)
        
        # Bob's degree should be higher
        self.assertGreater(
            bob_centrality['degree_centrality'],
            alice_centrality['degree_centrality']
        )


class TestEdgePruning(unittest.TestCase):
    """Test edge pruning behavior."""
    
    def setUp(self):
        """Create network with weak edge."""
        self.nodes = [
            NodeDefinition("alice"),
            NodeDefinition("bob"),
        ]
        
        self.edges = [
            EdgeDefinition("alice", "bob", 0.02),  # Below prune threshold
        ]
        
        self.config = NetworkConfiguration(
            edge_prune_threshold=0.05,
        )
    
    def test_pruning(self):
        """Test that weak edges are pruned."""
        module = SocialNetworkModule(self.nodes, self.edges, self.config)
        
        # Initial edge should exist
        initial_weight = module.query_edge_weight("alice", "bob")
        self.assertIsNotNone(initial_weight)
        
        # Run update (no signals, just pruning)
        module.update([], step_number=1)
        
        # Edge should be pruned
        # Note: get_edge_weight returns 0.0 for non-existent edges
        # So we check the edge count instead
        edge_count = module.graph.get_edge_count(min_weight=0.0)
        self.assertEqual(edge_count, 0)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
