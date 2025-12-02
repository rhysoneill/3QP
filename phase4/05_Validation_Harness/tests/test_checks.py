"""
Tests for validation checks.
"""

import sys
from pathlib import Path

# Add validation_harness to path
harness_path = Path(__file__).parent.parent
sys.path.insert(0, str(harness_path))

# Add phase4 workstreams to path
phase4_base = Path(__file__).parent.parent.parent
pattern_recognition_path = phase4_base / "03_Pattern_Recognition"
trajectory_analysis_path = phase4_base / "04_Trajectory_Analysis"

if str(pattern_recognition_path) not in sys.path:
    sys.path.insert(0, str(pattern_recognition_path))
if str(trajectory_analysis_path) not in sys.path:
    sys.path.insert(0, str(trajectory_analysis_path))

from validation_harness.checks import (
    CheckResult,
    ValidationRunResult,
    check_pattern_presence,
    check_trajectory_presence,
    check_structural_validity,
    check_qualitative_only_enforcement,
    perform_all_checks,
)
from validation_harness.config import (
    ExpectedPattern,
    ExpectedTrajectory,
    ValidationScenarioConfig,
    ValidationRunConfig,
)
from pattern_recognition.interfaces import PatternRecognitionResult
from pattern_recognition.evidence import PatternEvidence, PatternEvidenceBundle
from trajectory_analysis.models import (
    TrajectoryHypothesis,
    TrajectoryClassificationResult,
)
from trajectory_analysis.evidence import (
    TrajectorySupportStrength,
    TrajectoryEvidence,
    TrajectoryEvidenceBundle,
)


def test_check_result_creation():
    """Test creating a CheckResult."""
    result = CheckResult(
        check_id="test_check",
        passed=True,
        severity="INFO",
        message="Test message",
        details={"key": "value"},
    )
    
    assert result.check_id == "test_check"
    assert result.passed is True
    assert result.severity == "INFO"
    assert result.message == "Test message"
    assert result.details["key"] == "value"


def test_check_result_to_dict():
    """Test CheckResult serialization."""
    result = CheckResult(
        check_id="test",
        passed=False,
        severity="ERROR",
        message="Error message",
    )
    
    data = result.to_dict()
    
    assert data["check_id"] == "test"
    assert data["passed"] is False
    assert data["severity"] == "ERROR"
    assert data["message"] == "Error message"


def test_validation_run_result_summary():
    """Test ValidationRunResult summary generation."""
    checks = [
        CheckResult("check1", True, "INFO", "Passed"),
        CheckResult("check2", False, "ERROR", "Failed"),
        CheckResult("check3", True, "INFO", "Passed"),
    ]
    
    result = ValidationRunResult(
        run_id="run_001",
        scenario_id="test_scenario",
        passed=False,
        check_results=checks,
    )
    
    summary = result.summary()
    
    assert "2/3 checks passed" in summary
    assert "FAILED" in summary


def test_check_pattern_presence_required_found():
    """Test pattern presence check when required pattern is found."""
    scenario = ValidationScenarioConfig(
        scenario_id="test",
        label="Test",
        description="Test",
        expected_patterns=[
            ExpectedPattern("stable_pattern", True, "Stable pattern"),
        ],
        expected_trajectories=[],
    )
    
    run_config = ValidationRunConfig(run_id="run_001", scenario=scenario)
    
    evidence = PatternEvidenceBundle(evidence_items=[], metadata={})
    pattern_results = [
        PatternRecognitionResult(
            recognized_patterns=["stable_pattern"],
            evidence_bundle=evidence,
        ),
    ]
    
    results = check_pattern_presence(run_config, pattern_results)
    
    assert len(results) == 1
    assert results[0].passed is True


def test_check_pattern_presence_required_missing():
    """Test pattern presence check when required pattern is missing."""
    scenario = ValidationScenarioConfig(
        scenario_id="test",
        label="Test",
        description="Test",
        expected_patterns=[
            ExpectedPattern("stable_pattern", True, "Stable pattern"),
        ],
        expected_trajectories=[],
    )
    
    run_config = ValidationRunConfig(run_id="run_001", scenario=scenario)
    
    evidence = PatternEvidenceBundle(evidence_items=[], metadata={})
    pattern_results = [
        PatternRecognitionResult(
            recognized_patterns=["other_pattern"],
            evidence_bundle=evidence,
        ),
    ]
    
    results = check_pattern_presence(run_config, pattern_results)
    
    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].severity == "ERROR"


