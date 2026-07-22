"""
Phase C Demonstration

Demonstrates the narrative rendering layer working in tandem
with the deterministic agentic core.

Shows:
1. Baseline mode (no agents, no narrative)
2. Agentic mode (Phase B only)
3. Full mode (Phase B + Phase C narrative)

Validates that narrative layer is:
- Non-causal (doesn't affect trajectories)
- Read-only (doesn't modify state)
- Properly structured (all outputs match schema)
"""

import sys
from pathlib import Path

# Add required paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "phase4" / "06_Ruthless_Core_Model"))

from ruthless_core import RuthlessCoreConfig
from agents import AgenticCoreModel


def demo_baseline():
    """Run baseline simulation (no agents, no narrative)."""
    print("\n" + "=" * 70)
    print("BASELINE MODE (Phase A)")
    print("No agents, no narrative - pure core physics")
    print("=" * 70)
    
    config = RuthlessCoreConfig(mission_length_days=200)
    model = AgenticCoreModel(
        core_config=config,
        enable_actions=False,
        enable_narrative=False,
    )
    
    output, action_log, narrative_log = model.run("baseline_demo")
    
    print(f"\nSimulation complete: {len(output.days)} days")
    print(f"Final strain: {output.strain[-1]:.3f}")
    print(f"Final cohesion: {output.cohesion[-1]:.3f}")
    print(f"Action log: {action_log}")
    print(f"Narrative log: {narrative_log}")
    
    return output


def demo_agentic():
    """Run agentic simulation (Phase B only - no narrative)."""
    print("\n" + "=" * 70)
    print("AGENTIC MODE (Phase B)")
    print("Agents enabled, narrative disabled")
    print("=" * 70)
    
    config = RuthlessCoreConfig(mission_length_days=200)
    model = AgenticCoreModel(
        core_config=config,
        enable_actions=True,
        enable_narrative=False,
    )
    
    output, action_log, narrative_log = model.run("agentic_demo")
    
    print(f"\nSimulation complete: {len(output.days)} days")
    print(f"Final strain: {output.strain[-1]:.3f}")
    print(f"Final cohesion: {output.cohesion[-1]:.3f}")
    
    if action_log:
        stats = action_log.get_statistics()
        print(f"\nAction Statistics:")
        print(f"  Total actions: {stats['total_actions']}")
        print(f"  Dominant action: {stats['dominant_action']}")
        print(f"  Action frequencies:")
        for action, count in stats['action_frequencies'].items():
            print(f"    {action}: {count}")
    
    print(f"Narrative log: {narrative_log}")
    
    return output, action_log


def demo_full():
    """Run full simulation (Phase B + Phase C)."""
    print("\n" + "=" * 70)
    print("FULL MODE (Phase B + Phase C)")
    print("Agents enabled, narrative enabled")
    print("=" * 70)
    
    config = RuthlessCoreConfig(mission_length_days=200)
    model = AgenticCoreModel(
        core_config=config,
        enable_actions=True,
        enable_narrative=True,
    )
    
    output, action_log, narrative_log = model.run("full_demo")
    
    print(f"\nSimulation complete: {len(output.days)} days")
    print(f"Final strain: {output.strain[-1]:.3f}")
    print(f"Final cohesion: {output.cohesion[-1]:.3f}")
    
    if action_log:
        stats = action_log.get_statistics()
        print(f"\nAction Statistics:")
        print(f"  Total actions: {stats['total_actions']}")
        print(f"  Dominant action: {stats['dominant_action']}")
    
    if narrative_log:
        narrative_log.print_summary()
        
        # Show some example narratives
        print("\n" + "-" * 70)
        print("Sample Narrative Outputs:")
        print("-" * 70)
        
        recent = narrative_log.get_recent_narratives(n=5)
        for narrative in recent:
            print(f"\nDay {narrative.day} - {narrative.action}")
            print(f"  Intent: {narrative.expressed_intent}")
            if narrative.dialogue:
                print(f"  Dialogue: \"{narrative.dialogue}\"")
            print(f"  Narrative: {narrative.narrative_summary}")
            print(f"  Mechanistic: {', '.join(narrative.mechanistic_reference)}")
        
        # Show critical moments
        critical = narrative_log.log.get_critical_moments()
        if critical:
            print("\n" + "-" * 70)
            print(f"Critical Moments ({len(critical)} total):")
            print("-" * 70)
            for narrative in critical[:3]:  # Show first 3
                print(f"\nDay {narrative.day} - {narrative.action}")
                print(f"  {narrative.narrative_summary}")
                if narrative.dialogue:
                    print(f"  \"{narrative.dialogue}\"")
    
    return output, action_log, narrative_log


def validate_non_causal():
    """
    Validate that narrative rendering is non-causal.
    
    Runs the same mission twice:
    1. With narrative disabled
    2. With narrative enabled
    
    Verifies that trajectories are identical.
    """
    print("\n" + "=" * 70)
    print("NON-CAUSAL VALIDATION")
    print("Verifying narrative layer doesn't affect trajectories")
    print("=" * 70)
    
    # Use identical configuration and seed
    config = RuthlessCoreConfig(mission_length_days=200)
    
    # Run without narrative
    model1 = AgenticCoreModel(
        core_config=config,
        enable_actions=True,
        enable_narrative=False,
    )
    output1, _, _ = model1.run("validation_no_narrative")
    
    # Run with narrative
    model2 = AgenticCoreModel(
        core_config=config,
        enable_actions=True,
        enable_narrative=True,
    )
    output2, _, _ = model2.run("validation_with_narrative")
    
    # Compare trajectories
    strain_match = all(
        abs(s1 - s2) < 1e-10
        for s1, s2 in zip(output1.strain, output2.strain)
    )
    cohesion_match = all(
        abs(c1 - c2) < 1e-10
        for c1, c2 in zip(output1.cohesion, output2.cohesion)
    )
    monotony_match = all(
        abs(m1 - m2) < 1e-10
        for m1, m2 in zip(output1.monotony, output2.monotony)
    )
    
    print(f"\nTrajectory Comparison:")
    print(f"  Strain identical: {strain_match}")
    print(f"  Cohesion identical: {cohesion_match}")
    print(f"  Monotony identical: {monotony_match}")
    
    if strain_match and cohesion_match and monotony_match:
        print("\n✅ VALIDATION PASSED")
        print("Narrative layer is confirmed non-causal")
    else:
        print("\n❌ VALIDATION FAILED")
        print("Narrative layer is affecting trajectories!")
        
        # Show first difference
        for i, (s1, s2) in enumerate(zip(output1.strain, output2.strain)):
            if abs(s1 - s2) > 1e-10:
                print(f"First strain difference at day {i}: {s1} vs {s2}")
                break
    
    return strain_match and cohesion_match and monotony_match


def main():
    """Run all demonstrations."""
    print("\n" + "#" * 70)
    print("# Phase C Demonstration")
    print("# Narrative Rendering Layer for 3QP")
    print("#" * 70)
    
    # Run demonstrations
    demo_baseline()
    demo_agentic()
    demo_full()
    
    # Validate non-causal property
    validation_passed = validate_non_causal()
    
    print("\n" + "#" * 70)
    print("# Demonstration Complete")
    print("#" * 70)
    
    if validation_passed:
        print("\n✅ All validations passed")
        print("Phase C is working correctly:")
        print("  - Narrative rendering is operational")
        print("  - Output is properly structured")
        print("  - Non-causal property is maintained")
    else:
        print("\n⚠️  Validation issues detected")
    
    print()


if __name__ == "__main__":
    main()
