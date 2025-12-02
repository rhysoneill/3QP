"""
Tests for trajectory schema definitions.

These tests validate that trajectory archetypes and instances can be created
and that they properly integrate patterns, threads, and scenarios.
"""

import pytest
from semantic_schema.trajectories import (
    TrajectoryDefinition,
    TrajectoryInstance,
    DomainEvolution,
    TrajectoryArchetype,
    TrajectoryPhase,
    create_stable_adaptation_trajectory,
    create_gradual_drift_trajectory,
    create_third_quarter_trajectory,
    create_recovery_renewal_trajectory,
)


def test_domain_evolution_creation():
    """Test creating a domain evolution description."""
    evolution = DomainEvolution(
        domain="physiological",
        description="Sleep remains restorative throughout mission",
        inflection_points=["Initial adaptation", "Mid-mission stabilization"]
    )
    
    assert evolution.domain == "physiological"
    assert evolution.description is not None
    assert len(evolution.inflection_points) == 2


def test_domain_evolution_add_phase():
    """Test adding phase descriptions to domain evolution."""
    evolution = DomainEvolution(
        domain="physiological",
        description="Test"
    )
    
    evolution.add_phase_description("early-mission", "Adaptation phase")
    evolution.add_phase_description("mid-mission", "Stable phase")
    
    assert len(evolution.phase_descriptions) == 2
    assert "early-mission" in evolution.phase_descriptions


def test_trajectory_definition_creation():
    """Test creating a trajectory definition."""
    trajectory = TrajectoryDefinition(
        trajectory_id="traj_001",
        name="Test Trajectory",
        archetype=TrajectoryArchetype.STABLE_ADAPTATION,
        description="A test trajectory",
        narrative_arc="Test narrative arc",
        lived_experience="Test lived experience"
    )
    
    assert trajectory.trajectory_id == "traj_001"
    assert trajectory.archetype == TrajectoryArchetype.STABLE_ADAPTATION
    assert trajectory.narrative_arc is not None
    assert trajectory.lived_experience is not None


def test_trajectory_definition_add_domain_evolution():
    """Test adding domain evolutions to trajectory."""
    trajectory = TrajectoryDefinition(
        trajectory_id="traj_001",
        name="Test",
        archetype=TrajectoryArchetype.STABLE_ADAPTATION,
        description="Test",
        narrative_arc="Test"
    )
    
    evolution = DomainEvolution(
        domain="physiological",
        description="Stable throughout"
    )
    
    trajectory.add_domain_evolution(evolution)
    
    assert len(trajectory.domain_evolutions) == 1
    assert trajectory.domain_evolutions[0].domain == "physiological"


def test_trajectory_definition_add_phase_description():
    """Test adding phase descriptions to trajectory."""
    trajectory = TrajectoryDefinition(
        trajectory_id="traj_001",
        name="Test",
        archetype=TrajectoryArchetype.STABLE_ADAPTATION,
        description="Test",
        narrative_arc="Test"
    )
    
    trajectory.add_phase_description("early-mission", "Initial adaptation")
    trajectory.add_phase_description("mid-mission", "Stable operations")
    
    assert len(trajectory.phase_descriptions) == 2


def test_trajectory_definition_to_narrative():
    """Test generating narrative description of trajectory."""
    trajectory = create_stable_adaptation_trajectory()
    
    narrative = trajectory.to_narrative()
    
    assert "Trajectory: Stable Adaptation Trajectory" in narrative
    assert "Archetype: stable-adaptation" in narrative
    assert "Narrative Arc:" in narrative


def test_trajectory_instance_creation():
    """Test creating a trajectory instance."""
    instance = TrajectoryInstance(
        instance_id="instance_001",
        trajectory_definition_id="traj_001",
        trajectory_name="Test Trajectory",
        mission_id="mission_001",
        scenario_id="scenario_001",
        baseline_id="baseline_001",
        narrative_summary="Test summary"
    )
    
    assert instance.instance_id == "instance_001"
    assert instance.mission_id == "mission_001"
    assert instance.scenario_id == "scenario_001"
    assert instance.baseline_id == "baseline_001"


