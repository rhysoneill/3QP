"""
Validation checks for comparing expected vs observed results.

Implements qualitative checks without numeric logic, focusing on
pattern presence, trajectory archetype matching, and structural validation.
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal

from .config import ValidationRunConfig

# Add phase4 workstream paths - will be used by functions that need WS3/WS4
phase4_base = Path(__file__).parent.parent.parent
pattern_recognition_path = phase4_base / "03_Pattern_Recognition"
trajectory_analysis_path = phase4_base / "04_Trajectory_Analysis"

if str(pattern_recognition_path) not in sys.path:
    sys.path.insert(0, str(pattern_recognition_path))
if str(trajectory_analysis_path) not in sys.path:
    sys.path.insert(0, str(trajectory_analysis_path))


# Forbidden numeric/probabilistic metadata keys
FORBIDDEN_METADATA_KEYS = {
    "score",
    "probability",
    "confidence",
    "weight",
    "likelihood",
    "probability_score",
    "confidence_score",
    "certainty",
    "belief",
}


@dataclass
class CheckResult:
    """
    Result of a single validation check.
    
    Attributes:
        check_id: Unique identifier for this check
        passed: Whether the check passed
        severity: Severity level of check failure
        message: Human-readable message
        details: Additional categorical details
    """
    check_id: str
    passed: bool
    severity: Literal["INFO", "WARNING", "ERROR"]
    message: str
    details: dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "check_id": self.check_id,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class ValidationRunResult:
    """
    Complete result of a validation run.
    
    Attributes:
        run_id: ID of the validation run
        scenario_id: ID of the scenario being validated
        passed: Overall pass/fail status
        check_results: List of individual check results
        metadata: Additional categorical metadata
    """
    run_id: str
    scenario_id: str
    passed: bool
    check_results: list[CheckResult]
    metadata: dict[str, str] = field(default_factory=dict)
    
    def summary(self) -> str:
        """
        Generate short text summary.
        
        Returns:
            Brief summary of validation results
        """
        status = "PASSED" if self.passed else "FAILED"
        total_checks = len(self.check_results)
        passed_checks = sum(1 for c in self.check_results if c.passed)
        failed_checks = total_checks - passed_checks
        
        return (
            f"Validation {status}: {passed_checks}/{total_checks} checks passed "
            f"({failed_checks} failed) for scenario '{self.scenario_id}'"
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "passed": self.passed,
            "check_results": [c.to_dict() for c in self.check_results],
            "metadata": self.metadata,
        }


# ============================================================================
# Check Implementations
# ============================================================================

def check_pattern_presence(
    run_config: ValidationRunConfig,
    pattern_results: list,  # list[PatternRecognitionResult]
) -> list[CheckResult]:
    """
    Check that expected patterns are present in recognition results.
    
    For each ExpectedPattern(required=True), verifies that at least one
    PatternRecognitionResult contains that pattern type.
    
    Args:
        run_config: Validation run configuration
        pattern_results: List of pattern recognition results
    
    Returns:
        List of CheckResult objects
    """
    results = []
    
    # Collect all recognized patterns
    all_recognized = set()
    for result in pattern_results:
        all_recognized.update(result.recognized_patterns)
    
    # Check each expected pattern
    for expected in run_config.scenario.expected_patterns:
        check_id = f"pattern_presence_{expected.pattern_type}"
        
        if expected.pattern_type in all_recognized:
            results.append(
                CheckResult(
                    check_id=check_id,
                    passed=True,
                    severity="INFO",
                    message=f"Expected pattern '{expected.pattern_type}' was recognized",
                    details={
                        "pattern_type": expected.pattern_type,
                        "required": str(expected.required),
                    },
                )
            )
        else:
            # Pattern not found
            if expected.required:
                results.append(
                    CheckResult(
                        check_id=check_id,
                        passed=False,
                        severity="ERROR",
                        message=(
                            f"Required pattern '{expected.pattern_type}' was not recognized. "
                            f"Expected: {expected.description}"
                        ),
                        details={
                            "pattern_type": expected.pattern_type,
                            "required": "True",
                            "description": expected.description,
                        },
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=check_id,
                        passed=True,
                        severity="WARNING",
                        message=(
                            f"Optional pattern '{expected.pattern_type}' was not recognized. "
                            f"This is informational only."
                        ),
                        details={
                            "pattern_type": expected.pattern_type,
                            "required": "False",
                        },
                    )
                )
    
    return results


def check_trajectory_presence(
    run_config: ValidationRunConfig,
    trajectory_result,  # TrajectoryClassificationResult
) -> list[CheckResult]:
    """
    Check that expected trajectory archetypes are present.
    
    For each ExpectedTrajectory(required=True), verifies that the
    classification result has selected that archetype ID.
    
    Args:
        run_config: Validation run configuration
        trajectory_result: Trajectory classification result
    
    Returns:
        List of CheckResult objects
    """
    results = []
    
    selected = trajectory_result.selected_archetype_id
    candidate_ids = {h.archetype_id for h in trajectory_result.candidate_hypotheses}
    
    # Check each expected trajectory
    for expected in run_config.scenario.expected_trajectories:
        check_id = f"trajectory_presence_{expected.archetype_id}"
        
        # Check if it's the selected archetype
        if expected.archetype_id == selected:
            results.append(
                CheckResult(
                    check_id=check_id,
                    passed=True,
                    severity="INFO",
                    message=(
                        f"Expected trajectory '{expected.archetype_id}' was selected"
                    ),
                    details={
                        "archetype_id": expected.archetype_id,
                        "required": str(expected.required),
                        "status": "selected",
                    },
                )
            )
        elif expected.archetype_id in candidate_ids:
            # Present as candidate but not selected
            if expected.required:
                results.append(
                    CheckResult(
                        check_id=check_id,
                        passed=False,
                        severity="WARNING",
                        message=(
                            f"Required trajectory '{expected.archetype_id}' is a candidate "
                            f"but was not selected (selected: {selected})"
                        ),
                        details={
                            "archetype_id": expected.archetype_id,
                            "required": "True",
                            "status": "candidate_only",
                            "selected_archetype": selected or "none",
                        },
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=check_id,
                        passed=True,
                        severity="INFO",
                        message=(
                            f"Optional trajectory '{expected.archetype_id}' is a candidate"
                        ),
                        details={
                            "archetype_id": expected.archetype_id,
                            "required": "False",
                            "status": "candidate",
                        },
                    )
                )
        else:
            # Not present at all
            if expected.required:
                results.append(
                    CheckResult(
                        check_id=check_id,
                        passed=False,
                        severity="ERROR",
                        message=(
                            f"Required trajectory '{expected.archetype_id}' was not identified. "
                            f"Expected: {expected.description}"
                        ),
                        details={
                            "archetype_id": expected.archetype_id,
                            "required": "True",
                            "status": "missing",
                            "description": expected.description,
                        },
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=check_id,
                        passed=True,
                        severity="INFO",
                        message=(
                            f"Optional trajectory '{expected.archetype_id}' was not identified"
                        ),
                        details={
                            "archetype_id": expected.archetype_id,
                            "required": "False",
                            "status": "missing",
                        },
                    )
                )
    
    return results


def check_structural_validity(
    pattern_results: list,  # list[PatternRecognitionResult]
    trajectory_result,  # TrajectoryClassificationResult
) -> list[CheckResult]:
    """
    Check structural validity using WS3 and WS4 validators.
    
    Uses existing validators from pattern_recognition and trajectory_analysis
    to ensure results meet structural contracts.
    
    Args:
        pattern_results: List of pattern recognition results
        trajectory_result: Trajectory classification result
    
    Returns:
        List of CheckResult objects
    """
    # Import validators only when needed
    from pattern_recognition.validators import (
        RecognizerOutputValidator,
        EvidenceValidator,
    )
    from trajectory_analysis.validators import TrajectoryResultValidator
    
    results = []
    
    # Validate pattern recognition results
    for i, pattern_result in enumerate(pattern_results):
        check_id = f"structural_pattern_{i}"
        
        # Validate recognition result
        validation = RecognizerOutputValidator.validate_recognition_result(
            pattern_result
        )
        
        if validation.is_valid:
            results.append(
                CheckResult(
                    check_id=check_id,
                    passed=True,
                    severity="INFO",
                    message=f"Pattern result {i} is structurally valid",
                    details={"result_index": str(i)},
                )
            )
        else:
            error_msg = "; ".join(validation.errors)
            results.append(
                CheckResult(
                    check_id=check_id,
                    passed=False,
                    severity="ERROR",
                    message=f"Pattern result {i} has structural errors: {error_msg}",
                    details={
                        "result_index": str(i),
                        "error_count": str(len(validation.errors)),
                    },
                )
            )
        
        # Validate evidence bundle
        if hasattr(pattern_result.evidence_bundle, "__class__"):
            bundle_validation = EvidenceValidator.validate_evidence_bundle(
                pattern_result.evidence_bundle
            )
            
            if not bundle_validation.is_valid:
                bundle_errors = "; ".join(bundle_validation.errors)
                results.append(
                    CheckResult(
                        check_id=f"structural_pattern_evidence_{i}",
                        passed=False,
                        severity="ERROR",
                        message=f"Pattern evidence bundle {i} invalid: {bundle_errors}",
                        details={"result_index": str(i)},
                    )
                )
    
    # Validate trajectory classification result
    trajectory_validation = TrajectoryResultValidator.validate_classification_result(
        trajectory_result
    )
    
    if trajectory_validation.is_valid:
        results.append(
            CheckResult(
                check_id="structural_trajectory",
                passed=True,
                severity="INFO",
                message="Trajectory classification result is structurally valid",
                details={},
            )
        )
    else:
        error_msg = "; ".join(trajectory_validation.errors)
        results.append(
            CheckResult(
                check_id="structural_trajectory",
                passed=False,
                severity="ERROR",
                message=f"Trajectory result has structural errors: {error_msg}",
                details={"error_count": str(len(trajectory_validation.errors))},
            )
        )
    
    return results


def check_qualitative_only_enforcement(
    pattern_results: list,  # list[PatternRecognitionResult]
    trajectory_result,  # TrajectoryClassificationResult
) -> list[CheckResult]:
    """
    Ensure no numeric scoring fields appear in metadata.
    
    Checks that forbidden keys (score, probability, confidence, etc.)
    do not appear in any metadata dictionaries.
    
    Args:
        pattern_results: List of pattern recognition results
        trajectory_result: Trajectory classification result
    
    Returns:
        List of CheckResult objects
    """
    results = []
    violations = []
    
    # Check pattern results metadata
    for i, pattern_result in enumerate(pattern_results):
        for key in pattern_result.metadata.keys():
            if key.lower() in FORBIDDEN_METADATA_KEYS:
                violations.append(
                    f"Pattern result {i} metadata contains forbidden key: '{key}'"
                )
    
    # Check trajectory result metadata
    for key in trajectory_result.metadata.keys():
        if key.lower() in FORBIDDEN_METADATA_KEYS:
            violations.append(
                f"Trajectory result metadata contains forbidden key: '{key}'"
            )
    
    # Check trajectory hypotheses metadata
    for i, hyp in enumerate(trajectory_result.candidate_hypotheses):
        if hyp.metadata:
            for key in hyp.metadata.keys():
                if key.lower() in FORBIDDEN_METADATA_KEYS:
                    violations.append(
                        f"Trajectory hypothesis {i} metadata contains forbidden key: '{key}'"
                    )
    
    if violations:
        results.append(
            CheckResult(
                check_id="qualitative_only_enforcement",
                passed=False,
                severity="ERROR",
                message="Numeric/probabilistic metadata detected: " + "; ".join(violations),
                details={
                    "violation_count": str(len(violations)),
                    "forbidden_keys": ", ".join(sorted(FORBIDDEN_METADATA_KEYS)),
                },
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="qualitative_only_enforcement",
                passed=True,
                severity="INFO",
                message="No forbidden numeric/probabilistic metadata detected",
                details={},
            )
        )
    
    return results


# ============================================================================
# Main Check Orchestration
# ============================================================================

def perform_all_checks(
    run_config: ValidationRunConfig,
    encoded_states: list[dict],
    pattern_results: list,  # list[PatternRecognitionResult]
    trajectory_result,  # TrajectoryClassificationResult
) -> ValidationRunResult:
    """
    Perform all validation checks and aggregate results.
    
    Args:
        run_config: Validation run configuration
        encoded_states: Encoded state sequence (currently unused)
        pattern_results: Pattern recognition results
        trajectory_result: Trajectory classification result
    
    Returns:
        ValidationRunResult with all check results
    """
    all_checks = []
    
    # Pattern presence checks
    all_checks.extend(check_pattern_presence(run_config, pattern_results))
    
    # Trajectory presence checks
    all_checks.extend(check_trajectory_presence(run_config, trajectory_result))
    
    # Structural validity checks
    all_checks.extend(check_structural_validity(pattern_results, trajectory_result))
    
    # Qualitative-only enforcement
    all_checks.extend(
        check_qualitative_only_enforcement(pattern_results, trajectory_result)
    )
    
    # Determine overall pass/fail
    # Fails if any check with severity ERROR failed
    overall_passed = all(
        check.passed or check.severity != "ERROR"
        for check in all_checks
    )
    
    return ValidationRunResult(
        run_id=run_config.run_id,
        scenario_id=run_config.scenario.scenario_id,
        passed=overall_passed,
        check_results=all_checks,
        metadata={
            "scenario_label": run_config.scenario.label,
            "total_checks": str(len(all_checks)),
            "notes": run_config.notes,
        },
    )
