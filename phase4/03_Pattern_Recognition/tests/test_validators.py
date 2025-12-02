"""
Tests for pattern recognition validators.

Tests structural validation of evidence, results, and sequences.
"""

import pytest

from pattern_recognition.validators import (
    ValidationResult,
    EvidenceValidator,
    RecognizerOutputValidator,
    SequenceValidator,
)
from pattern_recognition.evidence import (
    PatternEvidence,
    PatternEvidenceBundle,
)
from pattern_recognition.interfaces import PatternRecognitionResult


class TestValidationResult:
    """Test ValidationResult helper class."""
    
    def test_creation_valid(self):
        """Test creating valid result."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_creation_invalid(self):
        """Test creating invalid result."""
        result = ValidationResult(
            is_valid=False,
            errors=["error1", "error2"],
            warnings=["warning1"]
        )
        assert not result.is_valid
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
    
    def test_add_error(self):
        """Test adding error."""
        result = ValidationResult(is_valid=True)
        result.add_error("Test error")
        
        assert not result.is_valid
        assert "Test error" in result.errors
    
    def test_add_warning(self):
        """Test adding warning."""
        result = ValidationResult(is_valid=True)
        result.add_warning("Test warning")
        
        assert result.is_valid  # Still valid
        assert "Test warning" in result.warnings
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        result = ValidationResult(
            is_valid=False,
            errors=["error"],
            warnings=["warning"]
        )
        
        result_dict = result.to_dict()
        assert result_dict["is_valid"] is False
        assert "error" in result_dict["errors"]
        assert "warning" in result_dict["warnings"]
    
    def test_repr(self):
        """Test string representation."""
        result = ValidationResult(is_valid=True)
        repr_str = repr(result)
        assert "VALID" in repr_str
        
        result.add_error("error")
        repr_str = repr(result)
        assert "INVALID" in repr_str
        assert "Errors: 1" in repr_str


class TestEvidenceValidator:
    """Test EvidenceValidator."""
    
    def test_validate_valid_evidence(self):
        """Test validating correct evidence."""
        evidence = PatternEvidence(
            pattern_type="test_pattern",
            indicator_label="Test indicator",
            qualitative_strength="strong",
            narrative="Test narrative"
        )
        
        result = EvidenceValidator.validate_evidence(evidence)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_invalid_type(self):
        """Test validating non-evidence object."""
        result = EvidenceValidator.validate_evidence("not_evidence")
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "must be PatternEvidence instance" in result.errors[0]
    
    def test_validate_empty_pattern_type(self):
        """Test validation catches empty pattern_type."""
        # This will raise during creation, so we can't test the validator directly
        # But we verify the validator checks it
        evidence = PatternEvidence(
            pattern_type="valid",
            indicator_label="Test",
            qualitative_strength="weak",
            narrative="Test"
        )
        # Manually set to empty (bypassing __post_init__)
        evidence.pattern_type = ""
        
        result = EvidenceValidator.validate_evidence(evidence)
        assert not result.is_valid
        assert any("pattern_type cannot be empty" in e for e in result.errors)
    
    def test_validate_invalid_strength(self):
        """Test validation catches invalid qualitative strength."""
        evidence = PatternEvidence(
            pattern_type="test",
            indicator_label="Test",
            qualitative_strength="weak",
            narrative="Test"
        )
        # Manually set invalid strength
        evidence.qualitative_strength = "invalid_strength"
        
        result = EvidenceValidator.validate_evidence(evidence)
        assert not result.is_valid
        assert any("qualitative_strength must be one of" in e for e in result.errors)
    
    def test_validate_warning_no_source(self):
        """Test warning when no source event or state."""
        evidence = PatternEvidence(
            pattern_type="test",
            indicator_label="Test",
            qualitative_strength="weak",
            narrative="Test"
        )
        
        result = EvidenceValidator.validate_evidence(evidence)
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("no source_event or source_state" in w for w in result.warnings)
    
    def test_validate_evidence_bundle_valid(self):
        """Test validating valid evidence bundle."""
        bundle = PatternEvidenceBundle()
        bundle.add_evidence(PatternEvidence(
            pattern_type="test",
            indicator_label="Test",
            qualitative_strength="weak",
            narrative="Test"
        ))
        
        result = EvidenceValidator.validate_evidence_bundle(bundle)
        assert result.is_valid
    
    def test_validate_bundle_invalid_type(self):
        """Test validating non-bundle object."""
        result = EvidenceValidator.validate_evidence_bundle("not_a_bundle")
        assert not result.is_valid
        assert "must be PatternEvidenceBundle instance" in result.errors[0]
    
    def test_validate_empty_bundle_warning(self):
        """Test warning for empty bundle."""
        bundle = PatternEvidenceBundle()
        
        result = EvidenceValidator.validate_evidence_bundle(bundle)
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("empty" in w.lower() for w in result.warnings)
    
    def test_validate_bundle_with_invalid_evidence(self):
        """Test bundle validation checks each evidence item."""
        bundle = PatternEvidenceBundle()
        
        # Add valid evidence
        bundle.add_evidence(PatternEvidence(
            pattern_type="test",
            indicator_label="Test",
            qualitative_strength="weak",
            narrative="Test"
        ))
        
        # Add evidence with invalid strength (manually set)
        invalid_evidence = PatternEvidence(
            pattern_type="test2",
            indicator_label="Test2",
            qualitative_strength="weak",
            narrative="Test2"
        )
        invalid_evidence.qualitative_strength = "invalid"
        bundle.add_evidence(invalid_evidence)
        
        result = EvidenceValidator.validate_evidence_bundle(bundle)
        assert not result.is_valid
        assert any("Evidence item 1:" in e for e in result.errors)


class TestRecognizerOutputValidator:
    """Test RecognizerOutputValidator."""
    
    def test_validate_valid_result(self):
        """Test validating correct recognition result."""
        result = PatternRecognitionResult(
            recognized_patterns=["pattern1", "pattern2"],
            evidence_bundle=PatternEvidenceBundle(),
            metadata={"schema_version": "1.0", "recognizer_versions": {}}
        )
        
        validation = RecognizerOutputValidator.validate_recognition_result(result)
        assert validation.is_valid
    
    def test_validate_invalid_type(self):
        """Test validating non-result object."""
        validation = RecognizerOutputValidator.validate_recognition_result("not_a_result")
        assert not validation.is_valid
        assert "must be PatternRecognitionResult instance" in validation.errors[0]
    
    def test_validate_invalid_patterns_type(self):
        """Test validation catches non-list patterns."""
        result = PatternRecognitionResult(
            recognized_patterns=["valid"],
            evidence_bundle=PatternEvidenceBundle(),
        )
        # Manually break it
        result.recognized_patterns = "not_a_list"
        
        validation = RecognizerOutputValidator.validate_recognition_result(result)
        assert not validation.is_valid
        assert any("must be a list" in e for e in validation.errors)
    
    def test_validate_non_string_patterns(self):
        """Test validation catches non-string pattern identifiers."""
        result = PatternRecognitionResult(
            recognized_patterns=["valid"],
            evidence_bundle=PatternEvidenceBundle(),
        )
        result.recognized_patterns = ["valid", 123, "another_valid"]
        
        validation = RecognizerOutputValidator.validate_recognition_result(result)
        assert not validation.is_valid
        assert any("must be a string" in e for e in validation.errors)
    
    def test_validate_empty_pattern_string(self):
        """Test validation catches empty pattern strings."""
        result = PatternRecognitionResult(
            recognized_patterns=["valid"],
            evidence_bundle=PatternEvidenceBundle(),
        )
        result.recognized_patterns = ["valid", "", "another"]
        
        validation = RecognizerOutputValidator.validate_recognition_result(result)
        assert not validation.is_valid
        assert any("cannot be empty" in e for e in validation.errors)
    
    def test_validate_invalid_evidence_bundle(self):
        """Test validation checks evidence bundle."""
        result = PatternRecognitionResult(
            recognized_patterns=["pattern"],
            evidence_bundle="not_a_bundle",
        )
        
        validation = RecognizerOutputValidator.validate_recognition_result(result)
        assert not validation.is_valid
        assert any("evidence_bundle" in e for e in validation.errors)
    
    def test_validate_missing_metadata_fields(self):
        """Test that auto-populated metadata fields are present."""
        result = PatternRecognitionResult(
            recognized_patterns=["pattern"],
            evidence_bundle=PatternEvidenceBundle(),
            metadata={}
        )
        
        validation = RecognizerOutputValidator.validate_recognition_result(result)
        # Should be valid - metadata fields are auto-populated
        assert validation.is_valid
        # PatternRecognitionResult auto-populates schema_version and recognizer_versions
        assert "schema_version" in result.metadata
        assert "recognizer_versions" in result.metadata
    
    def test_validate_narrative_generation(self):
        """Test validation checks narrative method."""
        result = PatternRecognitionResult(
            recognized_patterns=["pattern"],
            evidence_bundle=PatternEvidenceBundle(),
        )
        
        validation = RecognizerOutputValidator.validate_recognition_result(result)
        assert validation.is_valid
        # Should not error on narrative generation
    
    def test_validate_no_patterns_warning(self):
        """Test warning when no patterns recognized."""
        result = PatternRecognitionResult(
            recognized_patterns=[],
            evidence_bundle=PatternEvidenceBundle(),
        )
        
        validation = RecognizerOutputValidator.validate_recognition_result(result)
        assert validation.is_valid
        assert len(validation.warnings) > 0
        assert any("No patterns" in w for w in validation.warnings)
    
    def test_check_for_numeric_scoring_clean(self):
        """Test checking result with no numeric scoring."""
        result = PatternRecognitionResult(
            recognized_patterns=["pattern"],
            evidence_bundle=PatternEvidenceBundle(),
            metadata={"safe": "value"}
        )
        
        validation = RecognizerOutputValidator.check_for_numeric_scoring(result)
        assert validation.is_valid
        assert len(validation.errors) == 0
    
    def test_check_for_numeric_scoring_prohibited_fields(self):
        """Test detection of prohibited numeric fields."""
        result = PatternRecognitionResult(
            recognized_patterns=["pattern"],
            evidence_bundle=PatternEvidenceBundle(),
            metadata={
                "safe": "value",
                "score": 0.85,  # Prohibited!
                "confidence": 0.9  # Prohibited!
            }
        )
        
        validation = RecognizerOutputValidator.check_for_numeric_scoring(result)
        assert not validation.is_valid
        assert len(validation.errors) >= 2
        assert any("score" in e for e in validation.errors)
        assert any("confidence" in e for e in validation.errors)


class TestSequenceValidator:
    """Test SequenceValidator."""
    
    def test_validate_valid_sequence(self):
        """Test validating correct sequence."""
        states = [
            {"state_id": "s1", "schema_version": "1.0", "encoded_domains": {}},
            {"state_id": "s2", "schema_version": "1.0", "encoded_domains": {}},
            {"state_id": "s3", "schema_version": "1.0", "encoded_domains": {}},
        ]
        
        result = SequenceValidator.validate_sequence(states)
        assert result.is_valid
    
    def test_validate_invalid_type(self):
        """Test validating non-list."""
        result = SequenceValidator.validate_sequence("not_a_list")
        assert not result.is_valid
        assert "must be a list" in result.errors[0]
    
    def test_validate_empty_sequence(self):
        """Test validating empty sequence."""
        result = SequenceValidator.validate_sequence([])
        assert not result.is_valid
        assert "cannot be empty" in result.errors[0]
    
    def test_validate_non_dict_states(self):
        """Test validation catches non-dict states."""
        states = [
            {"state_id": "s1", "schema_version": "1.0"},
            "not_a_dict",
            {"state_id": "s3", "schema_version": "1.0"},
        ]
        
        result = SequenceValidator.validate_sequence(states)
        assert not result.is_valid
        assert any("must be a dictionary" in e for e in result.errors)
    
    def test_validate_missing_state_id(self):
        """Test warning for missing state_id."""
        states = [
            {"schema_version": "1.0"},  # Missing state_id
        ]
        
        result = SequenceValidator.validate_sequence(states)
        assert result.is_valid  # Just a warning
        assert len(result.warnings) > 0
        assert any("state_id" in w for w in result.warnings)
    
    def test_validate_missing_schema_version(self):
        """Test warning for missing schema_version."""
        states = [
            {"state_id": "s1"},  # Missing schema_version
        ]
        
        result = SequenceValidator.validate_sequence(states)
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("schema_version" in w for w in result.warnings)
    
    def test_validate_inconsistent_schema_versions(self):
        """Test warning for multiple schema versions."""
        states = [
            {"state_id": "s1", "schema_version": "1.0"},
            {"state_id": "s2", "schema_version": "2.0"},  # Different version!
        ]
        
        result = SequenceValidator.validate_sequence(states)
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("multiple schema versions" in w for w in result.warnings)
    
    def test_validate_sequence_metadata_empty(self):
        """Test metadata validation on empty sequence."""
        result = SequenceValidator.validate_sequence_metadata([])
        assert not result.is_valid
        assert "empty sequence" in result.errors[0]
    
    def test_validate_sequence_metadata_valid(self):
        """Test metadata validation on valid sequence."""
        states = [
            {"state_id": "s1", "timestamp": "2025-01-01T00:00:00"},
            {"state_id": "s2", "timestamp": "2025-01-01T01:00:00"},
        ]
        
        result = SequenceValidator.validate_sequence_metadata(states)
        assert result.is_valid
    
    def test_validate_sequence_metadata_out_of_order(self):
        """Test warning for out-of-order timestamps."""
        states = [
            {"state_id": "s1", "timestamp": "2025-01-01T02:00:00"},
            {"state_id": "s2", "timestamp": "2025-01-01T01:00:00"},  # Earlier!
        ]
        
        result = SequenceValidator.validate_sequence_metadata(states)
        assert result.is_valid  # Just a warning
        assert len(result.warnings) > 0
        assert any("out of order" in w for w in result.warnings)
