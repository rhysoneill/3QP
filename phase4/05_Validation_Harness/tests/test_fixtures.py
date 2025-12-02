"""
Tests for fixture data and scenarios.
"""

import sys
from pathlib import Path

# Add validation_harness to path
harness_path = Path(__file__).parent.parent
sys.path.insert(0, str(harness_path))

# Add phase4 workstreams to path for type checks
phase4_base = Path(__file__).parent.parent.parent
pattern_recognition_path = phase4_base / "03_Pattern_Recognition"
trajectory_analysis_path = phase4_base / "04_Trajectory_Analysis"

if str(pattern_recognition_path) not in sys.path:
    sys.path.insert(0, str(pattern_recognition_path))
if str(trajectory_analysis_path) not in sys.path:
    sys.path.insert(0, str(trajectory_analysis_path))

from validation_harness.fixtures import (
    get_fixture_scenarios,
    get_fixture_for_scenario,
)
from validation_harness.config import ValidationScenarioConfig

from pattern_recognition.interfaces import PatternRecognitionResult
from trajectory_analysis.models import TrajectoryClassificationResult


def test_get_fixture_scenarios_returns_list():
    """Test that get_fixture_scenarios returns a non-empty list."""
    scenarios = get_fixture_scenarios()
    
    assert isinstance(scenarios, list)
    assert len(scenarios) > 0


def test_get_fixture_scenarios_contains_configs():
    """Test that scenarios are ValidationScenarioConfig instances."""
    scenarios = get_fixture_scenarios()
    
    for scenario in scenarios:
        assert isinstance(scenario, ValidationScenarioConfig)


def test_get_fixture_scenarios_has_expected_scenarios():
    """Test that expected scenario IDs are present."""
    scenarios = get_fixture_scenarios()
    scenario_ids = {s.scenario_id for s in scenarios}
    
    expected_ids = {
        "stable_adaptation_case",
        "gradual_drift_case",
        "third_quarter_signature_case",
    }
    
    assert expected_ids.issubset(scenario_ids)


def test_fixture_scenarios_are_valid():
    """Test that all fixture scenarios pass validation."""
    scenarios = get_fixture_scenarios()
    
    for scenario in scenarios:
        is_valid, error = scenario.validate()
        assert is_valid, f"Scenario {scenario.scenario_id} invalid: {error}"


def test_get_fixture_for_stable_adaptation():
    """Test retrieving stable_adaptation_case fixture."""
    states, patterns, trajectory = get_fixture_for_scenario("stable_adaptation_case")
    
    # Check states
    assert isinstance(states, list)
    assert len(states) > 0
    assert all(isinstance(s, dict) for s in states)
    
    # Check pattern results
    assert isinstance(patterns, list)
    assert len(patterns) > 0
    assert all(isinstance(p, PatternRecognitionResult) for p in patterns)
    
    # Check trajectory result
    assert isinstance(trajectory, TrajectoryClassificationResult)


def test_get_fixture_for_gradual_drift():
    """Test retrieving gradual_drift_case fixture."""
    states, patterns, trajectory = get_fixture_for_scenario("gradual_drift_case")
    
    assert isinstance(states, list)
    assert len(states) > 0
    assert isinstance(patterns, list)
    assert len(patterns) > 0
    assert isinstance(trajectory, TrajectoryClassificationResult)


def test_get_fixture_for_third_quarter_signature():
    """Test retrieving third_quarter_signature_case fixture."""
    states, patterns, trajectory = get_fixture_for_scenario("third_quarter_signature_case")
    
    assert isinstance(states, list)
    assert len(states) > 0
    assert isinstance(patterns, list)
    assert len(patterns) > 0
    assert isinstance(trajectory, TrajectoryClassificationResult)


def test_get_fixture_for_unknown_scenario_raises():
    """Test that unknown scenario ID raises ValueError."""
    try:
        get_fixture_for_scenario("nonexistent_scenario")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown scenario_id" in str(e)


