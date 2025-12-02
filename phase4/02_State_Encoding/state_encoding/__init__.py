"""
State Encoding Layer for 3QP Phase 4

This module provides the canonical state encoding infrastructure that transforms
semantic schemas, observations, and qualitative descriptors into structured
representations consumable by downstream computational components.

The State Encoding Layer is a pure representation layer:
- It does NOT perform simulation
- It does NOT compute transitions or probabilities
- It does NOT implement scoring or heuristics
- It ONLY transforms, validates, and structures data

Core Components:
- interfaces: Abstract base classes defining encoding contracts
- encoders: Concrete implementations transforming schemas to encoded states
- validators: Consistency and alignment checking for encoded states
- mappers: Bridges from unstructured observations to semantic schemas
"""

from state_encoding.interfaces import (
    StateEncoder,
    ObservationMapper,
    SchemaBinder,
    EncodingResult
)

from state_encoding.encoders import (
    BaselineStateEncoder,
    ScenarioEventEncoder,
    PatternIndicatorEncoder,
    ThreadIndicatorEncoder
)

from state_encoding.validators import (
    EncodedStateValidator,
    SchemaAlignmentValidator,
    DomainConsistencyValidator,
    ValidationResult
)

from state_encoding.mappers import (
    ObservationToSchemaMapper,
    NarrativeToEventMapper,
    QualitativeDescriptorMapper
)

__all__ = [
    # Interfaces
    'StateEncoder',
    'ObservationMapper',
    'SchemaBinder',
    'EncodingResult',
    
    # Encoders
    'BaselineStateEncoder',
    'ScenarioEventEncoder',
    'PatternIndicatorEncoder',
    'ThreadIndicatorEncoder',
    
    # Validators
    'EncodedStateValidator',
    'SchemaAlignmentValidator',
    'DomainConsistencyValidator',
    'ValidationResult',
    
    # Mappers
    'ObservationToSchemaMapper',
    'NarrativeToEventMapper',
    'QualitativeDescriptorMapper',
]

__version__ = '0.1.0'
