"""
Thread Schema

Defines data structures for narrative threads—emergent meaning structures
that describe how domains, patterns, and events interweave across mission
duration. Corresponds to Phase 3, Workstream 4.

Key concepts:
- ThreadDefinition: What a thread means (domain relationships, influences)
- ThreadInstance: When a thread is recognized in a specific run
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class ThreadCategory(str, Enum):
    """Categories of narrative threads from Phase 3, Workstream 4."""
    DOMAIN_INTERACTION = "domain-interaction"  # Pairwise domain influences
    MISSION_PHASE = "mission-phase"  # Phase-specific cross-domain patterns
    COMPOSITE = "composite"  # Rich multi-domain narrative threads


class InfluenceType(str, Enum):
    """Types of influence one domain can have on another."""
    AMPLIFYING = "amplifying"  # Strengthens or intensifies
    CONSTRAINING = "constraining"  # Limits or restricts
    TRANSFORMING = "transforming"  # Changes character or quality
    TRIGGERING = "triggering"  # Initiates or catalyzes
    MODULATING = "modulating"  # Regulates or adjusts
    MUTUAL_REINFORCEMENT = "mutual-reinforcement"  # Bidirectional strengthening


class TemporalPattern(str, Enum):
    """Temporal patterns of thread activation."""
    GRADUAL = "gradual"  # Slow accumulation over time
    SUDDEN = "sudden"  # Rapid onset
    CYCLICAL = "cyclical"  # Repeating pattern
    SUSTAINED = "sustained"  # Persistent over duration
    EPISODIC = "episodic"  # Intermittent occurrence


@dataclass
class DomainInfluence:
    """
    Describes how one domain influences another within a thread.
    
    This is a qualitative relationship, not a computational function.
    """
    source_domain: str
    target_domain: str
    influence_type: InfluenceType
    description: str
    
    # Contextual conditions
    conditions: List[str] = field(default_factory=list)
    
    # Examples from Phase 3
    examples: List[str] = field(default_factory=list)
    
    # Qualitative strength descriptor
    strength_descriptor: Optional[str] = None  # e.g., "strong", "moderate", "subtle"


@dataclass
class ThreadDefinition:
    """
    Defines a narrative thread—a conceptual framework for understanding how
    domains, patterns, and events interweave across mission duration.
    
    Threads are not mechanisms or models; they are interpretive constructs
    that describe emergent meaning structures.
    """
    thread_id: str
    name: str
    category: ThreadCategory
    description: str
    
    # Domain influences that constitute this thread
    domain_influences: List[DomainInfluence] = field(default_factory=list)
    
    # Domains involved
    involved_domains: List[str] = field(default_factory=list)
    
    # Patterns typically associated with this thread
    associated_patterns: List[str] = field(default_factory=list)
    
    # Narrative descriptors
    narrative_description: Optional[str] = None
    implications: Optional[str] = None
    
    # Temporal characteristics
    temporal_pattern: Optional[TemporalPattern] = None
    
    # Recognition indicators (qualitative)
    recognition_indicators: List[str] = field(default_factory=list)
    
    # References to Phase 3 documentation
    phase3_references: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def add_domain_influence(self, influence: DomainInfluence) -> None:
        """Add a domain influence to the thread definition."""
        self.domain_influences.append(influence)
        
        # Update involved domains
        if influence.source_domain not in self.involved_domains:
            self.involved_domains.append(influence.source_domain)
        if influence.target_domain not in self.involved_domains:
            self.involved_domains.append(influence.target_domain)
    
    def to_narrative(self) -> str:
        """Generate a narrative description of the thread."""
        lines = [
            f"Thread: {self.name}",
            f"Category: {self.category.value}",
            "",
            f"Description: {self.description}",
            "",
        ]
        
        if self.narrative_description:
            lines.append(f"Narrative: {self.narrative_description}")
            lines.append("")
        
        if self.implications:
            lines.append(f"Implications: {self.implications}")
            lines.append("")
        
        if self.temporal_pattern:
            lines.append(f"Temporal Pattern: {self.temporal_pattern.value}")
            lines.append("")
        
        if self.involved_domains:
            domains = ", ".join(self.involved_domains)
            lines.append(f"Involved Domains: {domains}")
            lines.append("")
        
        if self.domain_influences:
            lines.append("Domain Influences:")
            for inf in self.domain_influences:
                lines.append(f"\n  {inf.source_domain} → {inf.target_domain}")
                lines.append(f"  Type: {inf.influence_type.value}")
                if inf.strength_descriptor:
                    lines.append(f"  Strength: {inf.strength_descriptor}")
                lines.append(f"  {inf.description}")
                if inf.conditions:
                    lines.append("  Conditions:")
                    for cond in inf.conditions:
                        lines.append(f"    - {cond}")
            lines.append("")
        
        if self.associated_patterns:
            lines.append("Associated Patterns:")
            for pattern in self.associated_patterns:
                lines.append(f"  - {pattern}")
            lines.append("")
        
        if self.recognition_indicators:
            lines.append("Recognition Indicators:")
            for indicator in self.recognition_indicators:
                lines.append(f"  - {indicator}")
            lines.append("")
        
        if self.phase3_references:
            lines.append("Phase 3 References:")
            for ref in self.phase3_references:
                lines.append(f"  - {ref}")
        
        return "\n".join(lines)


@dataclass
class ThreadInstance:
    """
    An instance of a thread recognized in a specific run or context.
    
    While ThreadDefinition describes what a thread means, ThreadInstance
    describes when and how it manifested.
    """
    instance_id: str
    thread_definition_id: str
    thread_name: str
    
    # Context of recognition
    scenario_id: Optional[str] = None
    mission_context: Optional[str] = None
    
    # Qualitative phase or timing descriptor
    phase_descriptor: Optional[str] = None  # e.g., "mid-mission drift phase"
    
    # Patterns involved in this thread instance
    pattern_instances: List[str] = field(default_factory=list)
    
    # Domain states during thread activation
    domain_states: Dict[str, str] = field(default_factory=dict)
    
    # Observations about how the thread manifested
    observations: List[str] = field(default_factory=list)
    
    # Narrative summary
    narrative_summary: Optional[str] = None
    
    # Related events that activated or sustained the thread
    related_events: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def add_pattern_instance(self, pattern_instance_id: str) -> None:
        """Link a pattern instance to this thread instance."""
        if pattern_instance_id not in self.pattern_instances:
            self.pattern_instances.append(pattern_instance_id)
    
    def add_observation(self, observation: str) -> None:
        """Add an observation about this thread instance."""
        self.observations.append(observation)
    
    def to_narrative(self) -> str:
        """Generate a narrative description of the thread instance."""
        lines = [
            f"Thread Instance: {self.thread_name}",
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
        
        if self.pattern_instances:
            lines.append("Pattern Instances:")
            for pattern in self.pattern_instances:
                lines.append(f"  - {pattern}")
            lines.append("")
        
        if self.related_events:
            lines.append("Related Events:")
            for event in self.related_events:
                lines.append(f"  - {event}")
        
        return "\n".join(lines)


def create_strain_reactivity_thread() -> ThreadDefinition:
    """
    Create the Strain-Reactivity Thread from Phase 3, Workstream 4.
    
    This is a composite thread describing how physiological strain increases
    emotional reactivity, which strains social bonds, which creates cognitive
    load, which feeds back to physiological stress.
    """
    thread = ThreadDefinition(
        thread_id="thread_composite_001",
        name="Strain–Reactivity Thread",
        category=ThreadCategory.COMPOSITE,
        description=(
            "A multi-domain thread where physiological strain increases emotional "
            "reactivity, which strains social dynamics, which increases cognitive "
            "load, creating a reinforcing cycle of stress and vulnerability."
        ),
        narrative_description=(
            "As physiological strain builds—through sleep disruption, sustained "
            "arousal, or depletion of physical reserves—emotional regulation becomes "
            "more difficult. Small frustrations trigger disproportionate reactions. "
            "This emotional volatility strains social relationships, creating tension "
            "and guardedness. The resulting social friction adds cognitive burden as "
            "crew members must navigate complex interpersonal dynamics while managing "
            "their own distress. This cognitive load feeds back into physiological "
            "stress, perpetuating the cycle."
        ),
        implications=(
            "Breaking this cycle requires intervention at multiple points: restoring "
            "physiological resources through rest, supporting emotional regulation, "
            "facilitating social repair, and reducing cognitive demands."
        ),
        temporal_pattern=TemporalPattern.GRADUAL,
        associated_patterns=[
            "Progressive sleep disruption",
            "Emotional reactivity increase",
            "Trust erosion",
            "Cognitive narrowing",
        ],
        recognition_indicators=[
            "Accumulating fatigue or sleep disruption",
            "Increased emotional volatility or irritability",
            "Escalating interpersonal tensions",
            "Reduced cognitive flexibility",
            "Crew members report feeling 'on edge'",
        ],
        phase3_references=[
            "Phase 3, Workstream 4: Composite Threads",
            "Phase 3, Workstream 4: Domain Interaction Threads",
        ],
    )
    
    thread.add_domain_influence(DomainInfluence(
        source_domain="physiological",
        target_domain="emotional",
        influence_type=InfluenceType.AMPLIFYING,
        description=(
            "Physiological strain (fatigue, arousal, depletion) reduces emotional "
            "regulation capacity, making individuals more reactive to stressors."
        ),
        strength_descriptor="strong",
        conditions=[
            "Sustained sleep disruption",
            "Chronic stress response activation",
            "Physical depletion",
        ],
        examples=[
            "Fatigued crew members respond with irritation to minor issues",
            "Sleep-deprived individuals have shorter emotional fuses",
        ],
    ))
    
    thread.add_domain_influence(DomainInfluence(
        source_domain="emotional",
        target_domain="social",
        influence_type=InfluenceType.CONSTRAINING,
        description=(
            "Emotional reactivity constrains social functioning by creating "
            "defensiveness, withdrawal, or hostile exchanges that damage trust."
        ),
        strength_descriptor="strong",
        conditions=[
            "High emotional volatility",
            "Poor emotional regulation",
            "Lack of psychological safety",
        ],
        examples=[
            "Irritable crew members snap at each other",
            "Emotional guardedness reduces open communication",
        ],
    ))
    
    thread.add_domain_influence(DomainInfluence(
        source_domain="social",
        target_domain="cognitive",
        influence_type=InfluenceType.AMPLIFYING,
        description=(
            "Strained social dynamics increase cognitive load as individuals must "
            "monitor interpersonal tensions, manage conflicts, and navigate complex "
            "relational dynamics."
        ),
        strength_descriptor="moderate",
        conditions=[
            "Active interpersonal conflict",
            "Trust erosion",
            "Communication breakdown",
        ],
        examples=[
            "Crew members spend cognitive resources worrying about relationships",
            "Need to carefully word communications adds mental burden",
        ],
    ))
    
    thread.add_domain_influence(DomainInfluence(
        source_domain="cognitive",
        target_domain="physiological",
        influence_type=InfluenceType.AMPLIFYING,
        description=(
            "Increased cognitive load and mental stress feed back into physiological "
            "stress responses, sustaining arousal and interfering with recovery."
        ),
        strength_descriptor="moderate",
        conditions=[
            "Sustained cognitive demands",
            "Unresolved interpersonal stress",
            "Limited recovery opportunities",
        ],
        examples=[
            "Worrying about relationships disrupts sleep",
            "Mental stress maintains physiological arousal",
        ],
    ))
    
    return thread


def create_meaning_erosion_thread() -> ThreadDefinition:
    """
    Create the Meaning Erosion Thread from Phase 3, Workstream 4.
    """
    thread = ThreadDefinition(
        thread_id="thread_composite_002",
        name="Meaning Erosion Thread",
        category=ThreadCategory.COMPOSITE,
        description=(
            "A thread describing how loss of connection to mission purpose erodes "
            "across cognitive, emotional, and social domains, creating a sense of "
            "emptiness or disconnection."
        ),
        narrative_description=(
            "As the mission extends, the original sense of purpose and meaning can "
            "fade. The mission's goals feel abstract and distant. This cognitive "
            "shift affects emotional engagement—tasks that once felt significant now "
            "feel rote. Social connections may weaken as shared purpose, a key "
            "foundation of cohesion, diminishes. The crew continues functioning but "
            "experiences an interior hollowness."
        ),
        implications=(
            "Restoring meaning requires intentional effort: reconnecting with mission "
            "significance, creating intermediate milestones, reflecting on purpose, "
            "and finding value in the experience itself."
        ),
        temporal_pattern=TemporalPattern.GRADUAL,
        associated_patterns=[
            "Cognitive disengagement",
            "Emotional flattening",
            "Motivational drift",
            "Social detachment",
        ],
        recognition_indicators=[
            "Crew describes mission as 'just going through the motions'",
            "Reduced intrinsic motivation",
            "Emotional tone becomes muted",
            "Decreased engagement with mission goals",
            "Loss of sense of shared purpose",
        ],
        phase3_references=[
            "Phase 3, Workstream 4: Composite Threads",
            "Phase 3, Workstream 5: Meaning Erosion Trajectory",
        ],
    )
    
    thread.add_domain_influence(DomainInfluence(
        source_domain="cognitive",
        target_domain="emotional",
        influence_type=InfluenceType.CONSTRAINING,
        description=(
            "Loss of cognitive connection to meaning constrains emotional engagement, "
            "reducing access to positive affect and intrinsic motivation."
        ),
        strength_descriptor="strong",
        conditions=[
            "Extended mission duration",
            "Temporal distance from meaningful endpoints",
            "Repetitive operational demands",
        ],
        examples=[
            "Tasks feel mechanical rather than purposeful",
            "Difficulty accessing enthusiasm or inspiration",
        ],
    ))
    
    thread.add_domain_influence(DomainInfluence(
        source_domain="emotional",
        target_domain="social",
        influence_type=InfluenceType.CONSTRAINING,
        description=(
            "Emotional disengagement reduces social connection as shared purpose—"
            "a key bonding element—weakens."
        ),
        strength_descriptor="moderate",
        conditions=[
            "Collective emotional flattening",
            "Shared sense of meaninglessness",
            "Lack of inspiring moments",
        ],
        examples=[
            "Crew members withdraw into individual routines",
            "Conversations become transactional rather than relational",
        ],
    ))
    
    thread.add_domain_influence(DomainInfluence(
        source_domain="social",
        target_domain="cognitive",
        influence_type=InfluenceType.AMPLIFYING,
        description=(
            "Weakened social bonds can reinforce cognitive disconnection from meaning "
            "as the collective narrative of mission significance erodes."
        ),
        strength_descriptor="moderate",
        conditions=[
            "Loss of shared rituals or celebrations",
            "Decreased collective reflection",
            "Fragmented crew identity",
        ],
        examples=[
            "Crew stops discussing mission significance together",
            "Loss of collective storytelling about the mission's value",
        ],
    ))
    
    return thread


def create_domain_interaction_thread_example() -> ThreadDefinition:
    """
    Create an example domain interaction thread (pairwise).
    """
    thread = ThreadDefinition(
        thread_id="thread_interaction_001",
        name="Physiology → Cognition Thread",
        category=ThreadCategory.DOMAIN_INTERACTION,
        description=(
            "Describes how physiological state directly influences cognitive "
            "functioning, particularly attention, decision-making, and mental clarity."
        ),
        narrative_description=(
            "When physiological systems are strained—through fatigue, sleep "
            "deprivation, or sustained stress—cognitive processes become compromised. "
            "Attention narrows, decision-making becomes more effortful, and mental "
            "clarity diminishes. This is a fundamental relationship that underpins "
            "many other cross-domain dynamics."
        ),
        temporal_pattern=TemporalPattern.SUSTAINED,
        recognition_indicators=[
            "Cognitive performance declines with fatigue",
            "Decision-making becomes slower or less confident",
            "Attention lapses increase with sleep disruption",
        ],
        phase3_references=[
            "Phase 3, Workstream 4: Domain Interaction Threads",
        ],
    )
    
    thread.add_domain_influence(DomainInfluence(
        source_domain="physiological",
        target_domain="cognitive",
        influence_type=InfluenceType.CONSTRAINING,
        description=(
            "Physiological strain constrains cognitive capacity by reducing "
            "available resources for attention, memory, and executive function."
        ),
        strength_descriptor="very strong",
        conditions=[
            "Sleep deprivation",
            "Sustained stress activation",
            "Physical exhaustion",
        ],
        examples=[
            "Fatigued crew members make more errors",
            "Sleep-deprived individuals struggle with complex decisions",
            "Physical exhaustion reduces attention span",
        ],
    ))
    
    return thread
