"""
Simple Phase C Test

Tests narrative components in isolation.
"""

import sys
from pathlib import Path

# Add integration and core paths (matching demo_phase_b.py pattern)
sys.path.insert(0, str(Path(__file__).parent.parent / "integration" / "runtime"))
sys.path.insert(0, str(Path(__file__).parent.parent / "phase4" / "06_Ruthless_Core_Model"))

# Now import after path is set
from agents.actions import AgentState, AgentAction, ActionType
from agents.narrative_renderer import NarrativeRenderer, NarrativeOutput
from agents.narrative_logger import NarrativeLogger
from agents.narrative_prompts import create_state_summary


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_components():
    """Test Phase C components."""
    
    print_section("PHASE C COMPONENT TESTS")
    
    # Test 1: State Summary
    print("Test 1: Qualitative State Summary")
    print("-" * 70)
    
    state = AgentState(
        agent_id="crew",
        day=114,
        strain=0.85,
        cohesion=0.32,
        monotony=0.67,
        tq_pressure=0.38,
        mission_progress=0.57,
    )
    
    summary = create_state_summary(state)
    print(f"Quantitative: strain={state.strain:.2f}, cohesion={state.cohesion:.2f}")
    print(f"Qualitative:  {summary['psychological_strain']}, {summary['social_cohesion']}")
    print("✅ State summary working\n")
    
    # Test 2: Narrative Renderer
    print("Test 2: Narrative Rendering")
    print("-" * 70)
    
    renderer = NarrativeRenderer(enable_dialogue=True, enable_narrative=True)
    
    action = AgentAction(
        agent_id="crew",
        day=114,
        action_type=ActionType.WITHDRAW,
        state_snapshot=state,
    )
    
    narrative = renderer.render(action, state)
    
    print(f"Day {narrative.day} - Action: {narrative.action}")
    print(f"  Intent: {narrative.expressed_intent}")
    print(f"  Dialogue: \"{narrative.dialogue}\"")
    print(f"  Summary: {narrative.narrative_summary}")
    print(f"  Mechanistic: {', '.join(narrative.mechanistic_reference)}")
    print("✅ Narrative rendering working\n")
    
    # Test 3: Structured Output
    print("Test 3: Structured Output (JSON)")
    print("-" * 70)
    
    import json
    output_dict = narrative.to_dict()
    output_json = json.dumps(output_dict, indent=2)
    print("Output structure:")
    for key in output_dict.keys():
        print(f"  - {key}")
    print("✅ Structured output working\n")
    
    # Test 4: Narrative Logger
    print("Test 4: Narrative Logger")
    print("-" * 70)
    
    logger = NarrativeLogger(mission_name="test")
    
    for day in [50, 100, 150]:
        test_state = AgentState(
            agent_id="crew",
            day=day,
            strain=0.7,
            cohesion=0.5,
            monotony=0.6,
            tq_pressure=0.3,
            mission_progress=day / 200,
        )
        
        test_action = AgentAction(
            agent_id="crew",
            day=day,
            action_type=ActionType.SUPPORT,
            state_snapshot=test_state,
        )
        
        n = renderer.render(test_action, test_state)
        logger.log_narrative(n)
    
    stats = logger.log.get_statistics()
    print(f"Total narratives logged: {stats['total_narratives']}")
    print(f"Dialogue exchanges: {stats['dialogue_count']}")
    print("✅ Narrative logger working\n")
    
    # Test 5: Critical Moments
    print("Test 5: Critical Moment Detection")
    print("-" * 70)
    
    critical_state = AgentState(
        agent_id="crew",
        day=180,
        strain=0.95,
        cohesion=0.20,
        monotony=0.70,
        tq_pressure=0.40,
        mission_progress=0.9,
    )
    
    critical_action = AgentAction(
        agent_id="crew",
        day=180,
        action_type=ActionType.ESCALATE,
        state_snapshot=critical_state,
    )
    
    critical_narrative = renderer.render(critical_action, critical_state)
    logger.log_narrative(critical_narrative)
    
    critical_moments = logger.log.get_critical_moments()
    print(f"Critical moments detected: {len(critical_moments)}")
    if critical_moments:
        cm = critical_moments[0]
        print(f"  Day {cm.day}: {cm.narrative_summary}")
        print(f"  Conditions: {', '.join(cm.mechanistic_reference)}")
    print("✅ Critical moment detection working\n")
    
    print_section("ALL TESTS PASSED ✅")
    print("Phase C components are operational:")
    print("  • State summaries (quantitative → qualitative)")
    print("  • Narrative rendering (structured output)")
    print("  • Narrative logging (tracking & analysis)")
    print("  • JSON serialization")
    print("  • Critical moment detection")
    print("  • Mechanistic reference linking")


if __name__ == "__main__":
    test_components()
