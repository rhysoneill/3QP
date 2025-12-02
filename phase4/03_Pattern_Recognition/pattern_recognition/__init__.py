"""
Pattern Recognition Engine
Phase 4 / Workstream 3

Pure architecture for pattern recognition - no computation.
Defines structures, contracts, and validators for recognizing qualitative patterns
using Semantic Schema Layer (WS1) and State Encoding Layer (WS2).

NO inference, algorithms, ML, or scoring - only types and interfaces.
"""

from .interfaces import (
    PatternRecognizer,
    SequenceAnalyzer,
    PatternAggregationEngine,
    PatternRecognitionResult,
)
from .evidence import (
    PatternEvidence,
    PatternEvidenceBundle,
)
from .recognizers import (
    StablePatternRecognizer,
    DriftPatternRecognizer,
    DisruptionPatternRecognizer,
    RecoveryPatternRecognizer,
)
from .registry import PatternRecognizerRegistry, create_default_registry
from .validators import (
    EvidenceValidator,
    RecognizerOutputValidator,
    SequenceValidator,
)

__version__ = "0.1.0"

__all__ = [
    # Interfaces
    "PatternRecognizer",
    "SequenceAnalyzer",
    "PatternAggregationEngine",
    "PatternRecognitionResult",
    # Evidence
    "PatternEvidence",
    "PatternEvidenceBundle",
    # Recognizers
    "StablePatternRecognizer",
    "DriftPatternRecognizer",
    "DisruptionPatternRecognizer",
    "RecoveryPatternRecognizer",
    # Registry
    "PatternRecognizerRegistry",
    "create_default_registry",
    # Validators
    "EvidenceValidator",
    "RecognizerOutputValidator",
    "SequenceValidator",
]