def test_check_pattern_presence_optional_missing():
    """Test pattern presence check when optional pattern is missing."""
    scenario = ValidationScenarioConfig(
        scenario_id="test",
        label="Test",
        description="Test",
        expected_patterns=[
            ExpectedPattern("optional_pattern", False, "Optional pattern"),
        ],
        expected_trajectories=[],
    )
    
    run_config = ValidationRunConfig(run_id="run_001", scenario=scenario)
    
    evidence = PatternEvidenceBundle(evidence_items=[], metadata={})
    pattern_results = [
        PatternRecognitionResult(
            recognized_patterns=["other_pattern"],
            evidence_bundle=evidence,
        ),
    ]
    
    results = check_pattern_presence(run_config, pattern_results)
    
    assert len(results) == 1
    # Should still pass overall, just with a warning
    assert results[0].passed is True
    assert results[0].severity == "WARNING"


def test_check_trajectory_presence_selected():
    """Test trajectory presence when expected archetype is selected."""
    scenario = ValidationScenarioConfig(
        scenario_id="test",
        label="Test",
        description="Test",
        expected_patterns=[],
        expected_trajectories=[
            ExpectedTrajectory("stable_adaptation", True, "Stable adaptation"),
        ],
    )
    
    run_config = ValidationRunConfig(run_id="run_001", scenario=scenario)
    
    hyp = TrajectoryHypothesis(
        archetype_id="stable_adaptation",
        label="Stable",
        support_strength=TrajectorySupportStrength.STRONG,
        rationale="Test",
    )
    
    evidence = TrajectoryEvidenceBundle(items=[])
    
    trajectory_result = TrajectoryClassificationResult(
        candidate_hypotheses=[hyp],
        supporting_evidence=evidence,
        selected_archetype_id="stable_adaptation",
    )
    
    results = check_trajectory_presence(run_config, trajectory_result)
    
    assert len(results) == 1
    assert results[0].passed is True


def test_check_trajectory_presence_missing():
    """Test trajectory presence when expected archetype is missing."""
    scenario = ValidationScenarioConfig(
        scenario_id="test",
        label="Test",
        description="Test",
        expected_patterns=[],
        expected_trajectories=[
            ExpectedTrajectory("stable_adaptation", True, "Stable adaptation"),
        ],
    )
    
    run_config = ValidationRunConfig(run_id="run_001", scenario=scenario)
    
    evidence = TrajectoryEvidenceBundle(items=[])
    
    trajectory_result = TrajectoryClassificationResult(
        candidate_hypotheses=[],
        supporting_evidence=evidence,
        selected_archetype_id=None,
    )
    
    results = check_trajectory_presence(run_config, trajectory_result)
    
    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].severity == "ERROR"


def test_check_structural_validity_valid_results():
    """Test structural validity with valid results."""
    evidence = PatternEvidenceBundle(evidence_items=[], metadata={})
    pattern_results = [
        PatternRecognitionResult(
            recognized_patterns=["pattern1"],
            evidence_bundle=evidence,
        ),
    ]
    
    hyp = TrajectoryHypothesis(
        archetype_id="test",
        label="Test",
        support_strength=TrajectorySupportStrength.MODERATE,
        rationale="Test rationale",
    )
    
    traj_evidence = TrajectoryEvidenceBundle(items=[])
    
    trajectory_result = TrajectoryClassificationResult(
        candidate_hypotheses=[hyp],
        supporting_evidence=traj_evidence,
    )
    
    results = check_structural_validity(pattern_results, trajectory_result)
    
    # Should have checks for pattern result and trajectory result
    assert len(results) >= 2
    # All should pass
    assert all(r.passed for r in results if r.severity == "ERROR")