def test_trajectory_instance_add_pattern():
    """Test adding pattern instances to trajectory instance."""
    instance = TrajectoryInstance(
        instance_id="instance_001",
        trajectory_definition_id="traj_001",
        trajectory_name="Test"
    )
    
    instance.add_pattern_instance("pattern_001")
    instance.add_pattern_instance("pattern_002")
    
    assert len(instance.pattern_instances) == 2
    
    # Adding duplicate should not create duplicate
    instance.add_pattern_instance("pattern_001")
    assert len(instance.pattern_instances) == 2


def test_trajectory_instance_add_thread():
    """Test adding thread instances to trajectory instance."""
    instance = TrajectoryInstance(
        instance_id="instance_001",
        trajectory_definition_id="traj_001",
        trajectory_name="Test"
    )
    
    instance.add_thread_instance("thread_001")
    instance.add_thread_instance("thread_002")
    
    assert len(instance.thread_instances) == 2


def test_trajectory_instance_add_event():
    """Test adding key events to trajectory instance."""
    instance = TrajectoryInstance(
        instance_id="instance_001",
        trajectory_definition_id="traj_001",
        trajectory_name="Test"
    )
    
    instance.add_key_event("event_001")
    instance.add_key_event("event_002")
    
    assert len(instance.key_events) == 2


def test_trajectory_instance_add_observation():
    """Test adding observations to trajectory instance."""
    instance = TrajectoryInstance(
        instance_id="instance_001",
        trajectory_definition_id="traj_001",
        trajectory_name="Test"
    )
    
    instance.add_observation("Observation 1")
    instance.add_observation("Observation 2")
    
    assert len(instance.observations) == 2


def test_trajectory_instance_set_domain_states():
    """Test setting domain states for a phase in trajectory instance."""
    instance = TrajectoryInstance(
        instance_id="instance_001",
        trajectory_definition_id="traj_001",
        trajectory_name="Test"
    )
    
    instance.set_domain_states_for_phase("early-mission", {
        "physiological": "well-rested",
        "cognitive": "clear-and-focused"
    })
    
    instance.set_domain_states_for_phase("mid-mission", {
        "physiological": "adequately-rested",
        "cognitive": "generally-clear"
    })
    
    assert len(instance.domain_states_by_phase) == 2
    assert "early-mission" in instance.domain_states_by_phase


def test_trajectory_instance_to_narrative():
    """Test generating narrative description of trajectory instance."""
    instance = TrajectoryInstance(
        instance_id="instance_001",
        trajectory_definition_id="traj_001",
        trajectory_name="Test Trajectory",
        narrative_summary="Test summary"
    )
    
    narrative = instance.to_narrative()
    
    assert "Trajectory Instance: Test Trajectory" in narrative
    assert "Instance ID: instance_001" in narrative


def test_create_stable_adaptation_trajectory():
    """Test creating stable adaptation trajectory."""
    trajectory = create_stable_adaptation_trajectory()
    
    assert trajectory.trajectory_id == "traj_stable_001"
    assert trajectory.archetype == TrajectoryArchetype.STABLE_ADAPTATION
    assert len(trajectory.domain_evolutions) >= 3
    assert len(trajectory.characteristic_patterns) > 0
    assert len(trajectory.characteristic_threads) > 0
    assert len(trajectory.phase_descriptions) > 0


def test_create_gradual_drift_trajectory():
    """Test creating gradual drift trajectory."""
    trajectory = create_gradual_drift_trajectory()
    
    assert trajectory.trajectory_id == "traj_drift_001"
    assert trajectory.archetype == TrajectoryArchetype.GRADUAL_DRIFT
    assert "drift" in trajectory.name.lower()
    assert len(trajectory.domain_evolutions) >= 3
    assert len(trajectory.characteristic_patterns) > 0


def test_create_third_quarter_trajectory():
    """Test creating third-quarter trajectory."""
    trajectory = create_third_quarter_trajectory()
    
    assert trajectory.trajectory_id == "traj_third_quarter_001"
    assert trajectory.archetype == TrajectoryArchetype.THIRD_QUARTER
    assert "third" in trajectory.name.lower()
    assert len(trajectory.characteristic_patterns) > 0


