"""
Tests for thread schema definitions.

These tests validate that thread definitions and instances can be created
and that domain relationships are properly represented.
"""

import pytest
from semantic_schema.threads import (
    ThreadDefinition,
    ThreadInstance,
    DomainInfluence,
    ThreadCategory,
    InfluenceType,
    TemporalPattern,
    create_strain_reactivity_thread,
    create_meaning_erosion_thread,
    create_domain_interaction_thread_example,
)


def test_domain_influence_creation():
    """Test creating a domain influence relationship."""
    influence = DomainInfluence(
        source_domain="physiological",
        target_domain="cognitive",
        influence_type=InfluenceType.CONSTRAINING,
        description="Fatigue constrains cognitive capacity",
        strength_descriptor="strong",
        conditions=["Sleep deprivation", "Sustained stress"],
        examples=["Fatigued crew members make more errors"]
    )
    
    assert influence.source_domain == "physiological"
    assert influence.target_domain == "cognitive"
    assert influence.influence_type == InfluenceType.CONSTRAINING
    assert influence.strength_descriptor == "strong"
    assert len(influence.conditions) == 2
    assert len(influence.examples) == 1


def test_thread_definition_creation():
    """Test creating a thread definition."""
    thread = ThreadDefinition(
        thread_id="thread_001",
        name="Test Thread",
        category=ThreadCategory.DOMAIN_INTERACTION,
        description="A test thread",
        involved_domains=["physiological", "cognitive"],
        narrative_description="Test narrative",
        temporal_pattern=TemporalPattern.GRADUAL
    )
    
    assert thread.thread_id == "thread_001"
    assert thread.category == ThreadCategory.DOMAIN_INTERACTION
    assert thread.temporal_pattern == TemporalPattern.GRADUAL
    assert len(thread.involved_domains) == 2


def test_thread_definition_add_domain_influence():
    """Test adding domain influences to thread definition."""
    thread = ThreadDefinition(
        thread_id="thread_001",
        name="Test Thread",
        category=ThreadCategory.DOMAIN_INTERACTION,
        description="Test"
    )
    
    influence = DomainInfluence(
        source_domain="physiological",
        target_domain="cognitive",
        influence_type=InfluenceType.CONSTRAINING,
        description="Test influence"
    )
    
    thread.add_domain_influence(influence)
    
    assert len(thread.domain_influences) == 1
    assert "physiological" in thread.involved_domains
    assert "cognitive" in thread.involved_domains


def test_thread_definition_to_narrative():
    """Test generating narrative description of thread."""
    thread = create_strain_reactivity_thread()
    
    narrative = thread.to_narrative()
    
    assert "Thread: Strain–Reactivity Thread" in narrative
    assert "Category: composite" in narrative
    assert "Domain Influences:" in narrative


def test_thread_instance_creation():
    """Test creating a thread instance."""
    instance = ThreadInstance(
        instance_id="instance_001",
        thread_definition_id="thread_001",
        thread_name="Test Thread",
        scenario_id="scenario_001",
        phase_descriptor="mid-mission drift",
        narrative_summary="Thread observed during mid-mission phase"
    )
    
    assert instance.instance_id == "instance_001"
    assert instance.thread_definition_id == "thread_001"
    assert instance.phase_descriptor == "mid-mission drift"


def test_thread_instance_add_pattern():
    """Test adding pattern instances to thread instance."""
    instance = ThreadInstance(
        instance_id="instance_001",
        thread_definition_id="thread_001",
        thread_name="Test Thread"
    )
    
    instance.add_pattern_instance("pattern_instance_001")
    instance.add_pattern_instance("pattern_instance_002")
    
    assert len(instance.pattern_instances) == 2
    
    # Adding duplicate should not create duplicate entry
    instance.add_pattern_instance("pattern_instance_001")
    assert len(instance.pattern_instances) == 2


def test_thread_instance_add_observation():
    """Test adding observations to thread instance."""
    instance = ThreadInstance(
        instance_id="instance_001",
        thread_definition_id="thread_001",
        thread_name="Test Thread"
    )
    
    instance.add_observation("Observed physiological strain")
    instance.add_observation("Observed emotional reactivity")
    
    assert len(instance.observations) == 2


def test_thread_instance_to_narrative():
    """Test generating narrative description of thread instance."""
    instance = ThreadInstance(
        instance_id="instance_001",
        thread_definition_id="thread_001",
        thread_name="Test Thread",
        narrative_summary="Test summary"
    )
    
    narrative = instance.to_narrative()
    
    assert "Thread Instance: Test Thread" in narrative
    assert "Instance ID: instance_001" in narrative


