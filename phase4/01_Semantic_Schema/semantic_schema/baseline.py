"""
Baseline State Schema

Defines data structures for representing baseline states—the stable, equilibrium 
configuration from which all operational scenarios begin. This schema captures 
the qualitative baseline state vocabulary from Phase 3, Workstream 1.

Key concepts:
- BaselineProfile: Multi-domain starting configuration
- DomainState: State within a specific domain (physiological, cognitive, etc.)
- SemanticTag: Descriptive labels like "well-rested", "cohesive", "low strain"
- ModuleReference: Links to module-level configurations (by reference, not modification)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class Domain(str, Enum):
    """Domains of crew functioning as defined in Phase 3."""
    PHYSIOLOGICAL = "physiological"
    COGNITIVE = "cognitive"
    EMOTIONAL = "emotional"
    SOCIAL = "social"
    WORKLOAD = "workload"
    OPERATIONAL = "operational"


class PhysiologicalTag(str, Enum):
    """Semantic tags for physiological states from Phase 3 Reference States."""
    # Sleep and Rest States
    WELL_RESTED = "well-rested"
    ADEQUATELY_RESTED = "adequately-rested"
    MODERATELY_FATIGUED = "moderately-fatigued"
    SIGNIFICANTLY_FATIGUED = "significantly-fatigued"
    SEVERELY_FATIGUED = "severely-fatigued"
    
    # Stress Response States
    CALM_AND_BALANCED = "calm-and-balanced"
    MILDLY_AROUSED = "mildly-aroused"
    MODERATELY_STRAINED = "moderately-strained"
    HIGHLY_STRAINED = "highly-strained"
    OVERWHELMED = "overwhelmed"
    
    # Physical Capacity States
    FULL_CAPACITY = "full-capacity"
    SLIGHTLY_REDUCED_CAPACITY = "slightly-reduced-capacity"
    MODERATELY_REDUCED_CAPACITY = "moderately-reduced-capacity"
    SIGNIFICANTLY_REDUCED_CAPACITY = "significantly-reduced-capacity"
    MINIMAL_CAPACITY = "minimal-capacity"


class CognitiveTag(str, Enum):
    """Semantic tags for cognitive states from Phase 3 Reference States."""
    # Mental Clarity States
    CLEAR_AND_FOCUSED = "clear-and-focused"
    GENERALLY_CLEAR = "generally-clear"
    SOMEWHAT_CLOUDED = "somewhat-clouded"
    SIGNIFICANTLY_CLOUDED = "significantly-clouded"
    SEVERELY_IMPAIRED = "severely-impaired"
    
    # Decision-Making States
    CONFIDENT_AND_DECISIVE = "confident-and-decisive"
    DELIBERATE_AND_CAUTIOUS = "deliberate-and-cautious"
    HESITANT = "hesitant"
    PARALYZED = "paralyzed"
    IMPULSIVE_OR_ERRATIC = "impulsive-or-erratic"
    
    # Belief and Understanding States
    CLEAR_UNDERSTANDING = "clear-understanding"
    GENERALLY_ACCURATE = "generally-accurate"
    PARTIAL_UNDERSTANDING = "partial-understanding"
    CONFUSED = "confused"
    DISORIENTED = "disoriented"


class EmotionalTag(str, Enum):
    """Semantic tags for emotional states from Phase 3 Reference States."""
    # Mood and Affect States
    STABLE_AND_POSITIVE = "stable-and-positive"
    NEUTRAL_AND_STEADY = "neutral-and-steady"
    MILDLY_NEGATIVE = "mildly-negative"
    MODERATELY_DISTURBED = "moderately-disturbed"
    SEVERELY_DISTURBED = "severely-disturbed"
    
    # Emotional Regulation States
    WELL_REGULATED = "well-regulated"
    GENERALLY_CONTROLLED = "generally-controlled"
    SOMEWHAT_DYSREGULATED = "somewhat-dysregulated"
    POORLY_REGULATED = "poorly-regulated"
    UNREGULATED = "unregulated"


class SocialTag(str, Enum):
    """Semantic tags for social states from Phase 3 Reference States."""
    # Crew Cohesion States
    HIGHLY_COHESIVE = "highly-cohesive"
    COHESIVE = "cohesive"
    ADEQUATE_COHESION = "adequate-cohesion"
    DEVELOPING_FRAGMENTATION = "developing-fragmentation"
    FRAGMENTED = "fragmented"
    
    # Communication States
    OPEN_AND_CONSTRUCTIVE = "open-and-constructive"
    FUNCTIONAL = "functional"
    STRAINED = "strained"
    DYSFUNCTIONAL = "dysfunctional"
    BREAKDOWN = "breakdown"
    
    # Trust and Support States
    HIGH_TRUST = "high-trust"
    MODERATE_TRUST = "moderate-trust"
    LOW_TRUST = "low-trust"
    DISTRUST = "distrust"
    HOSTILE = "hostile"


class WorkloadTag(str, Enum):
    """Semantic tags for workload and coping states from Phase 3 Reference States."""
    # Workload Perception States
    LIGHT_AND_MANAGEABLE = "light-and-manageable"
    MODERATE_AND_BALANCED = "moderate-and-balanced"
    HEAVY_BUT_TOLERABLE = "heavy-but-tolerable"
    OVERWHELMING = "overwhelming"
    CRUSHING = "crushing"
    
    # Coping Resource States
    ABUNDANT_RESOURCES = "abundant-resources"
    ADEQUATE_RESOURCES = "adequate-resources"
    STRAINED_RESOURCES = "strained-resources"
    DEPLETED_RESOURCES = "depleted-resources"
    EXHAUSTED_RESOURCES = "exhausted-resources"
    
    # Adaptive Capacity States
    HIGHLY_ADAPTIVE = "highly-adaptive"
    MODERATELY_ADAPTIVE = "moderately-adaptive"
    LIMITED_ADAPTABILITY = "limited-adaptability"
    RIGID = "rigid"
    MALADAPTIVE = "maladaptive"


class OperationalTag(str, Enum):
    """Semantic tags for operational environment states from Phase 3 Reference States."""
    # Operational Demand States
    ROUTINE_OPERATIONS = "routine-operations"
    ELEVATED_DEMANDS = "elevated-demands"
    HIGH_INTENSITY_OPERATIONS = "high-intensity-operations"
    CRISIS_OPERATIONS = "crisis-operations"
    CATASTROPHIC_EVENTS = "catastrophic-events"
    
    # Environmental Pressure States
    LOW_BACKGROUND_PRESSURE = "low-background-pressure"
    MODERATE_PRESSURE = "moderate-pressure"
    HEIGHTENED_PRESSURE = "heightened-pressure"
    SEVERE_PRESSURE = "severe-pressure"
    EXTREME_PRESSURE = "extreme-pressure"


@dataclass
class SemanticTag:
    """
    A semantic tag that describes a qualitative state within a domain.
    
    Tags provide human-readable labels that reference Phase 3 vocabulary
    without requiring numeric values.
    """
    domain: Domain
    label: str
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate that the tag corresponds to known semantic tags."""
        valid_tags = {
            Domain.PHYSIOLOGICAL: [t.value for t in PhysiologicalTag],
            Domain.COGNITIVE: [t.value for t in CognitiveTag],
            Domain.EMOTIONAL: [t.value for t in EmotionalTag],
            Domain.SOCIAL: [t.value for t in SocialTag],
            Domain.WORKLOAD: [t.value for t in WorkloadTag],
            Domain.OPERATIONAL: [t.value for t in OperationalTag],
        }
        
        if self.label not in valid_tags.get(self.domain, []):
            # Allow custom tags but add warning in description
            if self.description is None:
                self.description = f"Custom tag (not from Phase 3 reference states)"


