"""
Qualitative evidence structures for trajectory analysis.

This module defines evidence items, support strength levels, and evidence
bundles used in trajectory analysis. All evidence is qualitative and
structural—no numeric scoring is performed.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TrajectorySupportStrength(Enum):
    """
    Qualitative strength levels for trajectory evidence.
    
    No numeric values are assigned. These are purely categorical
    descriptors of evidence quality and contextual relevance.
    """
    SUGGESTIVE = "suggestive"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    CONTEXTUAL_ONLY = "contextual_only"
    
    @classmethod
    def is_valid(cls, value) -> bool:
        """
        Check if a value is a valid support strength.
        
        Args:
            value: Value to check (enum member or string)
            
        Returns:
            True if valid, False otherwise
        """
        if isinstance(value, cls):
            return True
        if isinstance(value, str):
            return value in [member.value for member in cls]
        return False


@dataclass
class TrajectoryEvidence:
    """
    A single qualitative evidence item for trajectory analysis.
    
    Evidence items reference specific archetypes and provide narrative
    explanations of why a particular trajectory pattern may be present.
    """
    archetype_id: str
    support_strength: TrajectorySupportStrength
    narrative: str
    source_pattern_type: Optional[str] = None
    source_event_id: Optional[str] = None
    source_state_id: Optional[str] = None
    metadata: Optional[dict[str, str]] = None
    
    def __post_init__(self):
        """Validate evidence fields."""
        if not self.archetype_id or not isinstance(self.archetype_id, str):
            raise ValueError("archetype_id must be a non-empty string")
        
        if not self.narrative or not isinstance(self.narrative, str):
            raise ValueError("narrative must be a non-empty string")
        
        if not isinstance(self.support_strength, TrajectorySupportStrength):
            raise ValueError(
                f"support_strength must be TrajectorySupportStrength enum, "
                f"got {type(self.support_strength)}"
            )
        
        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise ValueError("metadata must be dict or None")
    
    def to_narrative(self) -> str:
        """
        Generate narrative representation of this evidence.
        
        Returns:
            Human-readable description
        """
        source_info = []
        if self.source_pattern_type:
            source_info.append(f"pattern: {self.source_pattern_type}")
        if self.source_event_id:
            source_info.append(f"event: {self.source_event_id}")
        if self.source_state_id:
            source_info.append(f"state: {self.source_state_id}")
        
        source_str = f" ({', '.join(source_info)})" if source_info else ""
        
        return (
            f"[{self.support_strength.value.upper()}] "
            f"{self.archetype_id}: {self.narrative}{source_str}"
        )
    
    def to_dict(self) -> dict:
        """
        Convert evidence to dictionary representation.
        
        Returns:
            Dictionary with all evidence fields
        """
        return {
            "archetype_id": self.archetype_id,
            "support_strength": self.support_strength.value,
            "narrative": self.narrative,
            "source_pattern_type": self.source_pattern_type,
            "source_event_id": self.source_event_id,
            "source_state_id": self.source_state_id,
            "metadata": self.metadata or {}
        }


@dataclass
class TrajectoryEvidenceBundle:
    """
    Collection of trajectory evidence items.
    
    Provides filtering, grouping, and aggregation operations on
    evidence collections. All operations are structural only.
    """
    items: list[TrajectoryEvidence] = field(default_factory=list)
    
    def add(self, evidence: TrajectoryEvidence) -> None:
        """
        Add an evidence item to this bundle.
        
        Args:
            evidence: Evidence item to add
        """
        if not isinstance(evidence, TrajectoryEvidence):
            raise TypeError("evidence must be TrajectoryEvidence instance")
        self.items.append(evidence)
    
    def merge(self, other: "TrajectoryEvidenceBundle") -> "TrajectoryEvidenceBundle":
        """
        Merge with another evidence bundle.
        
        Returns a new bundle containing items from both. Original bundles
        are not modified.
        
        Args:
            other: Another evidence bundle to merge
            
        Returns:
            New merged TrajectoryEvidenceBundle
        """
        if not isinstance(other, TrajectoryEvidenceBundle):
            raise TypeError("other must be TrajectoryEvidenceBundle instance")
        
        return TrajectoryEvidenceBundle(items=self.items + other.items)
    
    def filter_by_archetype(self, archetype_id: str) -> "TrajectoryEvidenceBundle":
        """
        Filter evidence by archetype ID.
        
        Args:
            archetype_id: Archetype identifier to filter by
            
        Returns:
            New bundle with matching evidence items
        """
        filtered_items = [
            item for item in self.items
            if item.archetype_id == archetype_id
        ]
        return TrajectoryEvidenceBundle(items=filtered_items)
    
    def filter_by_strength(
        self,
        allowed: list[TrajectorySupportStrength]
    ) -> "TrajectoryEvidenceBundle":
        """
        Filter evidence by support strength levels.
        
        Args:
            allowed: List of allowed support strength values
            
        Returns:
            New bundle with matching evidence items
        """
        filtered_items = [
            item for item in self.items
            if item.support_strength in allowed
        ]
        return TrajectoryEvidenceBundle(items=filtered_items)
    
    def get_archetype_ids(self) -> list[str]:
        """
        Get unique archetype IDs from all evidence items.
        
        Returns:
            List of unique archetype identifiers
        """
        return list(set(item.archetype_id for item in self.items))
    
    def group_by_archetype(self) -> dict[str, list[TrajectoryEvidence]]:
        """
        Group evidence items by archetype ID.
        
        Returns:
            Dictionary mapping archetype IDs to evidence lists
        """
        groups: dict[str, list[TrajectoryEvidence]] = {}
        for item in self.items:
            if item.archetype_id not in groups:
                groups[item.archetype_id] = []
            groups[item.archetype_id].append(item)
        return groups
    
    def to_narrative(self) -> str:
        """
        Generate narrative representation of this bundle.
        
        Returns:
            Multi-line human-readable description
        """
        if not self.items:
            return "No trajectory evidence available."
        
        lines = [f"Trajectory Evidence Bundle ({len(self.items)} items):"]
        for item in self.items:
            lines.append(f"  - {item.to_narrative()}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """
        Convert bundle to dictionary representation.
        
        Returns:
            Dictionary with bundle metadata and items
        """
        return {
            "item_count": len(self.items),
            "archetype_ids": self.get_archetype_ids(),
            "items": [item.to_dict() for item in self.items]
        }
