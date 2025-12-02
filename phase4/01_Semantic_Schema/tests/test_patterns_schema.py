"""
Tests for pattern schema definitions.

These tests validate that pattern definitions and instances can be created
and that relationships are consistent.
"""

import pytest
from semantic_schema.patterns import (
    PatternDefinition,
    PatternInstance,
    StateCharacteristic,
    PatternClass,
    PatternScope,
    create_stable_pattern_example,
    create_drift_pattern_example,
    create_disruption_pattern_example,
    create_recovery_pattern_example,
)


def test_state_characteristic_creation():
    """Test creating a state characteristic."""
    char = StateCharacteristic(
        domain="physiological",
        characteristic_name="Stable Sleep",
        description="Regular sleep cycles with adequate recovery",
        indicators=["Sleep through scheduled periods", "Wake feeling refreshed"],
        examples=["Crew members sleep 7-8 hours consistently"]
    )
    
    assert char.domain == "physiological"
    assert char.characteristic_name == "Stable Sleep"
    assert len(char.indicators) == 2
    assert len(char.examples) == 1


def test_pattern_definition_creation():
    """Test creating a pattern definition."""
    pattern = PatternDefinition(
        pattern_id="pattern_001",
        name="Test Pattern",
        pattern_class=PatternClass.STABLE,
        pattern_scope=PatternScope.SINGLE_DOMAIN,
        description="A test pattern",
        involved_domains=["physiological"],
        narrative_description="Test narrative"
    )
    
    assert pattern.pattern_id == "pattern_001"
    assert pattern.pattern_class == PatternClass.STABLE
    assert pattern.pattern_scope == PatternScope.SINGLE_DOMAIN
    assert len(pattern.involved_domains) == 1


def test_pattern_definition_add_characteristic():
    """Test adding state characteristics to pattern definition."""
    pattern = PatternDefinition(
        pattern_id="pattern_001",
        name="Test Pattern",
        pattern_class=PatternClass.STABLE,
        pattern_scope=PatternScope.SINGLE_DOMAIN,
        description="Test"
    )
    
    char = StateCharacteristic(
        domain="physiological",
        characteristic_name="Test Characteristic",
        description="Test"
    )
    
    pattern.add_state_characteristic(char)
    
    assert len(pattern.state_characteristics) == 1
    assert "physiological" in pattern.involved_domains


def test_pattern_definition_to_narrative():
    """Test generating narrative description of pattern."""
    pattern = create_stable_pattern_example()
    
    narrative = pattern.to_narrative()
    
    assert "Pattern: High Coherence Pattern" in narrative
    assert "Class: stable" in narrative
    assert "Scope: whole-crew" in narrative


def test_pattern_instance_creation():
    """Test creating a pattern instance."""
    instance = PatternInstance(
        instance_id="instance_001",
        pattern_definition_id="pattern_001",
        pattern_name="Test Pattern",
        scenario_id="scenario_001",
        phase_descriptor="mid-mission",
        observations=["Observed stability in all domains"],
        narrative_summary="Pattern observed during stable mission phase"
    )
    
    assert instance.instance_id == "instance_001"
    assert instance.pattern_definition_id == "pattern_001"
    assert instance.phase_descriptor == "mid-mission"
    assert len(instance.observations) == 1


def test_pattern_instance_add_observation():
    """Test adding observations to pattern instance."""
    instance = PatternInstance(
        instance_id="instance_001",
        pattern_definition_id="pattern_001",
        pattern_name="Test Pattern"
    )
    
    instance.add_observation("First observation")
    instance.add_observation("Second observation")
    
    assert len(instance.observations) == 2


def test_pattern_instance_to_narrative():
    """Test generating narrative description of pattern instance."""
    instance = PatternInstance(
        instance_id="instance_001",
        pattern_definition_id="pattern_001",
        pattern_name="Test Pattern",
        narrative_summary="Test summary"
    )
    
    narrative = instance.to_narrative()
    
    assert "Pattern Instance: Test Pattern" in narrative
    assert "Instance ID: instance_001" in narrative