@dataclass
class ModuleReference:
    """
    Reference to a module-level configuration.
    
    This schema links to existing modules by reference only—it does not
    modify or contain their configurations.
    """
    module_name: str
    config_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class DomainState:
    """
    Qualitative state within a specific domain.
    
    Represents the baseline condition for one domain (physiological, cognitive,
    emotional, social, workload, operational) using semantic tags and narrative
    description.
    """
    domain: Domain
    primary_tag: SemanticTag
    secondary_tags: List[SemanticTag] = field(default_factory=list)
    narrative_description: Optional[str] = None
    
    # Optional module references for domains that map to specific modules
    module_references: List[ModuleReference] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate that primary tag matches the domain."""
        if self.primary_tag.domain != self.domain:
            raise ValueError(
                f"Primary tag domain ({self.primary_tag.domain}) must match "
                f"DomainState domain ({self.domain})"
            )
        
        # Validate secondary tags
        for tag in self.secondary_tags:
            if tag.domain != self.domain:
                raise ValueError(
                    f"Secondary tag domain ({tag.domain}) must match "
                    f"DomainState domain ({self.domain})"
                )


@dataclass
class BaselineProfile:
    """
    Multi-domain baseline configuration representing the stable, equilibrium
    state from which operational scenarios begin.
    
    This corresponds to the Baseline State Specification from Phase 3,
    Workstream 1. It captures the qualitative baseline across all domains
    without numeric values.
    """
    profile_id: str
    name: str
    description: str
    
    # Domain states
    physiological_state: DomainState
    cognitive_state: DomainState
    emotional_state: DomainState
    social_state: DomainState
    workload_state: DomainState
    operational_state: DomainState
    
    # Optional metadata
    mission_type: Optional[str] = None  # e.g., "long-duration exploration"
    crew_size_description: Optional[str] = None  # e.g., "small crew", not a number
    mission_phase: Optional[str] = None  # e.g., "pre-launch", "early mission"
    
    # Additional context
    assumptions: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate domain states match their expected domains."""
        expected_domains = {
            "physiological_state": Domain.PHYSIOLOGICAL,
            "cognitive_state": Domain.COGNITIVE,
            "emotional_state": Domain.EMOTIONAL,
            "social_state": Domain.SOCIAL,
            "workload_state": Domain.WORKLOAD,
            "operational_state": Domain.OPERATIONAL,
        }
        
        for attr_name, expected_domain in expected_domains.items():
            state = getattr(self, attr_name)
            if state.domain != expected_domain:
                raise ValueError(
                    f"{attr_name} must have domain {expected_domain}, "
                    f"got {state.domain}"
                )
    
    def get_domain_state(self, domain: Domain) -> DomainState:
        """Retrieve the state for a specific domain."""
        domain_map = {
            Domain.PHYSIOLOGICAL: self.physiological_state,
            Domain.COGNITIVE: self.cognitive_state,
            Domain.EMOTIONAL: self.emotional_state,
            Domain.SOCIAL: self.social_state,
            Domain.WORKLOAD: self.workload_state,
            Domain.OPERATIONAL: self.operational_state,
        }
        return domain_map[domain]
    
    def get_all_semantic_tags(self) -> List[SemanticTag]:
        """Retrieve all semantic tags across all domains."""
        tags = []
        for domain in Domain:
            state = self.get_domain_state(domain)
            tags.append(state.primary_tag)
            tags.extend(state.secondary_tags)
        return tags
    
    def to_narrative_summary(self) -> str:
        """Generate a narrative summary of the baseline profile."""
        summary_lines = [
            f"Baseline Profile: {self.name}",
            f"Description: {self.description}",
            "",
        ]
        
        if self.mission_type:
            summary_lines.append(f"Mission Type: {self.mission_type}")
        if self.crew_size_description:
            summary_lines.append(f"Crew Size: {self.crew_size_description}")
        if self.mission_phase:
            summary_lines.append(f"Mission Phase: {self.mission_phase}")
        
        summary_lines.append("")
        summary_lines.append("Domain States:")
        
        for domain in Domain:
            state = self.get_domain_state(domain)
            summary_lines.append(f"\n{domain.value.title()}:")
            summary_lines.append(f"  Primary: {state.primary_tag.label}")
            if state.secondary_tags:
                tags = ", ".join(t.label for t in state.secondary_tags)
                summary_lines.append(f"  Secondary: {tags}")
            if state.narrative_description:
                summary_lines.append(f"  Description: {state.narrative_description}")
        
        return "\n".join(summary_lines)


