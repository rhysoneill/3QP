"""
Tests for validation pipeline.
"""

import sys
from pathlib import Path

# Add validation_harness to path
harness_path = Path(__file__).parent.parent
sys.path.insert(0, str(harness_path))

from validation_harness.pipeline import run_validation
from validation_harness.config import (
    ExpectedPattern,
    ExpectedTrajectory,
    ValidationScenarioConfig,
    ValidationRunConfig,
)
from validation_harness.checks import ValidationRunResult
from validation_harness.fixtures import get_fixture_scenarios


def test_run_validation_with_stable_adaptation():
    """Test running validation with stable_adaptation_case."""
    # Get the stable_adaptation scenario from fixtures
    scenarios = get_fixture_scenarios()
    stable_scenario = next(
        s for s in scenarios if s.scenario_id == "stable_adaptation_case"
    )
    
    run_config = ValidationRunConfig(
        run_id="test_run_stable",
        scenario=stable_scenario,
        notes="Test run for stable adaptation",
    )
    
    result = run_validation(run_config)
    
    assert isinstance(result, ValidationRunResult)
    assert result.run_id == "test_run_stable"
    assert result.scenario_id == "stable_adaptation_case"
    assert len(result.check_results) > 0


def test_run_validation_with_gradual_drift():
    """Test running validation with gradual_drift_case."""
    scenarios = get_fixture_scenarios()
    drift_scenario = next(
        s for s in scenarios if s.scenario_id == "gradual_drift_case"
    )
    
    run_config = ValidationRunConfig(
        run_id="test_run_drift",
        scenario=drift_scenario,
    )
    
    result = run_validation(run_config)
    
    assert isinstance(result, ValidationRunResult)
    assert result.run_id == "test_run_drift"
    assert result.scenario_id == "gradual_drift_case"


def test_run_validation_with_third_quarter():
    """Test running validation with third_quarter_signature_case."""
    scenarios = get_fixture_scenarios()
    tq_scenario = next(
        s for s in scenarios if s.scenario_id == "third_quarter_signature_case"
    )
    
    run_config = ValidationRunConfig(
        run_id="test_run_3q",
        scenario=tq_scenario,
    )
    
    result = run_validation(run_config)
    
    assert isinstance(result, ValidationRunResult)
    assert result.run_id == "test_run_3q"
    assert result.scenario_id == "third_quarter_signature_case"


def test_run_validation_returns_checks():
    """Test that run_validation returns check results."""
    scenarios = get_fixture_scenarios()
    scenario = scenarios[0]
    
    run_config = ValidationRunConfig(
        run_id="test_checks",
        scenario=scenario,
    )
    
    result = run_validation(run_config)
    
    # Should have multiple checks
    assert len(result.check_results) > 0
    
    # Should have pattern presence checks
    pattern_checks = [
        c for c in result.check_results
        if c.check_id.startswith("pattern_presence_")
    ]
    assert len(pattern_checks) > 0
    
    # Should have trajectory presence checks
    trajectory_checks = [
        c for c in result.check_results
        if c.check_id.startswith("trajectory_presence_")
    ]
    assert len(trajectory_checks) > 0


def test_run_validation_with_invalid_config_raises():
    """Test that invalid config raises ValueError."""
    # Create invalid scenario (empty ID)
    invalid_scenario = ValidationScenarioConfig(
        scenario_id="",
        label="Invalid",
        description="Invalid scenario",
        expected_patterns=[],
        expected_trajectories=[],
    )
    
    run_config = ValidationRunConfig(
        run_id="test_invalid",
        scenario=invalid_scenario,
    )
    
    try:
        run_validation(run_config)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid ValidationRunConfig" in str(e)


def test_run_validation_with_unknown_scenario_raises():
    """Test that unknown scenario raises ValueError."""
    # Create scenario with ID that doesn't match any fixture
    unknown_scenario = ValidationScenarioConfig(
        scenario_id="unknown_scenario_xyz",
        label="Unknown",
        description="Unknown scenario",
        expected_patterns=[],
        expected_trajectories=[],
    )
    
    run_config = ValidationRunConfig(
        run_id="test_unknown",
        scenario=unknown_scenario,
    )
    
    try:
        run_validation(run_config)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Failed to retrieve fixture" in str(e)


def test_run_validation_passes_for_matching_fixture():
    """Test that validation passes when fixture matches expectations."""
    # stable_adaptation fixture should match its scenario expectations
    scenarios = get_fixture_scenarios()
    stable_scenario = next(
        s for s in scenarios if s.scenario_id == "stable_adaptation_case"
    )
    
    run_config = ValidationRunConfig(
        run_id="test_passing",
        scenario=stable_scenario,
    )
    
    result = run_validation(run_config)
    
    # Should pass because fixture is designed to match scenario
    assert result.passed is True


def test_run_validation_includes_metadata():
    """Test that validation result includes metadata."""
    scenarios = get_fixture_scenarios()
    scenario = scenarios[0]
    
    run_config = ValidationRunConfig(
        run_id="test_metadata",
        scenario=scenario,
        notes="Test notes",
        metadata={"key": "value"},
    )
    
    result = run_validation(run_config)
    
    assert "scenario_label" in result.metadata
    assert result.metadata["notes"] == "Test notes"


def test_run_validation_summary():
    """Test that validation result has working summary."""
    scenarios = get_fixture_scenarios()
    scenario = scenarios[0]
    
    run_config = ValidationRunConfig(
        run_id="test_summary",
        scenario=scenario,
    )
    
    result = run_validation(run_config)
    summary = result.summary()
    
    assert isinstance(summary, str)
    assert scenario.scenario_id in summary
    assert "checks passed" in summary


if __name__ == "__main__":
    # Run all tests
    import traceback
    
    tests = [
        test_run_validation_with_stable_adaptation,
        test_run_validation_with_gradual_drift,
        test_run_validation_with_third_quarter,
        test_run_validation_returns_checks,
        test_run_validation_with_invalid_config_raises,
        test_run_validation_with_unknown_scenario_raises,
        test_run_validation_passes_for_matching_fixture,
        test_run_validation_includes_metadata,
        test_run_validation_summary,
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
