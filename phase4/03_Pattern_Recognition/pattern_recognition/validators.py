"""
Validators for pattern recognition structures.

Implements structural validation for evidence, results, and sequences.
Does NOT evaluate correctness or quality - only validates structure and format.
"""

from typing import Dict, List, Any, Optional
from .interfaces import PatternRecognitionResult
from .evidence import PatternEvidence, PatternEvidenceBundle, QualitativeStrength


class ValidationResult:
    """Result of a validation check."""
    
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        """
        Initialize validation result.
        
        Args:
            is_valid: Whether validation passed
            errors: List of error messages
            warnings: List of warning messages
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }
    
    def __repr__(self) -> str:
        """String representation."""
        status = "VALID" if self.is_valid else "INVALID"
        parts = [f"ValidationResult({status})"]
        
        if self.errors:
            parts.append(f"Errors: {len(self.errors)}")
        
        if self.warnings:
            parts.append(f"Warnings: {len(self.warnings)}")
        
        return " - ".join(parts)


class EvidenceValidator:
    """
    Validator for pattern evidence structures.
    
    Checks evidence integrity and format - does NOT evaluate correctness.
    """
    
    @staticmethod
    def validate_evidence(evidence: PatternEvidence) -> ValidationResult:
        """
        Validate a single PatternEvidence instance.
        
        Args:
            evidence: PatternEvidence to validate
        
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        # Type check
        if not isinstance(evidence, PatternEvidence):
            result.add_error(
                f"Evidence must be PatternEvidence instance, got {type(evidence).__name__}"
            )
            return result
        
        # Check required fields
        if not evidence.pattern_type:
            result.add_error("pattern_type cannot be empty")
        
        if not evidence.indicator_label:
            result.add_error("indicator_label cannot be empty")
        
        if not evidence.narrative:
            result.add_error("narrative cannot be empty")
        
        # Validate qualitative strength
        if not QualitativeStrength.is_valid(evidence.qualitative_strength):
            valid_values = [s.value for s in QualitativeStrength]
            result.add_error(
                f"qualitative_strength must be one of {valid_values}, "
                f"got '{evidence.qualitative_strength}'"
            )
        
        # Check metadata
        if not isinstance(evidence.metadata, dict):
            result.add_error("metadata must be a dictionary")
        
        # Warnings for optional fields
        if not evidence.source_event and not evidence.source_state:
            result.add_warning("Evidence has no source_event or source_state")
        
        return result
    
    @staticmethod
    def validate_evidence_bundle(bundle: PatternEvidenceBundle) -> ValidationResult:
        """
        Validate a PatternEvidenceBundle.
        
        Args:
            bundle: PatternEvidenceBundle to validate
        
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        # Type check
        if not isinstance(bundle, PatternEvidenceBundle):
            result.add_error(
                f"Bundle must be PatternEvidenceBundle instance, got {type(bundle).__name__}"
            )
            return result
        
        # Check evidence items
        if not isinstance(bundle.evidence_items, list):
            result.add_error("evidence_items must be a list")
            return result
        
        # Validate each evidence item
        for i, evidence in enumerate(bundle.evidence_items):
            evidence_result = EvidenceValidator.validate_evidence(evidence)
            if not evidence_result.is_valid:
                for error in evidence_result.errors:
                    result.add_error(f"Evidence item {i}: {error}")
        
        # Check metadata
        if not isinstance(bundle.metadata, dict):
            result.add_error("metadata must be a dictionary")
        
        # Warnings
        if not bundle.evidence_items:
            result.add_warning("Evidence bundle is empty")
        
        return result


class RecognizerOutputValidator:
    """
    Validator for pattern recognition results.
    
    Checks result format and structure - does NOT evaluate pattern quality.
    """
    
    @staticmethod
    def validate_recognition_result(result: PatternRecognitionResult) -> ValidationResult:
        """
        Validate a PatternRecognitionResult.
        
        Args:
            result: PatternRecognitionResult to validate
        
        Returns:
            ValidationResult
        """
        validation = ValidationResult(is_valid=True)
        
        # Type check
        if not isinstance(result, PatternRecognitionResult):
            validation.add_error(
                f"Result must be PatternRecognitionResult instance, got {type(result).__name__}"
            )
            return validation
        
        # Check recognized_patterns
        if not isinstance(result.recognized_patterns, list):
            validation.add_error("recognized_patterns must be a list")
        else:
            # Check that all patterns are strings
            for i, pattern in enumerate(result.recognized_patterns):
                if not isinstance(pattern, str):
                    validation.add_error(
                        f"Pattern at index {i} must be a string, got {type(pattern).__name__}"
                    )
                elif not pattern:
                    validation.add_error(f"Pattern at index {i} cannot be empty")
        
        # Check evidence_bundle
        if result.evidence_bundle is not None:
            if isinstance(result.evidence_bundle, PatternEvidenceBundle):
                bundle_result = EvidenceValidator.validate_evidence_bundle(result.evidence_bundle)
                if not bundle_result.is_valid:
                    for error in bundle_result.errors:
                        validation.add_error(f"Evidence bundle: {error}")
            else:
                validation.add_error(
                    f"evidence_bundle must be PatternEvidenceBundle or None, "
                    f"got {type(result.evidence_bundle).__name__}"
                )
        
        # Check metadata
        if not isinstance(result.metadata, dict):
            validation.add_error("metadata must be a dictionary")
        else:
            # Check required metadata fields
            if "schema_version" not in result.metadata:
                validation.add_warning("metadata missing 'schema_version' field")
            
            if "recognizer_versions" not in result.metadata:
                validation.add_warning("metadata missing 'recognizer_versions' field")
        
        # Check narrative output
        try:
            narrative = result.narrative_summary()
            if not isinstance(narrative, str):
                validation.add_error("narrative_summary() must return a string")
            elif not narrative:
                validation.add_warning("narrative_summary() returned empty string")
        except Exception as e:
            validation.add_error(f"narrative_summary() raised exception: {e}")
        
        # Warnings
        if not result.recognized_patterns:
            validation.add_warning("No patterns recognized")
        
        return validation
    
    @staticmethod
    def check_for_numeric_scoring(result: PatternRecognitionResult) -> ValidationResult:
        """
        Check that result contains no numeric scoring or probabilities.
        
        Args:
            result: PatternRecognitionResult to check
        
        Returns:
            ValidationResult with errors if numeric scoring found
        """
        validation = ValidationResult(is_valid=True)
        
        # Check metadata for prohibited fields
        prohibited_keys = [
            "score", "confidence", "probability", "weight", "threshold",
            "certainty", "likelihood", "numeric_value", "statistical_value"
        ]
        
        for key in prohibited_keys:
            if key in result.metadata:
                validation.add_error(
                    f"Result metadata contains prohibited numeric field: '{key}'"
                )
        
        # Check evidence bundle
        if result.evidence_bundle and isinstance(result.evidence_bundle, PatternEvidenceBundle):
            for evidence in result.evidence_bundle.evidence_items:
                for key in prohibited_keys:
                    if key in evidence.metadata:
                        validation.add_error(
                            f"Evidence metadata contains prohibited numeric field: '{key}'"
                        )
        
        return validation


class SequenceValidator:
    """
    Validator for sequences of encoded states.
    
    Performs structural validation only - does NOT evaluate content quality.
    """
    
    @staticmethod
    def validate_sequence(encoded_states: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate a sequence of encoded states.
        
        Args:
            encoded_states: List of encoded states from WS2
        
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        # Type check
        if not isinstance(encoded_states, list):
            result.add_error("encoded_states must be a list")
            return result
        
        # Check non-empty
        if not encoded_states:
            result.add_error("encoded_states cannot be empty")
            return result
        
        # Check each state
        schema_versions = set()
        
        for i, state in enumerate(encoded_states):
            # Check type
            if not isinstance(state, dict):
                result.add_error(
                    f"State at index {i} must be a dictionary, got {type(state).__name__}"
                )
                continue
            
            # Check for required fields
            if "state_id" not in state:
                result.add_warning(f"State at index {i} missing 'state_id' field")
            
            if "schema_version" not in state:
                result.add_warning(f"State at index {i} missing 'schema_version' field")
            else:
                schema_versions.add(state["schema_version"])
            
            if "encoded_domains" not in state and "domains" not in state:
                result.add_warning(
                    f"State at index {i} missing 'encoded_domains' or 'domains' field"
                )
        
        # Check schema version consistency
        if len(schema_versions) > 1:
            result.add_warning(
                f"Sequence contains multiple schema versions: {schema_versions}"
            )
        
        return result
    
    @staticmethod
    def validate_sequence_metadata(encoded_states: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate metadata consistency across sequence.
        
        Args:
            encoded_states: List of encoded states
        
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        if not encoded_states:
            result.add_error("Cannot validate metadata of empty sequence")
            return result
        
        # Check timestamp ordering if available
        timestamps = []
        for i, state in enumerate(encoded_states):
            if isinstance(state, dict) and "timestamp" in state:
                timestamps.append((i, state["timestamp"]))
        
        if len(timestamps) > 1:
            # Check if timestamps are in order
            for j in range(len(timestamps) - 1):
                idx1, ts1 = timestamps[j]
                idx2, ts2 = timestamps[j + 1]
                
                if ts1 > ts2:
                    result.add_warning(
                        f"Timestamps out of order: state {idx1} ({ts1}) > state {idx2} ({ts2})"
                    )
        
        return result
