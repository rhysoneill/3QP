"""
Tests for scenario schema definitions.

These tests validate that scenario templates and event descriptors can be
instantiated with reasonable values.
"""

import pytest
from semantic_schema.scenarios import (
    ScenarioTemplate,
    EventDescriptor,
    EventStoryline,
    ScenarioType,
    EventCategory,
    EventIntensity,
    TemporalCharacter,
    create_nominal_scenario,
    create_disruption_scenario,
    create_third_quarter_scenario,
)


def test_event_descriptor_creation():
    """Test creating an event descriptor."""
    event = EventDescriptor(
        event_id="event_001",
        name="Equipment Malfunction",
        description="Critical system requires repair",
        category=EventCategory.OPERATIONAL,
        intensity=EventIntensity.SIGNIFICANT,
        temporal_character=TemporalCharacter.SUSTAINED,
        dominant_themes=["operational pressure", "uncertainty"],
        affected_domains=["operational", "cognitive", "workload"]
    )
    
    assert event.event_id == "event_001"
    assert event.name == "Equipment Malfunction"
    assert event.category == EventCategory.OPERATIONAL
    assert event.intensity == EventIntensity.SIGNIFICANT
    assert len(event.dominant_themes) == 2
    assert len(event.affected_domains) == 3


def test_event_descriptor_to_narrative():
    """Test generating narrative description of an event."""
    event = EventDescriptor(
        event_id="event_001",
        name="Test Event",
        description="A test event",
        category=EventCategory.SOCIAL,
        intensity=EventIntensity.MODERATE,
        temporal_character=TemporalCharacter.BRIEF_AND_TRANSIENT,
        narrative_context="Test context"
    )
    
    narrative = event.to_narrative()
    
    assert "Event: Test Event" in narrative
    assert "Category: social" in narrative
    assert "Intensity: moderate" in narrative


def test_event_storyline_creation():
    """Test creating an event storyline."""
    storyline = EventStoryline(
        storyline_id="story_001",
        name="Test Storyline",
        description="A test event sequence",
        phase_markers=["Phase 1", "Phase 2"],
        arc_description="A simple arc"
    )
    
    assert storyline.storyline_id == "story_001"
    assert storyline.name == "Test Storyline"
    assert len(storyline.events) == 0
    assert len(storyline.phase_markers) == 2


def test_event_storyline_add_event():
    """Test adding events to a storyline."""
    storyline = EventStoryline(
        storyline_id="story_001",
        name="Test Storyline",
        description="Test"
    )
    
    event1 = EventDescriptor(
        event_id="event_001",
        name="Event 1",
        description="First event",
        category=EventCategory.OPERATIONAL,
        intensity=EventIntensity.MILD,
        temporal_character=TemporalCharacter.BRIEF_AND_TRANSIENT
    )
    
    event2 = EventDescriptor(
        event_id="event_002",
        name="Event 2",
        description="Second event",
        category=EventCategory.SOCIAL,
        intensity=EventIntensity.MODERATE,
        temporal_character=TemporalCharacter.EPISODIC
    )
    
    storyline.add_event(event1)
    storyline.add_event(event2)
    
    assert len(storyline.events) == 2
    assert storyline.events[0].name == "Event 1"
    assert storyline.events[1].name == "Event 2"


def test_event_storyline_get_events_by_category():
    """Test retrieving events by category from storyline."""
    storyline = EventStoryline(
        storyline_id="story_001",
        name="Test",
        description="Test"
    )
    
    storyline.add_event(EventDescriptor(
        event_id="e1",
        name="Operational Event",
        description="Test",
        category=EventCategory.OPERATIONAL,
        intensity=EventIntensity.MILD,
        temporal_character=TemporalCharacter.BRIEF_AND_TRANSIENT
    ))
    
    storyline.add_event(EventDescriptor(
        event_id="e2",
        name="Social Event",
        description="Test",
        category=EventCategory.SOCIAL,
        intensity=EventIntensity.MILD,
        temporal_character=TemporalCharacter.BRIEF_AND_TRANSIENT
    ))
    
    operational_events = storyline.get_events_by_category(EventCategory.OPERATIONAL)
    assert len(operational_events) == 1
    assert operational_events[0].name == "Operational Event"


def test_event_storyline_get_events_by_intensity():
    """Test retrieving events by intensity from storyline."""
    storyline = EventStoryline(
        storyline_id="story_001",
        name="Test",
        description="Test"
    )
    
    storyline.add_event(EventDescriptor(
        event_id="e1",
        name="Mild Event",
        description="Test",
        category=EventCategory.OPERATIONAL,
        intensity=EventIntensity.MILD,
        temporal_character=TemporalCharacter.BRIEF_AND_TRANSIENT
    ))
    
    storyline.add_event(EventDescriptor(
        event_id="e2",
        name="Severe Event",
        description="Test",
        category=EventCategory.OPERATIONAL,
        intensity=EventIntensity.SEVERE,
        temporal_character=TemporalCharacter.BRIEF_AND_TRANSIENT
    ))
    
    severe_events = storyline.get_events_by_intensity(EventIntensity.SEVERE)
    assert len(severe_events) == 1
    assert severe_events[0].name == "Severe Event"


