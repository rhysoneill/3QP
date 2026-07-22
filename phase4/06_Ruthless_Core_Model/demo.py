"""
Demo: Ruthless Core Model

This script demonstrates how to:
1. Configure and run the Ruthless Core Model
2. Visualize the generated trajectories
3. Convert outputs to Phase 4 compatible formats
4. Integrate with Phase 4 trajectory analysis

Run this script to verify the model is working correctly.
"""

import sys
from pathlib import Path

# Add ruthless core to path
ruthless_core_path = Path(__file__).parent
if str(ruthless_core_path) not in sys.path:
    sys.path.insert(0, str(ruthless_core_path))

from ruthless_core import (
    RuthlessCoreConfig,
    RuthlessCoreModel,
    to_phase4_encoded_states,
    to_phase4_trajectory_result,
)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_basic_run():
    """Run basic simulation and display results."""
    print_section("1. Basic Ruthless Core Model Simulation")
    
    # Create configuration
    config = RuthlessCoreConfig(
        mission_length_days=200,
        q_peak=0.55,
        q_width=0.12,
        c_strain=0.011,
        c_q=0.020,
    )
    
    print(f"Mission length: {config.mission_length_days} days")
    print(f"TQ center: {config.q_center * 100:.1f}% of mission")
    print(f"TQ peak amplitude: {config.q_peak:.2f}")
    
    # Run simulation
    model = RuthlessCoreModel(config)
    output = model.run()
    
    print(f"\nSimulation complete. Generated {len(output)} time steps.")
    
    # Show summary statistics
    print("\n--- State Variable Summary ---")
    print(f"Monotony:    min={min(output.monotony):.3f}, max={max(output.monotony):.3f}")
    print(f"Strain:      min={min(output.strain):.3f}, max={max(output.strain):.3f}")
    print(f"Cohesion:    min={min(output.cohesion):.3f}, max={max(output.cohesion):.3f}")
    print(f"TQ Pressure: min={min(output.tq_pressure):.3f}, max={max(output.tq_pressure):.3f}")
    
    # Find third quarter characteristics
    min_cohesion_idx = output.cohesion.index(min(output.cohesion))
    min_cohesion_day = output.days[min_cohesion_idx]
    min_cohesion_progress = min_cohesion_day / len(output)
    
    print(f"\n--- Third Quarter Analysis ---")
    print(f"Minimum cohesion: {output.cohesion[min_cohesion_idx]:.3f}")
    print(f"Occurred on day: {min_cohesion_day} ({min_cohesion_progress:.1%} progress)")
    print(f"Is in third quarter range? {'YES' if 0.55 <= min_cohesion_progress <= 0.85 else 'NO'}")
    
    return output


def demo_phase4_integration(output):
    """Demonstrate Phase 4 integration."""
    print_section("2. Phase 4 Integration")
    
    # Convert to encoded states
    encoded_states = to_phase4_encoded_states(output)
    print(f"Generated {len(encoded_states)} encoded states")
    print("\nSample encoded state (day 100):")
    sample_state = encoded_states[100]
    print(f"  Day: {sample_state['day']}")
    print(f"  Mission progress: {sample_state['mission_progress']:.1%}")
    print(f"  Strain (physiological): {sample_state['domains']['physiological']['strain_level']:.3f}")
    print(f"  Cohesion (social): {sample_state['domains']['social']['cohesion']:.3f}")
    print(f"  Monotony (environmental): {sample_state['domains']['environmental']['monotony']:.3f}")
    
    # Convert to trajectory result
    trajectory_result = to_phase4_trajectory_result(output)
    print("\n--- Trajectory Classification ---")
    print(f"Archetype: {trajectory_result['archetype_id']}")
    print(f"Label: {trajectory_result['label']}")
    print(f"Support: {trajectory_result['support_strength']}")
    print(f"Evidence items: {len(trajectory_result['evidence'])}")
    if trajectory_result['evidence']:
        print(f"\nFirst evidence item:")
        print(f"  Type: {trajectory_result['evidence'][0]['item_type']}")
        print(f"  Description: {trajectory_result['evidence'][0]['description']}")


def demo_parameter_exploration():
    """Demonstrate parameter exploration."""
    print_section("3. Parameter Exploration")
    
    print("Running three scenarios with different TQ centers:\n")
    
    centers = [0.60, 0.70, 0.80]
    for center in centers:
        config = RuthlessCoreConfig(
            mission_length_days=200,
            q_center=center,
            q_peak=0.5,
        )
        model = RuthlessCoreModel(config)
        output = model.run()
        
        min_cohesion_idx = output.cohesion.index(min(output.cohesion))
        min_cohesion_day = output.days[min_cohesion_idx]
        min_cohesion_value = output.cohesion[min_cohesion_idx]
        
        print(f"TQ Center = {center:.1%}:")
        print(f"  Min cohesion: {min_cohesion_value:.3f} on day {min_cohesion_day}")


def main():
    """Run all demos."""
    print("=" * 70)
    print("  RUTHLESS CORE MODEL - DEMONSTRATION")
    print("=" * 70)
    
    # Run basic simulation
    output = demo_basic_run()
    
    # Show Phase 4 integration
    demo_phase4_integration(output)
    
    # Parameter exploration
    demo_parameter_exploration()
    
    print("\n" + "=" * 70)
    print("  Demo complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  - Open notebooks/ruthless_core_calibration.ipynb for visual calibration")
    print("  - Edit example_config.yaml to customize parameters")
    print("  - Import RuthlessCoreModel in your own scripts")


if __name__ == "__main__":
    main()
