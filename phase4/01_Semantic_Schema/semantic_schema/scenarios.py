"""
Scenario Schema

Defines data structures for scenario templates and event descriptors.
Scenarios describe sequences of events and stressors that challenge baseline
functioning, corresponding to Phase 3, Workstream 2.

Key concepts:
- ScenarioTemplate: Overall scenario structure (nominal, disruption, third-quarter)
- EventDescriptor: Individual events within a scenario
- EventStoryline: Ordered sequence of events forming a narrative arc
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class ScenarioType(str, Enum):
    """Types of scenario templates from Phase 3, Workstream 2."""
    NOMINAL_MISSION = "nominal-mission"
    STRESSOR_DRIVEN_DISRUPTION = "stressor-driven-disruption"
    THIRD_QUARTER_PHENOMENON = "third-quarter-phenomenon"
    CUSTOM = "custom"


class EventCategory(str, Enum):
    """Categories of events that can occur during scenarios."""
    OPERATIONAL = "operational"  # Equipment, procedures, mission tasks
    SOCIAL = "social"  # Interpersonal, communication, relationships
    ENVIRONMENTAL = "environmental"  # Habitat, external conditions
    COGNITIVE = "cognitive"  # Information, ambiguity, complexity
    EMOTIONAL = "emotional"  # Mood, affect, psychological experiences
    PHYSIOLOGICAL = "physiological"  # Health, sleep, physical demands
    COMBINED = "combined"  # Events affecting multiple categories


class EventIntensity(str, Enum):
    """Qualitative intensity levels for events."""
    MINIMAL = "minimal"
    MILD = "mild"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    SEVERE = "severe"
    CRITICAL = "critical"


class TemporalCharacter(str, Enum):
    """Temporal patterns of events from Phase 3 Reference States."""
    BRIEF_AND_TRANSIENT = "brief-and-transient"  # Moments to hours
    EPISODIC = "episodic"  # Recurs periodically with recovery
    SUSTAINED = "sustained"  # Days to weeks without respite
    CHRONIC = "chronic"  # Months without resolution
    ACCUMULATING = "accumulating"  # Compounds over time


@dataclass
class EventDescriptor:
    """
    Describes a discrete event within a scenario.
    
    Events are the inputs to the crew system—things that happen to crews
    that challenge, disrupt, support, or test functioning.
    """
    event_id: str
    name: str
    description: str
    category: EventCategory
    
    # Qualitative characteristics
    intensity: EventIntensity
    temporal_character: TemporalCharacter
    
    # Thematic tags
    dominant_themes: List[str] = field(default_factory=list)
    affected_domains: List[str] = field(default_factory=list)
    
    # Narrative context
    narrative_context: Optional[str] = None
    expected_impact: Optional[str] = None
    
    # Optional metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def to_narrative(self) -> str:
        """Generate a narrative description of the event."""
        lines = [
            f"Event: {self.name}",
            f"Category: {self.category.value}",
            f"Intensity: {self.intensity.value}",
            f"Temporal: {self.temporal_character.value}",
            "",
            f"Description: {self.description}",
        ]
        
        if self.dominant_themes:
            themes = ", ".join(self.dominant_themes)
            lines.append(f"Themes: {themes}")
        
        if self.affected_domains:
            domains = ", ".join(self.affected_domains)
            lines.append(f"Affected Domains: {domains}")
        
        if self.narrative_context:
            lines.append(f"\nContext: {self.narrative_context}")
        
        if self.expected_impact:
            lines.append(f"Expected Impact: {self.expected_impact}")
        
        return "\n".join(lines)


@dataclass
class EventStoryline:
    """
    An ordered sequence of events forming a scenario's narrative arc.
    
    The storyline can later be mapped to time, but does not require
    time units at this semantic level.
    """
    storyline_id: str
    name: str
    description: str
    
    # Ordered sequence of events
    events: List[EventDescriptor] = field(default_factory=list)
    
    # Qualitative phase markers (not time-based)
    phase_markers: List[str] = field(default_factory=list)
    
    # Narrative arc description
    arc_description: Optional[str] = None
    
    def add_event(self, event: EventDescriptor) -> None:
        """Add an event to the storyline."""
        self.events.append(event)
    
    def get_events_by_category(self, category: EventCategory) -> List[EventDescriptor]:
        """Retrieve all events of a specific category."""
        return [e for e in self.events if e.category == category]
    
    def get_events_by_intensity(self, intensity: EventIntensity) -> List[EventDescriptor]:
        """Retrieve all events of a specific intensity."""
        return [e for e in self.events if e.intensity == intensity]
    
    def to_narrative(self) -> str:
        """Generate a narrative summary of the storyline."""
        lines = [
            f"Storyline: {self.name}",
            f"Description: {self.description}",
            "",
        ]
        
        if self.arc_description:
            lines.append(f"Arc: {self.arc_description}")
            lines.append("")
        
        if self.phase_markers:
            lines.append("Phase Markers:")
            for marker in self.phase_markers:
                lines.append(f"  - {marker}")
            lines.append("")
        
        lines.append(f"Events ({len(self.events)} total):")
        for i, event in enumerate(self.events, 1):
            lines.append(f"\n{i}. {event.name}")
            lines.append(f"   {event.description}")
            lines.append(f"   [{event.category.value}, {event.intensity.value}]")
        
        return "\n".join(lines)


@dataclass
class ScenarioTemplate:
    """
    A scenario template describing mission conditions, crew states, and
    environmental pressures as they evolve over a mission.
    
    Templates correspond to the three main scenarios from Phase 3, Workstream 2:
    - Nominal Mission
    - Stressor-Driven Disruption
    - Third-Quarter Phenomenon
    
    Or custom scenarios built from these foundations.
    """
    template_id: str
    name: str
    scenario_type: ScenarioType
    description: str
    
    # Event storyline
    storyline: Optional[EventStoryline] = None
    
    # Qualitative characteristics
    dominant_pressures: List[str] = field(default_factory=list)
    dominant_themes: List[str] = field(default_factory=list)
    
    # Starting conditions reference
    baseline_reference: Optional[str] = None
    starting_conditions_description: Optional[str] = None
    
    # Expected adaptations and frictions
    expected_adaptations: List[str] = field(default_factory=list)
    expected_frictions: List[str] = field(default_factory=list)
    
    # Domain trajectory expectations (qualitative)
    domain_trajectory_descriptions: Dict[str, str] = field(default_factory=dict)
    
    # Narrative components
    narrative_arc: Optional[str] = None
    phase_descriptions: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def add_phase_description(self, phase_name: str, description: str) -> None:
        """Add a qualitative phase description to the scenario."""
        self.phase_descriptions[phase_name] = description
    
    def add_domain_trajectory(self, domain: str, description: str) -> None:
        """Add a qualitative trajectory description for a domain."""
        self.domain_trajectory_descriptions[domain] = description
    
    def to_narrative(self) -> str:
        """Generate a comprehensive narrative description of the scenario."""
        lines = [
            f"Scenario Template: {self.name}",
            f"Type: {self.scenario_type.value}",
            "",
            f"Description: {self.description}",
            "",
        ]
        
        if self.baseline_reference:
            lines.append(f"Baseline Reference: {self.baseline_reference}")
        
        if self.starting_conditions_description:
            lines.append(f"Starting Conditions: {self.starting_conditions_description}")
        
        lines.append("")
        
        if self.dominant_pressures:
            lines.append("Dominant Pressures:")
            for pressure in self.dominant_pressures:
                lines.append(f"  - {pressure}")
            lines.append("")
        
        if self.dominant_themes:
            lines.append("Dominant Themes:")
            for theme in self.dominant_themes:
                lines.append(f"  - {theme}")
            lines.append("")
        
        if self.narrative_arc:
            lines.append(f"Narrative Arc:")
            lines.append(f"{self.narrative_arc}")
            lines.append("")
        
        if self.phase_descriptions:
            lines.append("Phase Descriptions:")
            for phase, desc in self.phase_descriptions.items():
                lines.append(f"\n{phase}:")
                lines.append(f"  {desc}")
            lines.append("")
        
        if self.expected_adaptations:
            lines.append("Expected Adaptations:")
            for adaptation in self.expected_adaptations:
                lines.append(f"  - {adaptation}")
            lines.append("")
        
        if self.expected_frictions:
            lines.append("Expected Frictions:")
            for friction in self.expected_frictions:
                lines.append(f"  - {friction}")
            lines.append("")
        
        if self.domain_trajectory_descriptions:
            lines.append("Domain Trajectories:")
            for domain, desc in self.domain_trajectory_descriptions.items():
                lines.append(f"\n{domain}:")
                lines.append(f"  {desc}")
            lines.append("")
        
        if self.storyline:
            lines.append("=" * 60)
            lines.append(self.storyline.to_narrative())
        
        return "\n".join(lines)


def create_nominal_scenario() -> ScenarioTemplate:
    """
    Create a nominal mission scenario template from Phase 3, Workstream 2.
    """
    storyline = EventStoryline(
        storyline_id="storyline_nominal_001",
        name="Nominal Mission Storyline",
        description="Stable, well-functioning mission arc with predictable challenges",
        phase_markers=[
            "Early Mission Phase: Settlement and routine establishment",
            "Mid-Mission Stability: Plateau of steady operations",
            "Late Mission Phase: Anticipation and completion focus",
        ],
        arc_description=(
            "The mission proceeds smoothly from departure through stable "
            "operations to successful completion, with challenges absorbed "
            "within normal adaptive capacity."
        ),
    )
    
    # Add representative events
    storyline.add_event(EventDescriptor(
        event_id="event_nominal_001",
        name="Routine System Maintenance",
        description="Regular maintenance tasks as scheduled",
        category=EventCategory.OPERATIONAL,
        intensity=EventIntensity.MINIMAL,
        temporal_character=TemporalCharacter.EPISODIC,
        dominant_themes=["routine operations", "competence maintenance"],
        affected_domains=["operational", "cognitive"],
        narrative_context="Part of regular mission operations",
    ))
    
    storyline.add_event(EventDescriptor(
        event_id="event_nominal_002",
        name="Crew Social Activity",
        description="Scheduled crew bonding and recreational time",
        category=EventCategory.SOCIAL,
        intensity=EventIntensity.MINIMAL,
        temporal_character=TemporalCharacter.EPISODIC,
        dominant_themes=["cohesion maintenance", "mutual support"],
        affected_domains=["social", "emotional"],
        narrative_context="Planned social support activities",
    ))
    
    return ScenarioTemplate(
        template_id="scenario_nominal_001",
        name="Nominal Mission Scenario",
        scenario_type=ScenarioType.NOMINAL_MISSION,
        description=(
            "A stable, well-functioning mission arc where operations proceed "
            "as planned, crew members adapt successfully, social relationships "
            "remain cooperative, and workload remains manageable."
        ),
        storyline=storyline,
        baseline_reference="baseline_nominal_001",
        starting_conditions_description=(
            "Mission begins from baseline state with crew well-rested, "
            "cognitively clear, socially cohesive, and operating within "
            "manageable workload conditions."
        ),
        dominant_pressures=[
            "Routine maintenance",
            "Gradual adaptation to isolation",
            "Social stability under proximity",
            "Manageable monotony",
        ],
        dominant_themes=[
            "Sustained competence",
            "Social calibration",
            "Environmental familiarity",
            "Routine refinement",
        ],
        expected_adaptations=[
            "Routine refinement and efficiency",
            "Social calibration into comfortable patterns",
            "Environmental normalization",
            "Role mastery and confidence",
        ],
        expected_frictions=[
            "Minor interpersonal adjustments",
            "Occasional monotony challenges",
        ],
        narrative_arc=(
            "The crew transitions smoothly through mission phases, maintaining "
            "functional performance and positive dynamics from start to completion."
        ),
    )


def create_disruption_scenario() -> ScenarioTemplate:
    """
    Create a stressor-driven disruption scenario template from Phase 3, Workstream 2.
    """
    storyline = EventStoryline(
        storyline_id="storyline_disruption_001",
        name="Disruption Storyline",
        description="Mission encounters escalating pressures challenging baseline functioning",
        phase_markers=[
            "Baseline to Emergence: Initial smooth operations with subtle indicators",
            "Escalation: Triggering events introduce disruption",
            "Intensification: Strain accumulates across domains",
            "Critical Phase: Peak strain requiring adaptive response",
            "Resolution: Recovery or stabilization at new equilibrium",
        ],
        arc_description=(
            "The crew encounters escalating stressors that destabilize functioning, "
            "requiring adaptive responses to recover or stabilize."
        ),
    )
    
    # Add representative events
    storyline.add_event(EventDescriptor(
        event_id="event_disruption_001",
        name="Equipment Malfunction",
        description="Critical system requires extended repair effort",
        category=EventCategory.OPERATIONAL,
        intensity=EventIntensity.SIGNIFICANT,
        temporal_character=TemporalCharacter.SUSTAINED,
        dominant_themes=["operational pressure", "uncertainty", "workload spike"],
        affected_domains=["operational", "cognitive", "workload", "physiological"],
        narrative_context="Unexpected failure requiring immediate response",
        expected_impact=(
            "Increases workload, disrupts sleep, creates cognitive strain, "
            "tests problem-solving capacity"
        ),
    ))
    
    storyline.add_event(EventDescriptor(
        event_id="event_disruption_002",
        name="Interpersonal Conflict",
        description="Disagreement over repair priorities escalates",
        category=EventCategory.SOCIAL,
        intensity=EventIntensity.MODERATE,
        temporal_character=TemporalCharacter.EPISODIC,
        dominant_themes=["social friction", "trust erosion", "communication strain"],
        affected_domains=["social", "emotional", "cognitive"],
        narrative_context="Stress amplifies latent tensions",
        expected_impact="Weakens cohesion, strains communication, increases emotional reactivity",
    ))
    
    return ScenarioTemplate(
        template_id="scenario_disruption_001",
        name="Stressor-Driven Disruption Scenario",
        scenario_type=ScenarioType.STRESSOR_DRIVEN_DISRUPTION,
        description=(
            "A mission arc where the crew encounters escalating pressures that "
            "challenge baseline functioning through operational complications, "
            "equipment issues, interpersonal strain, or compounding stressors."
        ),
        storyline=storyline,
        baseline_reference="baseline_nominal_001",
        starting_conditions_description=(
            "Mission begins from baseline state, identical to nominal scenario, "
            "with distinction emerging as events unfold."
        ),
        dominant_pressures=[
            "Compounding demands",
            "Resource depletion",
            "Uncertainty and ambiguity",
            "Social friction under stress",
            "Adaptive challenge",
        ],
        dominant_themes=[
            "Resilience testing",
            "Creative problem-solving",
            "Trust under pressure",
            "Cognitive reprioritization",
        ],
        expected_adaptations=[
            "Creative problem-solving",
            "Social mobilization and mutual support",
            "Cognitive reprioritization",
            "Leadership activation",
        ],
        expected_frictions=[
            "Interpersonal conflict",
            "Social withdrawal",
            "Cognitive narrowing",
            "Fatigue accumulation",
            "Communication breakdown",
        ],
        narrative_arc=(
            "The crew moves from baseline through disruption and escalating strain "
            "to a critical phase requiring adaptive response, then toward resolution "
            "through recovery or stabilization at a new equilibrium."
        ),
    )


def create_third_quarter_scenario() -> ScenarioTemplate:
    """
    Create a third-quarter phenomenon scenario template from Phase 3, Workstream 2.
    """
    return ScenarioTemplate(
        template_id="scenario_third_quarter_001",
        name="Third-Quarter Phenomenon Scenario",
        scenario_type=ScenarioType.THIRD_QUARTER_PHENOMENON,
        description=(
            "A mission arc where psychological, social, and operational drift "
            "accumulates during the middle portion of the mission timeline, driven "
            "by cumulative monotony, temporal disengagement, and motivational erosion."
        ),
        baseline_reference="baseline_nominal_001",
        starting_conditions_description=(
            "Mission begins from baseline with strong motivation and engagement. "
            "Early phases proceed smoothly, mirroring nominal scenario."
        ),
        dominant_pressures=[
            "Temporal ambiguity and distance from endpoints",
            "Cumulative monotony",
            "Motivational erosion",
            "Social saturation",
            "Psychological endurance",
        ],
        dominant_themes=[
            "Meaning and purpose erosion",
            "Third-quarter slump",
            "Gradual disengagement",
            "Effort without proximate goals",
        ],
        expected_adaptations=[
            "Conscious re-engagement efforts",
            "Variety creation through personal projects",
            "Social reconnection activities",
            "Temporal structuring with milestones",
            "Purpose renewal through reflection",
        ],
        expected_frictions=[
            "Passive drift and disengagement",
            "Social withdrawal",
            "Performance degradation",
            "Emotional suppression",
            "Accumulated irritations",
        ],
        narrative_arc=(
            "The crew begins with energy and purpose, proceeds through early "
            "adaptation, then enters a mid-mission slump characterized by temporal "
            "disengagement and motivational drift. Recovery occurs through intentional "
            "renewal or proximity to mission endpoint."
        ),
    )
