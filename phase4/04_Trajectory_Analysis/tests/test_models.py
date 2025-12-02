"""
Tests for trajectory analysis data models.

Validates trajectory hypotheses, analysis results, and classification results.
"""

import pytest

from trajectory_analysis.models import (
    TrajectoryHypothesis,
    TrajectoryAnalysisResult,
    TrajectoryClassificationResult
)
from trajectory_analysis.evidence import (
    TrajectorySupportStrength,
    TrajectoryEvidence,
    TrajectoryEvidenceBundle
)


class TestTrajectoryHypothesis:
    """Tests for TrajectoryHypothesis dataclass."""
    
    def test_creation_with_required_fields(self):
        """Hypothesis can be created with required fields."""
        hyp = TrajectoryHypothesis(
            archetype_id="stable_adaptation",
            label="Stable Adaptation",
            support_strength=TrajectorySupportStrength.MODERATE,
            rationale="Test rationale for hypothesis"
        )
        
        assert hyp.archetype_id == "stable_adaptation"
        assert hyp.label == "Stable Adaptation"
        assert hyp.support_strength == TrajectorySupportStrength.MODERATE
        assert hyp.rationale == "Test rationale for hypothesis"
        assert hyp.source_patterns == []
        assert hyp.metadata is None
    
    def test_creation_with_all_fields(self):
        """Hypothesis can be created with all fields."""
        hyp = TrajectoryHypothesis(
            archetype_id="test_arch",
            label="Test Label",
            support_strength=TrajectorySupportStrength.STRONG,
            rationale="Full rationale",
            source_patterns=["pattern1", "pattern2"],
            metadata={"key": "value"}
        )
        
        assert hyp.source_patterns == ["pattern1", "pattern2"]
        assert hyp.metadata == {"key": "value"}
    
    def test_validation_empty_archetype_id(self):
        """Empty archetype_id raises ValueError."""
        with pytest.raises(ValueError, match="archetype_id"):
            TrajectoryHypothesis(
                archetype_id="",
                label="Test",
                support_strength=TrajectorySupportStrength.WEAK,
                rationale="Test"
            )
    
    def test_validation_empty_label(self):
        """Empty label raises ValueError."""
        with pytest.raises(ValueError, match="label"):
            TrajectoryHypothesis(
                archetype_id="test",
                label="",
                support_strength=TrajectorySupportStrength.WEAK,
                rationale="Test"
            )
    
    def test_validation_empty_rationale(self):
        """Empty rationale raises ValueError."""
        with pytest.raises(ValueError, match="rationale"):
            TrajectoryHypothesis(
                archetype_id="test",
                label="Test",
                support_strength=TrajectorySupportStrength.WEAK,
                rationale=""
            )
    
    def test_validation_invalid_support_strength(self):
        """Invalid support_strength raises ValueError."""
        with pytest.raises(ValueError, match="support_strength"):
            TrajectoryHypothesis(
                archetype_id="test",
                label="Test",
                support_strength="not_enum",
                rationale="Test"
            )
    
    def test_to_narrative_basic(self):
        """to_narrative returns readable description."""
        hyp = TrajectoryHypothesis(
            archetype_id="stable_adaptation",
            label="Stable Adaptation",
            support_strength=TrajectorySupportStrength.MODERATE,
            rationale="Shows consistent adaptation patterns"
        )
        
        narrative = hyp.to_narrative()
        assert isinstance(narrative, str)
        assert "Stable Adaptation" in narrative
        assert "stable_adaptation" in narrative
        assert "Shows consistent adaptation patterns" in narrative
        assert "moderate" in narrative
    
    def test_to_narrative_with_patterns(self):
        """to_narrative includes source patterns."""
        hyp = TrajectoryHypothesis(
            archetype_id="test",
            label="Test",
            support_strength=TrajectorySupportStrength.STRONG,
            rationale="Test rationale",
            source_patterns=["pattern_a", "pattern_b"]
        )
        
        narrative = hyp.to_narrative()
        assert "pattern_a" in narrative
        assert "pattern_b" in narrative


