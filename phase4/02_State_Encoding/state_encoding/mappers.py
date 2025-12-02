"""
Mappers for translating unstructured observations into semantic schema objects.

This module provides the bridge between:
- Raw/unstructured observations → semantic schema objects
- Qualitative descriptors → semantic tags
- Narrative event notes → structured event objects
- Textual assessments → schema-compliant representations

All mappers perform direct, rule-based translation only. They do NOT:
- Perform NLP or text analysis
- Perform inference or classification
- Recognize patterns
- Make probabilistic decisions

Mappers rely on explicit input structure provided by the calling context.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from state_encoding.interfaces import ObservationMapper
from state_encoding.encoders import (
    BaselineProfile, ScenarioEvent, PatternIndicator, ThreadIndicator
)


class ObservationToSchemaMapper(ObservationMapper):
    """
    Mapper for converting observations to semantic schema objects.
    
    The ObservationToSchemaMapper handles direct translation of
    structured observation dictionaries into BaselineProfile objects
    that can be consumed by encoders.
    
    Example Input:
        {
            "profile_id": "baseline_001",
            "physiological": {
                "sleep_quality": "restless",
                "energy_level": "low"
            },
            "psychological": {
                "mood": "anxious",
                "stress_level": "moderate"
            },
            "social": {
                "social_support": "limited",
                "cohesion": "weak"
            },
            "environmental": {
                "workload": "high",
                "resources": "constrained"
            }
        }
    
    Output: BaselineProfile object
    """
    
    def __init__(self):
        self._supported_types = {"baseline_observation", "physiological", "psychological"}
    
    def map(self, observation: Dict[str, Any]) -> BaselineProfile:
        """
        Map an observation to a BaselineProfile schema object.
        
        Args:
            observation: Structured observation dictionary
            
        Returns:
            BaselineProfile semantic schema object
            
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required = self.get_required_fields()
        missing = [field for field in required if field not in observation]
        
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        # Extract profile ID
        profile_id = observation.get("profile_id", "unknown")
        
        # Extract domain states with defaults
        physiological_state = observation.get("physiological", {})
        psychological_state = observation.get("psychological", {})
        social_state = observation.get("social", {})
        environmental_context = observation.get("environmental", {})
        
        # Extract metadata
        metadata = observation.get("metadata", {})
        
        # Create and return BaselineProfile
        return BaselineProfile(
            profile_id=profile_id,
            physiological_state=physiological_state,
            psychological_state=psychological_state,
            social_state=social_state,
            environmental_context=environmental_context,
            metadata=metadata
        )
    
    def supports_observation_type(self, observation_type: str) -> bool:
        """Check if this mapper supports a given observation type."""
        return observation_type in self._supported_types
    
    def get_required_fields(self) -> List[str]:
        """Return list of required fields for mapping."""
        return ["profile_id"]


