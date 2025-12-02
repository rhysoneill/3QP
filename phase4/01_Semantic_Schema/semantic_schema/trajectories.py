"""
Trajectory Schema

Defines data structures for trajectory archetypes and instances. Trajectories
describe whole-mission narrative arcs that integrate baseline states, scenarios,
patterns, and threads. Corresponds to Phase 3, Workstream 5.

Key concepts:
- TrajectoryArchetype: Major qualitative trajectory patterns (stable, drift, etc.)
- TrajectoryInstance: A specific mission's trajectory characterization
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class TrajectoryArchetype(str, Enum):
    """
    Major trajectory archetypes from Phase 3, Workstream 5.
    """
    STABLE_ADAPTATION = "stable-adaptation"
    GRADUAL_DRIFT = "gradual-drift"
    DISRUPTION_STABILIZATION = "disruption-stabilization"
    THIRD_QUARTER = "third-quarter"
    CUMULATIVE_STRAIN = "cumulative-strain"
    MEANING_EROSION = "meaning-erosion"
    RECOVERY_RENEWAL = "recovery-renewal"
    DIVERGENT_CREW = "divergent-crew"
    CUSTOM = "custom"


class TrajectoryPhase(str, Enum):
    """Common trajectory phases (qualitative, not time-based)."""
    EARLY_MISSION = "early-mission"
    TRANSITION = "transition"
    MID_MISSION = "mid-mission"
    THIRD_QUARTER = "third-quarter"
    LATE_MISSION = "late-mission"
    CRITICAL_PHASE = "critical-phase"
    RESOLUTION = "resolution"
    COMPLETION = "completion"


@dataclass
class DomainEvolution:
    """
    Describes how a domain evolves across a trajectory.
    
    This is qualitative, not numeric—describing the character of change.
    """
    domain: str
    description: str
    
    # Phases of evolution (qualitative descriptors)
    phase_descriptions: Dict[str, str] = field(default_factory=dict)
    
    # Key transitions or inflection points
    inflection_points: List[str] = field(default_factory=list)
    
    def add_phase_description(self, phase: str, description: str) -> None:
        """Add a description of how this domain behaves in a specific phase."""
        self.phase_descriptions[phase] = description


@dataclass
class TrajectoryDefinition:
    """
    Defines a trajectory archetype—a recurring narrative arc that characterizes
    how missions unfold across all domains.
    
    Trajectories are the highest-level interpretive framework in the semantic
    schema, integrating baseline states, scenarios, patterns, and threads into
    coherent whole-mission narratives.
    """
    trajectory_id: str
    name: str
    archetype: TrajectoryArchetype
    description: str
    
    # Narrative arc
    narrative_arc: str
    
    # Domain evolutions across this trajectory
    domain_evolutions: List[DomainEvolution] = field(default_factory=list)
    
    # Patterns typically seen in this trajectory
    characteristic_patterns: List[str] = field(default_factory=list)
    
    # Threads typically active in this trajectory
    characteristic_threads: List[str] = field(default_factory=list)
    
    # Scenarios that commonly lead to this trajectory
    related_scenarios: List[str] = field(default_factory=list)
    
    # Qualitative phases
    phase_descriptions: Dict[str, str] = field(default_factory=dict)
    
    # Lived experience description
    lived_experience: Optional[str] = None
    
    # Potential inflection points
    inflection_points: List[str] = field(default_factory=list)
    
    # Variations across individuals/missions
    variation_notes: List[str] = field(default_factory=list)
    
    # References to Phase 3 documentation
    phase3_references: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def add_domain_evolution(self, evolution: DomainEvolution) -> None:
        """Add a domain evolution description to this trajectory."""
        self.domain_evolutions.append(evolution)
    
    def add_phase_description(self, phase: str, description: str) -> None:
        """Add a phase description to the trajectory."""
        self.phase_descriptions[phase] = description
    
    def to_narrative(self) -> str:
        """Generate a comprehensive narrative description of the trajectory."""
        lines = [
            f"Trajectory: {self.name}",
            f"Archetype: {self.archetype.value}",
            "",
            f"Description: {self.description}",
            "",
            f"Narrative Arc:",
            f"{self.narrative_arc}",
            "",
        ]
        
        if self.lived_experience:
            lines.append(f"Lived Experience:")
            lines.append(f"{self.lived_experience}")
            lines.append("")
        
        if self.phase_descriptions:
            lines.append("Trajectory Phases:")
            for phase, desc in self.phase_descriptions.items():
                lines.append(f"\n{phase}:")
                lines.append(f"  {desc}")
            lines.append("")
        
        if self.domain_evolutions:
            lines.append("Domain Evolutions:")
            for evolution in self.domain_evolutions:
                lines.append(f"\n{evolution.domain.title()}:")
                lines.append(f"  {evolution.description}")
                if evolution.phase_descriptions:
                    for phase, desc in evolution.phase_descriptions.items():
                        lines.append(f"  {phase}: {desc}")
            lines.append("")
        
        if self.characteristic_patterns:
            lines.append("Characteristic Patterns:")
            for pattern in self.characteristic_patterns:
                lines.append(f"  - {pattern}")
            lines.append("")
        
        if self.characteristic_threads:
            lines.append("Characteristic Threads:")
            for thread in self.characteristic_threads:
                lines.append(f"  - {thread}")
            lines.append("")
        
        if self.inflection_points:
            lines.append("Potential Inflection Points:")
            for point in self.inflection_points:
                lines.append(f"  - {point}")
            lines.append("")
        
        if self.variation_notes:
            lines.append("Variation Notes:")
            for note in self.variation_notes:
                lines.append(f"  - {note}")
            lines.append("")
        
        if self.related_scenarios:
            scenarios = ", ".join(self.related_scenarios)
            lines.append(f"Related Scenarios: {scenarios}")
            lines.append("")
        
        if self.phase3_references:
            lines.append("Phase 3 References:")
            for ref in self.phase3_references:
                lines.append(f"  - {ref}")
        
        return "\n".join(lines)


@dataclass
class TrajectoryInstance:
    """
    A specific mission's trajectory—a characterization of how that particular
    mission unfolded across domains.
    
    This links the abstract trajectory archetype to a concrete mission context.
    """
    instance_id: str
    trajectory_definition_id: str
    trajectory_name: str
    
    # Mission context
    mission_id: Optional[str] = None
    mission_description: Optional[str] = None
    scenario_id: Optional[str] = None
    
    # Baseline reference
    baseline_id: Optional[str] = None
    
    # Pattern instances that occurred
    pattern_instances: List[str] = field(default_factory=list)
    
    # Thread instances that were active
    thread_instances: List[str] = field(default_factory=list)
    
    # Key events along the trajectory
    key_events: List[str] = field(default_factory=list)
    
    # Narrative summary of this specific trajectory
    narrative_summary: Optional[str] = None
    
    # Rationale for trajectory classification
    classification_rationale: Optional[str] = None
    
    # Domain states at key phases
    domain_states_by_phase: Dict[str, Dict[str, str]] = field(default_factory=dict)
    
    # Observations and notes
    observations: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def add_pattern_instance(self, pattern_instance_id: str) -> None:
        """Link a pattern instance to this trajectory."""
        if pattern_instance_id not in self.pattern_instances:
            self.pattern_instances.append(pattern_instance_id)
    
    def add_thread_instance(self, thread_instance_id: str) -> None:
        """Link a thread instance to this trajectory."""
        if thread_instance_id not in self.thread_instances:
            self.thread_instances.append(thread_instance_id)
    
    def add_key_event(self, event_id: str) -> None:
        """Add a key event to the trajectory."""
        if event_id not in self.key_events:
            self.key_events.append(event_id)
    
    def add_observation(self, observation: str) -> None:
        """Add an observation about this trajectory instance."""
        self.observations.append(observation)
    
    def set_domain_states_for_phase(self, phase: str, domain_states: Dict[str, str]) -> None:
        """Record domain states at a specific phase."""
        self.domain_states_by_phase[phase] = domain_states
    
    def to_narrative(self) -> str:
        """Generate a narrative description of this trajectory instance."""
        lines = [
            f"Trajectory Instance: {self.trajectory_name}",
            f"Instance ID: {self.instance_id}",
            "",
        ]
        
        if self.mission_id:
            lines.append(f"Mission: {self.mission_id}")
        
        if self.mission_description:
            lines.append(f"Description: {self.mission_description}")
        
        if self.scenario_id:
            lines.append(f"Scenario: {self.scenario_id}")
        
        if self.baseline_id:
            lines.append(f"Baseline: {self.baseline_id}")
        
        lines.append("")
        
        if self.narrative_summary:
            lines.append(f"Summary:")
            lines.append(f"{self.narrative_summary}")
            lines.append("")
        
        if self.classification_rationale:
            lines.append(f"Rationale:")
            lines.append(f"{self.classification_rationale}")
            lines.append("")
        
        if self.observations:
            lines.append("Observations:")
            for obs in self.observations:
                lines.append(f"  - {obs}")
            lines.append("")
        
        if self.key_events:
            lines.append(f"Key Events ({len(self.key_events)}):")
            for event in self.key_events:
                lines.append(f"  - {event}")
            lines.append("")
        
        if self.pattern_instances:
            lines.append(f"Pattern Instances ({len(self.pattern_instances)}):")
            for pattern in self.pattern_instances:
                lines.append(f"  - {pattern}")
            lines.append("")
        
        if self.thread_instances:
            lines.append(f"Thread Instances ({len(self.thread_instances)}):")
            for thread in self.thread_instances:
                lines.append(f"  - {thread}")
            lines.append("")
        
        if self.domain_states_by_phase:
            lines.append("Domain States by Phase:")
            for phase, states in self.domain_states_by_phase.items():
                lines.append(f"\n{phase}:")
                for domain, state in states.items():
                    lines.append(f"  {domain}: {state}")
        
        return "\n".join(lines)


def create_stable_adaptation_trajectory() -> TrajectoryDefinition:
    """
    Create the Stable Adaptation Trajectory from Phase 3, Workstream 5.
    """
    trajectory = TrajectoryDefinition(
        trajectory_id="traj_stable_001",
        name="Stable Adaptation Trajectory",
        archetype=TrajectoryArchetype.STABLE_ADAPTATION,
        description=(
            "The crew transitions smoothly from departure into a sustained state "
            "of effective functioning. Early challenges are absorbed with minimal "
            "disruption. All domains maintain coherence throughout."
        ),
        narrative_arc=(
            "The mission proceeds smoothly through all phases, with the crew "
            "maintaining functional performance and positive dynamics from start "
            "to completion. Challenges are real but navigable."
        ),
        lived_experience=(
            "The mission feels manageable. Crews describe a sense of flow, rhythm, "
            "and competence. The crew feels connected—to each other, to the mission, "
            "to themselves. There is a quiet confidence that the mission is "
            "unfolding as it should."
        ),
        characteristic_patterns=[
            "High coherence",
            "Balanced engagement",
            "Relational stability",
            "Adaptive responsiveness",
        ],
        characteristic_threads=[
            "Stable physiological baselines",
            "Preserved meaning and purpose",
            "Deepening trust and cohesion",
            "Sustained cognitive flexibility",
        ],
        related_scenarios=[
            "Nominal Mission Scenario",
        ],
        inflection_points=[
            "Unexpected events that test adaptability",
            "Relational challenges requiring navigation",
            "Subtle drift requiring intentional renewal",
        ],
        variation_notes=[
            "Not all crew members experience trajectory identically",
            "Mission design affects likelihood of stable adaptation",
            "Stable trajectories are actively sustained, not static",
        ],
        phase3_references=[
            "Phase 3, Workstream 5: Trajectory Archetypes",
            "Phase 3, Workstream 5: A. Stable Adaptation Trajectory",
        ],
    )
    
    # Domain evolutions
    phys_evolution = DomainEvolution(
        domain="physiological",
        description=(
            "Sleep remains restorative; circadian rhythms stabilize; energy levels "
            "fluctuate within tolerable ranges; physical health is sustained."
        ),
    )
    phys_evolution.add_phase_description(
        TrajectoryPhase.EARLY_MISSION.value,
        "Initial adaptation to space environment proceeds smoothly"
    )
    phys_evolution.add_phase_description(
        TrajectoryPhase.MID_MISSION.value,
        "Physiological functioning stabilizes into sustainable patterns"
    )
    phys_evolution.add_phase_description(
        TrajectoryPhase.LATE_MISSION.value,
        "Physical capacity maintained through mission completion"
    )
    trajectory.add_domain_evolution(phys_evolution)
    
    cog_evolution = DomainEvolution(
        domain="cognitive",
        description=(
            "Attention, memory, and decision-making remain flexible and adaptive; "
            "reflective capacity is preserved."
        ),
    )
    trajectory.add_domain_evolution(cog_evolution)
    
    social_evolution = DomainEvolution(
        domain="social",
        description=(
            "Trust, communication, and mutual support deepen; conflicts are "
            "navigated constructively."
        ),
    )
    trajectory.add_domain_evolution(social_evolution)
    
    # Phase descriptions
    trajectory.add_phase_description(
        TrajectoryPhase.EARLY_MISSION.value,
        "Crew settles into mission environment, establishing routines and "
        "refining communication patterns"
    )
    trajectory.add_phase_description(
        TrajectoryPhase.MID_MISSION.value,
        "Mission enters plateau phase of predictable routines, stable social "
        "functioning, and consistent performance"
    )
    trajectory.add_phase_description(
        TrajectoryPhase.LATE_MISSION.value,
        "Anticipation of completion strengthens cohesion; crew demonstrates "
        "mature competence"
    )
    
    return trajectory


def create_gradual_drift_trajectory() -> TrajectoryDefinition:
    """
    Create the Gradual Drift Trajectory from Phase 3, Workstream 5.
    """
    trajectory = TrajectoryDefinition(
        trajectory_id="traj_drift_001",
        name="Gradual Drift Trajectory",
        archetype=TrajectoryArchetype.GRADUAL_DRIFT,
        description=(
            "The mission begins smoothly, but across the lifecycle, a slow erosion "
            "emerges. Sleep becomes less restorative; cognitive sharpness dulls; "
            "emotional tone flattens; social interactions become more effortful."
        ),
        narrative_arc=(
            "No single event precipitates the drift. Instead, the cumulative weight "
            "of isolation, confinement, and distance gradually narrows the crew's "
            "inner and outer worlds. The drift is subtle enough that crews may not "
            "recognize it until well into the mission."
        ),
        lived_experience=(
            "The mission feels manageable but diminished. Crews describe functioning "
            "on autopilot—going through the motions without the vitality that "
            "characterized earlier phases. There is no crisis, but there is a quiet "
            "loss of color, energy, and meaning."
        ),
        characteristic_patterns=[
            "Progressive sleep disruption",
            "Cognitive narrowing",
            "Emotional withdrawal",
            "Motivational drift",
            "Relational detachment",
        ],
        characteristic_threads=[
            "Gradual meaning erosion",
            "Incremental withdrawal from engagement",
            "Cognitive narrowing under chronic demand",
        ],
        related_scenarios=[
            "Third-Quarter Phenomenon Scenario",
        ],
        inflection_points=[
            "Recognition moments when drift is named",
            "External stimulation that interrupts drift",
            "Endogenous recovery through unexpected insight",
        ],
        variation_notes=[
            "Some crew members drift more profoundly than others",
            "Mission design can mitigate or exacerbate drift",
            "Longer missions may be more vulnerable",
        ],
        phase3_references=[
            "Phase 3, Workstream 5: Trajectory Archetypes",
            "Phase 3, Workstream 5: B. Gradual Drift Trajectory",
        ],
    )
    
    # Domain evolutions
    phys_evolution = DomainEvolution(
        domain="physiological",
        description=(
            "Sleep quality declines incrementally; energy levels lower; physical "
            "vitality feels muted."
        ),
        inflection_points=[
            "Transition from adequate to moderately disrupted sleep",
            "Accumulation of fatigue becomes noticeable",
        ],
    )
    trajectory.add_domain_evolution(phys_evolution)
    
    cog_evolution = DomainEvolution(
        domain="cognitive",
        description=(
            "Attention narrows; cognitive flexibility decreases; reflective "
            "capacity diminishes; thinking becomes more rigid."
        ),
    )
    trajectory.add_domain_evolution(cog_evolution)
    
    emot_evolution = DomainEvolution(
        domain="emotional",
        description=(
            "Emotional range compresses; feelings flatten into mild negativity or "
            "numbness; meaning and purpose drift out of focus."
        ),
    )
    trajectory.add_domain_evolution(emot_evolution)
    
    # Phase descriptions
    trajectory.add_phase_description(
        TrajectoryPhase.EARLY_MISSION.value,
        "Mission proceeds smoothly with no indication of coming drift"
    )
    trajectory.add_phase_description(
        TrajectoryPhase.MID_MISSION.value,
        "Subtle erosion begins—imperceptible at first, cumulative over time"
    )
    trajectory.add_phase_description(
        TrajectoryPhase.LATE_MISSION.value,
        "Crews describe being 'not quite themselves'—functional but diminished"
    )
    
    return trajectory


def create_third_quarter_trajectory() -> TrajectoryDefinition:
    """
    Create the Third-Quarter Trajectory from Phase 3, Workstream 5.
    """
    return TrajectoryDefinition(
        trajectory_id="traj_third_quarter_001",
        name="Third-Quarter Phenomenon Trajectory",
        archetype=TrajectoryArchetype.THIRD_QUARTER,
        description=(
            "The mission begins with energy and purpose, proceeds through early "
            "adaptation, then enters a mid-mission slump characterized by temporal "
            "disengagement, motivational drift, and social fatigue."
        ),
        narrative_arc=(
            "Somewhere in the latter-middle stretch, energy wanes; purpose feels "
            "distant; engagement becomes effortful. The end is too far to motivate; "
            "the beginning too distant to sustain novelty. This is the psychological "
            "slump of being stuck in the middle."
        ),
        lived_experience=(
            "The mission feels endless and effortful. Crews describe being worn down "
            "not by dramatic challenges but by the sheer weight of continuation. "
            "There is a quiet longing for change, for relief, for something to "
            "interrupt the monotony."
        ),
        characteristic_patterns=[
            "Temporal disengagement",
            "Motivational drift",
            "Social fatigue",
            "Cognitive disengagement",
            "Emotional flattening",
        ],
        characteristic_threads=[
            "Mid-mission meaning erosion",
            "Progressive withdrawal from social engagement",
        ],
        related_scenarios=[
            "Third-Quarter Phenomenon Scenario",
        ],
        inflection_points=[
            "Meaningful milestones that mark progress",
            "Intentional renewal interventions",
            "Relational deepening moments",
            "Anticipation as endpoint approaches",
        ],
        variation_notes=[
            "Not all missions exhibit distinct third-quarter dynamics",
            "Crew members may experience slump at different moments",
            "Mission design can mitigate third-quarter effect",
        ],
        phase3_references=[
            "Phase 3, Workstream 5: Trajectory Archetypes",
            "Phase 3, Workstream 5: D. Third-Quarter Trajectory",
        ],
    )


def create_recovery_renewal_trajectory() -> TrajectoryDefinition:
    """
    Create the Recovery-Renewal Trajectory from Phase 3, Workstream 5.
    """
    return TrajectoryDefinition(
        trajectory_id="traj_recovery_001",
        name="Recovery–Renewal Trajectory",
        archetype=TrajectoryArchetype.RECOVERY_RENEWAL,
        description=(
            "The mission begins in a state of strain or depletion, but rather than "
            "continuing along a trajectory of decline, the arc shifts. Recovery "
            "begins and renewal follows—crews rediscover purpose, vitality, and "
            "connection."
        ),
        narrative_arc=(
            "This trajectory describes rebound and regeneration—the movement from "
            "constraint or depletion back toward coherence, resilience, and wholeness. "
            "It demonstrates that trajectories are not fixed."
        ),
        lived_experience=(
            "The mission feels revitalized. Crews describe coming back to themselves, "
            "rediscovering energy and clarity that had been lost. There is often "
            "surprise at the shift—recognition that recovery is possible."
        ),
        characteristic_patterns=[
            "Physiological recovery",
            "Cognitive reawakening",
            "Emotional renewal",
            "Relational repair",
        ],
        characteristic_threads=[
            "Restored meaning and purpose",
            "Relational deepening and repair",
            "Cognitive flexibility restoration",
        ],
        inflection_points=[
            "Structured interventions creating space for recovery",
            "Relational turning points restoring trust",
            "External stimulation providing renewal",
            "Endogenous resilience emerging spontaneously",
        ],
        variation_notes=[
            "Recovery may unfold at different rates for different crew members",
            "Some domains may recover more fully than others",
            "Not all strained trajectories ultimately recover",
        ],
        phase3_references=[
            "Phase 3, Workstream 5: Trajectory Archetypes",
            "Phase 3, Workstream 5: G. Recovery–Renewal Trajectory",
        ],
    )