class TestTrajectoryAnalysisResult:
    """Tests for TrajectoryAnalysisResult dataclass."""
    
    def test_creation_minimal(self):
        """Analysis result can be created with required fields."""
        hyp = TrajectoryHypothesis(
            archetype_id="test",
            label="Test",
            support_strength=TrajectorySupportStrength.WEAK,
            rationale="Test"
        )
        
        bundle = TrajectoryEvidenceBundle()
        
        result = TrajectoryAnalysisResult(
            hypotheses=[hyp],
            evidence_bundle=bundle,
            analyzer_id="test_analyzer",
            analyzer_version="1.0.0"
        )
        
        assert len(result.hypotheses) == 1
        assert result.analyzer_id == "test_analyzer"
        assert result.analyzer_version == "1.0.0"
        assert isinstance(result.metadata, dict)
    
    def test_creation_with_metadata(self):
        """Analysis result can include metadata."""
        hyp = TrajectoryHypothesis(
            archetype_id="test",
            label="Test",
            support_strength=TrajectorySupportStrength.WEAK,
            rationale="Test"
        )
        
        result = TrajectoryAnalysisResult(
            hypotheses=[hyp],
            evidence_bundle=TrajectoryEvidenceBundle(),
            analyzer_id="test",
            analyzer_version="1.0",
            metadata={"custom": "value"}
        )
        
        assert result.metadata == {"custom": "value"}
    
    def test_validation_hypotheses_not_list(self):
        """Non-list hypotheses raises ValueError."""
        with pytest.raises(ValueError, match="hypotheses"):
            TrajectoryAnalysisResult(
                hypotheses="not_a_list",
                evidence_bundle=TrajectoryEvidenceBundle(),
                analyzer_id="test",
                analyzer_version="1.0"
            )
    
    def test_validation_invalid_evidence_bundle(self):
        """Invalid evidence_bundle raises ValueError."""
        with pytest.raises(ValueError, match="evidence_bundle"):
            TrajectoryAnalysisResult(
                hypotheses=[],
                evidence_bundle="not_a_bundle",
                analyzer_id="test",
                analyzer_version="1.0"
            )
    
    def test_validation_empty_analyzer_id(self):
        """Empty analyzer_id raises ValueError."""
        with pytest.raises(ValueError, match="analyzer_id"):
            TrajectoryAnalysisResult(
                hypotheses=[],
                evidence_bundle=TrajectoryEvidenceBundle(),
                analyzer_id="",
                analyzer_version="1.0"
            )
    
    def test_primary_hypothesis_with_hypotheses(self):
        """primary_hypothesis returns first hypothesis."""
        hyp1 = TrajectoryHypothesis(
            archetype_id="arch1",
            label="First",
            support_strength=TrajectorySupportStrength.STRONG,
            rationale="First"
        )
        
        hyp2 = TrajectoryHypothesis(
            archetype_id="arch2",
            label="Second",
            support_strength=TrajectorySupportStrength.WEAK,
            rationale="Second"
        )
        
        result = TrajectoryAnalysisResult(
            hypotheses=[hyp1, hyp2],
            evidence_bundle=TrajectoryEvidenceBundle(),
            analyzer_id="test",
            analyzer_version="1.0"
        )
        
        primary = result.primary_hypothesis()
        assert primary == hyp1
        assert primary.archetype_id == "arch1"
    
    def test_primary_hypothesis_empty(self):
        """primary_hypothesis returns None when empty."""
        result = TrajectoryAnalysisResult(
            hypotheses=[],
            evidence_bundle=TrajectoryEvidenceBundle(),
            analyzer_id="test",
            analyzer_version="1.0"
        )
        
        assert result.primary_hypothesis() is None
    
    def test_to_narrative(self):
        """to_narrative returns readable summary."""
        hyp = TrajectoryHypothesis(
            archetype_id="test",
            label="Test Hypothesis",
            support_strength=TrajectorySupportStrength.MODERATE,
            rationale="Test rationale"
        )
        
        result = TrajectoryAnalysisResult(
            hypotheses=[hyp],
            evidence_bundle=TrajectoryEvidenceBundle(),
            analyzer_id="test_analyzer",
            analyzer_version="2.0"
        )
        
        narrative = result.to_narrative()
        assert isinstance(narrative, str)
        assert "test_analyzer" in narrative
        assert "2.0" in narrative
        assert "Test Hypothesis" in narrative
    
    def test_to_narrative_no_hypotheses(self):
        """to_narrative handles empty hypotheses."""
        result = TrajectoryAnalysisResult(
            hypotheses=[],
            evidence_bundle=TrajectoryEvidenceBundle(),
            analyzer_id="test",
            analyzer_version="1.0"
        )
        
        narrative = result.to_narrative()
        assert "No trajectory hypotheses" in narrative


