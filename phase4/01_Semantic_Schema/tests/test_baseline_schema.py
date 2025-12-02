"""
Tests for baseline schema definitions.

These tests validate that baseline schemas can be instantiated with reasonable
values and that relationships are consistent.
"""

import pytest
from semantic_schema.baseline import (
    BaselineProfile,
    DomainState,
    SemanticTag,
    ModuleReference,
    Domain,
    PhysiologicalTag,
    CognitiveTag,
    EmotionalTag,
    SocialTag,
    WorkloadTag,
    OperationalTag,
    create_nominal_baseline,
)


def test_semantic_tag_creation():
    """Test creating a semantic tag with valid domain and label."""
    tag = SemanticTag(
        domain=Domain.PHYSIOLOGICAL,
        label=PhysiologicalTag.WELL_RESTED.value,
        description="Crew member is well-rested"
    )
    
    assert tag.domain == Domain.PHYSIOLOGICAL
    assert tag.label == PhysiologicalTag.WELL_RESTED.value
    assert tag.description is not None


def test_semantic_tag_custom():
    """Test creating a custom semantic tag not in predefined enums."""
    tag = SemanticTag(
        domain=Domain.PHYSIOLOGICAL,
        label="custom-state",
        description="A custom physiological state"
    )
    
    assert tag.label == "custom-state"
    assert "custom" in tag.description.lower()


def test_module_reference_creation():
    """Test creating a module reference."""
    ref = ModuleReference(
        module_name="slowfast_physiology",
        config_id="config_001",
        description="Reference to physiology module configuration"
    )
    
    assert ref.module_name == "slowfast_physiology"
    assert ref.config_id == "config_001"


def test_domain_state_creation():
    """Test creating a domain state with tags."""
    primary_tag = SemanticTag(
        domain=Domain.PHYSIOLOGICAL,
        label=PhysiologicalTag.WELL_RESTED.value
    )
    
    secondary_tag = SemanticTag(
        domain=Domain.PHYSIOLOGICAL,
        label=PhysiologicalTag.CALM_AND_BALANCED.value
    )
    
    state = DomainState(
        domain=Domain.PHYSIOLOGICAL,
        primary_tag=primary_tag,
        secondary_tags=[secondary_tag],
        narrative_description="Stable physiological functioning"
    )
    
    assert state.domain == Domain.PHYSIOLOGICAL
    assert state.primary_tag == primary_tag
    assert len(state.secondary_tags) == 1
    assert state.narrative_description is not None


def test_domain_state_validation():
    """Test that domain state validates tag domains match."""
    primary_tag = SemanticTag(
        domain=Domain.COGNITIVE,
        label=CognitiveTag.CLEAR_AND_FOCUSED.value
    )
    
    # Should raise ValueError when primary tag domain doesn't match
    with pytest.raises(ValueError):
        DomainState(
            domain=Domain.PHYSIOLOGICAL,
            primary_tag=primary_tag
        )


def test_baseline_profile_creation():
    """Test creating a complete baseline profile."""
    baseline = create_nominal_baseline()
    
    assert baseline.profile_id == "baseline_nominal_001"
    assert baseline.name == "Nominal Baseline"
    assert baseline.physiological_state.domain == Domain.PHYSIOLOGICAL
    assert baseline.cognitive_state.domain == Domain.COGNITIVE
    assert baseline.emotional_state.domain == Domain.EMOTIONAL
    assert baseline.social_state.domain == Domain.SOCIAL
    assert baseline.workload_state.domain == Domain.WORKLOAD
    assert baseline.operational_state.domain == Domain.OPERATIONAL


def test_baseline_profile_get_domain_state():
    """Test retrieving domain states from baseline profile."""
    baseline = create_nominal_baseline()
    
    phys_state = baseline.get_domain_state(Domain.PHYSIOLOGICAL)
    assert phys_state.domain == Domain.PHYSIOLOGICAL
    
    cog_state = baseline.get_domain_state(Domain.COGNITIVE)
    assert cog_state.domain == Domain.COGNITIVE


def test_baseline_profile_get_all_tags():
    """Test retrieving all semantic tags from baseline profile."""
    baseline = create_nominal_baseline()
    
    all_tags = baseline.get_all_semantic_tags()
    assert len(all_tags) > 0
    
    # Should have at least one tag per domain (primary tags)
    assert len(all_tags) >= 6


def test_baseline_profile_to_narrative():
    """Test generating narrative summary from baseline profile."""
    baseline = create_nominal_baseline()
    
    narrative = baseline.to_narrative_summary()
    
    assert "Baseline Profile: Nominal Baseline" in narrative
    assert "Physiological:" in narrative
    assert "Cognitive:" in narrative
    assert "Social:" in narrative


def test_baseline_profile_validation():
    """Test that baseline profile validates domain states match expected domains."""
    # Create mismatched domain state
    wrong_state = DomainState(
        domain=Domain.COGNITIVE,
        primary_tag=SemanticTag(
            domain=Domain.COGNITIVE,
            label=CognitiveTag.CLEAR_AND_FOCUSED.value
        )
    )
    
    correct_states = {
        field: create_nominal_baseline().get_domain_state(domain)
        for field, domain in [
            ("cognitive_state", Domain.COGNITIVE),
            ("emotional_state", Domain.EMOTIONAL),
            ("social_state", Domain.SOCIAL),
            ("workload_state", Domain.WORKLOAD),
            ("operational_state", Domain.OPERATIONAL),
        ]
    }
    
    # Should raise ValueError when domain doesn't match
    with pytest.raises(ValueError):
        BaselineProfile(
            profile_id="test",
            name="Test",
            description="Test baseline",
            physiological_state=wrong_state,  # Cognitive state in physiological slot
            **correct_states
        )


def test_domain_state_with_module_references():
    """Test creating domain state with module references."""
    module_ref = ModuleReference(
        module_name="slowfast_physiology",
        config_id="baseline_config"
    )
    
    state = DomainState(
        domain=Domain.PHYSIOLOGICAL,
        primary_tag=SemanticTag(
            domain=Domain.PHYSIOLOGICAL,
            label=PhysiologicalTag.WELL_RESTED.value
        ),
        module_references=[module_ref]
    )
    
    assert len(state.module_references) == 1
    assert state.module_references[0].module_name == "slowfast_physiology"


def test_all_semantic_tag_enums():
    """Test that all semantic tag enums are accessible."""
    # Physiological tags
    assert PhysiologicalTag.WELL_RESTED.value == "well-rested"
    assert PhysiologicalTag.CALM_AND_BALANCED.value == "calm-and-balanced"
    
    # Cognitive tags
    assert CognitiveTag.CLEAR_AND_FOCUSED.value == "clear-and-focused"
    assert CognitiveTag.CONFIDENT_AND_DECISIVE.value == "confident-and-decisive"
    
    # Emotional tags
    assert EmotionalTag.STABLE_AND_POSITIVE.value == "stable-and-positive"
    assert EmotionalTag.WELL_REGULATED.value == "well-regulated"
    
    # Social tags
    assert SocialTag.COHESIVE.value == "cohesive"
    assert SocialTag.HIGH_TRUST.value == "high-trust"
    
    # Workload tags
    assert WorkloadTag.MODERATE_AND_BALANCED.value == "moderate-and-balanced"
    assert WorkloadTag.ADEQUATE_RESOURCES.value == "adequate-resources"
    
    # Operational tags
    assert OperationalTag.ROUTINE_OPERATIONS.value == "routine-operations"
    assert OperationalTag.LOW_BACKGROUND_PRESSURE.value == "low-background-pressure"
