"""
Validators for trajectory analysis structures.

This module provides validation for trajectory evidence, hypotheses,
analysis results, and input sequences. Validates structural correctness
and contract compliance, not analytical correctness.
"""

from dataclasses import dataclass, field

from .evidence import TrajectoryEvidence, TrajectoryEvidenceBundle, TrajectorySupportStrength
from .models import TrajectoryAnalysisResult, TrajectoryClassificationResult


@dataclass
class ValidationResult:
    """
    Result of a validation operation.
    
    Contains validation status and any errors or warnings encountered.
    """
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    def add_error(self, message: str) -> None:
        """
        Add an error message and mark validation as failed.
        
        Args:
            message: Error description
        """
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """
        Add a warning message without failing validation.
        
        Args:
            message: Warning description
        """
        self.warnings.append(message)
    
    def to_dict(self) -> dict:
        """
        Convert validation result to dictionary.
        
        Returns:
            Dictionary representation of validation result
        """
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings
        }


class TrajectoryEvidenceValidator:
    """
    Validator for trajectory evidence items and bundles.
    
    Checks structural correctness and required field presence.
    """
    
    @staticmethod
    def validate_evidence(evidence: TrajectoryEvidence) -> ValidationResult:
        """
        Validate a single trajectory evidence item.
        
        Args:
            evidence: Evidence item to validate
            
        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult()
        
        # Type check
        if not isinstance(evidence, TrajectoryEvidence):
            result.add_error(
                f"Expected TrajectoryEvidence, got {type(evidence)}"
            )
            return result
        
        # Validate archetype_id
        if not evidence.archetype_id:
            result.add_error("archetype_id is empty")
        elif not isinstance(evidence.archetype_id, str):
            result.add_error(
                f"archetype_id must be string, got {type(evidence.archetype_id)}"
            )
        
        # Validate support_strength
        if not isinstance(evidence.support_strength, TrajectorySupportStrength):
            result.add_error(
                f"support_strength must be TrajectorySupportStrength enum, "
                f"got {type(evidence.support_strength)}"
            )
        
        # Validate narrative
        if not evidence.narrative:
            result.add_error("narrative is empty")
        elif not isinstance(evidence.narrative, str):
            result.add_error(
                f"narrative must be string, got {type(evidence.narrative)}"
            )
        
        # Validate metadata if present
        if evidence.metadata is not None:
            if not isinstance(evidence.metadata, dict):
                result.add_error(
                    f"metadata must be dict or None, got {type(evidence.metadata)}"
                )
        
        # Check for narrative method
        try:
            narrative = evidence.to_narrative()
            if not isinstance(narrative, str):
                result.add_error("to_narrative() must return string")
        except Exception as e:
            result.add_error(f"to_narrative() raised exception: {e}")
        
        return result
    
    @staticmethod
    def validate_bundle(bundle: TrajectoryEvidenceBundle) -> ValidationResult:
        """
        Validate a trajectory evidence bundle.
        
        Args:
            bundle: Evidence bundle to validate
            
        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult()
        
        # Type check
        if not isinstance(bundle, TrajectoryEvidenceBundle):
            result.add_error(
                f"Expected TrajectoryEvidenceBundle, got {type(bundle)}"
            )
            return result
        
        # Validate items field
        if not isinstance(bundle.items, list):
            result.add_error(
                f"items must be list, got {type(bundle.items)}"
            )
            return result
        
        # Validate each item
        for i, item in enumerate(bundle.items):
            item_result = TrajectoryEvidenceValidator.validate_evidence(item)
            if not item_result.is_valid:
                for error in item_result.errors:
                    result.add_error(f"Item {i}: {error}")
        
        # Check narrative method
        try:
            narrative = bundle.to_narrative()
            if not isinstance(narrative, str):
                result.add_error("to_narrative() must return string")
        except Exception as e:
            result.add_error(f"to_narrative() raised exception: {e}")
        
        return result


