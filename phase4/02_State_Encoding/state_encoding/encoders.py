"""
Concrete StateEncoder implementations for transforming semantic schemas
into canonical encoded state representations.

This module provides encoders for:
- Baseline profiles → encoded baseline state
- Scenario events → encoded event fragments
- Pattern indicators → encoded pattern hints
- Thread indicators → encoded relational hints

All encoders preserve semantic fidelity from Phase 3 and output
structured representations without performing computation, inference,
or scoring.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from state_encoding.interfaces import StateEncoder, EncodingResult, EncodingStatus


@dataclass
class BaselineProfile:
    """
    Semantic schema representing a baseline profile.
    
    This is a minimal example schema object. In Workstream 1,
    this would be defined with full semantic richness.
    """
    profile_id: str
    physiological_state: Dict[str, str]
    psychological_state: Dict[str, str]
    social_state: Dict[str, str]
    environmental_context: Dict[str, str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScenarioEvent:
    """
    Semantic schema representing a scenario event.
    
    Events capture discrete occurrences within a scenario timeline.
    """
    event_id: str
    event_type: str
    timestamp: Optional[str]
    actors: List[str]
    descriptors: Dict[str, str]
    context: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternIndicator:
    """
    Semantic schema representing a pattern indicator.
    
    Pattern indicators are hints about potential patterns present
    in a state, without performing actual pattern recognition.
    """
    indicator_id: str
    pattern_type: str
    indicators: List[str]
    confidence_level: str  # qualitative: "strong", "moderate", "weak"
    context: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreadIndicator:
    """
    Semantic schema representing a thread/relational indicator.
    
    Thread indicators capture cross-module relationships and
    connections without performing relational computation.
    """
    thread_id: str
    thread_type: str
    related_entities: List[str]
    relationship_descriptors: Dict[str, str]
    context: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaselineStateEncoder(StateEncoder):
    """
    Encoder for transforming baseline profiles into encoded states.
    
    The BaselineStateEncoder takes a BaselineProfile (semantic schema from
    Workstream 1) and produces a canonical encoded state representation
    suitable for downstream consumption.
    
    Output Structure:
        {
            "profile_id": str,
            "domains": {
                "physiological": {...},
                "psychological": {...},
                "social": {...},
                "environmental": {...}
            },
            "encoding_metadata": {...}
        }
    """
    
    def __init__(self, schema_version: str = "1.0.0"):
        self.schema_version = schema_version
    
    def encode(self, schema_object: Any) -> EncodingResult:
        """Transform a BaselineProfile into an encoded state."""
        if not self.validate_input(schema_object):
            return EncodingResult(
                status=EncodingStatus.INVALID_INPUT,
                encoded_state=None,
                metadata={"encoder": "BaselineStateEncoder"},
                errors=["Invalid input: expected BaselineProfile"],
                source_reference=None
            )
        
        profile = schema_object
        
        encoded_state = {
            "profile_id": profile.profile_id,
            "domains": {
                "physiological": profile.physiological_state,
                "psychological": profile.psychological_state,
                "social": profile.social_state,
                "environmental": profile.environmental_context
            },
            "encoding_metadata": {
                "encoder_version": self.schema_version,
                "encoder_type": "baseline",
                "original_metadata": profile.metadata
            }
        }
        
        return EncodingResult(
            status=EncodingStatus.SUCCESS,
            encoded_state=encoded_state,
            metadata={
                "encoder": "BaselineStateEncoder",
                "schema_version": self.schema_version,
                "profile_id": profile.profile_id
            },
            errors=[],
            source_reference=profile.profile_id
        )
    
    def validate_input(self, schema_object: Any) -> bool:
        """Validate that input is a BaselineProfile."""
        if not isinstance(schema_object, BaselineProfile):
            return False
        
        # Check required fields
        required_attrs = [
            'profile_id', 'physiological_state', 'psychological_state',
            'social_state', 'environmental_context'
        ]
        return all(hasattr(schema_object, attr) for attr in required_attrs)
    
    def get_schema_version(self) -> str:
        """Return the semantic schema version."""
        return self.schema_version
    
    def to_narrative(self, encoded_state: Dict[str, Any]) -> str:
        """Convert encoded state to human-readable narrative."""
        profile_id = encoded_state.get("profile_id", "Unknown")
        domains = encoded_state.get("domains", {})
        
        narrative_parts = [f"Baseline Profile: {profile_id}"]
        
        for domain_name, domain_state in domains.items():
            narrative_parts.append(f"\n{domain_name.capitalize()}:")
            for key, value in domain_state.items():
                narrative_parts.append(f"  - {key}: {value}")
        
        return "\n".join(narrative_parts)


class ScenarioEventEncoder(StateEncoder):
    """
    Encoder for transforming scenario events into encoded event fragments.
    
    The ScenarioEventEncoder processes discrete events from scenario
    timelines and produces structured event representations that can
    be sequenced and analyzed by downstream components.
    
    Output Structure:
        {
            "event_id": str,
            "event_type": str,
            "temporal_context": {...},
            "actors": [...],
            "descriptors": {...},
            "context": {...},
            "encoding_metadata": {...}
        }
    """
    
    def __init__(self, schema_version: str = "1.0.0"):
        self.schema_version = schema_version
    
    def encode(self, schema_object: Any) -> EncodingResult:
        """Transform a ScenarioEvent into an encoded event fragment."""
        if not self.validate_input(schema_object):
            return EncodingResult(
                status=EncodingStatus.INVALID_INPUT,
                encoded_state=None,
                metadata={"encoder": "ScenarioEventEncoder"},
                errors=["Invalid input: expected ScenarioEvent"],
                source_reference=None
            )
        
        event = schema_object
        
        encoded_state = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "temporal_context": {
                "timestamp": event.timestamp
            },
            "actors": event.actors,
            "descriptors": event.descriptors,
            "context": event.context,
            "encoding_metadata": {
                "encoder_version": self.schema_version,
                "encoder_type": "scenario_event",
                "original_metadata": event.metadata
            }
        }
        
        return EncodingResult(
            status=EncodingStatus.SUCCESS,
            encoded_state=encoded_state,
            metadata={
                "encoder": "ScenarioEventEncoder",
                "schema_version": self.schema_version,
                "event_id": event.event_id,
                "event_type": event.event_type
            },
            errors=[],
            source_reference=event.event_id
        )
    
    def validate_input(self, schema_object: Any) -> bool:
        """Validate that input is a ScenarioEvent."""
        if not isinstance(schema_object, ScenarioEvent):
            return False
        
        required_attrs = [
            'event_id', 'event_type', 'actors', 'descriptors', 'context'
        ]
        return all(hasattr(schema_object, attr) for attr in required_attrs)
    
    def get_schema_version(self) -> str:
        """Return the semantic schema version."""
        return self.schema_version
    
    def to_narrative(self, encoded_state: Dict[str, Any]) -> str:
        """Convert encoded event to human-readable narrative."""
        event_id = encoded_state.get("event_id", "Unknown")
        event_type = encoded_state.get("event_type", "Unknown")
        actors = encoded_state.get("actors", [])
        descriptors = encoded_state.get("descriptors", {})
        
        narrative = f"Event: {event_id} (Type: {event_type})\n"
        narrative += f"Actors: {', '.join(actors)}\n"
        narrative += "Descriptors:\n"
        for key, value in descriptors.items():
            narrative += f"  - {key}: {value}\n"
        
        return narrative


class PatternIndicatorEncoder(StateEncoder):
    """
    Encoder for transforming pattern indicators into encoded pattern hints.
    
    The PatternIndicatorEncoder structures pattern indicators (semantic
    hints about potential patterns) into a format consumable by the
    pattern recognition engine (Workstream 3).
    
    Important: This encoder does NOT perform pattern recognition or
    classification. It only structures hints provided in the schema.
    
    Output Structure:
        {
            "indicator_id": str,
            "pattern_type": str,
            "indicators": [...],
            "confidence_level": str,
            "context": {...},
            "encoding_metadata": {...}
        }
    """
    
    def __init__(self, schema_version: str = "1.0.0"):
        self.schema_version = schema_version
    
    def encode(self, schema_object: Any) -> EncodingResult:
        """Transform a PatternIndicator into encoded pattern hints."""
        if not self.validate_input(schema_object):
            return EncodingResult(
                status=EncodingStatus.INVALID_INPUT,
                encoded_state=None,
                metadata={"encoder": "PatternIndicatorEncoder"},
                errors=["Invalid input: expected PatternIndicator"],
                source_reference=None
            )
        
        indicator = schema_object
        
        encoded_state = {
            "indicator_id": indicator.indicator_id,
            "pattern_type": indicator.pattern_type,
            "indicators": indicator.indicators,
            "confidence_level": indicator.confidence_level,
            "context": indicator.context,
            "encoding_metadata": {
                "encoder_version": self.schema_version,
                "encoder_type": "pattern_indicator",
                "original_metadata": indicator.metadata
            }
        }
        
        return EncodingResult(
            status=EncodingStatus.SUCCESS,
            encoded_state=encoded_state,
            metadata={
                "encoder": "PatternIndicatorEncoder",
                "schema_version": self.schema_version,
                "indicator_id": indicator.indicator_id,
                "pattern_type": indicator.pattern_type
            },
            errors=[],
            source_reference=indicator.indicator_id
        )
    
    def validate_input(self, schema_object: Any) -> bool:
        """Validate that input is a PatternIndicator."""
        if not isinstance(schema_object, PatternIndicator):
            return False
        
        required_attrs = [
            'indicator_id', 'pattern_type', 'indicators', 
            'confidence_level', 'context'
        ]
        return all(hasattr(schema_object, attr) for attr in required_attrs)
    
    def get_schema_version(self) -> str:
        """Return the semantic schema version."""
        return self.schema_version
    
    def to_narrative(self, encoded_state: Dict[str, Any]) -> str:
        """Convert encoded pattern hints to human-readable narrative."""
        indicator_id = encoded_state.get("indicator_id", "Unknown")
        pattern_type = encoded_state.get("pattern_type", "Unknown")
        indicators = encoded_state.get("indicators", [])
        confidence = encoded_state.get("confidence_level", "Unknown")
        
        narrative = f"Pattern Indicator: {indicator_id}\n"
        narrative += f"Pattern Type: {pattern_type}\n"
        narrative += f"Confidence: {confidence}\n"
        narrative += f"Indicators: {', '.join(indicators)}\n"
        
        return narrative


class ThreadIndicatorEncoder(StateEncoder):
    """
    Encoder for transforming thread indicators into encoded relational hints.
    
    The ThreadIndicatorEncoder structures cross-module relational hints
    into a format that downstream components can use to understand
    connections without performing relational computation.
    
    Output Structure:
        {
            "thread_id": str,
            "thread_type": str,
            "related_entities": [...],
            "relationship_descriptors": {...},
            "context": {...},
            "encoding_metadata": {...}
        }
    """
    
    def __init__(self, schema_version: str = "1.0.0"):
        self.schema_version = schema_version
    
    def encode(self, schema_object: Any) -> EncodingResult:
        """Transform a ThreadIndicator into encoded relational hints."""
        if not self.validate_input(schema_object):
            return EncodingResult(
                status=EncodingStatus.INVALID_INPUT,
                encoded_state=None,
                metadata={"encoder": "ThreadIndicatorEncoder"},
                errors=["Invalid input: expected ThreadIndicator"],
                source_reference=None
            )
        
        thread = schema_object
        
        encoded_state = {
            "thread_id": thread.thread_id,
            "thread_type": thread.thread_type,
            "related_entities": thread.related_entities,
            "relationship_descriptors": thread.relationship_descriptors,
            "context": thread.context,
            "encoding_metadata": {
                "encoder_version": self.schema_version,
                "encoder_type": "thread_indicator",
                "original_metadata": thread.metadata
            }
        }
        
        return EncodingResult(
            status=EncodingStatus.SUCCESS,
            encoded_state=encoded_state,
            metadata={
                "encoder": "ThreadIndicatorEncoder",
                "schema_version": self.schema_version,
                "thread_id": thread.thread_id,
                "thread_type": thread.thread_type
            },
            errors=[],
            source_reference=thread.thread_id
        )
    
    def validate_input(self, schema_object: Any) -> bool:
        """Validate that input is a ThreadIndicator."""
        if not isinstance(schema_object, ThreadIndicator):
            return False
        
        required_attrs = [
            'thread_id', 'thread_type', 'related_entities',
            'relationship_descriptors', 'context'
        ]
        return all(hasattr(schema_object, attr) for attr in required_attrs)
    
    def get_schema_version(self) -> str:
        """Return the semantic schema version."""
        return self.schema_version
    
    def to_narrative(self, encoded_state: Dict[str, Any]) -> str:
        """Convert encoded thread hints to human-readable narrative."""
        thread_id = encoded_state.get("thread_id", "Unknown")
        thread_type = encoded_state.get("thread_type", "Unknown")
        entities = encoded_state.get("related_entities", [])
        descriptors = encoded_state.get("relationship_descriptors", {})
        
        narrative = f"Thread: {thread_id} (Type: {thread_type})\n"
        narrative += f"Related Entities: {', '.join(entities)}\n"
        narrative += "Relationships:\n"
        for key, value in descriptors.items():
            narrative += f"  - {key}: {value}\n"
        
        return narrative