class TestTrajectoryClassificationResult:
    """Tests for TrajectoryClassificationResult dataclass."""
    
    def test_creation_minimal(self):
        """Classification result can be created with required fields."""
        result = TrajectoryClassificationResult(
            candidate_hypotheses=[],
            supporting_evidence=TrajectoryEvidenceBundle()
        )
        
        assert result.candidate_hypotheses == []
        assert isinstance(result.supporting_evidence, TrajectoryEvidenceBundle)
        assert isinstance(result.metadata, dict)
        assert result.trajectory_id is None
        assert result.selected_archetype_id is None
    
    def test_creation_with_all_fields(self):
        """Classification result can include all fields."""
        hyp = TrajectoryHypothesis(
            archetype_id="stable_adaptation",
            label="Stable",
            support_strength=TrajectorySupportStrength.STRONG,
            rationale="Test"
        )
        
        result = TrajectoryClassificationResult(
            trajectory_id="mission_001",
            selected_archetype_id="stable_adaptation",
            candidate_hypotheses=[hyp],
            supporting_evidence=TrajectoryEvidenceBundle(),
            metadata={"classifier": "test"}
        )
        
        assert result.trajectory_id == "mission_001"
        assert result.selected_archetype_id == "stable_adaptation"
        assert len(result.candidate_hypotheses) == 1
        assert result.metadata == {"classifier": "test"}
    
    def test_validation_invalid_hypotheses(self):
        """Non-list candidate_hypotheses raises ValueError."""
        with pytest.raises(ValueError, match="candidate_hypotheses"):
            TrajectoryClassificationResult(
                candidate_hypotheses="not_list",
                supporting_evidence=TrajectoryEvidenceBundle()
            )
    
    def test_validation_invalid_evidence(self):
        """Invalid supporting_evidence raises ValueError."""
        with pytest.raises(ValueError, match="supporting_evidence"):
            TrajectoryClassificationResult(
                candidate_hypotheses=[],
                supporting_evidence="not_bundle"
            )
    
    def test_validation_empty_trajectory_id(self):
        """Empty trajectory_id raises ValueError."""
        with pytest.raises(ValueError, match="trajectory_id"):
            TrajectoryClassificationResult(
                trajectory_id="",
                candidate_hypotheses=[],
                supporting_evidence=TrajectoryEvidenceBundle()
            )
    
    def test_validation_empty_selected_archetype(self):
        """Empty selected_archetype_id raises ValueError."""
        with pytest.raises(ValueError, match="selected_archetype_id"):
            TrajectoryClassificationResult(
                selected_archetype_id="",
                candidate_hypotheses=[],
                supporting_evidence=TrajectoryEvidenceBundle()
            )
    
    def test_to_narrative_with_selection(self):
        """to_narrative shows selected archetype."""
        hyp = TrajectoryHypothesis(
            archetype_id="stable_adaptation",
            label="Stable Adaptation",
            support_strength=TrajectorySupportStrength.STRONG,
            rationale="Shows stability"
        )
        
        result = TrajectoryClassificationResult(
            trajectory_id="mission_001",
            selected_archetype_id="stable_adaptation",
            candidate_hypotheses=[hyp],
            supporting_evidence=TrajectoryEvidenceBundle()
        )
        
        narrative = result.to_narrative()
        assert isinstance(narrative, str)
        assert "mission_001" in narrative
        assert "stable_adaptation" in narrative
        assert "Stable Adaptation" in narrative
    
    def test_to_narrative_no_selection(self):
        """to_narrative handles no selected archetype."""
        result = TrajectoryClassificationResult(
            candidate_hypotheses=[],
            supporting_evidence=TrajectoryEvidenceBundle()
        )
        
        narrative = result.to_narrative()
        assert "No archetype selected" in narrative
        assert "No candidate hypotheses" in narrative
