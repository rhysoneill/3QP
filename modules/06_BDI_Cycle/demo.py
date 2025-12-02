"""
Demo script for the BDI Cognitive Cycle module.

This script demonstrates the basic functionality of the BDI module
including belief revision, desire formation, and intention selection.
"""

import sys
from pathlib import Path

# Add module to path
module_path = Path(__file__).parent / "bdi_cycle"
sys.path.insert(0, str(module_path.parent))

from bdi_cycle import (
    BDIModule,
    BDIInput,
    BDIConfig,
    BeliefAssertion,
    DomainOntology,
    PredicateSchema,
    ControlSignal,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_state_summary(module: BDIModule):
    """Print a summary of the BDI module state."""
    summary = module.get_state_summary()
    
    print(f"Timestep: {summary['timestep']}")
    print(f"Beliefs: {summary['belief_count']}")
    print(f"Desires: {summary['desire_count']}")
    print(f"Intentions: {summary['intention_count']}")
    
    if summary['beliefs']:
        print("\nCurrent Beliefs:")
        for belief in summary['beliefs']:
            print(f"  - {belief['predicate']} "
                  f"(confidence: {belief['confidence']:.2f}, "
                  f"source: {belief['source']})")
    
    if summary['desires']:
        print("\nCurrent Desires:")
        for desire in summary['desires']:
            print(f"  - {desire['goal']} "
                  f"(priority: {desire['priority']:.2f}, "
                  f"utility: {desire['utility']:.2f})")
    
    if summary['intentions']:
        print("\nCurrent Intentions:")
        for intention in summary['intentions']:
            print(f"  - {intention['goal']} "
                  f"(commitment: {intention['commitment']:.2f})")


def demo_basic_cycle():
    """Demonstrate basic BDI cycle execution."""
    print_section("Basic BDI Cycle Demo")
    
    # Create domain ontology
    ontology = DomainOntology()
    
    # Register predicates for a space mission scenario
    ontology.register_predicate(PredicateSchema(
        name="resource_level",
        argument_types=[str, float],
        description="Current level of a resource",
        category="state"
    ))
    ontology.register_predicate(PredicateSchema(
        name="system_status",
        argument_types=[str, str],
        description="Status of a system",
        category="state"
    ))
    ontology.register_predicate(PredicateSchema(
        name="crew_condition",
        argument_types=[str, str],
        description="Condition of a crew member",
        category="state"
    ))
    
    # Create BDI module
    config = BDIConfig(
        confidence_decay_rate=0.0,
        minimum_confidence_threshold=0.2,
        max_belief_set_size=100
    )
    bdi = BDIModule(config=config, ontology=ontology)
    bdi.initialize()
    
    print("BDI Module initialized with space mission ontology")
    print(f"Configuration: max_belief_set_size={config.max_belief_set_size}, "
          f"min_confidence={config.minimum_confidence_threshold}")
    
    # Timestep 0: Initial perceptions
    print("\n--- Timestep 0: Initial Perceptions ---")
    input_t0 = BDIInput(
        timestep=0,
        new_beliefs=[
            BeliefAssertion("resource_level", ["oxygen", 0.95], 0.99, "perception"),
            BeliefAssertion("resource_level", ["water", 0.88], 0.95, "perception"),
            BeliefAssertion("resource_level", ["power", 0.75], 0.90, "perception"),
            BeliefAssertion("system_status", ["life_support", "nominal"], 0.98, "perception"),
            BeliefAssertion("crew_condition", ["pilot", "healthy"], 0.92, "perception"),
        ]
    )
    
    output_t0 = bdi.execute_cycle(input_t0)
    print(f"Status: {output_t0.status.code}")
    print(f"Statistics: {output_t0.cycle_statistics.beliefs_added} beliefs added, "
          f"cycle time: {output_t0.cycle_statistics.cycle_duration_ms:.2f}ms")
    print_state_summary(bdi)
    
    # Timestep 1: Update some beliefs
    print("\n--- Timestep 1: Resource Depletion ---")
    input_t1 = BDIInput(
        timestep=1,
        new_beliefs=[
            BeliefAssertion("resource_level", ["oxygen", 0.82], 0.98, "perception"),
            BeliefAssertion("resource_level", ["power", 0.65], 0.95, "perception"),
            BeliefAssertion("system_status", ["power_system", "degraded"], 0.85, "perception"),
        ]
    )
    
    output_t1 = bdi.execute_cycle(input_t1)
    print(f"Status: {output_t1.status.code}")
    print(f"Statistics: {output_t1.cycle_statistics.beliefs_added} added, "
          f"{output_t1.cycle_statistics.beliefs_updated} updated")
    print_state_summary(bdi)
    
    # Timestep 2: Critical situation
    print("\n--- Timestep 2: Critical Alert ---")
    input_t2 = BDIInput(
        timestep=2,
        new_beliefs=[
            BeliefAssertion("resource_level", ["oxygen", 0.55], 0.99, "perception"),
            BeliefAssertion("system_status", ["life_support", "critical"], 0.95, "perception"),
            BeliefAssertion("crew_condition", ["pilot", "stressed"], 0.88, "perception"),
        ]
    )
    
    output_t2 = bdi.execute_cycle(input_t2)
    print(f"Status: {output_t2.status.code}")
    print(f"Statistics: {output_t2.cycle_statistics.beliefs_updated} updated")
    print_state_summary(bdi)


def demo_belief_confidence():
    """Demonstrate belief confidence handling."""
    print_section("Belief Confidence Demo")
    
    ontology = DomainOntology()
    ontology.register_predicate(PredicateSchema(
        name="sensor_reading",
        argument_types=[str, float],
        description="Sensor reading",
        category="state"
    ))
    
    config = BDIConfig(minimum_confidence_threshold=0.5)
    bdi = BDIModule(config=config, ontology=ontology)
    bdi.initialize()
    
    print("Testing belief confidence handling")
    print(f"Minimum confidence threshold: {config.minimum_confidence_threshold}")
    
    # Add beliefs with different confidence levels
    input_t0 = BDIInput(
        timestep=0,
        new_beliefs=[
            BeliefAssertion("sensor_reading", ["temperature", 22.5], 0.95, "perception"),
            BeliefAssertion("sensor_reading", ["pressure", 101.3], 0.75, "perception"),
            BeliefAssertion("sensor_reading", ["humidity", 45.0], 0.40, "perception"),  # Below threshold
            BeliefAssertion("sensor_reading", ["radiation", 0.02], 0.20, "perception"),  # Below threshold
        ]
    )
    
    output = bdi.execute_cycle(input_t0)
    
    print(f"\nInput: 4 beliefs with varying confidence")
    print(f"Output: {len(output.beliefs)} beliefs retained")
    print(f"Low-confidence beliefs were pruned (< {config.minimum_confidence_threshold})")
    print_state_summary(bdi)


def demo_configuration_update():
    """Demonstrate runtime configuration updates."""
    print_section("Runtime Configuration Update Demo")
    
    ontology = DomainOntology()
    ontology.register_predicate(PredicateSchema(
        name="test_belief",
        argument_types=[int],
        description="Test belief",
        category="state"
    ))
    
    bdi = BDIModule(ontology=ontology)
    bdi.initialize()
    
    print("Initial configuration:")
    print(f"  max_belief_set_size: {bdi.config.max_belief_set_size}")
    
    # Update configuration
    from bdi_cycle.types import ConfigurationUpdate
    
    input_with_config = BDIInput(
        timestep=0,
        new_beliefs=[],
        configuration_update=ConfigurationUpdate(
            parameter_name="max_belief_set_size",
            parameter_value=50
        )
    )
    
    output = bdi.execute_cycle(input_with_config)
    
    print(f"\nConfiguration updated via BDI input")
    print(f"  max_belief_set_size: {bdi.config.max_belief_set_size}")
    print(f"Status: {output.status.code}")


def demo_control_signals():
    """Demonstrate control signal handling."""
    print_section("Control Signals Demo")
    
    ontology = DomainOntology()
    ontology.register_predicate(PredicateSchema(
        name="state",
        argument_types=[str],
        description="State",
        category="state"
    ))
    
    bdi = BDIModule(ontology=ontology)
    bdi.initialize()
    
    # Normal execution
    print("Timestep 0: Normal execution (RUN)")
    input_t0 = BDIInput(
        timestep=0,
        new_beliefs=[BeliefAssertion("state", ["active"], 1.0, "perception")],
        control_signal=ControlSignal.RUN
    )
    output_t0 = bdi.execute_cycle(input_t0)
    print(f"  Status: {output_t0.status.code}, Beliefs: {len(output_t0.beliefs)}")
    
    # Pause
    print("\nTimestep 1: Paused (PAUSE)")
    input_t1 = BDIInput(
        timestep=1,
        new_beliefs=[BeliefAssertion("state", ["paused"], 1.0, "perception")],
        control_signal=ControlSignal.PAUSE
    )
    output_t1 = bdi.execute_cycle(input_t1)
    print(f"  Status: {output_t1.status.code}, Beliefs: {len(output_t1.beliefs)} (unchanged)")
    
    # Reset
    print("\nTimestep 1 (retry): Reset (RESET)")
    input_reset = BDIInput(
        timestep=1,
        new_beliefs=[],
        control_signal=ControlSignal.RESET
    )
    output_reset = bdi.execute_cycle(input_reset)
    print(f"  Status: {output_reset.status.code}, Beliefs: {len(output_reset.beliefs)} (cleared)")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("  BDI COGNITIVE CYCLE MODULE - DEMONSTRATION")
    print("="*60)
    
    try:
        demo_basic_cycle()
        demo_belief_confidence()
        demo_configuration_update()
        demo_control_signals()
        
        print_section("Demo Complete")
        print("All demonstrations completed successfully!")
        print("\nThe BDI module provides:")
        print("  ✓ Symbolic belief representation")
        print("  ✓ Deterministic belief revision")
        print("  ✓ Configurable confidence thresholds")
        print("  ✓ Runtime configuration updates")
        print("  ✓ Control signal handling (run/pause/reset)")
        print("  ✓ Extensible domain ontologies")
        print("\nReady for integration with 3QP system!\n")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