class TrajectoryResultValidator:
    """
    Validator for trajectory analysis and classification results.
    
    Checks structural correctness, metadata validity, and ensures
    no numeric scoring fields are present.
    """
    
    # Forbidden metadata keys that imply numeric scoring
    FORBIDDEN_METADATA_KEYS = [
        "score", "probability", "confidence", "weight",
        "likelihood", "certainty", "rating"
    ]
    
    @staticmethod
    def validate_analysis_result(result: TrajectoryAnalysisResult) -> ValidationResult:
        """
        Validate a trajectory analysis result.
        
        Args:
            result: Analysis result to validate
            
        Returns:
            ValidationResult with any errors or warnings
        """
        validation = ValidationResult()
        
        # Type check
        if not isinstance(result, TrajectoryAnalysisResult):
            validation.add_error(
                f"Expected TrajectoryAnalysisResult, got {type(result)}"
            )
            return validation
        
        # Validate hypotheses
        if not isinstance(result.hypotheses, list):
            validation.add_error(
                f"hypotheses must be list, got {type(result.hypotheses)}"
            )
        
        # Validate evidence_bundle
        bundle_result = TrajectoryEvidenceValidator.validate_bundle(
            result.evidence_bundle
        )
        if not bundle_result.is_valid:
            for error in bundle_result.errors:
                validation.add_error(f"Evidence bundle: {error}")
        
        # Validate analyzer_id
        if not result.analyzer_id:
            validation.add_error("analyzer_id is empty")
        elif not isinstance(result.analyzer_id, str):
            validation.add_error(
                f"analyzer_id must be string, got {type(result.analyzer_id)}"
            )
        
        # Validate analyzer_version
        if not result.analyzer_version:
            validation.add_error("analyzer_version is empty")
        elif not isinstance(result.analyzer_version, str):
            validation.add_error(
                f"analyzer_version must be string, got {type(result.analyzer_version)}"
            )
        
        # Validate metadata
        if not isinstance(result.metadata, dict):
            validation.add_error(
                f"metadata must be dict, got {type(result.metadata)}"
            )
        else:
            # Check for forbidden numeric scoring keys
            for key in result.metadata:
                key_lower = key.lower()
                for forbidden in TrajectoryResultValidator.FORBIDDEN_METADATA_KEYS:
                    if forbidden in key_lower:
                        validation.add_error(
                            f"Forbidden numeric scoring key in metadata: '{key}' "
                            f"(contains '{forbidden}')"
                        )
        
        # Check narrative method
        try:
            narrative = result.to_narrative()
            if not isinstance(narrative, str):
                validation.add_error("to_narrative() must return string")
        except Exception as e:
            validation.add_error(f"to_narrative() raised exception: {e}")
        
        return validation
    
    @staticmethod
    def validate_classification_result(
        result: TrajectoryClassificationResult
    ) -> ValidationResult:
        """
        Validate a trajectory classification result.
        
        Args:
            result: Classification result to validate
            
        Returns:
            ValidationResult with any errors or warnings
        """
        validation = ValidationResult()
        
        # Type check
        if not isinstance(result, TrajectoryClassificationResult):
            validation.add_error(
                f"Expected TrajectoryClassificationResult, got {type(result)}"
            )
            return validation
        
        # Validate candidate_hypotheses
        if not isinstance(result.candidate_hypotheses, list):
            validation.add_error(
                f"candidate_hypotheses must be list, got {type(result.candidate_hypotheses)}"
            )
        
        # Validate supporting_evidence
        bundle_result = TrajectoryEvidenceValidator.validate_bundle(
            result.supporting_evidence
        )
        if not bundle_result.is_valid:
            for error in bundle_result.errors:
                validation.add_error(f"Supporting evidence: {error}")
        
        # Validate metadata
        if not isinstance(result.metadata, dict):
            validation.add_error(
                f"metadata must be dict, got {type(result.metadata)}"
            )
        else:
            # Check for forbidden numeric scoring keys
            for key in result.metadata:
                key_lower = key.lower()
                for forbidden in TrajectoryResultValidator.FORBIDDEN_METADATA_KEYS:
                    if forbidden in key_lower:
                        validation.add_error(
                            f"Forbidden numeric scoring key in metadata: '{key}' "
                            f"(contains '{forbidden}')"
                        )
        
        # Validate trajectory_id if present
        if result.trajectory_id is not None:
            if not isinstance(result.trajectory_id, str):
                validation.add_error(
                    f"trajectory_id must be string or None, got {type(result.trajectory_id)}"
                )
            elif not result.trajectory_id:
                validation.add_error("trajectory_id is empty string")
        
        # Validate selected_archetype_id if present
        if result.selected_archetype_id is not None:
            if not isinstance(result.selected_archetype_id, str):
                validation.add_error(
                    f"selected_archetype_id must be string or None, "
                    f"got {type(result.selected_archetype_id)}"
                )
            elif not result.selected_archetype_id:
                validation.add_error("selected_archetype_id is empty string")
        
        # Check narrative method
        try:
            narrative = result.to_narrative()
            if not isinstance(narrative, str):
                validation.add_error("to_narrative() must return string")
        except Exception as e:
            validation.add_error(f"to_narrative() raised exception: {e}")
        
        return validation


class SequenceInputValidator:
    """
    Validator for input sequences to trajectory analyzers.
    
    Validates encoded states and pattern results for basic structural
    correctness without inspecting deep content.
    """
    
    @staticmethod
    def validate_inputs(
        encoded_states: list[dict],
        pattern_results: list[object]
    ) -> ValidationResult:
        """
        Validate input sequences for trajectory analysis.
        
        Args:
            encoded_states: List of encoded state dictionaries
            pattern_results: List of pattern recognition results
            
        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult()
        
        # Validate encoded_states
        if not isinstance(encoded_states, list):
            result.add_error(
                f"encoded_states must be list, got {type(encoded_states)}"
            )
        else:
            if len(encoded_states) == 0:
                result.add_warning("encoded_states is empty")
            
            for i, state in enumerate(encoded_states):
                if not isinstance(state, dict):
                    result.add_error(
                        f"encoded_states[{i}] must be dict, got {type(state)}"
                    )
        
        # Validate pattern_results
        if not isinstance(pattern_results, list):
            result.add_error(
                f"pattern_results must be list, got {type(pattern_results)}"
            )
        else:
            if len(pattern_results) == 0:
                result.add_warning("pattern_results is empty")
            
            # Basic type checking - pattern results should be objects
            # with certain attributes (recognized_patterns, evidence_bundle)
            # but we don't import WS3, so we do minimal checking here
            for i, pr in enumerate(pattern_results):
                if pr is None:
                    result.add_error(f"pattern_results[{i}] is None")
                # Check for expected attributes if object is not None
                elif hasattr(pr, '__dict__'):
                    # Object-like, check for common attributes
                    if not hasattr(pr, 'recognized_patterns'):
                        result.add_warning(
                            f"pattern_results[{i}] missing 'recognized_patterns' attribute"
                        )
                    if not hasattr(pr, 'evidence_bundle'):
                        result.add_warning(
                            f"pattern_results[{i}] missing 'evidence_bundle' attribute"
                        )
        
        return result
