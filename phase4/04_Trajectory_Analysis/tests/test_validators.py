"""
Tests for trajectory analysis validators.

Validates structural validation of evidence, results, and inputs.
"""

import pytest
from dataclasses import dataclass

from trajectory_analysis.validators import (
    ValidationResult,
    TrajectoryEvidenceValidator,
    TrajectoryResultValidator,
    SequenceInputValidator
)
from trajectory_analysis.evidence import (
    TrajectorySupportStrength,
    TrajectoryEvidence,
    TrajectoryEvidenceBundle
)
from trajectory_analysis.models import (
    TrajectoryHypothesis,
    TrajectoryAnalysisResult,
    TrajectoryClassificationResult
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_creation_default(self):
        """ValidationResult starts valid with no errors."""
        result = ValidationResult()
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
    
    def test_add_error(self):
        """add_error adds error and marks invalid."""
        result = ValidationResult()
        
        result.add_error("Test error")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Test error" in result.errors
    
    def test_add_warning(self):
        """add_warning adds warning without invalidating."""
        result = ValidationResult()
        
        result.add_warning("Test warning")
        
        assert result.is_valid is True
        assert len(result.warnings) == 1
        assert "Test warning" in result.warnings
    
    def test_to_dict(self):
        """to_dict returns structured representation."""
        result = ValidationResult()
        result.add_error("Error 1")
        result.add_warning("Warning 1")
        
        data = result.to_dict()
        
        assert isinstance(data, dict)
        assert data["is_valid"] is False
        assert data["error_count"] == 1
        assert data["warning_count"] == 1
        assert "Error 1" in data["errors"]
        assert "Warning 1" in data["warnings"]


class TestTrajectoryEvidenceValidator:
    """Tests for TrajectoryEvidenceValidator."""
    
    def test_validate_evidence_valid(self):
        """Valid evidence passes validation."""
        evidence = TrajectoryEvidence(
            archetype_id="test",
            support_strength=TrajectorySupportStrength.MODERATE,
            narrative="Test narrative"
        )
        
        result = TrajectoryEvidenceValidator.validate_evidence(evidence)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_evidence_wrong_type(self):
        """Non-TrajectoryEvidence fails validation."""
        result = TrajectoryEvidenceValidator.validate_evidence("not_evidence")
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_validate_evidence_empty_archetype(self):
        """Empty archetype_id is detected."""
        # This should raise during creation, but test validator response
        try:
            evidence = TrajectoryEvidence(
                archetype_id="",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative="Test"
            )
            # If creation succeeds, validate should catch it
            result = TrajectoryEvidenceValidator.validate_evidence(evidence)
            assert not result.is_valid
        except ValueError:
            # Expected - creation validation catches it
            pass
    
    def test_validate_bundle_valid(self):
        """Valid bundle passes validation."""
        evidence = TrajectoryEvidence(
            archetype_id="test",
            support_strength=TrajectorySupportStrength.WEAK,
            narrative="Test"
        )
        
        bundle = TrajectoryEvidenceBundle(items=[evidence])
        result = TrajectoryEvidenceValidator.validate_bundle(bundle)
        
        assert result.is_valid
    
    def test_validate_bundle_wrong_type(self):
        """Non-bundle fails validation."""
        result = TrajectoryEvidenceValidator.validate_bundle("not_bundle")
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_validate_bundle_validates_items(self):
        """Bundle validation checks each item."""
        # Create a mock invalid evidence by bypassing __init__
        class InvalidEvidence:
            pass
        
        bundle = TrajectoryEvidenceBundle()
        bundle.items = [InvalidEvidence()]
        
        result = TrajectoryEvidenceValidator.validate_bundle(bundle)
        
        assert not result.is_valid
        assert any("Item 0" in error for error in result.errors)


class TestTrajectoryResultValidator:
    """Tests for TrajectoryResultValidator."""
    
    def test_validate_analysis_result_valid(self):
        """Valid analysis result passes validation."""
        hyp = TrajectoryHypothesis(
            archetype_id="test",
            label="Test",
            support_strength=TrajectorySupportStrength.WEAK,
            rationale="Test"
        )
        
        result = TrajectoryAnalysisResult(
            hypotheses=[hyp],
            evidence_bundle=TrajectoryEvidenceBundle(),
            analyzer_id="test_analyzer",
            analyzer_version="1.0"
        )
        
        validation = TrajectoryResultValidator.validate_analysis_result(result)
        
        assert validation.is_valid
        assert len(validation.errors) == 0
    
    def test_validate_analysis_result_wrong_type(self):
        """Non-result fails validation."""
        validation = TrajectoryResultValidator.validate_analysis_result("not_result")
        
        assert not validation.is_valid
    
    def test_validate_analysis_result_forbidden_metadata_score(self):
        """Result with 'score' in metadata fails."""
        result = TrajectoryAnalysisResult(
            hypotheses=[],
            evidence_bundle=TrajectoryEvidenceBundle(),
            analyzer_id="test",
            analyzer_version="1.0",
            metadata={"final_score": "0.95"}
        )
        
        validation = TrajectoryResultValidator.validate_analysis_result(result)
        
        assert not validation.is_valid
        assert any("Forbidden" in error and "score" in error.lower() for error in validation.errors)
    
    def test_validate_analysis_result_forbidden_metadata_probability(self):
        """Result with 'probability' in metadata fails."""
        result = TrajectoryAnalysisResult(
            hypotheses=[],
            evidence_bundle=TrajectoryEvidenceBundle(),
            analyzer_id="test",
            analyzer_version="1.0",
            metadata={"trajectory_probability": "high"}
        )
        
        validation = TrajectoryResultValidator.validate_analysis_result(result)
        
        assert not validation.is_valid
        assert any("Forbidden" in error and "probability" in error.lower() for error in validation.errors)
    
    def test_validate_analysis_result_forbidden_metadata_confidence(self):
        """Result with 'confidence' in metadata fails."""
        result = TrajectoryAnalysisResult(
            hypotheses=[],
            evidence_bundle=TrajectoryEvidenceBundle(),
            analyzer_id="test",
            analyzer_version="1.0",
            metadata={"confidence_level": "0.8"}
        )
        
        validation = TrajectoryResultValidator.validate_analysis_result(result)
        
        assert not validation.is_valid
        assert any("Forbidden" in error for error in validation.errors)
    
    def test_validate_classification_result_valid(self):
        """Valid classification result passes validation."""
        result = TrajectoryClassificationResult(
            candidate_hypotheses=[],
            supporting_evidence=TrajectoryEvidenceBundle(),
            metadata={"classifier": "test"}
        )
        
        validation = TrajectoryResultValidator.validate_classification_result(result)
        
        assert validation.is_valid
    
    def test_validate_classification_result_wrong_type(self):
        """Non-result fails validation."""
        validation = TrajectoryResultValidator.validate_classification_result("not_result")
        
        assert not validation.is_valid
    
    def test_validate_classification_result_forbidden_metadata(self):
        """Classification result with forbidden keys fails."""
        result = TrajectoryClassificationResult(
            candidate_hypotheses=[],
            supporting_evidence=TrajectoryEvidenceBundle(),
            metadata={"weighted_score": "100"}
        )
        
        validation = TrajectoryResultValidator.validate_classification_result(result)
        
        assert not validation.is_valid
        assert any("Forbidden" in error for error in validation.errors)
    
    def test_forbidden_metadata_keys_list(self):
        """Check all forbidden keys are tested."""
        forbidden = TrajectoryResultValidator.FORBIDDEN_METADATA_KEYS
        
        assert "score" in forbidden
        assert "probability" in forbidden
        assert "confidence" in forbidden
        assert "weight" in forbidden


class TestSequenceInputValidator:
    """Tests for SequenceInputValidator."""
    
    @dataclass
    class PatternResultStub:
        """Stub for pattern recognition result."""
        recognized_patterns: list[str]
        evidence_bundle: object
        metadata: dict
    
    def test_validate_inputs_valid(self):
        """Valid inputs pass validation."""
        encoded_states = [{"state": "test"}]
        pattern_results = [self.PatternResultStub([], None, {})]
        
        result = SequenceInputValidator.validate_inputs(
            encoded_states,
            pattern_results
        )
        
        assert result.is_valid
    
    def test_validate_inputs_wrong_states_type(self):
        """Non-list encoded_states fails."""
        result = SequenceInputValidator.validate_inputs(
            "not_list",
            []
        )
        
        assert not result.is_valid
        assert any("encoded_states" in error for error in result.errors)
    
    def test_validate_inputs_wrong_patterns_type(self):
        """Non-list pattern_results fails."""
        result = SequenceInputValidator.validate_inputs(
            [],
            "not_list"
        )
        
        assert not result.is_valid
        assert any("pattern_results" in error for error in result.errors)
    
    def test_validate_inputs_empty_states_warning(self):
        """Empty encoded_states produces warning."""
        result = SequenceInputValidator.validate_inputs([], [])
        
        # May still be valid but should have warning
        assert len(result.warnings) > 0
        assert any("encoded_states" in warning for warning in result.warnings)
    
    def test_validate_inputs_empty_patterns_warning(self):
        """Empty pattern_results produces warning."""
        result = SequenceInputValidator.validate_inputs([{}], [])
        
        assert len(result.warnings) > 0
        assert any("pattern_results" in warning for warning in result.warnings)
    
    def test_validate_inputs_non_dict_state(self):
        """Non-dict state fails validation."""
        result = SequenceInputValidator.validate_inputs(
            ["not_dict"],
            []
        )
        
        assert not result.is_valid
        assert any("encoded_states[0]" in error for error in result.errors)
    
    def test_validate_inputs_none_pattern_result(self):
        """None pattern result fails validation."""
        result = SequenceInputValidator.validate_inputs(
            [{}],
            [None]
        )
        
        assert not result.is_valid
        assert any("pattern_results[0]" in error for error in result.errors)
    
    def test_validate_inputs_missing_attributes_warning(self):
        """Pattern result missing expected attributes produces warning."""
        class IncompleteResult:
            pass
        
        result = SequenceInputValidator.validate_inputs(
            [{}],
            [IncompleteResult()]
        )
        
        # Should have warnings about missing attributes
        assert len(result.warnings) > 0
