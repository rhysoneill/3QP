"""
Phase B Demo - Agentic Behavior Demonstration

This script demonstrates the Phase B agentic layer by:
1. Running a baseline mission (no agents)
2. Running an agentic mission (with action selection)
3. Comparing the results
4. Showing action logs and fingerprint integration

Usage:
    python demo_phase_b.py
"""

import sys
from pathlib import Path

# Add integration runtime to path
sys.path.insert(0, str(Path(__file__).parent.parent / "integration" / "runtime"))
sys.path.insert(0, str(Path(__file__).parent.parent / "phase4" / "06_Ruthless_Core_Model"))

from runtime_config import RuntimeConfig
from mission_runner import run_mission
from ruthless_core import RuthlessCoreConfig


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_mission_summary(result, mode_name: str):
    """Print summary of mission results."""
    print(f"\n{mode_name} Results:")
    print("-" * 50)
    
    cohesion = result.core_output.cohesion
    strain = result.core_output.strain
    
    print(f"  Final Cohesion:    {cohesion[-1]:.3f}")
    print(f"  Minimum Cohesion:  {min(cohesion):.3f} (day {cohesion.index(min(cohesion))})")
    print(f"  Final Strain:      {strain[-1]:.3f}")
    print(f"  Maximum Strain:    {max(strain):.3f} (day {strain.index(max(strain))})")
    
    if result.collapse_fingerprint:
        fp = result.collapse_fingerprint
        print(f"\n  Collapse Fingerprint:")
        print(f"    Risk Score:      {fp.risk_score:.3f} ({fp.risk_category})")
        print(f"    Collapse Timing: {fp.collapse_timing:.1%} (day {fp.collapse_day})")
        print(f"    Collapse Depth:  {fp.collapse_depth:.3f}")
    
    if result.action_log:
        stats = result.action_log.get_statistics()
        print(f"\n  Agent Actions:")
        print(f"    Total Actions:   {stats['total_actions']}")
        print(f"    Action Counts:")
        for action, count in sorted(stats['action_counts'].items()):
            freq = stats['action_frequencies'][action]
            print(f"      {action:12s}: {count:3d} ({freq:.1%})")
        
        if 'dominant_action' in stats:
            print(f"    Dominant Action: {stats['dominant_action']} ({stats['dominant_action_frequency']:.1%})")
        
        # Show pre-collapse actions if available
        if result.collapse_fingerprint:
            fp_metadata = result.collapse_fingerprint.metadata
            if 'pre_collapse_actions' in fp_metadata:
                pre_collapse = fp_metadata['pre_collapse_actions']
                print(f"\n  Pre-Collapse Actions (20-day window):")
                print(f"    Dominant: {pre_collapse.get('dominant_action', 'N/A')}")
                print(f"    Sequence: {' → '.join(pre_collapse['action_sequence'])}")


def run_baseline_mission():
    """Run baseline mission without agentic layer."""
    print_section("BASELINE MISSION (No Agents)")
    
    config = RuntimeConfig(
        mission_name="baseline_demo",
        mission_length_days=200,
        verbose=False
    )
    
    result = run_mission(
        runtime_config=config,
        enable_agents=False
    )
    
    print_mission_summary(result, "Baseline")
    return result


def run_agentic_mission():
    """Run mission with agentic layer enabled."""
    print_section("AGENTIC MISSION (Phase B Enabled)")
    
    config = RuntimeConfig(
        mission_name="agentic_demo",
        mission_length_days=200,
        verbose=False
    )
    
    result = run_mission(
        runtime_config=config,
        enable_agents=True
    )
    
    print_mission_summary(result, "Agentic")
    return result


def compare_results(baseline, agentic):
    """Compare baseline and agentic results."""
    print_section("COMPARISON")
    
    baseline_min_cohesion = min(baseline.core_output.cohesion)
    agentic_min_cohesion = min(agentic.core_output.cohesion)
    
    baseline_max_strain = max(baseline.core_output.strain)
    agentic_max_strain = max(agentic.core_output.strain)
    
    print("Impact of Agentic Layer:")
    print("-" * 50)
    print(f"  Minimum Cohesion:")
    print(f"    Baseline: {baseline_min_cohesion:.3f}")
    print(f"    Agentic:  {agentic_min_cohesion:.3f}")
    print(f"    Δ:        {agentic_min_cohesion - baseline_min_cohesion:+.3f}")
    
    print(f"\n  Maximum Strain:")
    print(f"    Baseline: {baseline_max_strain:.3f}")
    print(f"    Agentic:  {agentic_max_strain:.3f}")
    print(f"    Δ:        {agentic_max_strain - baseline_max_strain:+.3f}")
    
    if baseline.collapse_fingerprint and agentic.collapse_fingerprint:
        baseline_risk = baseline.collapse_fingerprint.risk_score
        agentic_risk = agentic.collapse_fingerprint.risk_score
        
        print(f"\n  Risk Score:")
        print(f"    Baseline: {baseline_risk:.3f} ({baseline.collapse_fingerprint.risk_category})")
        print(f"    Agentic:  {agentic_risk:.3f} ({agentic.collapse_fingerprint.risk_category})")
        print(f"    Δ:        {agentic_risk - baseline_risk:+.3f}")


def demonstrate_action_transparency(agentic_result):
    """Show action decision transparency."""
    print_section("ACTION DECISION TRANSPARENCY")
    
    if not agentic_result.action_log:
        print("No action log available.")
        return
    
    print("Sample action decisions (first 20 days):")
    print("-" * 70)
    
    actions = agentic_result.action_log.log.actions[:20]
    for action in actions:
        state = action.state_snapshot
        metadata = action.metadata or {}
        reason = metadata.get('reason', 'N/A')
        
        print(f"Day {action.day:3d}: {str(action.action_type):10s} | "
              f"S={state.strain:.2f} C={state.cohesion:.2f} M={state.monotony:.2f} TQ={state.tq_pressure:.2f} | "
              f"{reason}")


def main():
    """Run Phase B demonstration."""
    print_section("PHASE B: ACTION/INTENT LAYER DEMONSTRATION")
    
    print("This demonstration shows:")
    print("  • Deterministic action selection based on agent state")
    print("  • Action effects on interaction patterns (not psychology)")
    print("  • Complete action logging and traceability")
    print("  • Integration with collapse fingerprinting")
    print("  • Comparison between baseline and agentic behavior")
    
    # Run missions
    baseline_result = run_baseline_mission()
    agentic_result = run_agentic_mission()
    
    # Compare
    compare_results(baseline_result, agentic_result)
    
    # Show transparency
    demonstrate_action_transparency(agentic_result)
    
    # Final summary
    print_section("PHASE B IMPLEMENTATION COMPLETE")
    print("✓ Action model with 5 action types (WITHDRAW, ENGAGE, SUPPORT, ESCALATE, MAINTAIN)")
    print("✓ Deterministic intent policy with explicit thresholds")
    print("✓ Action effects modulate inputs without bypassing physics")
    print("✓ Complete action logging with pre-collapse analysis")
    print("✓ Fingerprint integration for action-collapse correlation")
    print("✓ Full causal transparency maintained")
    print("\nThe system is now agentic while preserving behavioral physics.")
    print("\nNext: Phase C (LLM integration, dialogue, social texture)")


if __name__ == "__main__":
    main()