def test_scenario_template_creation():
    """Test creating a scenario template."""
    scenario = ScenarioTemplate(
        template_id="scenario_001",
        name="Test Scenario",
        scenario_type=ScenarioType.NOMINAL_MISSION,
        description="A test scenario",
        baseline_reference="baseline_nominal_001",
        dominant_pressures=["Routine operations"],
        dominant_themes=["Adaptation"]
    )
    
    assert scenario.template_id == "scenario_001"
    assert scenario.scenario_type == ScenarioType.NOMINAL_MISSION
    assert len(scenario.dominant_pressures) == 1
    assert len(scenario.dominant_themes) == 1


def test_scenario_template_with_storyline():
    """Test scenario template with event storyline."""
    storyline = EventStoryline(
        storyline_id="story_001",
        name="Test Story",
        description="Test"
    )
    
    scenario = ScenarioTemplate(
        template_id="scenario_001",
        name="Test Scenario",
        scenario_type=ScenarioType.NOMINAL_MISSION,
        description="Test",
        storyline=storyline
    )
    
    assert scenario.storyline is not None
    assert scenario.storyline.storyline_id == "story_001"


def test_scenario_template_add_phase_description():
    """Test adding phase descriptions to scenario."""
    scenario = ScenarioTemplate(
        template_id="scenario_001",
        name="Test",
        scenario_type=ScenarioType.NOMINAL_MISSION,
        description="Test"
    )
    
    scenario.add_phase_description("Early Mission", "Crew adapts to environment")
    scenario.add_phase_description("Mid Mission", "Stable operations")
    
    assert len(scenario.phase_descriptions) == 2
    assert "Early Mission" in scenario.phase_descriptions


def test_scenario_template_add_domain_trajectory():
    """Test adding domain trajectory descriptions to scenario."""
    scenario = ScenarioTemplate(
        template_id="scenario_001",
        name="Test",
        scenario_type=ScenarioType.NOMINAL_MISSION,
        description="Test"
    )
    
    scenario.add_domain_trajectory("physiological", "Remains stable throughout")
    scenario.add_domain_trajectory("cognitive", "Clear and focused")
    
    assert len(scenario.domain_trajectory_descriptions) == 2
    assert "physiological" in scenario.domain_trajectory_descriptions


def test_scenario_template_to_narrative():
    """Test generating narrative description of scenario."""
    scenario = create_nominal_scenario()
    
    narrative = scenario.to_narrative()
    
    assert "Scenario Template: Nominal Mission Scenario" in narrative
    assert "Type: nominal-mission" in narrative
    assert "Dominant Pressures:" in narrative


def test_create_nominal_scenario():
    """Test creating nominal scenario from factory function."""
    scenario = create_nominal_scenario()
    
    assert scenario.template_id == "scenario_nominal_001"
    assert scenario.scenario_type == ScenarioType.NOMINAL_MISSION
    assert scenario.storyline is not None
    assert len(scenario.storyline.events) >= 2
    assert len(scenario.dominant_pressures) > 0


def test_create_disruption_scenario():
    """Test creating disruption scenario from factory function."""
    scenario = create_disruption_scenario()
    
    assert scenario.template_id == "scenario_disruption_001"
    assert scenario.scenario_type == ScenarioType.STRESSOR_DRIVEN_DISRUPTION
    assert scenario.storyline is not None
    assert len(scenario.storyline.events) >= 2
    
    # Should have events with significant intensity
    severe_events = [e for e in scenario.storyline.events 
                     if e.intensity == EventIntensity.SIGNIFICANT]
    assert len(severe_events) > 0


def test_create_third_quarter_scenario():
    """Test creating third-quarter scenario from factory function."""
    scenario = create_third_quarter_scenario()
    
    assert scenario.template_id == "scenario_third_quarter_001"
    assert scenario.scenario_type == ScenarioType.THIRD_QUARTER_PHENOMENON
    assert "third-quarter" in scenario.name.lower() or "third quarter" in scenario.name.lower()
    assert len(scenario.dominant_themes) > 0


def test_event_category_enum():
    """Test event category enum values."""
    assert EventCategory.OPERATIONAL.value == "operational"
    assert EventCategory.SOCIAL.value == "social"
    assert EventCategory.ENVIRONMENTAL.value == "environmental"
    assert EventCategory.COGNITIVE.value == "cognitive"
    assert EventCategory.EMOTIONAL.value == "emotional"


def test_event_intensity_enum():
    """Test event intensity enum values."""
    assert EventIntensity.MINIMAL.value == "minimal"
    assert EventIntensity.MODERATE.value == "moderate"
    assert EventIntensity.SEVERE.value == "severe"


def test_temporal_character_enum():
    """Test temporal character enum values."""
    assert TemporalCharacter.BRIEF_AND_TRANSIENT.value == "brief-and-transient"
    assert TemporalCharacter.SUSTAINED.value == "sustained"
    assert TemporalCharacter.CHRONIC.value == "chronic"
