"""
Tests for validator implementations.

These tests verify:
- Structural consistency validation
- Schema alignment validation
- Domain consistency validation
- ValidationResult functionality
- Error and warning detection
"""

import unittest
from state_encoding.validators import (
    EncodedStateValidator, SchemaAlignmentValidator,
    DomainConsistencyValidator, ValidationResult,
    ValidationIssue, ValidationSeverity
)


class TestValidationResult(unittest.TestCase):
    """Test cases for ValidationResult dataclass."""
    
    def test_valid_result_no_issues(self):
        """Test valid result with no issues."""
        result = ValidationResult(
            is_valid=True,
            issues=[],
            validated_fields={"field1", "field2"},
            metadata={"validator": "test"}
        )
        
        self.assertTrue(result.is_valid)
        self.assertFalse(result.has_errors())
        self.assertFalse(result.has_warnings())
    
    def test_result_with_errors(self):
        """Test result with error-level issues."""
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field_path="test.field",
                message="Test error"
            )
        ]
        
        result = ValidationResult(
            is_valid=False,
            issues=issues,
            validated_fields=set(),
            metadata={}
        )
        
        self.assertFalse(result.is_valid)
        self.assertTrue(result.has_errors())
        self.assertEqual(len(result.get_errors()), 1)
    
    def test_result_with_warnings(self):
        """Test result with warning-level issues."""
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                field_path="test.field",
                message="Test warning"
            )
        ]
        
        result = ValidationResult(
            is_valid=True,
            issues=issues,
            validated_fields=set(),
            metadata={}
        )
        
        self.assertTrue(result.is_valid)
        self.assertFalse(result.has_errors())
        self.assertTrue(result.has_warnings())
        self.assertEqual(len(result.get_warnings()), 1)
    
    def test_summary_generation(self):
        """Test summary generation for validation results."""
        # Valid result
        valid_result = ValidationResult(
            is_valid=True,
            issues=[],
            validated_fields={"field1", "field2"},
            metadata={}
        )
        
        summary = valid_result.to_summary()
        self.assertIn("passed", summary)
        
        # Invalid result with errors
        invalid_result = ValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field_path="test.field",
                    message="Test error"
                )
            ],
            validated_fields=set(),
            metadata={}
        )
        
        summary = invalid_result.to_summary()
        self.assertIn("failed", summary)
        self.assertIn("error", summary.lower())


class TestEncodedStateValidator(unittest.TestCase):
    """Test cases for EncodedStateValidator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = EncodedStateValidator(
            required_fields=["profile_id", "domains"]
        )
    
    def test_validate_complete_state(self):
        """Test validation of complete encoded state."""
        state = {
            "profile_id": "test_001",
            "domains": {
                "physiological": {"sleep": "restless"},
                "psychological": {"mood": "anxious"}
            },
            "encoding_metadata": {
                "encoder_type": "baseline",
                "encoder_version": "1.0.0"
            }
        }
        
        result = self.validator.validate(state)
        
        self.assertTrue(result.is_valid)
        self.assertFalse(result.has_errors())
        self.assertIn("profile_id", result.validated_fields)
        self.assertIn("domains", result.validated_fields)
    
    def test_validate_missing_required_field(self):
        """Test validation with missing required field."""
        state = {
            "profile_id": "test_001"
            # Missing "domains"
        }
        
        result = self.validator.validate(state)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(result.has_errors())
        
        errors = result.get_errors()
        self.assertEqual(len(errors), 1)
        self.assertIn("domains", errors[0].message)
    
    def test_validate_missing_metadata(self):
        """Test validation with missing encoding metadata."""
        state = {
            "profile_id": "test_001",
            "domains": {}
            # Missing encoding_metadata
        }
        
        result = self.validator.validate(state)
        
        # Should still be valid (only warning)
        self.assertTrue(result.is_valid)
        self.assertTrue(result.has_warnings())
        
        warnings = result.get_warnings()
        self.assertGreater(len(warnings), 0)
    
    def test_validate_missing_encoder_type(self):
        """Test validation with incomplete metadata."""
        state = {
            "profile_id": "test_001",
            "domains": {},
            "encoding_metadata": {
                "encoder_version": "1.0.0"
                # Missing encoder_type
            }
        }
        
        result = self.validator.validate(state)
        
        self.assertTrue(result.is_valid)
        self.assertTrue(result.has_warnings())


class TestSchemaAlignmentValidator(unittest.TestCase):
    """Test cases for SchemaAlignmentValidator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = SchemaAlignmentValidator(
            valid_semantic_tags={"restless", "anxious", "high", "moderate"},
            valid_domains={"physiological", "psychological", "social"}
        )
    
    def test_validate_aligned_state(self):
        """Test validation of schema-aligned state."""
        state = {
            "domains": {
                "physiological": {"sleep": "restless"},
                "psychological": {"mood": "anxious"}
            },
            "encoding_metadata": {
                "encoder_version": "1.0.0"
            }
        }
        
        result = self.validator.validate(state, schema_version="1.0.0")
        
        self.assertTrue(result.is_valid)
        self.assertFalse(result.has_errors())
    
    def test_validate_schema_version_mismatch(self):
        """Test validation with schema version mismatch."""
        state = {
            "domains": {},
            "encoding_metadata": {
                "encoder_version": "1.0.0"
            }
        }
        
        result = self.validator.validate(state, schema_version="2.0.0")
        
        # Should be valid with warning
        self.assertTrue(result.is_valid)
        self.assertTrue(result.has_warnings())
    
    def test_validate_invalid_domain(self):
        """Test validation with invalid domain."""
        state = {
            "domains": {
                "physiological": {},
                "invalid_domain": {}
            },
            "encoding_metadata": {}
        }
        
        result = self.validator.validate(state)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(result.has_errors())
        
        errors = result.get_errors()
        self.assertTrue(any("invalid_domain" in err.message for err in errors))
    
    def test_validate_valid_domains(self):
        """Test validation with all valid domains."""
        state = {
            "domains": {
                "physiological": {},
                "psychological": {},
                "social": {}
            },
            "encoding_metadata": {}
        }
        
        result = self.validator.validate(state)
        
        self.assertTrue(result.is_valid)
        self.assertFalse(result.has_errors())