class NarrativeToEventMapper(ObservationMapper):
    """
    Mapper for converting narrative descriptions to ScenarioEvent objects.
    
    The NarrativeToEventMapper translates structured event descriptions
    (e.g., from scenario timelines or event logs) into ScenarioEvent
    semantic schema objects.
    
    Example Input:
        {
            "event_id": "evt_001",
            "event_type": "mission_assignment",
            "timestamp": "2024-03-15T08:00:00Z",
            "actors": ["crew_member_1", "crew_member_2"],
            "description": "High-stakes mission assigned to crew",
            "descriptors": {
                "urgency": "high",
                "complexity": "moderate",
                "stakes": "critical"
            },
            "context": {
                "location": "command_center",
                "mission_phase": "pre_deployment"
            }
        }
    
    Output: ScenarioEvent object
    """
    
    def __init__(self):
        self._supported_types = {"narrative_event", "scenario_event", "timeline_event"}
    
    def map(self, observation: Dict[str, Any]) -> ScenarioEvent:
        """
        Map a narrative description to a ScenarioEvent schema object.
        
        Args:
            observation: Structured event description
            
        Returns:
            ScenarioEvent semantic schema object
            
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required = self.get_required_fields()
        missing = [field for field in required if field not in observation]
        
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        # Extract event fields
        event_id = observation["event_id"]
        event_type = observation["event_type"]
        timestamp = observation.get("timestamp")
        actors = observation.get("actors", [])
        descriptors = observation.get("descriptors", {})
        context = observation.get("context", {})
        metadata = observation.get("metadata", {})
        
        # If description is provided, add to context
        if "description" in observation:
            context["description"] = observation["description"]
        
        # Create and return ScenarioEvent
        return ScenarioEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=timestamp,
            actors=actors,
            descriptors=descriptors,
            context=context,
            metadata=metadata
        )
    
    def supports_observation_type(self, observation_type: str) -> bool:
        """Check if this mapper supports a given observation type."""
        return observation_type in self._supported_types
    
    def get_required_fields(self) -> List[str]:
        """Return list of required fields for mapping."""
        return ["event_id", "event_type"]


class QualitativeDescriptorMapper(ObservationMapper):
    """
    Mapper for converting qualitative descriptors to semantic schema objects.
    
    The QualitativeDescriptorMapper handles translation of qualitative
    descriptors (e.g., "sleep: restless", "mood: anxious") into structured
    semantic representations. It supports mapping to both PatternIndicator
    and ThreadIndicator objects.
    
    Example Input (Pattern Indicator):
        {
            "type": "pattern_indicator",
            "indicator_id": "pat_001",
            "pattern_type": "stress_response",
            "indicators": ["elevated_heart_rate", "disrupted_sleep", "irritability"],
            "confidence": "moderate",
            "context": {
                "timeframe": "past_week",
                "domain": "physiological"
            }
        }
    
    Example Input (Thread Indicator):
        {
            "type": "thread_indicator",
            "thread_id": "thread_001",
            "thread_type": "social_cohesion",
            "entities": ["crew_member_1", "crew_member_2", "crew_member_3"],
            "relationships": {
                "cohesion_level": "moderate",
                "trust_level": "building"
            },
            "context": {
                "timeframe": "current",
                "scope": "team"
            }
        }
    
    Output: PatternIndicator or ThreadIndicator object
    """
    
    def __init__(self):
        self._supported_types = {
            "pattern_indicator", "thread_indicator",
            "qualitative_descriptor", "relational_hint"
        }
    
    def map(self, observation: Dict[str, Any]) -> Any:
        """
        Map a qualitative descriptor to appropriate schema object.
        
        Args:
            observation: Structured descriptor dictionary
            
        Returns:
            PatternIndicator, ThreadIndicator, or other schema object
            
        Raises:
            ValueError: If required fields are missing or type is unsupported
        """
        obs_type = observation.get("type", "").lower()
        
        if obs_type == "pattern_indicator":
            return self._map_pattern_indicator(observation)
        elif obs_type == "thread_indicator":
            return self._map_thread_indicator(observation)
        else:
            raise ValueError(f"Unsupported observation type: {obs_type}")
    
    def _map_pattern_indicator(self, observation: Dict[str, Any]) -> PatternIndicator:
        """Map to PatternIndicator schema object."""
        required = ["indicator_id", "pattern_type", "indicators"]
        missing = [field for field in required if field not in observation]
        
        if missing:
            raise ValueError(f"Missing required fields for pattern_indicator: {missing}")
        
        return PatternIndicator(
            indicator_id=observation["indicator_id"],
            pattern_type=observation["pattern_type"],
            indicators=observation["indicators"],
            confidence_level=observation.get("confidence", "unknown"),
            context=observation.get("context", {}),
            metadata=observation.get("metadata", {})
        )
    
    def _map_thread_indicator(self, observation: Dict[str, Any]) -> ThreadIndicator:
        """Map to ThreadIndicator schema object."""
        required = ["thread_id", "thread_type", "entities"]
        missing = [field for field in required if field not in observation]
        
        if missing:
            raise ValueError(f"Missing required fields for thread_indicator: {missing}")
        
        # Handle both "entities" and "related_entities" field names
        entities = observation.get("entities") or observation.get("related_entities", [])
        
        # Handle both "relationships" and "relationship_descriptors" field names
        relationships = (
            observation.get("relationships") or 
            observation.get("relationship_descriptors", {})
        )
        
        return ThreadIndicator(
            thread_id=observation["thread_id"],
            thread_type=observation["thread_type"],
            related_entities=entities,
            relationship_descriptors=relationships,
            context=observation.get("context", {}),
            metadata=observation.get("metadata", {})
        )
    
    def supports_observation_type(self, observation_type: str) -> bool:
        """Check if this mapper supports a given observation type."""
        return observation_type.lower() in self._supported_types
    
    def get_required_fields(self) -> List[str]:
        """Return list of required fields for mapping."""
        # Varies by type, so return common field
        return ["type"]


@dataclass
class SemanticTag:
    """
    Representation of a semantic tag from the semantic schema.
    
    Semantic tags are qualitative labels that preserve Phase 3's
    qualitative nature while providing structure for Phase 4.
    
    Examples:
        - RESTLESS (sleep quality)
        - ANXIOUS (mood)
        - HIGH (workload)
        - LIMITED (social support)
    """
    tag_id: str
    tag_label: str
    domain: str
    description: str
    
    @classmethod
    def from_descriptor(cls, descriptor: str, domain: str = "general") -> "SemanticTag":
        """
        Create a SemanticTag from a qualitative descriptor.
        
        Args:
            descriptor: Qualitative descriptor (e.g., "restless")
            domain: Domain context (e.g., "physiological")
            
        Returns:
            SemanticTag object
        """
        tag_id = f"{domain}_{descriptor}".lower()
        
        return cls(
            tag_id=tag_id,
            tag_label=descriptor,
            domain=domain,
            description=f"{descriptor.capitalize()} state in {domain} domain"
        )


class SemanticTagMapper:
    """
    Helper mapper for converting raw descriptors to semantic tags.
    
    This mapper handles the translation of raw qualitative descriptors
    (strings) into structured SemanticTag objects that can be used
    throughout the encoding layer.
    
    Example:
        Input: "restless" (domain: "sleep_quality")
        Output: SemanticTag(tag_id="sleep_quality_restless", ...)
    """
    
    def __init__(self, predefined_tags: Optional[Dict[str, SemanticTag]] = None):
        """
        Initialize mapper with predefined semantic tags.
        
        Args:
            predefined_tags: Dictionary of predefined tags (key: tag_id)
        """
        self.predefined_tags = predefined_tags or {}
    
    def map_descriptor(self, descriptor: str, domain: str = "general") -> SemanticTag:
        """
        Map a descriptor string to a SemanticTag.
        
        Args:
            descriptor: Qualitative descriptor
            domain: Domain context
            
        Returns:
            SemanticTag object
        """
        tag_id = f"{domain}_{descriptor}".lower()
        
        # Check if predefined
        if tag_id in self.predefined_tags:
            return self.predefined_tags[tag_id]
        
        # Create new tag
        return SemanticTag.from_descriptor(descriptor, domain)
    
    def map_descriptor_dict(self, descriptors: Dict[str, str], 
                           domain: str = "general") -> Dict[str, SemanticTag]:
        """
        Map a dictionary of descriptors to semantic tags.
        
        Args:
            descriptors: Dictionary of field → descriptor pairs
            domain: Domain context
            
        Returns:
            Dictionary of field → SemanticTag pairs
        """
        return {
            field: self.map_descriptor(descriptor, f"{domain}_{field}")
            for field, descriptor in descriptors.items()
        }
    
    def register_tag(self, tag: SemanticTag) -> None:
        """
        Register a predefined semantic tag.
        
        Args:
            tag: SemanticTag to register
        """
        self.predefined_tags[tag.tag_id] = tag
    
    def get_tags_for_domain(self, domain: str) -> List[SemanticTag]:
        """
        Get all predefined tags for a specific domain.
        
        Args:
            domain: Domain name
            
        Returns:
            List of SemanticTags in that domain
        """
        return [
            tag for tag in self.predefined_tags.values()
            if tag.domain == domain
        ]
