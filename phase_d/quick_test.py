"""
Quick test of Phase D demo with minimal experiments (for fast validation)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from phase_d.experiment_harness import ExperimentHarness, ExperimentConfig, ExperimentFamily
from phase_d.data_collector import DataCollector
from phase_d.analysis.counterfactual_analysis import CounterfactualAnalyzer
from phase_d.failure_taxonomy import FailureTaxonomy


def main():
    print("=" * 80)
    print("PHASE D QUICK TEST (Minimal Experiments)")
    print("=" * 80)
    
    harness = ExperimentHarness()
    collector = DataCollector()
    
    # Run just 3 quick experiments
    configs = [
        ExperimentConfig(
            experiment_id="quick_test_1",
            family=ExperimentFamily.MISSION_DURATION,
            baseline_duration=50,  # Short for speed
            duration_multiplier=0.9,
        ),
        ExperimentConfig(
            experiment_id="quick_test_2",
            family=ExperimentFamily.MISSION_DURATION,
            baseline_duration=50,
            duration_multiplier=1.0,
        ),
        ExperimentConfig(
            experiment_id="quick_test_3",
            family=ExperimentFamily.MISSION_DURATION,
            baseline_duration=50,
            duration_multiplier=1.1,
        ),
    ]
    
    print(f"\nRunning {len(configs)} quick experiments...")
    results = harness.run_batch(configs)
    
    # Collect data
    for result in results:
        run_data = collector.collect_from_result(result)
        collector.save_run(run_data)
    
    # Quick analysis
    print("\n" + "=" * 80)
    print("QUICK ANALYSIS")
    print("=" * 80)
    
    all_runs = collector.load_all_runs(family="mission_duration")
    
    analyzer = CounterfactualAnalyzer()
    analyzer.load_runs(all_runs)
    
    duration_analysis = analyzer.analyze_duration_effects()
    print(f"\nDuration correlation: {duration_analysis['correlations'].get('duration_vs_collapse_day', 0.0):.3f}")
    
    # Taxonomy
    taxonomy = FailureTaxonomy()
    taxonomy_summary = taxonomy.analyze_runs(all_runs)
    
    print(f"\nCollapse modes identified:")
    for mode_type, data in taxonomy_summary['classifications'].items():
        if data['count'] > 0:
            print(f"  {mode_type}: {data['count']} runs")
    
    print("\n" + "=" * 80)
    print("✅ QUICK TEST COMPLETE")
    print("=" * 80)
    print("\nPhase D is working correctly.")
    print("Run demo_phase_d.py for full demonstration with all experiments.")


if __name__ == "__main__":
    main()