class TestDomainConsistencyValidator(unittest.TestCase):
    """Test cases for DomainConsistencyValidator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = DomainConsistencyValidator()
    
    def test_validate_consistent_domains(self):
        """Test validation of consistent domain states."""
        state = {
            "domains": {
                "physiological": {
                    "energy_level": "moderate",
                    "sleep_quality": "adequate"
                }
            }
        }
        
        result = self.validator.validate(state)
        
        self.assertTrue(result.is_valid)
        self.assertFalse(result.has_errors())
    
    def test_validate_contradictory_physiological_state(self):
        """Test validation with contradictory physiological indicators."""
        state = {
            "domains": {
                "physiological": {
                    "energy_level": "high",
                    "sleep_quality": "severely_disrupted"
                }
            }
        }
        
        result = self.validator.validate(state)
        
        # Should be valid with warning (contradictions are warnings, not errors)
        self.assertTrue(result.is_valid)
        self.assertTrue(result.has_warnings())
        
        warnings = result.get_warnings()
        self.assertTrue(any("contradiction" in warn.message.lower() for warn in warnings))
    
    def test_validate_specific_domain(self):
        """Test validation of specific domain."""
        state = {
            "domains": {
                "physiological": {"sleep": "restless"},
                "psychological": {"mood": "anxious"}
            }
        }
        
        result = self.validator.validate(state, domain="physiological")
        
        self.assertTrue(result.is_valid)
    
    def test_validate_contradictory_indicators(self):
        """Test validation with contradictory indicators."""
        state = {
            "indicators": ["high_morale", "low_morale"]
        }
        
        result = self.validator.validate(state)
        
        self.assertTrue(result.is_valid)
        self.assertTrue(result.has_warnings())
        
        warnings = result.get_warnings()
        self.assertTrue(any("contradictory" in warn.message.lower() for warn in warnings))
    
    def test_validate_non_contradictory_indicators(self):
        """Test validation with non-contradictory indicators."""
        state = {
            "indicators": ["high_morale", "strong_cohesion"]
        }
        
        result = self.validator.validate(state)
        
        self.assertTrue(result.is_valid)
        self.assertFalse(result.has_warnings())
    
    def test_validate_temporal_context(self):
        """Test validation with temporal context."""
        state = {
            "temporal_context": {
                "timestamp": "2024-03-15T08:00:00Z"
            }
        }
        
        result = self.validator.validate(state)
        
        self.assertTrue(result.is_valid)
        self.assertIn("temporal_context", result.validated_fields)


if __name__ == '__main__':
    unittest.main()
