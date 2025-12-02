"""
Tests for validation configuration dataclasses.
"""

import sys
from pathlib import Path

# Add validation_harness to path
harness_path = Path(__file__).parent.parent
sys.path.insert(0, str(harness_path))

from validation_harness.config import (
    ExpectedPattern,
    ExpectedTrajectory,
    ValidationScenarioConfig,
    ValidationRunConfig,
)


def test_expected_pattern_creation():
    """Test creating an ExpectedPattern."""
    pattern = ExpectedPattern(
        pattern_type="stable_pattern",
        required=True,
        description="A stable pattern for testing",
    )
    
    assert pattern.pattern_type == "stable_pattern"
    assert pattern.required is True
    assert pattern.description == "A stable pattern for testing"


def test_expected_pattern_to_dict():
    """Test ExpectedPattern serialization."""
    pattern = ExpectedPattern(
        pattern_type="drift_pattern",
        required=False,
        description="Optional drift pattern",
    )
    
    data = pattern.to_dict()
    
    assert data["pattern_type"] == "drift_pattern"
    assert data["required"] is False
    assert data["description"] == "Optional drift pattern"


def test_expected_pattern_from_dict():
    """Test ExpectedPattern deserialization."""
    data = {
        "pattern_type": "recovery_pattern",
        "required": True,
        "description": "Recovery pattern description",
    }
    
    pattern = ExpectedPattern.from_dict(data)
    
    assert pattern.pattern_type == "recovery_pattern"
    assert pattern.required is True
    assert pattern.description == "Recovery pattern description"


def test_expected_pattern_validate_success():
    """Test validation of valid ExpectedPattern."""
    pattern = ExpectedPattern(
        pattern_type="test_pattern",
        required=True,
        description="Test description",
    )
    
    is_valid, error = pattern.validate()
    
    assert is_valid is True
    assert error == ""


def test_expected_pattern_validate_empty_type():
    """Test validation fails for empty pattern_type."""
    pattern = ExpectedPattern(
        pattern_type="",
        required=True,
        description="Test description",
    )
    
    is_valid, error = pattern.validate()
    
    assert is_valid is False
    assert "pattern_type" in error


def test_expected_pattern_validate_empty_description():
    """Test validation fails for empty description."""
    pattern = ExpectedPattern(
        pattern_type="test_pattern",
        required=True,
        description="   ",
    )
    
    is_valid, error = pattern.validate()
    
    assert is_valid is False
    assert "description" in error


def test_expected_trajectory_creation():
    """Test creating an ExpectedTrajectory."""
    trajectory = ExpectedTrajectory(
        archetype_id="stable_adaptation",
        required=True,
        description="Stable adaptation trajectory",
    )
    
    assert trajectory.archetype_id == "stable_adaptation"
    assert trajectory.required is True
    assert trajectory.description == "Stable adaptation trajectory"


def test_expected_trajectory_roundtrip():
    """Test ExpectedTrajectory serialization roundtrip."""
    original = ExpectedTrajectory(
        archetype_id="gradual_drift",
        required=False,
        description="Drift trajectory",
    )
    
    data = original.to_dict()
    restored = ExpectedTrajectory.from_dict(data)
    
    assert restored.archetype_id == original.archetype_id
    assert restored.required == original.required
    assert restored.description == original.description


def test_validation_scenario_config_creation():
    """Test creating a ValidationScenarioConfig."""
    patterns = [
        ExpectedPattern("pattern1", True, "First pattern"),
        ExpectedPattern("pattern2", False, "Second pattern"),
    ]
    
    trajectories = [
        ExpectedTrajectory("traj1", True, "First trajectory"),
    ]
    
    scenario = ValidationScenarioConfig(
        scenario_id="test_scenario",
        label="Test Scenario",
        description="A test scenario",
        expected_patterns=patterns,
        expected_trajectories=trajectories,
        metadata={"key": "value"},
    )
    
    assert scenario.scenario_id == "test_scenario"
    assert scenario.label == "Test Scenario"
    assert len(scenario.expected_patterns) == 2
    assert len(scenario.expected_trajectories) == 1
    assert scenario.metadata["key"] == "value"


def test_validation_scenario_config_validate_success():
    """Test validation of valid scenario config."""
    scenario = ValidationScenarioConfig(
        scenario_id="valid_scenario",
        label="Valid",
        description="A valid scenario",
        expected_patterns=[
            ExpectedPattern("p1", True, "Pattern 1"),
        ],
        expected_trajectories=[
            ExpectedTrajectory("t1", True, "Trajectory 1"),
        ],
    )
    
    is_valid, error = scenario.validate()
    
    assert is_valid is True
    assert error == ""


def test_validation_scenario_config_validate_empty_id():
    """Test validation fails for empty scenario_id."""
    scenario = ValidationScenarioConfig(
        scenario_id="",
        label="Valid",
        description="A scenario",
        expected_patterns=[],
        expected_trajectories=[],
    )
    
    is_valid, error = scenario.validate()
    
    assert is_valid is False
    assert "scenario_id" in error


