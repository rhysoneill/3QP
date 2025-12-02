"""
Qualitative evidence system for pattern recognition.

Defines non-numeric evidence structures supporting pattern identification.
NO scoring, probabilities, or confidence metrics.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class QualitativeStrength(Enum):
    """Qualitative strength indicators - NO NUMERIC VALUES."""
    
    SUGGESTIVE = "suggestive"
    WEAK = "weak"
    STRONG = "strong"
    CONTEXTUAL = "contextual"
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if value is a valid qualitative strength."""
        try:
            cls(value)
            return True
        except ValueError:
            return False


@dataclass
class PatternEvidence:
    """
    A single qualitative indicator supporting a pattern.
    
    Contains NO numeric scoring or probability - only qualitative descriptions
    and contextual information.
    """
    
    pattern_type: str
    indicator_label: str
    qualitative_strength: str
    narrative: str
    source_event: Optional[str] = None
    source_state: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate evidence structure on creation."""
        if not self.pattern_type:
            raise ValueError("pattern_type cannot be empty")
        
        if not self.indicator_label:
            raise ValueError("indicator_label cannot be empty")
        
        if not self.narrative:
            raise ValueError("narrative cannot be empty")
        
        # Validate qualitative strength
        if not QualitativeStrength.is_valid(self.qualitative_strength):
            valid_values = [s.value for s in QualitativeStrength]
            raise ValueError(
                f"qualitative_strength must be one of {valid_values}, "
                f"got '{self.qualitative_strength}'"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert evidence to dictionary representation.
        
        Returns:
            Dictionary representation
        """
        return {
            "pattern_type": self.pattern_type,
            "indicator_label": self.indicator_label,
            "qualitative_strength": self.qualitative_strength,
            "narrative": self.narrative,
            "source_event": self.source_event,
            "source_state": self.source_state,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def to_narrative(self) -> str:
        """
        Generate human-readable narrative.
        
        Returns:
            Narrative description
        """
        parts = [
            f"[{self.qualitative_strength.upper()}] {self.indicator_label}",
            f"Pattern: {self.pattern_type}",
            f"Description: {self.narrative}",
        ]
        
        if self.source_event:
            parts.append(f"Source Event: {self.source_event}")
        
        if self.source_state:
            parts.append(f"Source State: {self.source_state}")
        
        return " | ".join(parts)


@dataclass
class PatternEvidenceBundle:
    """
    Collection of evidence objects supporting pattern recognition.
    
    Organized by domain, thread, or recognizer. Contains NO numerical
    weighting, normalization, scores, or confidence metrics.
    """
    
    evidence_items: List[PatternEvidence] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_evidence(self, evidence: PatternEvidence) -> None:
        """
        Add evidence to the bundle.
        
        Args:
            evidence: PatternEvidence to add
        """
        if not isinstance(evidence, PatternEvidence):
            raise TypeError("evidence must be a PatternEvidence instance")
        
        self.evidence_items.append(evidence)
    
    def merge(self, other: 'PatternEvidenceBundle') -> 'PatternEvidenceBundle':
        """
        Merge another evidence bundle into this one.
        
        Args:
            other: Another PatternEvidenceBundle to merge
        
        Returns:
            New merged PatternEvidenceBundle
        
        Note:
            Creates a new bundle - does NOT modify existing bundles
        """
        if not isinstance(other, PatternEvidenceBundle):
            raise TypeError("other must be a PatternEvidenceBundle instance")
        
        merged = PatternEvidenceBundle(
            evidence_items=self.evidence_items.copy() + other.evidence_items.copy(),
            metadata={
                **self.metadata,
                "merged_from": [
                    self.metadata.get("bundle_id", "unknown"),
                    other.metadata.get("bundle_id", "unknown"),
                ],
                "merged_at": datetime.now().isoformat(),
            },
        )
        
        return merged
    
    def filter_by_pattern_type(self, pattern_type: str) -> List[PatternEvidence]:
        """
        Filter evidence by pattern type.
        
        Args:
            pattern_type: Pattern type to filter by
        
        Returns:
            List of matching evidence items
        """
        return [
            evidence for evidence in self.evidence_items
            if evidence.pattern_type == pattern_type
        ]
    
    def filter_by_strength(self, strength: str) -> List[PatternEvidence]:
        """
        Filter evidence by qualitative strength.
        
        Args:
            strength: Qualitative strength to filter by
        
        Returns:
            List of matching evidence items
        """
        if not QualitativeStrength.is_valid(strength):
            raise ValueError(f"Invalid qualitative strength: {strength}")
        
        return [
            evidence for evidence in self.evidence_items
            if evidence.qualitative_strength == strength
        ]
    
    def get_pattern_types(self) -> List[str]:
        """
        Get all unique pattern types in this bundle.
        
        Returns:
            List of unique pattern types
        """
        return list(set(
            evidence.pattern_type
            for evidence in self.evidence_items
        ))
    
    def get_evidence_count(self) -> int:
        """
        Get total count of evidence items.
        
        Returns:
            Count of evidence items
        """
        return len(self.evidence_items)
    
    def get_evidence_by_pattern(self) -> Dict[str, List[PatternEvidence]]:
        """
        Group evidence by pattern type.
        
        Returns:
            Dictionary mapping pattern types to evidence lists
        """
        grouped: Dict[str, List[PatternEvidence]] = {}
        
        for evidence in self.evidence_items:
            if evidence.pattern_type not in grouped:
                grouped[evidence.pattern_type] = []
            grouped[evidence.pattern_type].append(evidence)
        
        return grouped
    
    def to_narrative(self) -> str:
        """
        Generate human-readable narrative summary.
        
        Returns:
            Narrative description of all evidence
        """
        if not self.evidence_items:
            return "No evidence in bundle."
        
        lines = [
            f"Evidence Bundle: {self.get_evidence_count()} items",
            f"Pattern Types: {', '.join(self.get_pattern_types())}",
            "",
        ]
        
        # Group by pattern type
        by_pattern = self.get_evidence_by_pattern()
        
        for pattern_type, evidence_list in by_pattern.items():
            lines.append(f"{pattern_type} ({len(evidence_list)} items):")
            for evidence in evidence_list:
                lines.append(f"  • {evidence.to_narrative()}")
            lines.append("")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert bundle to dictionary representation.
        
        Returns:
            Dictionary representation
        """
        return {
            "evidence_items": [item.to_dict() for item in self.evidence_items],
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "evidence_count": self.get_evidence_count(),
            "pattern_types": self.get_pattern_types(),
        }