def create_nominal_baseline() -> BaselineProfile:
    """
    Create a nominal baseline profile representing optimal crew functioning.
    
    This baseline corresponds to the Phase 3 Baseline State Specification.
    """
    return BaselineProfile(
        profile_id="baseline_nominal_001",
        name="Nominal Baseline",
        description=(
            "Stable, equilibrium configuration representing optimal crew "
            "functioning under normal mission conditions with no exceptional "
            "stressors or degraded states."
        ),
        mission_type="long-duration spaceflight",
        crew_size_description="small crew",
        mission_phase="early mission",
        
        physiological_state=DomainState(
            domain=Domain.PHYSIOLOGICAL,
            primary_tag=SemanticTag(
                domain=Domain.PHYSIOLOGICAL,
                label=PhysiologicalTag.WELL_RESTED.value,
                description="Crew members are well-rested with adequate recovery"
            ),
            secondary_tags=[
                SemanticTag(
                    domain=Domain.PHYSIOLOGICAL,
                    label=PhysiologicalTag.CALM_AND_BALANCED.value,
                    description="Physiological systems in homeostatic state"
                ),
                SemanticTag(
                    domain=Domain.PHYSIOLOGICAL,
                    label=PhysiologicalTag.FULL_CAPACITY.value,
                    description="Physical reserves intact"
                ),
            ],
            narrative_description=(
                "Stable physiological functioning with regular sleep cycles, "
                "balanced stress response systems, and adequate physical capacity."
            ),
        ),
        
        cognitive_state=DomainState(
            domain=Domain.COGNITIVE,
            primary_tag=SemanticTag(
                domain=Domain.COGNITIVE,
                label=CognitiveTag.CLEAR_AND_FOCUSED.value,
                description="Clear situational awareness and mental clarity"
            ),
            secondary_tags=[
                SemanticTag(
                    domain=Domain.COGNITIVE,
                    label=CognitiveTag.CONFIDENT_AND_DECISIVE.value,
                    description="Effective decision-making processes"
                ),
                SemanticTag(
                    domain=Domain.COGNITIVE,
                    label=CognitiveTag.CLEAR_UNDERSTANDING.value,
                    description="Accurate mental models and beliefs"
                ),
            ],
            narrative_description=(
                "Clear cognitive functioning with accurate situational awareness, "
                "aligned understanding of mission objectives, and coherent "
                "decision-making processes."
            ),
        ),
        
        emotional_state=DomainState(
            domain=Domain.EMOTIONAL,
            primary_tag=SemanticTag(
                domain=Domain.EMOTIONAL,
                label=EmotionalTag.STABLE_AND_POSITIVE.value,
                description="Stable mood and positive emotional tone"
            ),
            secondary_tags=[
                SemanticTag(
                    domain=Domain.EMOTIONAL,
                    label=EmotionalTag.WELL_REGULATED.value,
                    description="Effective emotional regulation"
                ),
            ],
            narrative_description=(
                "Stable emotional tone with effective regulation, baseline "
                "motivation, and appropriate emotional responses."
            ),
        ),
        
        social_state=DomainState(
            domain=Domain.SOCIAL,
            primary_tag=SemanticTag(
                domain=Domain.SOCIAL,
                label=SocialTag.COHESIVE.value,
                description="Cooperative relationships and functional communication"
            ),
            secondary_tags=[
                SemanticTag(
                    domain=Domain.SOCIAL,
                    label=SocialTag.OPEN_AND_CONSTRUCTIVE.value,
                    description="Clear and constructive communication patterns"
                ),
                SemanticTag(
                    domain=Domain.SOCIAL,
                    label=SocialTag.HIGH_TRUST.value,
                    description="Strong mutual trust and support"
                ),
            ],
            narrative_description=(
                "Cooperative relationships, functional communication patterns, "
                "shared sense of purpose, and equitable role distribution."
            ),
        ),
        
        workload_state=DomainState(
            domain=Domain.WORKLOAD,
            primary_tag=SemanticTag(
                domain=Domain.WORKLOAD,
                label=WorkloadTag.MODERATE_AND_BALANCED.value,
                description="Balanced workload matching available resources"
            ),
            secondary_tags=[
                SemanticTag(
                    domain=Domain.WORKLOAD,
                    label=WorkloadTag.ADEQUATE_RESOURCES.value,
                    description="Sufficient coping resources"
                ),
                SemanticTag(
                    domain=Domain.WORKLOAD,
                    label=WorkloadTag.MODERATELY_ADAPTIVE.value,
                    description="Adaptive capacity available"
                ),
            ],
            narrative_description=(
                "Predictable operational demands with adequate coping resources "
                "and balanced task allocation."
            ),
        ),
        
        operational_state=DomainState(
            domain=Domain.OPERATIONAL,
            primary_tag=SemanticTag(
                domain=Domain.OPERATIONAL,
                label=OperationalTag.ROUTINE_OPERATIONS.value,
                description="Routine operational demands"
            ),
            secondary_tags=[
                SemanticTag(
                    domain=Domain.OPERATIONAL,
                    label=OperationalTag.LOW_BACKGROUND_PRESSURE.value,
                    description="Stable habitat with minimal stressors"
                ),
            ],
            narrative_description=(
                "Stable habitat conditions with reliable infrastructure and "
                "routine operational tempo."
            ),
        ),
        
        assumptions=[
            "Crew members are well-prepared and trained",
            "No pre-existing health or psychological conditions",
            "Mission infrastructure is functioning as designed",
            "No acute emergencies or equipment failures",
        ],
        notes=[
            "This baseline represents the reference state from Phase 3, Workstream 1",
            "All scenarios begin from this baseline or a variant of it",
        ],
    )