def test_validation_scenario_config_validate_duplicate_patterns():
    """Test validation fails for duplicate pattern types."""
    scenario = ValidationScenarioConfig(
        scenario_id="dup_scenario",
        label="Duplicate",
        description="Scenario with duplicate patterns",
        expected_patterns=[
            ExpectedPattern("same_pattern", True, "First"),
            ExpectedPattern("same_pattern", False, "Second"),
        ],
        expected_trajectories=[],
    )
    
    is_valid, error = scenario.validate()
    
    assert is_valid is False
    assert "Duplicate pattern_type" in error


def test_validation_scenario_config_validate_duplicate_trajectories():
    """Test validation fails for duplicate archetype IDs."""
    scenario = ValidationScenarioConfig(
        scenario_id="dup_traj_scenario",
        label="Duplicate Trajectories",
        description="Scenario with duplicate trajectories",
        expected_patterns=[],
        expected_trajectories=[
            ExpectedTrajectory("same_traj", True, "First"),
            ExpectedTrajectory("same_traj", False, "Second"),
        ],
    )
    
    is_valid, error = scenario.validate()
    
    assert is_valid is False
    assert "Duplicate archetype_id" in error


def test_validation_run_config_creation():
    """Test creating a ValidationRunConfig."""
    scenario = ValidationScenarioConfig(
        scenario_id="test_scenario",
        label="Test",
        description="Test scenario",
        expected_patterns=[],
        expected_trajectories=[],
    )
    
    run_config = ValidationRunConfig(
        run_id="run_001",
        scenario=scenario,
        notes="Test run notes",
        metadata={"run_type": "test"},
    )
    
    assert run_config.run_id == "run_001"
    assert run_config.scenario.scenario_id == "test_scenario"
    assert run_config.notes == "Test run notes"
    assert run_config.metadata["run_type"] == "test"


def test_validation_run_config_roundtrip():
    """Test ValidationRunConfig serialization roundtrip."""
    scenario = ValidationScenarioConfig(
        scenario_id="roundtrip_scenario",
        label="Roundtrip",
        description="Test roundtrip",
        expected_patterns=[
            ExpectedPattern("p1", True, "Pattern"),
        ],
        expected_trajectories=[
            ExpectedTrajectory("t1", True, "Trajectory"),
        ],
    )
    
    original = ValidationRunConfig(
        run_id="roundtrip_run",
        scenario=scenario,
        notes="Notes",
        metadata={"key": "value"},
    )
    
    data = original.to_dict()
    restored = ValidationRunConfig.from_dict(data)
    
    assert restored.run_id == original.run_id
    assert restored.scenario.scenario_id == original.scenario.scenario_id
    assert restored.notes == original.notes
    assert restored.metadata == original.metadata


def test_validation_run_config_validate_success():
    """Test validation of valid run config."""
    scenario = ValidationScenarioConfig(
        scenario_id="valid",
        label="Valid",
        description="Valid scenario",
        expected_patterns=[],
        expected_trajectories=[],
    )
    
    run_config = ValidationRunConfig(
        run_id="valid_run",
        scenario=scenario,
    )
    
    is_valid, error = run_config.validate()
    
    assert is_valid is True
    assert error == ""


def test_validation_run_config_validate_empty_run_id():
    """Test validation fails for empty run_id."""
    scenario = ValidationScenarioConfig(
        scenario_id="valid",
        label="Valid",
        description="Valid scenario",
        expected_patterns=[],
        expected_trajectories=[],
    )
    
    run_config = ValidationRunConfig(
        run_id="",
        scenario=scenario,
    )
    
    is_valid, error = run_config.validate()
    
    assert is_valid is False
    assert "run_id" in error


def test_validation_run_config_validate_invalid_scenario():
    """Test validation fails for invalid scenario."""
    # Create invalid scenario (empty ID)
    scenario = ValidationScenarioConfig(
        scenario_id="",
        label="Invalid",
        description="Invalid scenario",
        expected_patterns=[],
        expected_trajectories=[],
    )
    
    run_config = ValidationRunConfig(
        run_id="valid_run",
        scenario=scenario,
    )
    
    is_valid, error = run_config.validate()
    
    assert is_valid is False
    assert "scenario" in error.lower()


if __name__ == "__main__":
    # Run all tests
    import traceback
    
    tests = [
        test_expected_pattern_creation,
        test_expected_pattern_to_dict,
        test_expected_pattern_from_dict,
        test_expected_pattern_validate_success,
        test_expected_pattern_validate_empty_type,
        test_expected_pattern_validate_empty_description,
        test_expected_trajectory_creation,
        test_expected_trajectory_roundtrip,
        test_validation_scenario_config_creation,
        test_validation_scenario_config_validate_success,
        test_validation_scenario_config_validate_empty_id,
        test_validation_scenario_config_validate_duplicate_patterns,
        test_validation_scenario_config_validate_duplicate_trajectories,
        test_validation_run_config_creation,
        test_validation_run_config_roundtrip,
        test_validation_run_config_validate_success,
        test_validation_run_config_validate_empty_run_id,
        test_validation_run_config_validate_invalid_scenario,
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
