"""
Pattern Schema

Defines data structures for pattern definitions and instances. Patterns are
recurring signatures of change or stability within or across domains,
corresponding to Phase 3, Workstream 3.

Key concepts:
- PatternDefinition: What a pattern means in terms of state characteristics
- PatternInstance: When a pattern is recognized in a run
- PatternClass: Temporal character (stable, drift, disruption, recovery)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class PatternClass(str, Enum):
    """
    Pattern classes based on temporal character from Phase 3, Workstream 3.
    """
    STABLE = "stable"  # Equilibrium states maintaining coherence
    DRIFT = "drift"  # Gradual, imperceptible shifts from baseline
    DISRUPTION = "disruption"  # Acute destabilization
    RECOVERY = "recovery"  # Restabilization following disruption or drift


class PatternScope(str, Enum):
    """Scope of pattern influence."""
    SINGLE_DOMAIN = "single-domain"  # Pattern within one domain
    CROSS_DOMAIN = "cross-domain"  # Pattern spanning multiple domains
    WHOLE_CREW = "whole-crew"  # Pattern affecting entire crew system


@dataclass
class StateCharacteristic:
    """
    A characteristic of state that defines part of a pattern.
    
    Patterns are defined by configurations of state characteristics
    rather than numeric thresholds.
    """
    domain: str
    characteristic_name: str
    description: str
    
    # Qualitative indicators
    indicators: List[str] = field(default_factory=list)
    
    # Examples from Phase 3
    examples: List[str] = field(default_factory=list)


@dataclass
class PatternDefinition:
    """
    Defines what a pattern means in terms of state characteristics.
    
    Patterns describe how states evolve or persist, providing qualitative
    frameworks for recognizing recurring configurations.
    """
    pattern_id: str
    name: str
    pattern_class: PatternClass
    pattern_scope: PatternScope
    description: str
    
    # State characteristics that define this pattern
    state_characteristics: List[StateCharacteristic] = field(default_factory=list)
    
    # Domains involved
    involved_domains: List[str] = field(default_factory=list)
    
    # Narrative descriptors
    narrative_description: Optional[str] = None
    typical_context: Optional[str] = None
    
    # Recognition criteria (qualitative)
    recognition_indicators: List[str] = field(default_factory=list)
    
    # References to Phase 3 documentation
    phase3_references: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def add_state_characteristic(self, characteristic: StateCharacteristic) -> None:
        """Add a state characteristic to the pattern definition."""
        self.state_characteristics.append(characteristic)
        
        # Update involved domains if needed
        if characteristic.domain not in self.involved_domains:
            self.involved_domains.append(characteristic.domain)
    
    def to_narrative(self) -> str:
        """Generate a narrative description of the pattern."""
        lines = [
            f"Pattern: {self.name}",
            f"Class: {self.pattern_class.value}",
            f"Scope: {self.pattern_scope.value}",
            "",
            f"Description: {self.description}",
            "",
        ]
        
        if self.narrative_description:
            lines.append(f"Narrative: {self.narrative_description}")
            lines.append("")
        
        if self.typical_context:
            lines.append(f"Typical Context: {self.typical_context}")
            lines.append("")
        
        if self.involved_domains:
            domains = ", ".join(self.involved_domains)
            lines.append(f"Involved Domains: {domains}")
            lines.append("")
        
        if self.recognition_indicators:
            lines.append("Recognition Indicators:")
            for indicator in self.recognition_indicators:
                lines.append(f"  - {indicator}")
            lines.append("")
        
        if self.state_characteristics:
            lines.append("State Characteristics:")
            for char in self.state_characteristics:
                lines.append(f"\n  {char.domain}: {char.characteristic_name}")
                lines.append(f"    {char.description}")
                if char.indicators:
                    lines.append("    Indicators:")
                    for ind in char.indicators:
                        lines.append(f"      - {ind}")
        
        if self.phase3_references:
            lines.append("\nPhase 3 References:")
            for ref in self.phase3_references:
                lines.append(f"  - {ref}")
        
        return "\n".join(lines)


@dataclass
class PatternInstance:
    """
    An instance of a pattern recognized in a specific run or context.
    
    While PatternDefinition describes what a pattern is, PatternInstance
    describes when and where it appeared.
    """
    instance_id: str
    pattern_definition_id: str
    pattern_name: str
    
    # Context of recognition
    scenario_id: Optional[str] = None
    mission_context: Optional[str] = None
    
    # Qualitative phase or timing descriptor (not numeric)
    phase_descriptor: Optional[str] = None  # e.g., "mid-mission", "after equipment failure"
    
    # Specific observations
    observations: List[str] = field(default_factory=list)
    
    # Domain states at time of recognition
    domain_states: Dict[str, str] = field(default_factory=dict)
    
    # Narrative summary
    narrative_summary: Optional[str] = None
    
    # Related patterns or events
    related_patterns: List[str] = field(default_factory=list)
    related_events: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def add_observation(self, observation: str) -> None:
        """Add an observation about this pattern instance."""
        self.observations.append(observation)
    
    def to_narrative(self) -> str:
        """Generate a narrative description of the pattern instance."""
        lines = [
            f"Pattern Instance: {self.pattern_name}",
            f"Instance ID: {self.instance_id}",
            "",
        ]
        
        if self.scenario_id:
            lines.append(f"Scenario: {self.scenario_id}")
        
        if self.mission_context:
            lines.append(f"Mission Context: {self.mission_context}")
        
        if self.phase_descriptor:
            lines.append(f"Phase: {self.phase_descriptor}")
        
        lines.append("")
        
        if self.narrative_summary:
            lines.append(f"Summary: {self.narrative_summary}")
            lines.append("")
        
        if self.observations:
            lines.append("Observations:")
            for obs in self.observations:
                lines.append(f"  - {obs}")
            lines.append("")
        
        if self.domain_states:
            lines.append("Domain States:")
            for domain, state in self.domain_states.items():
                lines.append(f"  {domain}: {state}")
            lines.append("")
        
        if self.related_patterns:
            patterns = ", ".join(self.related_patterns)
            lines.append(f"Related Patterns: {patterns}")
        
        if self.related_events:
            events = ", ".join(self.related_events)
            lines.append(f"Related Events: {events}")
        
        return "\n".join(lines)


def create_stable_pattern_example() -> PatternDefinition:
    """
    Create an example stable pattern from Phase 3, Workstream 3.
    """
    pattern = PatternDefinition(
        pattern_id="pattern_stable_001",
        name="High Coherence Pattern",
        pattern_class=PatternClass.STABLE,
        pattern_scope=PatternScope.WHOLE_CREW,
        description=(
            "Equilibrium state where physiological regulation, cognitive clarity, "
            "emotional steadiness, and social cohesion persist without significant "
            "drift or disruption."
        ),
        narrative_description=(
            "The crew operates in a state of sustained coherence where all domains "
            "maintain functional stability. There is alignment between individual "
            "and collective functioning, balanced adaptation to demands, and "
            "preserved capacity for flexible response."
        ),
        typical_context=(
            "Nominal mission phases with routine operations, adequate resources, "
            "and no exceptional stressors."
        ),
        recognition_indicators=[
            "Consistent performance across operational tasks",
            "Stable sleep patterns and restorative recovery",
            "Clear decision-making without confusion or paralysis",
            "Cooperative communication and mutual support",
            "Balanced workload perception",
            "Sustained engagement with mission purpose",
        ],
        phase3_references=[
            "Phase 3, Workstream 3: Stable Patterns",
            "Phase 3, Workstream 1: Baseline State Specification",
        ],
    )
    
    pattern.add_state_characteristic(StateCharacteristic(
        domain="physiological",
        characteristic_name="Stable Physiological Functioning",
        description="Well-rested state with balanced stress responses",
        indicators=[
            "Regular sleep cycles",
            "Adequate recovery from daily demands",
            "No cumulative fatigue",
        ],
        examples=["Crew members sleep through scheduled rest periods"],
    ))
    
    pattern.add_state_characteristic(StateCharacteristic(
        domain="cognitive",
        characteristic_name="Clear Mental Functioning",
        description="Sharp attention, accurate understanding, effective decisions",
        indicators=[
            "Sustained focus on tasks",
            "Accurate situational awareness",
            "Confident decision-making",
        ],
        examples=["Crew members execute procedures without confusion"],
    ))
    
    pattern.add_state_characteristic(StateCharacteristic(
        domain="social",
        characteristic_name="Cohesive Team Dynamics",
        description="Trust, cooperation, and constructive communication",
        indicators=[
            "Open information sharing",
            "Mutual support during challenges",
            "Constructive conflict resolution",
        ],
        examples=["Crew members collaborate smoothly on tasks"],
    ))
    
    return pattern


def create_drift_pattern_example() -> PatternDefinition:
    """
    Create an example drift pattern from Phase 3, Workstream 3.
    """
    pattern = PatternDefinition(
        pattern_id="pattern_drift_001",
        name="Gradual Sleep Disruption Pattern",
        pattern_class=PatternClass.DRIFT,
        pattern_scope=PatternScope.SINGLE_DOMAIN,
        description=(
            "Progressive erosion of sleep quality characterized by incremental "
            "increases in sleep latency, fragmentation, or insufficiency that "
            "accumulate without dramatic markers."
        ),
        narrative_description=(
            "Sleep begins to deteriorate in subtle ways—taking slightly longer to "
            "fall asleep, waking more frequently during rest periods, feeling less "
            "refreshed upon waking. The changes are gradual enough that crews may "
            "not recognize the pattern until fatigue becomes noticeable."
        ),
        typical_context=(
            "Mid-mission phases with cumulative monotony, circadian drift, or "
            "sustained low-level stress that incrementally disrupts sleep architecture."
        ),
        recognition_indicators=[
            "Incrementally increasing sleep latency",
            "More frequent nighttime awakenings",
            "Subjective sense of less restorative sleep",
            "Gradual accumulation of daytime fatigue",
            "Subtle decline in alertness or energy",
        ],
        phase3_references=[
            "Phase 3, Workstream 3: Drift Patterns",
            "Phase 3, Workstream 1: Sleep and Fatigue Conditions",
        ],
    )
    
    pattern.add_state_characteristic(StateCharacteristic(
        domain="physiological",
        characteristic_name="Progressive Sleep Quality Decline",
        description="Slow erosion of sleep quality over extended periods",
        indicators=[
            "Sleep becomes less deep or restorative",
            "Circadian rhythms show subtle phase shifts",
            "Recovery from daily demands feels incomplete",
        ],
        examples=[
            "Crew members report feeling 'not quite rested'",
            "Minor increase in errors or lapses in attention",
        ],
    ))
    
    return pattern


def create_disruption_pattern_example() -> PatternDefinition:
    """
    Create an example disruption pattern from Phase 3, Workstream 3.
    """
    pattern = PatternDefinition(
        pattern_id="pattern_disruption_001",
        name="Acute Trust Erosion Pattern",
        pattern_class=PatternClass.DISRUPTION,
        pattern_scope=PatternScope.CROSS_DOMAIN,
        description=(
            "Sudden destabilization of social trust following a specific event, "
            "betrayal, or perceived unfairness that fractures previously stable "
            "crew relationships."
        ),
        narrative_description=(
            "A triggering event—conflict over decision-making, perceived inequity, "
            "or communication breakdown—creates a rapid shift in how crew members "
            "view each other. Trust that was previously assumed becomes questioned. "
            "This disrupts not only social dynamics but also cognitive assumptions "
            "about the crew system."
        ),
        typical_context=(
            "Following interpersonal conflicts, leadership failures, or situations "
            "where fairness or competence is questioned under stress."
        ),
        recognition_indicators=[
            "Sudden shift from cooperative to guarded communication",
            "Increased skepticism about others' motives",
            "Withdrawal from collaborative activities",
            "Explicit expressions of doubt or frustration",
            "Defensive or hostile interpersonal exchanges",
        ],
        phase3_references=[
            "Phase 3, Workstream 3: Disruption Patterns",
            "Phase 3, Workstream 1: Social Cohesion States",
        ],
    )
    
    pattern.add_state_characteristic(StateCharacteristic(
        domain="social",
        characteristic_name="Trust Breakdown",
        description="Rapid shift from trust to suspicion or guardedness",
        indicators=[
            "Information sharing becomes selective",
            "Support becomes conditional or withheld",
            "Communication becomes strained or formal",
        ],
        examples=[
            "Crew members stop volunteering information",
            "Conflicts escalate rather than resolve",
        ],
    ))
    
    pattern.add_state_characteristic(StateCharacteristic(
        domain="cognitive",
        characteristic_name="Belief Disruption",
        description="Shift in beliefs about crew reliability and cohesion",
        indicators=[
            "Mental models of 'trustworthy crew' are challenged",
            "Increased cognitive load from monitoring others",
            "Uncertainty about others' intentions",
        ],
        examples=[
            "Crew members second-guess each other's actions",
            "Increased need for verification and checking",
        ],
    ))
    
    return pattern


def create_recovery_pattern_example() -> PatternDefinition:
    """
    Create an example recovery pattern from Phase 3, Workstream 3.
    """
    pattern = PatternDefinition(
        pattern_id="pattern_recovery_001",
        name="Relational Repair Pattern",
        pattern_class=PatternClass.RECOVERY,
        pattern_scope=PatternScope.CROSS_DOMAIN,
        description=(
            "Gradual restoration of trust and cohesion following social disruption "
            "through intentional repair efforts, vulnerability, and renewed "
            "mutual support."
        ),
        narrative_description=(
            "After a period of strained relationships, crew members begin the work "
            "of repair—through honest conversations, acknowledgment of hurt, "
            "vulnerability, or simply the passage of shared experience. Trust "
            "rebuilds incrementally, not all at once."
        ),
        typical_context=(
            "Following trust erosion or conflict, when crews engage in repair work "
            "through communication, leadership intervention, or external support."
        ),
        recognition_indicators=[
            "Increased willingness to engage in difficult conversations",
            "Acknowledgment of past conflict without defensiveness",
            "Renewed offers of support or collaboration",
            "Softening of hostile or guarded communication",
            "Return to shared activities or rituals",
        ],
        phase3_references=[
            "Phase 3, Workstream 3: Recovery Patterns",
            "Phase 3, Workstream 1: Social Cohesion States",
        ],
    )
    
    pattern.add_state_characteristic(StateCharacteristic(
        domain="social",
        characteristic_name="Trust Restoration",
        description="Incremental rebuilding of trust and mutual support",
        indicators=[
            "Communication becomes more open",
            "Cooperation increases on shared tasks",
            "Conflicts resolve more constructively",
        ],
        examples=[
            "Crew members apologize or acknowledge mistakes",
            "Shared humor or light moments return",
        ],
    ))
    
    pattern.add_state_characteristic(StateCharacteristic(
        domain="emotional",
        characteristic_name="Emotional Reconnection",
        description="Return of emotional availability and warmth",
        indicators=[
            "Emotional tone becomes less guarded",
            "Positive affect emerges in interactions",
            "Crew members express care for each other",
        ],
        examples=[
            "Crew members check in on each other's wellbeing",
            "Expressions of appreciation or gratitude",
        ],
    ))
    
    return pattern
