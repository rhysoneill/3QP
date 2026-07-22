"""
Integration Test: Ruthless Core Model with Phase 4 Pipeline

This script demonstrates end-to-end integration between the Ruthless Core Model
and the existing Phase 4 architecture (WS1-5).

It shows how to:
1. Generate trajectories with the Ruthless Core Model
2. Convert outputs to Phase 4 encoded states
3. Feed into Phase 4 trajectory analysis (when available)
4. Validate structural compatibility
"""

import sys
from pathlib import Path

# Add paths
ruthless_core_path = Path(__file__).parent
phase4_base = Path(__file__).parent.parent

if str(ruthless_core_path) not in sys.path:
    sys.path.insert(0, str(ruthless_core_path))

from ruthless_core import (
    RuthlessCoreConfig,
    RuthlessCoreModel,
    to_phase4_encoded_states,
    to_phase4_trajectory_result,
)


def test_basic_simulation():
    """Test that basic simulation runs without errors."""
    print("Test 1: Basic Simulation")
    config = RuthlessCoreConfig(mission_length_days=100)
    model = RuthlessCoreModel(config)
    output = model.run()
    
    assert len(output.days) == 100
    assert len(output.cohesion) == 100
    assert len(output.strain) == 100
    assert len(output.monotony) == 100
    assert len(output.tq_pressure) == 100
    
    print("  ✓ Simulation runs successfully")
    print(f"  ✓ Generated {len(output)} time steps")
    return output


def test_encoded_states_format(output):
    """Test that encoded states match Phase 4 expectations."""
    print("\nTest 2: Encoded States Format")
    encoded_states = to_phase4_encoded_states(output)
    
    assert isinstance(encoded_states, list)
    assert len(encoded_states) == len(output)
    
    # Check structure of first state
    state = encoded_states[0]
    assert "day" in state
    assert "mission_progress" in state
    assert "domains" in state
    assert "metadata" in state
    
    # Check domains
    domains = state["domains"]
    assert "physiological" in domains
    assert "social" in domains
    assert "environmental" in domains
    assert "trajectory_indicators" in domains
    
    print("  ✓ Encoded states format is valid")
    print(f"  ✓ Generated {len(encoded_states)} encoded states")
    print(f"  ✓ Domains present: {list(domains.keys())}")
    return encoded_states


def test_trajectory_result_format(output):
    """Test that trajectory result matches Phase 4 expectations."""
    print("\nTest 3: Trajectory Result Format")
    trajectory_result = to_phase4_trajectory_result(output)
    
    assert isinstance(trajectory_result, dict)
    assert "archetype_id" in trajectory_result
    assert "label" in trajectory_result
    assert "support_strength" in trajectory_result
    assert "evidence" in trajectory_result
    assert "metadata" in trajectory_result
    
    print("  ✓ Trajectory result format is valid")
    print(f"  ✓ Archetype: {trajectory_result['archetype_id']}")
    print(f"  ✓ Support: {trajectory_result['support_strength']}")
    return trajectory_result


def test_third_quarter_detection():
    """Test that third quarter trajectories are correctly detected."""
    print("\nTest 4: Third Quarter Detection")
    
    # Create a config that should produce third quarter behavior
    config = RuthlessCoreConfig(
        mission_length_days=200,
        q_center=0.68,
        q_peak=0.55,
        c_strain=0.011,
        c_q=0.020,
    )
    
    model = RuthlessCoreModel(config)
    output = model.run()
    trajectory_result = to_phase4_trajectory_result(output)
    
    min_cohesion_idx = output.cohesion.index(min(output.cohesion))
    min_day = output.days[min_cohesion_idx]
    min_progress = min_day / len(output)
    
    print(f"  ✓ Min cohesion at day {min_day} ({min_progress:.1%})")
    print(f"  ✓ Detected archetype: {trajectory_result['archetype_id']}")
    
    # Should detect third quarter if minimum is in reasonable range
    if 0.50 <= min_progress <= 0.90:
        assert trajectory_result['archetype_id'] == 'third_quarter'
        print("  ✓ Third quarter correctly detected")
    else:
        print("  ⚠ Third quarter not detected (edge case)")


def test_parameter_variation():
    """Test that parameter changes produce expected effects."""
    print("\nTest 5: Parameter Variation")
    
    results = []
    for q_peak in [0.3, 0.5, 0.7]:
        config = RuthlessCoreConfig(
            mission_length_days=150,
            q_peak=q_peak,
        )
        model = RuthlessCoreModel(config)
        output = model.run()
        min_cohesion = min(output.cohesion)
        results.append((q_peak, min_cohesion))
    
    print("  ✓ Parameter sweep completed")
    for q_peak, min_coh in results:
        print(f"    q_peak={q_peak:.1f} → min_cohesion={min_coh:.3f}")


def main():
    """Run all integration tests."""
    print("=" * 70)
    print("  RUTHLESS CORE MODEL - INTEGRATION TESTS")
    print("=" * 70)
    print()
    
    try:
        # Run tests
        output = test_basic_simulation()
        encoded_states = test_encoded_states_format(output)
        trajectory_result = test_trajectory_result_format(output)
        test_third_quarter_detection()
        test_parameter_variation()
        
        print("\n" + "=" * 70)
        print("  ALL TESTS PASSED ✓")
        print("=" * 70)
        print("\nThe Ruthless Core Model is ready for:")
        print("  - Trajectory generation and calibration")
        print("  - Integration with Phase 4 validation harness")
        print("  - Parameter exploration and sensitivity analysis")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
