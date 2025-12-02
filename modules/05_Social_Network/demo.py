"""
Demo script for the Social Network module.

Demonstrates tie dynamics, clique formation, and metric computation.
"""

import logging
from social_network import (
    InteractionSignal,
    NodeDefinition,
    EdgeDefinition,
    NetworkConfiguration,
    SocialNetworkModule,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_basic_network():
    """Demonstrate basic network operations."""
    print_section("Basic Network Operations")
    
    # Create a small crew
    nodes = [
        NodeDefinition("Alice", {"role": "Commander"}),
        NodeDefinition("Bob", {"role": "Engineer"}),
        NodeDefinition("Charlie", {"role": "Scientist"}),
        NodeDefinition("Diana", {"role": "Medic"}),
    ]
    
    # Initial relationships
    edges = [
        EdgeDefinition("Alice", "Bob", 0.6),
        EdgeDefinition("Alice", "Charlie", 0.4),
        EdgeDefinition("Bob", "Charlie", 0.5),
        EdgeDefinition("Diana", "Alice", 0.3),
    ]
    
    # Create module
    module = SocialNetworkModule(nodes, edges)
    
    # Initial state
    print("\nInitial Network State:")
    summary = module.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    return module


def demo_tie_strengthening(module: SocialNetworkModule):
    """Demonstrate tie strengthening through positive interactions."""
    print_section("Tie Strengthening")
    
    # Strong positive interactions between Alice and Bob
    signals = [
        InteractionSignal("Alice", "Bob", intensity=0.9, duration=2, timestamp=1),
        InteractionSignal("Bob", "Alice", intensity=0.9, duration=2, timestamp=1),
    ]
    
    print("\nApplying positive interactions between Alice and Bob...")
    
    initial_weight = module.query_edge_weight("Alice", "Bob")
    print(f"Initial Alice-Bob tie strength: {initial_weight:.3f}")
    
    # Run update
    module.update(signals, step_number=1)
    
    new_weight = module.query_edge_weight("Alice", "Bob")
    print(f"After interaction tie strength: {new_weight:.3f}")
    print(f"Change: +{new_weight - initial_weight:.3f}")


def demo_tie_weakening(module: SocialNetworkModule):
    """Demonstrate tie weakening through lack of interaction."""
    print_section("Tie Weakening")
    
    initial_weight = module.query_edge_weight("Diana", "Alice")
    print(f"\nInitial Diana-Alice tie strength: {initial_weight:.3f}")
    
    print("\nSimulating 5 time steps with no interaction...")
    
    # No interactions involving Diana
    for step in range(2, 7):
        signals = [
            InteractionSignal("Alice", "Bob", intensity=0.7, duration=1, timestamp=step),
            InteractionSignal("Bob", "Charlie", intensity=0.6, duration=1, timestamp=step),
        ]
        module.update(signals, step_number=step)
    
    final_weight = module.query_edge_weight("Diana", "Alice")
    print(f"After 5 steps tie strength: {final_weight:.3f}")
    print(f"Change: {final_weight - initial_weight:.3f}")


def demo_clique_formation(module: SocialNetworkModule):
    """Demonstrate clique detection."""
    print_section("Clique Formation")
    
    # Strengthen triangle: Alice-Bob-Charlie
    print("\nStrengthening Alice-Bob-Charlie triangle...")
    
    for step in range(7, 12):
        signals = [
            InteractionSignal("Alice", "Bob", intensity=0.9, duration=1, timestamp=step),
            InteractionSignal("Bob", "Charlie", intensity=0.9, duration=1, timestamp=step),
            InteractionSignal("Alice", "Charlie", intensity=0.8, duration=1, timestamp=step),
        ]
        module.update(signals, step_number=step)
    
    # Check clique detection
    clique_snapshot = module.get_clique_snapshot()
    
    print(f"\nDetected {len(clique_snapshot.cliques)} clique(s):")
    for clique in clique_snapshot.cliques:
        members = ", ".join(sorted(clique.member_node_ids))
        print(f"  Clique {clique.clique_id}: [{members}]")
        print(f"    Stability: {clique.stability_index:.3f}")
        print(f"    Formed at step: {clique.formation_tick}")
    
    # Check membership
    print("\nClique membership:")
    for node_id in ["Alice", "Bob", "Charlie", "Diana"]:
        cliques = module.query_clique_membership(node_id)
        print(f"  {node_id}: {len(cliques)} clique(s)")


def demo_structural_metrics(module: SocialNetworkModule):
    """Demonstrate structural metric computation."""
    print_section("Structural Metrics")
    
    metrics = module.get_structural_metrics()
    
    print("\nGlobal Metrics:")
    print(f"  Cohesion: {metrics.global_cohesion:.3f}")
    print(f"  Density: {metrics.normalized_density:.3f}")
    print(f"  Fragmentation: {metrics.fragmentation_index:.3f}")
    print(f"  Clustering Coefficient: {metrics.global_clustering_coefficient:.3f}")
    print(f"  Clique Coverage: {metrics.clique_coverage:.3f}")
    print(f"  Component Count: {metrics.component_count}")
    
    print("\nNode Centrality:")
    for node_id in ["Alice", "Bob", "Charlie", "Diana"]:
        centrality = module.query_node_centrality(node_id)
        if centrality:
            print(f"  {node_id}:")
            print(f"    Degree: {centrality['degree_centrality']:.3f}")
            print(f"    Betweenness: {centrality['betweenness_centrality']:.3f}")


def demo_network_evolution():
    """Demonstrate network evolution over time."""
    print_section("Network Evolution Over Time")
    
    # Create crew
    nodes = [
        NodeDefinition(f"Crew{i}") for i in range(1, 6)
    ]
    
    # Start with sparse connections
    edges = [
        EdgeDefinition("Crew1", "Crew2", 0.3),
        EdgeDefinition("Crew3", "Crew4", 0.3),
    ]
    
    module = SocialNetworkModule(nodes, edges)
    
    print("\nSimulating 20 time steps with varied interactions...")
    
    # Track metrics over time
    cohesion_history = []
    clique_count_history = []
    
    for step in range(1, 21):
        # Generate random-ish interaction pattern
        signals = []
        
        # Early phase: distributed interactions
        if step < 10:
            signals = [
                InteractionSignal("Crew1", "Crew2", intensity=0.7, duration=1, timestamp=step),
                InteractionSignal("Crew3", "Crew4", intensity=0.7, duration=1, timestamp=step),
                InteractionSignal("Crew2", "Crew3", intensity=0.5, duration=1, timestamp=step),
            ]
        # Later phase: clustered interactions
        else:
            signals = [
                InteractionSignal("Crew1", "Crew2", intensity=0.9, duration=1, timestamp=step),
                InteractionSignal("Crew2", "Crew3", intensity=0.9, duration=1, timestamp=step),
                InteractionSignal("Crew1", "Crew3", intensity=0.8, duration=1, timestamp=step),
            ]
        
        module.update(signals, step_number=step)
        
        # Record metrics
        metrics = module.get_structural_metrics()
        cliques = module.get_clique_snapshot()
        
        cohesion_history.append(metrics.global_cohesion)
        clique_count_history.append(len(cliques.cliques))
    
    # Print evolution summary
    print("\nEvolution Summary:")
    print(f"  Steps 1-5 avg cohesion: {sum(cohesion_history[:5])/5:.3f}")
    print(f"  Steps 16-20 avg cohesion: {sum(cohesion_history[15:20])/5:.3f}")
    print(f"  Final clique count: {clique_count_history[-1]}")
    
    # Final state
    print("\nFinal Network State:")
    summary = module.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("  Social Network Module - Demonstration")
    print("=" * 60)
    
    # Basic network operations
    module = demo_basic_network()
    
    # Tie dynamics
    demo_tie_strengthening(module)
    demo_tie_weakening(module)
    
    # Clique formation
    demo_clique_formation(module)
    
    # Structural metrics
    demo_structural_metrics(module)
    
    # Network evolution
    demo_network_evolution()
    
    print_section("Demo Complete")
    print("\nThe Social Network module successfully demonstrated:")
    print("  ✓ Graph representation and storage")
    print("  ✓ Tie strengthening and weakening dynamics")
    print("  ✓ Passive decay mechanics")
    print("  ✓ Clique detection and tracking")
    print("  ✓ Structural metric computation")
    print("  ✓ Network evolution over time")
    print()


if __name__ == '__main__':
    main()
