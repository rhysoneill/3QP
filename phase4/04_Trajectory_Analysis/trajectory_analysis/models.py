"""
Core data models for trajectory analysis and classification.

This module defines the primary structural dataclasses for trajectory
hypotheses, analysis results, and classification results. All models
are qualitative and contain no numeric scoring.
"""

from dataclasses import dataclass, field
from typing import Optional

from .evidence import TrajectorySupportStrength, TrajectoryEvidenceBundle


@dataclass
class TrajectoryHypothesis:
    """
    Represents a hypothesis that a certain trajectory archetype is active.
    
    Hypotheses are qualitative assertions about trajectory patterns,
    supported by narrative rationale and evidence references.
    """
    archetype_id: str
    label: str
    support_strength: TrajectorySupportStrength
    rationale: str
    source_patterns: list[str] = field(default_factory=list)
    metadata: Optional[dict[str, str]] = None
    
    def __post_init__(self):
        """Validate hypothesis fields."""
        if not self.archetype_id or not isinstance(self.archetype_id, str):
            raise ValueError("archetype_id must be a non-empty string")
        
        if not self.label or not isinstance(self.label, str):
            raise ValueError("label must be a non-empty string")
        
        if not self.rationale or not isinstance(self.rationale, str):
            raise ValueError("rationale must be a non-empty string")
        
        if not isinstance(self.support_strength, TrajectorySupportStrength):
            raise ValueError(
                f"support_strength must be TrajectorySupportStrength enum, "
                f"got {type(self.support_strength)}"
            )
        
        if not isinstance(self.source_patterns, list):
            raise ValueError("source_patterns must be a list")
        
        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise ValueError("metadata must be dict or None")
    
    def to_narrative(self) -> str:
        """
        Generate narrative representation of this hypothesis.
        
        Returns:
            Single paragraph describing the hypothesis
        """
        pattern_info = ""
        if self.source_patterns:
            pattern_list = ", ".join(self.source_patterns)
            pattern_info = f" This hypothesis is supported by patterns: {pattern_list}."
        
        return (
            f"{self.label} ({self.archetype_id}): {self.rationale} "
            f"[Support: {self.support_strength.value}]{pattern_info}"
        )


@dataclass
class TrajectoryAnalysisResult:
    """
    Represents the output of a trajectory analyzer.
    
    Contains trajectory hypotheses, supporting evidence, and metadata
    about the analysis process. No numeric scoring is included.
    """
    hypotheses: list[TrajectoryHypothesis]
    evidence_bundle: TrajectoryEvidenceBundle
    analyzer_id: str
    analyzer_version: str
    metadata: dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate analysis result fields."""
        if not isinstance(self.hypotheses, list):
            raise ValueError("hypotheses must be a list")
        
        if not isinstance(self.evidence_bundle, TrajectoryEvidenceBundle):
            raise ValueError("evidence_bundle must be TrajectoryEvidenceBundle")
        
        if not self.analyzer_id or not isinstance(self.analyzer_id, str):
            raise ValueError("analyzer_id must be a non-empty string")
        
        if not self.analyzer_version or not isinstance(self.analyzer_version, str):
            raise ValueError("analyzer_version must be a non-empty string")
        
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dict")
    
    def primary_hypothesis(self) -> Optional[TrajectoryHypothesis]:
        """
        Return the primary (first) hypothesis, if any.
        
        Returns:
            First hypothesis or None if list is empty
        """
        return self.hypotheses[0] if self.hypotheses else None
    
    def to_narrative(self) -> str:
        """
        Generate multi-line narrative summary of analysis results.
        
        Returns:
            Human-readable description of the analysis
        """
        lines = [
            f"Trajectory Analysis Result (Analyzer: {self.analyzer_id} v{self.analyzer_version})",
            ""
        ]
        
        if not self.hypotheses:
            lines.append("No trajectory hypotheses identified.")
        else:
            lines.append(f"Identified {len(self.hypotheses)} trajectory hypothesis(es):")
            lines.append("")
            for i, hyp in enumerate(self.hypotheses, 1):
                lines.append(f"{i}. {hyp.to_narrative()}")
            lines.append("")
        
        lines.append("Evidence Summary:")
        lines.append(self.evidence_bundle.to_narrative())
        
        if self.metadata:
            lines.append("")
            lines.append("Metadata:")
            for key, value in self.metadata.items():
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)


@dataclass
class TrajectoryClassificationResult:
    """
    Represents a final trajectory classification.
    
    Contains the selected archetype (if any), candidate hypotheses,
    and supporting evidence. This is the output of a classifier or
    aggregation engine.
    """
    candidate_hypotheses: list[TrajectoryHypothesis]
    supporting_evidence: TrajectoryEvidenceBundle
    metadata: dict[str, str] = field(default_factory=dict)
    trajectory_id: Optional[str] = None
    selected_archetype_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate classification result fields."""
        if not isinstance(self.candidate_hypotheses, list):
            raise ValueError("candidate_hypotheses must be a list")
        
        if not isinstance(self.supporting_evidence, TrajectoryEvidenceBundle):
            raise ValueError("supporting_evidence must be TrajectoryEvidenceBundle")
        
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dict")
        
        if self.trajectory_id is not None:
            if not isinstance(self.trajectory_id, str) or not self.trajectory_id:
                raise ValueError("trajectory_id must be non-empty string or None")
        
        if self.selected_archetype_id is not None:
            if not isinstance(self.selected_archetype_id, str) or not self.selected_archetype_id:
                raise ValueError("selected_archetype_id must be non-empty string or None")
    
    def to_narrative(self) -> str:
        """
        Generate narrative summary of the classification.
        
        Returns:
            Multi-line human-readable description
        """
        lines = ["Trajectory Classification Result"]
        
        if self.trajectory_id:
            lines.append(f"Trajectory ID: {self.trajectory_id}")
        
        lines.append("")
        
        if self.selected_archetype_id:
            lines.append(f"Selected Archetype: {self.selected_archetype_id}")
            
            # Find matching hypothesis if available
            matching = [
                h for h in self.candidate_hypotheses
                if h.archetype_id == self.selected_archetype_id
            ]
            if matching:
                lines.append(f"  {matching[0].label}")
                lines.append(f"  Rationale: {matching[0].rationale}")
        else:
            lines.append("No archetype selected.")
        
        lines.append("")
        
        if self.candidate_hypotheses:
            lines.append(f"Candidate Hypotheses ({len(self.candidate_hypotheses)}):")
            for i, hyp in enumerate(self.candidate_hypotheses, 1):
                lines.append(f"  {i}. {hyp.archetype_id} - {hyp.label} [{hyp.support_strength.value}]")
        else:
            lines.append("No candidate hypotheses.")
        
        lines.append("")
        lines.append("Supporting Evidence:")
        lines.append(self.supporting_evidence.to_narrative())
        
        if self.metadata:
            lines.append("")
            lines.append("Metadata:")
            for key, value in self.metadata.items():
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)