def test_stable_adaptation_fixture_has_expected_patterns():
    """Test stable_adaptation fixture contains expected pattern types."""
    _, patterns, _ = get_fixture_for_scenario("stable_adaptation_case")
    
    all_patterns = set()
    for result in patterns:
        all_patterns.update(result.recognized_patterns)
    
    # Should contain stable_pattern
    assert "stable_pattern" in all_patterns


def test_gradual_drift_fixture_has_expected_patterns():
    """Test gradual_drift fixture contains expected pattern types."""
    _, patterns, _ = get_fixture_for_scenario("gradual_drift_case")
    
    all_patterns = set()
    for result in patterns:
        all_patterns.update(result.recognized_patterns)
    
    # Should contain drift_pattern
    assert "drift_pattern" in all_patterns


def test_third_quarter_fixture_has_expected_patterns():
    """Test third_quarter_signature fixture contains expected pattern types."""
    _, patterns, _ = get_fixture_for_scenario("third_quarter_signature_case")
    
    all_patterns = set()
    for result in patterns:
        all_patterns.update(result.recognized_patterns)
    
    # Should contain disruption and recovery patterns
    assert "disruption_pattern" in all_patterns
    assert "recovery_pattern" in all_patterns


def test_stable_adaptation_fixture_has_expected_trajectory():
    """Test stable_adaptation fixture has expected trajectory archetype."""
    _, _, trajectory = get_fixture_for_scenario("stable_adaptation_case")
    
    assert trajectory.selected_archetype_id == "stable_adaptation"


def test_gradual_drift_fixture_has_expected_trajectory():
    """Test gradual_drift fixture has expected trajectory archetype."""
    _, _, trajectory = get_fixture_for_scenario("gradual_drift_case")
    
    assert trajectory.selected_archetype_id == "gradual_drift"


def test_third_quarter_fixture_has_expected_trajectory():
    """Test third_quarter_signature fixture has expected trajectory archetype."""
    _, _, trajectory = get_fixture_for_scenario("third_quarter_signature_case")
    
    assert trajectory.selected_archetype_id == "third_quarter_signature"


def test_fixtures_have_metadata():
    """Test that fixture results include metadata."""
    _, patterns, trajectory = get_fixture_for_scenario("stable_adaptation_case")
    
    # Check pattern metadata
    for pattern in patterns:
        assert hasattr(pattern, 'metadata')
        assert isinstance(pattern.metadata, dict)
    
    # Check trajectory metadata
    assert hasattr(trajectory, 'metadata')
    assert isinstance(trajectory.metadata, dict)


def test_fixtures_have_evidence():
    """Test that fixture results include evidence."""
    _, patterns, trajectory = get_fixture_for_scenario("stable_adaptation_case")
    
    # Check pattern evidence
    for pattern in patterns:
        assert hasattr(pattern, 'evidence_bundle')
        assert pattern.evidence_bundle is not None
    
    # Check trajectory evidence
    assert hasattr(trajectory, 'supporting_evidence')
    assert trajectory.supporting_evidence is not None


if __name__ == "__main__":
    # Run all tests
    import traceback
    
    tests = [
        test_get_fixture_scenarios_returns_list,
        test_get_fixture_scenarios_contains_configs,
        test_get_fixture_scenarios_has_expected_scenarios,
        test_fixture_scenarios_are_valid,
        test_get_fixture_for_stable_adaptation,
        test_get_fixture_for_gradual_drift,
        test_get_fixture_for_third_quarter_signature,
        test_get_fixture_for_unknown_scenario_raises,
        test_stable_adaptation_fixture_has_expected_patterns,
        test_gradual_drift_fixture_has_expected_patterns,
        test_third_quarter_fixture_has_expected_patterns,
        test_stable_adaptation_fixture_has_expected_trajectory,
        test_gradual_drift_fixture_has_expected_trajectory,
        test_third_quarter_fixture_has_expected_trajectory,
        test_fixtures_have_metadata,
        test_fixtures_have_evidence,
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