def test_create_strain_reactivity_thread():
    """Test creating strain-reactivity thread example."""
    thread = create_strain_reactivity_thread()
    
    assert thread.thread_id == "thread_composite_001"
    assert thread.category == ThreadCategory.COMPOSITE
    assert thread.name == "Strain–Reactivity Thread"
    assert len(thread.domain_influences) >= 4  # Should have multiple influences
    
    # Check that it's a cycle
    domains_with_outgoing = set(inf.source_domain for inf in thread.domain_influences)
    assert "physiological" in domains_with_outgoing
    assert "emotional" in domains_with_outgoing
    assert "social" in domains_with_outgoing
    assert "cognitive" in domains_with_outgoing


def test_create_meaning_erosion_thread():
    """Test creating meaning erosion thread example."""
    thread = create_meaning_erosion_thread()
    
    assert thread.thread_id == "thread_composite_002"
    assert thread.category == ThreadCategory.COMPOSITE
    assert "meaning" in thread.name.lower()
    assert len(thread.domain_influences) >= 3


def test_create_domain_interaction_thread_example():
    """Test creating domain interaction thread example."""
    thread = create_domain_interaction_thread_example()
    
    assert thread.thread_id == "thread_interaction_001"
    assert thread.category == ThreadCategory.DOMAIN_INTERACTION
    assert len(thread.domain_influences) >= 1
    
    # Should be pairwise interaction
    assert len(thread.involved_domains) == 2


def test_thread_category_enum():
    """Test thread category enum values."""
    assert ThreadCategory.DOMAIN_INTERACTION.value == "domain-interaction"
    assert ThreadCategory.MISSION_PHASE.value == "mission-phase"
    assert ThreadCategory.COMPOSITE.value == "composite"


def test_influence_type_enum():
    """Test influence type enum values."""
    assert InfluenceType.AMPLIFYING.value == "amplifying"
    assert InfluenceType.CONSTRAINING.value == "constraining"
    assert InfluenceType.TRANSFORMING.value == "transforming"
    assert InfluenceType.TRIGGERING.value == "triggering"
    assert InfluenceType.MODULATING.value == "modulating"
    assert InfluenceType.MUTUAL_REINFORCEMENT.value == "mutual-reinforcement"


def test_temporal_pattern_enum():
    """Test temporal pattern enum values."""
    assert TemporalPattern.GRADUAL.value == "gradual"
    assert TemporalPattern.SUDDEN.value == "sudden"
    assert TemporalPattern.CYCLICAL.value == "cyclical"
    assert TemporalPattern.SUSTAINED.value == "sustained"
    assert TemporalPattern.EPISODIC.value == "episodic"


def test_thread_with_associated_patterns():
    """Test that threads include associated patterns."""
    thread = create_strain_reactivity_thread()
    
    assert len(thread.associated_patterns) > 0


def test_thread_with_recognition_indicators():
    """Test that threads include recognition indicators."""
    thread = create_strain_reactivity_thread()
    
    assert len(thread.recognition_indicators) > 0


def test_thread_with_phase3_references():
    """Test that threads include Phase 3 references."""
    thread = create_strain_reactivity_thread()
    
    assert len(thread.phase3_references) > 0
    assert any("Phase 3" in ref for ref in thread.phase3_references)


def test_domain_influence_with_conditions():
    """Test domain influence includes conditional logic."""
    influence = DomainInfluence(
        source_domain="physiological",
        target_domain="emotional",
        influence_type=InfluenceType.AMPLIFYING,
        description="Test",
        conditions=["Condition 1", "Condition 2"]
    )
    
    assert len(influence.conditions) == 2


def test_thread_instance_with_domain_states():
    """Test thread instance with domain states recorded."""
    instance = ThreadInstance(
        instance_id="instance_001",
        thread_definition_id="thread_001",
        thread_name="Test Thread",
        domain_states={
            "physiological": "moderately-fatigued",
            "emotional": "mildly-negative",
            "social": "strained"
        }
    )
    
    assert len(instance.domain_states) == 3


def test_thread_instance_with_related_events():
    """Test thread instance with related events linked."""
    instance = ThreadInstance(
        instance_id="instance_001",
        thread_definition_id="thread_001",
        thread_name="Test Thread",
        related_events=["event_001", "event_002"]
    )
    
    assert len(instance.related_events) == 2


def test_composite_thread_multi_domain():
    """Test that composite threads involve multiple domains."""
    thread = create_strain_reactivity_thread()
    
    assert thread.category == ThreadCategory.COMPOSITE
    assert len(thread.involved_domains) >= 4  # Should involve many domains


def test_domain_interaction_thread_pairwise():
    """Test that domain interaction threads are pairwise."""
    thread = create_domain_interaction_thread_example()
    
    assert thread.category == ThreadCategory.DOMAIN_INTERACTION
    # Should primarily focus on one or two domains
    assert len(thread.involved_domains) <= 2