def test_check_qualitative_only_enforcement_clean():
    """Test qualitative-only enforcement with clean metadata."""
    evidence = PatternEvidenceBundle(evidence_items=[], metadata={})
    pattern_results = [
        PatternRecognitionResult(
            recognized_patterns=["pattern1"],
            evidence_bundle=evidence,
            metadata={"schema_version": "0.1.0"},
        ),
    ]
    
    hyp = TrajectoryHypothesis(
        archetype_id="test",
        label="Test",
        support_strength=TrajectorySupportStrength.MODERATE,
        rationale="Test",
        metadata={"category": "test"},
    )
    
    traj_evidence = TrajectoryEvidenceBundle(items=[])
    
    trajectory_result = TrajectoryClassificationResult(
        candidate_hypotheses=[hyp],
        supporting_evidence=traj_evidence,
        metadata={"classifier": "test"},
    )
    
    results = check_qualitative_only_enforcement(pattern_results, trajectory_result)
    
    assert len(results) == 1
    assert results[0].passed is True


def test_check_qualitative_only_enforcement_forbidden_key():
    """Test qualitative-only enforcement detects forbidden keys."""
    evidence = PatternEvidenceBundle(evidence_items=[], metadata={})
    pattern_results = [
        PatternRecognitionResult(
            recognized_patterns=["pattern1"],
            evidence_bundle=evidence,
            metadata={"score": "0.95"},  # Forbidden!
        ),
    ]
    
    hyp = TrajectoryHypothesis(
        archetype_id="test",
        label="Test",
        support_strength=TrajectorySupportStrength.MODERATE,
        rationale="Test",
    )
    
    traj_evidence = TrajectoryEvidenceBundle(items=[])
    
    trajectory_result = TrajectoryClassificationResult(
        candidate_hypotheses=[hyp],
        supporting_evidence=traj_evidence,
    )
    
    results = check_qualitative_only_enforcement(pattern_results, trajectory_result)
    
    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].severity == "ERROR"


def test_perform_all_checks():
    """Test performing all checks together."""
    scenario = ValidationScenarioConfig(
        scenario_id="test",
        label="Test",
        description="Test",
        expected_patterns=[
            ExpectedPattern("stable_pattern", True, "Stable"),
        ],
        expected_trajectories=[
            ExpectedTrajectory("stable_adaptation", True, "Stable"),
        ],
    )
    
    run_config = ValidationRunConfig(run_id="run_001", scenario=scenario)
    
    encoded_states = [{"state_id": "s1"}]
    
    evidence = PatternEvidenceBundle(evidence_items=[], metadata={})
    pattern_results = [
        PatternRecognitionResult(
            recognized_patterns=["stable_pattern"],
            evidence_bundle=evidence,
        ),
    ]
    
    hyp = TrajectoryHypothesis(
        archetype_id="stable_adaptation",
        label="Stable",
        support_strength=TrajectorySupportStrength.STRONG,
        rationale="Test",
    )
    
    traj_evidence = TrajectoryEvidenceBundle(items=[])
    
    trajectory_result = TrajectoryClassificationResult(
        candidate_hypotheses=[hyp],
        supporting_evidence=traj_evidence,
        selected_archetype_id="stable_adaptation",
    )
    
    result = perform_all_checks(
        run_config,
        encoded_states,
        pattern_results,
        trajectory_result,
    )
    
    assert isinstance(result, ValidationRunResult)
    assert result.run_id == "run_001"
    assert result.scenario_id == "test"
    assert len(result.check_results) > 0


if __name__ == "__main__":
    # Run all tests
    import traceback
    
    tests = [
        test_check_result_creation,
        test_check_result_to_dict,
        test_validation_run_result_summary,
        test_check_pattern_presence_required_found,
        test_check_pattern_presence_required_missing,
        test_check_pattern_presence_optional_missing,
        test_check_trajectory_presence_selected,
        test_check_trajectory_presence_missing,
        test_check_structural_validity_valid_results,
        test_check_qualitative_only_enforcement_clean,
        test_check_qualitative_only_enforcement_forbidden_key,
        test_perform_all_checks,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}")
            traceback.print_exc()
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
