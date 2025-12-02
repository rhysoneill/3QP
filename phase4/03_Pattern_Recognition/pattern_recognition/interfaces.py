"""
Core interfaces for the Pattern Recognition Engine.

Defines abstract base classes and result types for pattern recognition architecture.
NO COMPUTATION - only contracts and structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class PatternRecognitionResult:
    """
    Result of pattern recognition analysis.
    
    Contains qualitative pattern identifiers and evidence, but NO numeric scoring,
    probabilities, or confidence values.
    """
    
    recognized_patterns: List[str]  # Qualitative pattern identifiers
    evidence_bundle: Any  # PatternEvidenceBundle (imported later to avoid circular deps)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate result structure on creation."""
        if not isinstance(self.recognized_patterns, list):
            raise TypeError("recognized_patterns must be a list")
        
        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dict")
        
        # Ensure metadata contains required fields
        if "schema_version" not in self.metadata:
            self.metadata["schema_version"] = "unknown"
        
        if "recognizer_versions" not in self.metadata:
            self.metadata["recognizer_versions"] = {}
    
    def narrative_summary(self) -> str:
        """
        Generate human-readable narrative summary.
        
        Returns:
            Narrative description of recognized patterns
        """
        if not self.recognized_patterns:
            return "No patterns recognized in the provided state(s)."
        
        summary_lines = [
            f"Pattern Recognition Summary ({self.timestamp.isoformat()})",
            f"Schema Version: {self.metadata.get('schema_version', 'unknown')}",
            "",
            f"Recognized Patterns ({len(self.recognized_patterns)}):",
        ]
        
        for pattern in self.recognized_patterns:
            summary_lines.append(f"  - {pattern}")
        
        # Add evidence summary if available
        if self.evidence_bundle and hasattr(self.evidence_bundle, 'to_narrative'):
            summary_lines.append("")
            summary_lines.append("Evidence Summary:")
            summary_lines.append(self.evidence_bundle.to_narrative())
        
        return "\n".join(summary_lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary representation.
        
        Returns:
            Dictionary representation of the result
        """
        return {
            "recognized_patterns": self.recognized_patterns,
            "evidence_bundle": self.evidence_bundle.to_dict() if hasattr(self.evidence_bundle, 'to_dict') else None,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class PatternRecognizer(ABC):
    """
    Abstract base class for pattern recognizers.
    
    Defines the contract for analyzing encoded states and recognizing patterns.
    Implementations MUST NOT perform actual computation - only return structured
    placeholder results.
    """
    
    @abstractmethod
    def analyze_encoded_state(self, encoded_state: Dict[str, Any]) -> PatternRecognitionResult:
        """
        Analyze a single encoded state for patterns.
        
        Args:
            encoded_state: Encoded state from WS2 State Encoding Layer
        
        Returns:
            PatternRecognitionResult with placeholder evidence
        
        Note:
            This is a structural method only. Implementations should NOT perform
            actual pattern detection - only return properly formatted results.
        """
        pass
    
    @abstractmethod
    def analyze_sequence(self, encoded_states: List[Dict[str, Any]]) -> PatternRecognitionResult:
        """
        Analyze a sequence of encoded states for temporal patterns.
        
        Args:
            encoded_states: List of encoded states from WS2
        
        Returns:
            PatternRecognitionResult with placeholder evidence
        
        Note:
            This is a structural method only. Implementations should NOT perform
            actual sequence analysis - only return properly formatted results.
        """
        pass
    
    @abstractmethod
    def get_supported_pattern_types(self) -> List[str]:
        """
        Get list of pattern types this recognizer supports.
        
        Returns:
            List of pattern type identifiers
        """
        pass
    
    def get_version(self) -> str:
        """
        Get recognizer version.
        
        Returns:
            Version string
        """
        return getattr(self, '__version__', '0.1.0')
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get recognizer metadata.
        
        Returns:
            Dictionary of metadata
        """
        return {
            'recognizer_type': self.__class__.__name__,
            'version': self.get_version(),
            'supported_patterns': self.get_supported_pattern_types(),
        }


class SequenceAnalyzer(ABC):
    """
    Abstract base class for temporal pattern context analysis.
    
    Accepts sequences of encoded states and returns evidence bundles.
    NO COMPUTATION - only structural contracts.
    """
    
    @abstractmethod
    def analyze_temporal_context(
        self,
        encoded_states: List[Dict[str, Any]],
        window_size: Optional[int] = None
    ) -> Any:  # Returns PatternEvidenceBundle
        """
        Analyze temporal context across a sequence of states.
        
        Args:
            encoded_states: Sequence of encoded states from WS2
            window_size: Optional window size for context analysis
        
        Returns:
            PatternEvidenceBundle with placeholder evidence
        
        Note:
            This is a structural method only. NO actual temporal analysis.
        """
        pass
    
    @abstractmethod
    def get_sequence_requirements(self) -> Dict[str, Any]:
        """
        Get requirements for sequence analysis.
        
        Returns:
            Dictionary describing sequence requirements (min length, etc.)
        """
        pass


class PatternAggregationEngine(ABC):
    """
    Abstract base class for aggregating evidence from multiple recognizers.
    
    Combines evidence and produces unified recognition results.
    NO COMPUTATION - only structural aggregation.
    """
    
    @abstractmethod
    def aggregate_evidence(
        self,
        recognition_results: List[PatternRecognitionResult]
    ) -> PatternRecognitionResult:
        """
        Aggregate evidence from multiple recognition results.
        
        Args:
            recognition_results: List of results from different recognizers
        
        Returns:
            Unified PatternRecognitionResult
        
        Note:
            This is a structural method only. NO numeric weighting or scoring.
        """
        pass
    
    @abstractmethod
    def resolve_conflicts(
        self,
        conflicting_patterns: List[str]
    ) -> List[str]:
        """
        Resolve conflicts between recognized patterns.
        
        Args:
            conflicting_patterns: List of potentially conflicting pattern IDs
        
        Returns:
            Resolved list of patterns
        
        Note:
            This is a structural method only. Resolution is rule-based, not computed.
        """
        pass
