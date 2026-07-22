"""
Quick Validation Script for Phase D

Fast validation that Phase D components work correctly without
running full experiment suite.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from phase_d.experiment_harness import (
    ExperimentHarness,
    ExperimentConfig,
    ExperimentFamily,
)
from phase_d.data_collector import DataCollector
from phase_d.analysis.counterfactual_analysis import CounterfactualAnalyzer
from phase_d.failure_taxonomy import FailureTaxonomy, CollapseModeType


def test_experiment_harness():
    """Test that experiment harness can run a simple experiment."""
    print("\n--- Testing Experiment Harness ---")
    
    harness = ExperimentHarness()
    
    config = ExperimentConfig(
        experiment_id="test_baseline",
        family=ExperimentFamily.MISSION_DURATION,
        baseline_duration=100,  # Shorter for quick test
        duration_multiplier=1.0,
    )
    
    result = harness.run_experiment(config, save_result=False)
    
    assert result is not None, "Experiment failed to run"
    assert result.fingerprint is not None, "No fingerprint generated"
    assert result.action_log is not None, "No action log generated"
    
    print(f"  ✓ Experiment ran successfully")
    print(f"  ✓ Collapse day: {result.fingerprint.collapse_day}")
    print(f"  ✓ Collapse depth: {result.fingerprint.collapse_depth:.3f}")
    
    return result


def test_data_collector(result):
    """Test data collection from experiment result."""
    print("\n--- Testing Data Collector ---")
    
    collector = DataCollector()
    run_data = collector.collect_from_result(result)
    
    assert run_data is not None, "Failed to collect run data"
    assert run_data.fingerprint is not None, "No fingerprint in run data"
    assert len(run_data.action_frequencies) > 0, "No action frequencies"
    
    print(f"  ✓ Data collected successfully")
    print(f"  ✓ Run ID: {run_data.run_id}")
    print(f"  ✓ Action types recorded: {len(run_data.action_frequencies)}")
    print(f"  ✓ Dominant action: {run_data.get_dominant_action()}")
    
    return run_data


def test_counterfactual_analyzer(run_data):
    """Test counterfactual analysis capabilities."""
    print("\n--- Testing Counterfactual Analyzer ---")
    
    analyzer = CounterfactualAnalyzer()
    analyzer.load_runs([run_data])
    
    # Test action-collapse correlation
    analysis = analyzer.analyze_action_collapse_correlation()
    
    assert analysis is not None, "Analysis failed"
    assert "by_collapse_timing" in analysis, "Missing timing analysis"
    
    print(f"  ✓ Analysis completed successfully")
    print(f"  ✓ Collapse timing categories: {len(analysis['by_collapse_timing'])}")
    
    return analyzer


def test_failure_taxonomy(run_data):
    """Test failure taxonomy classification."""
    print("\n--- Testing Failure Taxonomy ---")
    
    taxonomy = FailureTaxonomy()
    
    # Classify single run
    mode_type = taxonomy.classify_run(run_data)
    
    assert mode_type is not None, "Classification failed"
    
    print(f"  ✓ Run classified successfully")
    print(f"  ✓ Mode type: {mode_type.value}")
    
    # Analyze runs
    summary = taxonomy.analyze_runs([run_data])
    
    assert summary is not None, "Taxonomy analysis failed"
    assert summary["total_runs"] == 1, "Incorrect run count"
    
    print(f"  ✓ Taxonomy analysis completed")
    
    # Get mode definition
    mode = taxonomy.get_mode(mode_type)
    if mode:
        print(f"  ✓ Mode definition: {mode.name}")
        print(f"    Description: {mode.description[:80]}...")
    
    return taxonomy


def test_experiment_runner():
    """Test experiment runner functions."""
    print("\n--- Testing Experiment Runner ---")
    
    from phase_d.experiment_runner import (
        run_mission_duration_sweep,
        _create_crew_variants,
    )
    
    # Test crew variant creation
    crews = _create_crew_variants()
    
    assert len(crews) == 3, "Should create 3 crew variants"
    assert all(len(c.members) == 3 for c in crews), "All crews should have 3 members"
    
    print(f"  ✓ Crew variants created successfully")
    for crew in crews:
        print(f"    - {crew.crew_name}")
    
    print(f"  ✓ Experiment runner validated")


def main():
    """Run all validation tests."""
    print("=" * 80)
    print("PHASE D VALIDATION")
    print("=" * 80)
    print("\nRunning quick validation tests...")
    
    try:
        # Test experiment harness
        result = test_experiment_harness()
        
        # Test data collector
        run_data = test_data_collector(result)
        
        # Test analyzer
        analyzer = test_counterfactual_analyzer(run_data)
        
        # Test taxonomy
        taxonomy = test_failure_taxonomy(run_data)
        
        # Test runner
        test_experiment_runner()
        
        print("\n" + "=" * 80)
        print("✅ ALL VALIDATION TESTS PASSED")
        print("=" * 80)
        print("\nPhase D components are working correctly.")
        print("Run demo_phase_d.py for full demonstration.")
        
        return True
        
    except AssertionError as e:
        print("\n" + "=" * 80)
        print("❌ VALIDATION FAILED")
        print("=" * 80)
        print(f"\nError: {e}")
        return False
    
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ VALIDATION ERROR")
        print("=" * 80)
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