def test_create_recovery_renewal_trajectory():
    """Test creating recovery-renewal trajectory."""
    trajectory = create_recovery_renewal_trajectory()
    
    assert trajectory.trajectory_id == "traj_recovery_001"
    assert trajectory.archetype == TrajectoryArchetype.RECOVERY_RENEWAL
    assert "recovery" in trajectory.name.lower() or "renewal" in trajectory.name.lower()
    assert len(trajectory.characteristic_patterns) > 0


def test_trajectory_archetype_enum():
    """Test trajectory archetype enum values."""
    assert TrajectoryArchetype.STABLE_ADAPTATION.value == "stable-adaptation"
    assert TrajectoryArchetype.GRADUAL_DRIFT.value == "gradual-drift"
    assert TrajectoryArchetype.DISRUPTION_STABILIZATION.value == "disruption-stabilization"
    assert TrajectoryArchetype.THIRD_QUARTER.value == "third-quarter"
    assert TrajectoryArchetype.CUMULATIVE_STRAIN.value == "cumulative-strain"
    assert TrajectoryArchetype.MEANING_EROSION.value == "meaning-erosion"
    assert TrajectoryArchetype.RECOVERY_RENEWAL.value == "recovery-renewal"
    assert TrajectoryArchetype.DIVERGENT_CREW.value == "divergent-crew"


def test_trajectory_phase_enum():
    """Test trajectory phase enum values."""
    assert TrajectoryPhase.EARLY_MISSION.value == "early-mission"
    assert TrajectoryPhase.MID_MISSION.value == "mid-mission"
    assert TrajectoryPhase.THIRD_QUARTER.value == "third-quarter"
    assert TrajectoryPhase.LATE_MISSION.value == "late-mission"


def test_trajectory_with_phase3_references():
    """Test that trajectories include Phase 3 references."""
    trajectory = create_stable_adaptation_trajectory()
    
    assert len(trajectory.phase3_references) > 0
    assert any("Phase 3" in ref for ref in trajectory.phase3_references)


def test_trajectory_with_inflection_points():
    """Test that trajectories include inflection points."""
    trajectory = create_stable_adaptation_trajectory()
    
    assert len(trajectory.inflection_points) > 0


def test_trajectory_with_variation_notes():
    """Test that trajectories include variation notes."""
    trajectory = create_stable_adaptation_trajectory()
    
    assert len(trajectory.variation_notes) > 0


def test_trajectory_with_related_scenarios():
    """Test that trajectories link to related scenarios."""
    trajectory = create_stable_adaptation_trajectory()
    
    assert len(trajectory.related_scenarios) > 0


def test_domain_evolution_in_trajectory():
    """Test that domain evolutions are properly integrated."""
    trajectory = create_stable_adaptation_trajectory()
    
    assert len(trajectory.domain_evolutions) > 0
    
    for evolution in trajectory.domain_evolutions:
        assert evolution.domain is not None
        assert evolution.description is not None


def test_trajectory_instance_comprehensive():
    """Test creating a comprehensive trajectory instance."""
    instance = TrajectoryInstance(
        instance_id="instance_001",
        trajectory_definition_id="traj_001",
        trajectory_name="Test Trajectory",
        mission_id="mission_001",
        scenario_id="scenario_001",
        baseline_id="baseline_001",
        narrative_summary="Comprehensive test",
        classification_rationale="Rationale for classification"
    )
    
    instance.add_pattern_instance("pattern_001")
    instance.add_thread_instance("thread_001")
    instance.add_key_event("event_001")
    instance.add_observation("Test observation")
    instance.set_domain_states_for_phase("mid-mission", {
        "physiological": "adequately-rested"
    })
    
    assert len(instance.pattern_instances) == 1
    assert len(instance.thread_instances) == 1
    assert len(instance.key_events) == 1
    assert len(instance.observations) == 1
    assert len(instance.domain_states_by_phase) == 1
    assert instance.classification_rationale is not None
