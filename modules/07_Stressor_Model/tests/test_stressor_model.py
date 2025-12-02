"""
Tests for the Stressor Model module.

Validates stressor dynamics, intensity bounds, temporal consistency,
and data contract compliance.
"""

import pytest
from datetime import datetime
import math

from stressor_model import (
    StressorModel,
    MissionConfig,
    StressorParameterSet,
    UpdateCycleInput,
    StressorCategory,
    SpikeEvent,
    NoiseConfig,
    NoiseType,
    PhaseDefinition,
    PhaseType,
    ScheduledEvent,
    EventType,
    StressorModifier,
)


class TestStressorModel:
    """Test suite for StressorModel core functionality."""
    
    def test_initialization(self):
        """Test basic initialization."""
        config = MissionConfig(
            mission_id="TEST_001",
            mission_start_date=datetime(2025, 1, 1),
            mission_duration_days=180.0,
            random_seed=42,
            stressor_parameters=[
                StressorParameterSet(
                    stressor_id="test_stressor",
                    category=StressorCategory.OPERATIONAL,
                    baseline=0.3,
                    max_intensity=0.9,
                )
            ],
        )
        
        model = StressorModel()
        model.initialize(config)
        
        assert model.current_time == 0.0
        assert model.mission_config == config
    
    def test_constant_intensity(self):
        """Test constant baseline stressor."""
        config = MissionConfig(
            mission_id="TEST_002",
            mission_start_date=datetime(2025, 1, 1),
            mission_duration_days=7.0,
            random_seed=42,
            stressor_parameters=[
                StressorParameterSet(
                    stressor_id="constant_stressor",
                    category=StressorCategory.ENVIRONMENTAL,
                    baseline=0.5,
                    max_intensity=0.5,
                )
            ],
        )
        
        model = StressorModel()
        model.initialize(config)
        
        # Update for 7 days
        for day in range(7):
            update_input = UpdateCycleInput(
                current_time=float(day + 1),
                delta_time=1.0,
            )
            result = model.update(update_input)
            
            # Should remain constant
            stressor = result.get_stressor("constant_stressor")
            assert stressor is not None
            assert abs(stressor.current_intensity - 0.5) < 0.01
    
    def test_exponential_decay(self):
        """Test exponential decay dynamics."""
        config = MissionConfig(
            mission_id="TEST_003",
            mission_start_date=datetime(2025, 1, 1),
            mission_duration_days=10.0,
            random_seed=42,
            stressor_parameters=[
                StressorParameterSet(
                    stressor_id="decay_stressor",
                    category=StressorCategory.OPERATIONAL,
                    baseline=0.2,
                    max_intensity=1.0,
                    decay_tau=2.0,  # 2-day time constant
                )
            ],
        )
        
        model = StressorModel()
        model.initialize(config)
        
        # Manually set high initial intensity
        state = model.registry.get_state("decay_stressor")
        state.current_intensity = 0.8
        
        # Update and observe decay
        intensities = []
        for day in range(10):
            update_input = UpdateCycleInput(
                current_time=float(day + 1),
                delta_time=1.0,
            )
            result = model.update(update_input)
            stressor = result.get_stressor("decay_stressor")
            intensities.append(stressor.current_intensity)
        
        # Should decay toward baseline
        assert intensities[0] > intensities[5]
        assert intensities[-1] < 0.4  # Near baseline after 10 days
    
    def test_linear_accumulation(self):
        """Test linear accumulation dynamics."""
        config = MissionConfig(
            mission_id="TEST_004",
            mission_start_date=datetime(2025, 1, 1),
            mission_duration_days=10.0,
            random_seed=42,
            stressor_parameters=[
                StressorParameterSet(
                    stressor_id="accumulation_stressor",
                    category=StressorCategory.TEMPORAL,
                    baseline=0.1,
                    max_intensity=0.9,
                    accumulation_rate=0.05,  # 0.05 per day
                )
            ],
        )
        
        model = StressorModel()
        model.initialize(config)
        
        # Update and observe accumulation
        intensities = []
        for day in range(10):
            update_input = UpdateCycleInput(
                current_time=float(day + 1),
                delta_time=1.0,
            )
            result = model.update(update_input)
            stressor = result.get_stressor("accumulation_stressor")
            intensities.append(stressor.current_intensity)
        
        # Should increase linearly
        assert intensities[0] < intensities[5]
        assert intensities[5] < intensities[9]
        
        # Should saturate at max_intensity
        assert intensities[-1] <= 0.9
    
    def test_periodic_cadence(self):
        """Test periodic sinusoidal variation."""
        config = MissionConfig(
            mission_id="TEST_005",
            mission_start_date=datetime(2025, 1, 1),
            mission_duration_days=14.0,
            random_seed=42,
            stressor_parameters=[
                StressorParameterSet(
                    stressor_id="periodic_stressor",
                    category=StressorCategory.OPERATIONAL,
                    baseline=0.5,
                    max_intensity=1.0,
                    cadence_period=7.0,  # Weekly cycle
                    cadence_amplitude=0.2,
                )
            ],
        )
        
        model = StressorModel()
        model.initialize(config)
        
        # Update for two weeks
        intensities = []
        for day in range(14):
            update_input = UpdateCycleInput(
                current_time=float(day + 1),
                delta_time=1.0,
            )
            result = model.update(update_input)
            stressor = result.get_stressor("periodic_stressor")
            intensities.append(stressor.current_intensity)
        
        # Should oscillate
        max_val = max(intensities)
        min_val = min(intensities)
        assert max_val > 0.6  # Above baseline
        assert min_val < 0.4  # Below baseline
    
    def test_scheduled_spike(self):
        """Test scheduled spike events."""
        spike_event = SpikeEvent(
            trigger_time=5.0,
            magnitude=0.4,
            duration=1.0,
        )
        
        config = MissionConfig(
            mission_id="TEST_006",
            mission_start_date=datetime(2025, 1, 1),
            mission_duration_days=10.0,
            random_seed=42,
            stressor_parameters=[
                StressorParameterSet(
                    stressor_id="spike_stressor",
                    category=StressorCategory.OPERATIONAL,
                    baseline=0.2,
                    max_intensity=1.0,
                    spike_schedule=[spike_event],
                )
            ],
        )
        
        model = StressorModel()
        model.initialize(config)
        
        # Update and observe spike
        intensities = []
        for day in range(10):
            update_input = UpdateCycleInput(
                current_time=float(day + 1),
                delta_time=1.0,
            )
            result = model.update(update_input)
            stressor = result.get_stressor("spike_stressor")
            intensities.append(stressor.current_intensity)
        
        # Should spike around day 5
        assert intensities[4] > intensities[2]  # Day 5 higher than day 3
        assert intensities[4] > intensities[7]  # Day 5 higher than day 8
    
    def test_intensity_bounds(self):
        """Test that intensity values remain in [0, 1]."""
        config = MissionConfig(
            mission_id="TEST_007",
            mission_start_date=datetime(2025, 1, 1),
            mission_duration_days=30.0,
            random_seed=42,
            stressor_parameters=[
                StressorParameterSet(
                    stressor_id="bounded_stressor",
                    category=StressorCategory.OPERATIONAL,
                    baseline=0.5,
                    max_intensity=1.0,
                    accumulation_rate=0.1,
                    cadence_amplitude=0.3,
                    cadence_period=5.0,
                )
            ],
        )
        
        model = StressorModel()
        model.initialize(config)
        
        # Update for 30 days with various dynamics
        for day in range(30):
            update_input = UpdateCycleInput(
                current_time=float(day + 1),
                delta_time=1.0,
            )
            result = model.update(update_input)
            
            # Check all stressors are bounded
            for stressor in result.operational_stressors:
                assert 0.0 <= stressor.current_intensity <= 1.0
            for stressor in result.environmental_stressors:
                assert 0.0 <= stressor.current_intensity <= 1.0
            for stressor in result.temporal_stressors:
                assert 0.0 <= stressor.current_intensity <= 1.0
            for stressor in result.monotony_stressors:
                assert 0.0 <= stressor.current_intensity <= 1.0
    
    def test_accumulated_exposure(self):
        """Test accumulated exposure calculation."""
        config = MissionConfig(
            mission_id="TEST_008",
            mission_start_date=datetime(2025, 1, 1),
            mission_duration_days=10.0,
            random_seed=42,
            stressor_parameters=[
                StressorParameterSet(
                    stressor_id="exposure_stressor",
                    category=StressorCategory.ENVIRONMENTAL,
                    baseline=0.5,
                    max_intensity=0.5,
                )
            ],
        )
        
        model = StressorModel()
        model.initialize(config)
        
        # Update for 10 days at constant 0.5 intensity
        for day in range(10):
            update_input = UpdateCycleInput(
                current_time=float(day + 1),
                delta_time=1.0,
            )
            result = model.update(update_input)
        
        # Accumulated exposure should be ~5.0 intensity-days
        stressor = result.get_stressor("exposure_stressor")
        assert 4.5 <= stressor.accumulated_exposure <= 5.5
    
    def test_event_modifiers(self):
        """Test event-triggered intensity modifiers."""
        config = MissionConfig(
            mission_id="TEST_009",
            mission_start_date=datetime(2025, 1, 1),
            mission_duration_days=10.0,
            random_seed=42,
            stressor_parameters=[
                StressorParameterSet(
                    stressor_id="event_stressor",
                    category=StressorCategory.OPERATIONAL,
                    baseline=0.3,
                    max_intensity=1.0,
                )
            ],
            event_schedule=[
                ScheduledEvent(
                    event_id="EVA_001",
                    event_time=5.0,
                    event_type=EventType.EVA,
                    stressor_modifiers=[
                        StressorModifier(
                            stressor_id="event_stressor",
                            intensity_delta=0.4,
                            duration=2.0,
                        )
                    ],
                )
            ],
        )
        
        model = StressorModel()
        model.initialize(config)
        
        # Update to day 5 and trigger event
        for day in range(4):
            update_input = UpdateCycleInput(
                current_time=float(day + 1),
                delta_time=1.0,
            )
            model.update(update_input)
        
        # Trigger event on day 5
        from stressor_model.types import TriggeredEvent
        update_input = UpdateCycleInput(
            current_time=5.0,
            delta_time=1.0,
            triggered_events=[
                TriggeredEvent(
                    event_id="EVA_001",
                    event_type=EventType.EVA,
                    event_time=5.0,
                )
            ],
        )
        result_day5 = model.update(update_input)
        
        # Day 5: should have increased intensity
        stressor_day5 = result_day5.get_stressor("event_stressor")
        
        # Continue to day 6 (modifier still active)
        update_input = UpdateCycleInput(
            current_time=6.0,
            delta_time=1.0,
        )
        result_day6 = model.update(update_input)
        stressor_day6 = result_day6.get_stressor("event_stressor")
        
        # Should still be elevated
        assert stressor_day6.current_intensity > 0.5
        
        # Continue to day 8 (modifier expired)
        update_input = UpdateCycleInput(
            current_time=7.0,
            delta_time=1.0,
        )
        model.update(update_input)
        
        update_input = UpdateCycleInput(
            current_time=8.0,
            delta_time=1.0,
        )
        result_day8 = model.update(update_input)
        stressor_day8 = result_day8.get_stressor("event_stressor")
        
        # Should return to baseline
        assert stressor_day8.current_intensity < stressor_day6.current_intensity
    
    def test_summary_metrics(self):
        """Test summary metric computation."""
        config = MissionConfig(
            mission_id="TEST_010",
            mission_start_date=datetime(2025, 1, 1),
            mission_duration_days=1.0,
            random_seed=42,
            stressor_parameters=[
                StressorParameterSet(
                    stressor_id="op_stressor",
                    category=StressorCategory.OPERATIONAL,
                    baseline=0.6,
                ),
                StressorParameterSet(
                    stressor_id="env_stressor",
                    category=StressorCategory.ENVIRONMENTAL,
                    baseline=0.4,
                ),
                StressorParameterSet(
                    stressor_id="temp_stressor",
                    category=StressorCategory.TEMPORAL,
                    baseline=0.3,
                ),
                StressorParameterSet(
                    stressor_id="mono_stressor",
                    category=StressorCategory.MONOTONY,
                    baseline=0.5,
                ),
            ],
        )
        
        model = StressorModel()
        model.initialize(config)
        
        update_input = UpdateCycleInput(
            current_time=1.0,
            delta_time=1.0,
        )
        result = model.update(update_input)
        
        # Check summary metrics
        assert result.summary_metrics.total_operational_intensity > 0.5
        assert result.summary_metrics.total_environmental_intensity > 0.3
        assert result.summary_metrics.total_temporal_intensity > 0.2
        assert result.summary_metrics.total_monotony_intensity > 0.4
        assert 0.0 <= result.summary_metrics.overall_stressor_load <= 1.0
    
    def test_temporal_consistency(self):
        """Test that mission time must be monotonic."""
        config = MissionConfig(
            mission_id="TEST_011",
            mission_start_date=datetime(2025, 1, 1),
            mission_duration_days=10.0,
            random_seed=42,
            stressor_parameters=[
                StressorParameterSet(
                    stressor_id="test_stressor",
                    category=StressorCategory.OPERATIONAL,
                    baseline=0.5,
                )
            ],
        )
        
        model = StressorModel()
        model.initialize(config)
        
        # Update to day 5
        update_input = UpdateCycleInput(
            current_time=5.0,
            delta_time=5.0,
        )
        model.update(update_input)
        
        # Try to regress time
        with pytest.raises(ValueError):
            update_input = UpdateCycleInput(
                current_time=3.0,
                delta_time=1.0,
            )
            model.update(update_input)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