def test_create_stable_pattern_example():
    """Test creating stable pattern example."""
    pattern = create_stable_pattern_example()
    
    assert pattern.pattern_id == "pattern_stable_001"
    assert pattern.pattern_class == PatternClass.STABLE
    assert pattern.pattern_scope == PatternScope.WHOLE_CREW
    assert len(pattern.state_characteristics) >= 3  # Should have multiple domains
    assert "physiological" in pattern.involved_domains
    assert "cognitive" in pattern.involved_domains
    assert "social" in pattern.involved_domains


def test_create_drift_pattern_example():
    """Test creating drift pattern example."""
    pattern = create_drift_pattern_example()
    
    assert pattern.pattern_id == "pattern_drift_001"
    assert pattern.pattern_class == PatternClass.DRIFT
    assert pattern.pattern_scope == PatternScope.SINGLE_DOMAIN
    assert "sleep" in pattern.name.lower()
    assert "physiological" in pattern.involved_domains


def test_create_disruption_pattern_example():
    """Test creating disruption pattern example."""
    pattern = create_disruption_pattern_example()
    
    assert pattern.pattern_id == "pattern_disruption_001"
    assert pattern.pattern_class == PatternClass.DISRUPTION
    assert pattern.pattern_scope == PatternScope.CROSS_DOMAIN
    assert "trust" in pattern.name.lower()
    assert "social" in pattern.involved_domains
    assert "cognitive" in pattern.involved_domains


def test_create_recovery_pattern_example():
    """Test creating recovery pattern example."""
    pattern = create_recovery_pattern_example()
    
    assert pattern.pattern_id == "pattern_recovery_001"
    assert pattern.pattern_class == PatternClass.RECOVERY
    assert pattern.pattern_scope == PatternScope.CROSS_DOMAIN
    assert "repair" in pattern.name.lower() or "recovery" in pattern.name.lower()
    assert len(pattern.involved_domains) >= 2


def test_pattern_class_enum():
    """Test pattern class enum values."""
    assert PatternClass.STABLE.value == "stable"
    assert PatternClass.DRIFT.value == "drift"
    assert PatternClass.DISRUPTION.value == "disruption"
    assert PatternClass.RECOVERY.value == "recovery"


def test_pattern_scope_enum():
    """Test pattern scope enum values."""
    assert PatternScope.SINGLE_DOMAIN.value == "single-domain"
    assert PatternScope.CROSS_DOMAIN.value == "cross-domain"
    assert PatternScope.WHOLE_CREW.value == "whole-crew"


def test_pattern_with_phase3_references():
    """Test that patterns include Phase 3 references."""
    pattern = create_stable_pattern_example()
    
    assert len(pattern.phase3_references) > 0
    assert any("Phase 3" in ref for ref in pattern.phase3_references)


def test_pattern_recognition_indicators():
    """Test that patterns include recognition indicators."""
    pattern = create_stable_pattern_example()
    
    assert len(pattern.recognition_indicators) > 0


def test_state_characteristic_in_pattern():
    """Test that state characteristics are properly integrated into patterns."""
    pattern = create_stable_pattern_example()
    
    assert len(pattern.state_characteristics) > 0
    
    for char in pattern.state_characteristics:
        assert char.domain in pattern.involved_domains
        assert char.characteristic_name is not None
        assert char.description is not None


def test_pattern_instance_with_domain_states():
    """Test pattern instance with domain states recorded."""
    instance = PatternInstance(
        instance_id="instance_001",
        pattern_definition_id="pattern_001",
        pattern_name="Test Pattern",
        domain_states={
            "physiological": "well-rested",
            "cognitive": "clear-and-focused",
            "social": "cohesive"
        }
    )
    
    assert len(instance.domain_states) == 3
    assert instance.domain_states["physiological"] == "well-rested"


def test_pattern_instance_with_related_patterns():
    """Test pattern instance with related patterns linked."""
    instance = PatternInstance(
        instance_id="instance_001",
        pattern_definition_id="pattern_001",
        pattern_name="Test Pattern",
        related_patterns=["pattern_002", "pattern_003"]
    )
    
    assert len(instance.related_patterns) == 2
    assert "pattern_002" in instance.related_patterns


def test_pattern_instance_with_related_events():
    """Test pattern instance with related events linked."""
    instance = PatternInstance(
        instance_id="instance_001",
        pattern_definition_id="pattern_001",
        pattern_name="Test Pattern",
        related_events=["event_001", "event_002"]
    )
    
    assert len(instance.related_events) == 2
    assert "event_001" in instance.related_events
