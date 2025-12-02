"""
Core interfaces and abstract base classes for the State Encoding Layer.

These interfaces define the contracts for all encoding operations within
the 3QP Phase 4 architecture. They establish clear boundaries between:
- Semantic schema representation (input)
- Encoded state representation (output)
- Validation and consistency checking
- Observation-to-schema mapping

All interfaces are purely structural — they define WHAT must be provided,
not HOW computation should occur.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class EncodingStatus(Enum):
    """Status codes for encoding operations."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    INVALID_INPUT = "invalid_input"


@dataclass
class EncodingResult:
    """
    Result container for state encoding operations.
    
    The EncodingResult represents the outcome of transforming semantic
    schemas or observations into canonical encoded state representations.
    
    Conceptual Role in 3QP:
    - Provides a standard interface for all encoding operations
    - Enables downstream components to uniformly consume encoded states
    - Separates encoding success/failure from computational logic
    - Maintains traceability from raw input to structured representation
    
    Fields:
        status: Success/failure status of encoding
        encoded_state: The canonical state representation (dict or structured object)
        metadata: Additional context about the encoding (schemas used, timestamps, etc.)
        errors: List of error messages if encoding failed or was partial
        source_reference: Optional reference to original input for traceability
    """
    status: EncodingStatus
    encoded_state: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    errors: List[str]
    source_reference: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if encoding was successful and state is usable."""
        return self.status == EncodingStatus.SUCCESS and self.encoded_state is not None
    
    def to_narrative(self) -> str:
        """
        Convert encoded state to human-readable narrative.
        
        This method supports debugging and Phase 3 alignment by providing
        qualitative interpretations of encoded states.
        """
        raise NotImplementedError("Subclasses must implement to_narrative()")


class StateEncoder(ABC):
    """
    Abstract base class for all state encoders.
    
    Conceptual Role in 3QP:
    StateEncoders transform semantic schema objects (from Workstream 1) into
    canonical encoded state representations. These encoders are the bridge
    between qualitative semantic descriptions and structured data that
    downstream components (pattern recognition, trajectory classification,
    intervention reasoning) can process.
    
    Key Principles:
    - Encoders transform but do not compute
    - Encoders structure but do not infer
    - Encoders validate input alignment but do not score
    - Encoders preserve semantic fidelity from Phase 3
    
    Subclasses will implement specific encoding strategies for:
    - Baseline profiles
    - Scenario events
    - Pattern indicators
    - Thread relational hints
    """
    
    @abstractmethod
    def encode(self, schema_object: Any) -> EncodingResult:
        """
        Transform a semantic schema object into an encoded state.
        
        Args:
            schema_object: A semantic schema from Workstream 1
            
        Returns:
            EncodingResult containing the canonical encoded state
            
        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement encode()")
    
    @abstractmethod
    def validate_input(self, schema_object: Any) -> bool:
        """
        Validate that input schema is compatible with this encoder.
        
        Args:
            schema_object: A semantic schema to validate
            
        Returns:
            True if schema is compatible, False otherwise
        """
        raise NotImplementedError("Subclasses must implement validate_input()")
    
    @abstractmethod
    def get_schema_version(self) -> str:
        """
        Return the semantic schema version this encoder supports.
        
        Returns:
            Version string (e.g., "1.0.0")
        """
        raise NotImplementedError("Subclasses must implement get_schema_version()")


class ObservationMapper(ABC):
    """
    Abstract base class for observation-to-schema mapping.
    
    Conceptual Role in 3QP:
    ObservationMappers bridge the gap between raw/unstructured observations
    and semantic schema objects. They handle the translation of:
    - Qualitative descriptors → semantic tags
    - Narrative event notes → structured event objects
    - Textual assessments → schema-compliant representations
    
    Key Principles:
    - Mappers do NOT perform NLP or inference
    - Mappers do NOT classify or recognize patterns
    - Mappers ONLY perform direct, rule-based translation
    - Mappers rely on explicit input structure (provided by test suite)
    
    Example:
        Input: {"sleep_quality": "restless"}
        Output: SemanticTag.RESTLESS (from Workstream 1 schema)
    """
    
    @abstractmethod
    def map(self, observation: Dict[str, Any]) -> Any:
        """
        Map an observation to a semantic schema object.
        
        Args:
            observation: Unstructured or semi-structured observation data
            
        Returns:
            A semantic schema object from Workstream 1
            
        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement map()")
    
    @abstractmethod
    def supports_observation_type(self, observation_type: str) -> bool:
        """
        Check if this mapper supports a given observation type.
        
        Args:
            observation_type: Type identifier (e.g., "physiological", "behavioral")
            
        Returns:
            True if supported, False otherwise
        """
        raise NotImplementedError("Subclasses must implement supports_observation_type()")
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """
        Return list of required fields for mapping.
        
        Returns:
            List of field names that must be present in observation
        """
        raise NotImplementedError("Subclasses must implement get_required_fields()")


class SchemaBinder(ABC):
    """
    Abstract base class for binding encoded states to semantic schemas.
    
    Conceptual Role in 3QP:
    SchemaB inders ensure that encoded states remain aligned with their
    originating semantic schemas throughout the Phase 4 pipeline. They:
    - Track schema provenance
    - Verify schema compatibility
    - Maintain semantic version alignment
    - Enable schema evolution without breaking encoded states
    
    This is critical for maintaining Phase 3's qualitative integrity as
    states flow through computational components.
    """
    
    @abstractmethod
    def bind(self, encoded_state: Dict[str, Any], schema_id: str) -> Dict[str, Any]:
        """
        Bind an encoded state to a semantic schema.
        
        Args:
            encoded_state: The encoded state representation
            schema_id: Identifier of the semantic schema
            
        Returns:
            Encoded state with schema binding metadata
            
        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement bind()")
    
    @abstractmethod
    def verify_binding(self, encoded_state: Dict[str, Any]) -> bool:
        """
        Verify that an encoded state has valid schema binding.
        
        Args:
            encoded_state: The encoded state to verify
            
        Returns:
            True if binding is valid, False otherwise
        """
        raise NotImplementedError("Subclasses must implement verify_binding()")
    
    @abstractmethod
    def get_bound_schema_id(self, encoded_state: Dict[str, Any]) -> Optional[str]:
        """
        Extract the schema ID bound to an encoded state.
        
        Args:
            encoded_state: The encoded state
            
        Returns:
            Schema ID if bound, None otherwise
        """
        raise NotImplementedError("Subclasses must implement get_bound_schema_id()")
