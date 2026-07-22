"""
Quick Phase C validation test.

Tests that the narrative components work correctly.
"""

import sys
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent / "phase4" / "06_Ruthless_Core_Model"))

# Now we can import
from agents.actions import AgentState, AgentAction, ActionType
from agents.narrative_renderer import NarrativeRenderer
from agents.narrative_logger import NarrativeLogger
from agents.narrative_prompts import create_state_summary


def test_state_summary():
    """Test qualitative state summary creation."""
    print("\n=== Testing State Summary ===")
    
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
    print(f"State: strain={state.strain}, cohesion={state.cohesion}")
    print(f"Summary: {summary}")
    assert summary["psychological_strain"] == "high"
    assert summary["social_cohesion"] == "low"
    print("✅ State summary working correctly")


def test_narrative_renderer():
    """Test narrative rendering."""
    print("\n=== Testing Narrative Renderer ===")
    
    renderer = NarrativeRenderer(
        enable_dialogue=True,
        enable_narrative=True,
    )
    
    state = AgentState(
        agent_id="crew",
        day=114,
        strain=0.85,
        cohesion=0.32,
        monotony=0.67,
        tq_pressure=0.38,
        mission_progress=0.57,
    )
    
    action = AgentAction(
        agent_id="crew",
        day=114,
        action_type=ActionType.WITHDRAW,
        state_snapshot=state,
    )
    
    narrative = renderer.render(action, state)
    
    print(f"\nDay {narrative.day} - {narrative.action}")
    print(f"Intent: {narrative.expressed_intent}")
    print(f"Dialogue: {narrative.dialogue}")
    print(f"Summary: {narrative.narrative_summary}")
    print(f"Mechanistic: {narrative.mechanistic_reference}")
    
    assert narrative.agent_id == "crew"
    assert narrative.day == 114
    assert narrative.action == "withdraw"
    assert narrative.expressed_intent is not None
    assert narrative.dialogue is not None
    assert narrative.narrative_summary is not None
    assert len(narrative.mechanistic_reference) > 0
    
    print("✅ Narrative renderer working correctly")


def test_narrative_logger():
    """Test narrative logging."""
    print("\n=== Testing Narrative Logger ===")
    
    logger = NarrativeLogger(mission_name="test_mission")
    renderer = NarrativeRenderer()
    
    # Create multiple narratives
    for day in [50, 100, 150]:
        state = AgentState(
            agent_id="crew",
            day=day,
            strain=0.7 + (day / 1000),
            cohesion=0.5 - (day / 1000),
            monotony=0.6,
            tq_pressure=0.3,
            mission_progress=day / 200,
        )
        
        action = AgentAction(
            agent_id="crew",
            day=day,
            action_type=ActionType.SUPPORT if day < 100 else ActionType.WITHDRAW,
            state_snapshot=state,
        )
        
        narrative = renderer.render(action, state)
        logger.log_narrative(narrative)
    
    stats = logger.log.get_statistics()
    print(f"Total narratives: {stats['total_narratives']}")
    print(f"Dialogue count: {stats['dialogue_count']}")
    print(f"Narratives by action: {stats['narratives_by_action']}")
    
    assert stats["total_narratives"] == 3
    print("✅ Narrative logger working correctly")


def test_structured_output():
    """Test that outputs are properly structured."""
    print("\n=== Testing Structured Output ===")
    
    renderer = NarrativeRenderer()
    
    state = AgentState(
        agent_id="crew",
        day=114,
        strain=0.95,
        cohesion=0.20,
        monotony=0.67,
        tq_pressure=0.38,
        mission_progress=0.57,
    )
    
    action = AgentAction(
        agent_id="crew",
        day=114,
        action_type=ActionType.ESCALATE,
        state_snapshot=state,
    )
    
    narrative = renderer.render(action, state)
    
    # Convert to dict and JSON
    as_dict = narrative.to_dict()
    as_json = narrative.to_json()
    
    print(f"Output as dict: {list(as_dict.keys())}")
    print(f"Output as JSON (length): {len(as_json)} chars")
    
    assert "agent_id" in as_dict
    assert "expressed_intent" in as_dict
    assert "mechanistic_reference" in as_dict
    assert len(as_json) > 0
    
    print("✅ Structured output working correctly")


def test_mechanistic_reference():
    """Test that mechanistic references are correct."""
    print("\n=== Testing Mechanistic Reference ===")
    
    renderer = NarrativeRenderer()
    
    # Test critical strain
    state = AgentState(
        agent_id="crew",
        day=100,
        strain=0.95,
        cohesion=0.5,
        monotony=0.5,
        tq_pressure=0.2,
        mission_progress=0.5,
    )
    
    action = AgentAction(
        agent_id="crew",
        day=100,
        action_type=ActionType.WITHDRAW,
        state_snapshot=state,
    )
    
    narrative = renderer.render(action, state)
    
    print(f"High strain state → mechanistic ref: {narrative.mechanistic_reference}")
    assert "strain_critical" in narrative.mechanistic_reference
    
    # Test critical cohesion
    state.strain = 0.5
    state.cohesion = 0.20
    action.action_type = ActionType.ESCALATE
    
    narrative = renderer.render(action, state)
    
    print(f"Low cohesion state → mechanistic ref: {narrative.mechanistic_reference}")
    assert "cohesion_critical" in narrative.mechanistic_reference
    
    print("✅ Mechanistic reference working correctly")


def main():
    """Run all tests."""
    print("\n" + "#" * 70)
    print("# Phase C Component Tests")
    print("#" * 70)
    
    try:
        test_state_summary()
        test_narrative_renderer()
        test_narrative_logger()
        test_structured_output()
        test_mechanistic_reference()
        
        print("\n" + "#" * 70)
        print("# All Tests Passed ✅")
        print("#" * 70)
        print("\nPhase C components are working correctly:")
        print("  - State summaries convert quantitative → qualitative")
        print("  - Narrative renderer generates structured output")
        print("  - Narrative logger tracks outputs")
        print("  - Outputs are properly structured (JSON serializable)")
        print("  - Mechanistic references link to thresholds")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
