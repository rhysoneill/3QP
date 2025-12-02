"""
Trajectory Analysis Architecture (Phase 4 / Workstream 4)

This package provides the architectural layer for trajectory analysis
and classification in the 3QP system. It defines interfaces, data models,
evidence structures, and validators for trajectory-level reasoning.

IMPORTANT: This is a pure architecture layer with ZERO computation.
No actual trajectory detection, scoring, or machine learning is performed.
All components are structural placeholders for future implementation.

Public API:
-----------

Interfaces:
    - TrajectoryAnalyzer: ABC for trajectory sequence analysis
    - TrajectoryClassifier: ABC for trajectory classification
    - TrajectoryAggregationEngine: ABC for aggregating multiple analyses

Data Models:
    - TrajectoryHypothesis: Qualitative trajectory pattern hypothesis
    - TrajectoryAnalysisResult: Output from trajectory analyzer
    - TrajectoryClassificationResult: Final trajectory classification

Evidence:
    - TrajectorySupportStrength: Qualitative evidence strength enum
    - TrajectoryEvidence: Single evidence item
    - TrajectoryEvidenceBundle: Collection of evidence items

Analyzers (Placeholders):
    - SimpleTrajectoryAnalyzer: Minimal placeholder analyzer
    - StableAdaptationAnalyzer: Placeholder for stable_adaptation archetype
    - TrajectoryHeuristicClassifier: Placeholder classifier
    - SimpleAggregationEngine: Placeholder aggregation engine

Registry:
    - TrajectoryAnalysisRegistry: Central component registry
    - create_default_registry: Factory for pre-populated registry

Validators:
    - ValidationResult: Validation outcome container
    - TrajectoryEvidenceValidator: Evidence validation
    - TrajectoryResultValidator: Result validation
    - SequenceInputValidator: Input validation

Version: 0.1.0
"""

__version__ = "0.1.0"

# Core interfaces
from .interfaces import (
    TrajectoryAnalyzer,
    TrajectoryClassifier,
    TrajectoryAggregationEngine
)

# Data models
from .models import (
    TrajectoryHypothesis,
    TrajectoryAnalysisResult,
    TrajectoryClassificationResult
)

# Evidence structures
from .evidence import (
    TrajectorySupportStrength,
    TrajectoryEvidence,
    TrajectoryEvidenceBundle
)

# Placeholder analyzers and classifiers
from .analyzers import (
    SimpleTrajectoryAnalyzer,
    StableAdaptationAnalyzer,
    TrajectoryHeuristicClassifier,
    SimpleAggregationEngine
)

# Registry
from .registry import (
    TrajectoryAnalysisRegistry,
    create_default_registry
)

# Validators
from .validators import (
    ValidationResult,
    TrajectoryEvidenceValidator,
    TrajectoryResultValidator,
    SequenceInputValidator
)

__all__ = [
    # Version
    "__version__",
    
    # Interfaces
    "TrajectoryAnalyzer",
    "TrajectoryClassifier",
    "TrajectoryAggregationEngine",
    
    # Data models
    "TrajectoryHypothesis",
    "TrajectoryAnalysisResult",
    "TrajectoryClassificationResult",
    
    # Evidence
    "TrajectorySupportStrength",
    "TrajectoryEvidence",
    "TrajectoryEvidenceBundle",
    
    # Analyzers
    "SimpleTrajectoryAnalyzer",
    "StableAdaptationAnalyzer",
    "TrajectoryHeuristicClassifier",
    "SimpleAggregationEngine",
    
    # Registry
    "TrajectoryAnalysisRegistry",
    "create_default_registry",
    
    # Validators
    "ValidationResult",
    "TrajectoryEvidenceValidator",
    "TrajectoryResultValidator",
    "SequenceInputValidator",
]
