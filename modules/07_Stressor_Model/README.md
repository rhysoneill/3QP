# Module 07: Stressor Model

## Overview

The **Stressor Model** module generates time-varying stressor signals representing mission-relevant demands in isolated, confined environments such as lunar habitats. It is part of the 3QP behavioral twin architecture and provides external demand signals without interpreting psychological states or behavioral responses.

## Key Features

- **Four Stressor Categories**: Operational, Environmental, Temporal, and Monotony stressors
- **Multiple Temporal Dynamics**: Constant baselines, exponential decay, linear accumulation, periodic cadence
- **Scheduled Spikes**: Planned events (EVAs, maintenance) with Gaussian pulse dynamics
- **Event-Driven Modifiers**: Mission events can temporarily modify stressor intensities
- **Deterministic & Reproducible**: Seeded random number generation ensures reproducibility
- **Bounded Intensities**: All values guaranteed to remain in [0, 1]

## Installation

From the module directory:

```bash
pip install -e .
```

For development with testing support:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from datetime import datetime
from stressor_model import (
    StressorModel,
    MissionConfig,
    StressorParameterSet,
    UpdateCycleInput,
    StressorCategory,
)

# Create mission configuration
config = MissionConfig(
    mission_id="LUNAR_HABITAT_001",
    mission_start_date=datetime(2026, 1, 1),
    mission_duration_days=180.0,
    random_seed=42,
    stressor_parameters=[
        StressorParameterSet(
            stressor_id="task_density",
            category=StressorCategory.OPERATIONAL,
            baseline=0.4,
            max_intensity=0.9,
            cadence_period=7.0,  # Weekly variation
            cadence_amplitude=0.15,
        ),
        StressorParameterSet(
            stressor_id="confinement_index",
            category=StressorCategory.ENVIRONMENTAL,
            baseline=0.6,
            max_intensity=0.6,
        ),
    ],
)

# Initialize model
model = StressorModel()
model.initialize(config)

# Update for each simulation timestep
for day in range(180):
    update_input = UpdateCycleInput(
        current_time=float(day + 1),
        delta_time=1.0,
    )
    result = model.update(update_input)
    
    # Access stressor values
    task_density = result.get_stressor("task_density")
    print(f"Day {day + 1}: Task Density = {task_density.current_intensity:.3f}")
```

## Stressor Categories

### Operational Stressors
Time-bound demands from mission tasks and schedules:
- Task Density
- Schedule Compression
- Procedure Complexity
- Resource Constraints

### Environmental Stressors
Persistent or episodic habitat conditions:
- Confinement Index
- Ambient Noise Level
- Thermal Variance
- Illumination Irregularity

### Temporal Stressors
Derived from mission time and phase structure:
- Mission Duration Accumulator
- Phase Transition Proximity
- Earth Distance Effect
- Return Window Approach

### Monotony Stressors
Chronic signals from repetitive patterns:
- Routine Repetition Index
- Sensory Monotony
- Social Pattern Stagnation
- Task Variety Deficit

## Temporal Dynamics

### Constant Baseline
```python
StressorParameterSet(
    stressor_id="confinement",
    baseline=0.6,
    max_intensity=0.6,
)
```

### Exponential Decay
```python
StressorParameterSet(
    stressor_id="stress_recovery",
    baseline=0.2,
    decay_tau=2.0,  # 2-day time constant
)
```

### Linear Accumulation
```python
StressorParameterSet(
    stressor_id="mission_duration",
    baseline=0.1,
    accumulation_rate=0.01,  # per day
)
```

### Periodic Cadence
```python
StressorParameterSet(
    stressor_id="weekly_tasks",
    baseline=0.5,
    cadence_period=7.0,  # Weekly cycle
    cadence_amplitude=0.2,
)
```

### Scheduled Spikes
```python
from stressor_model import SpikeEvent

StressorParameterSet(
    stressor_id="eva_workload",
    baseline=0.2,
    spike_schedule=[
        SpikeEvent(trigger_time=10.0, magnitude=0.6, duration=0.5),
        SpikeEvent(trigger_time=30.0, magnitude=0.7, duration=0.5),
    ],
)
```

## Event-Driven Modifiers

Mission events can temporarily modify stressor intensities:

```python
from stressor_model import ScheduledEvent, EventType, StressorModifier

config = MissionConfig(
    # ... other config ...
    event_schedule=[
        ScheduledEvent(
            event_id="EVA_001",
            event_time=15.0,
            event_type=EventType.EVA,
            stressor_modifiers=[
                StressorModifier(
                    stressor_id="operational_load",
                    intensity_delta=0.4,
                    duration=0.5,  # Half-day event
                )
            ],
        )
    ],
)
```

Trigger the event during simulation:

```python
from stressor_model.types import TriggeredEvent

update_input = UpdateCycleInput(
    current_time=15.0,
    delta_time=1.0,
    triggered_events=[
        TriggeredEvent(
            event_id="EVA_001",
            event_type=EventType.EVA,
            event_time=15.0,
        )
    ],
)
```

## Output Structure

The `StressorIntensityVector` contains:

```python
result = model.update(update_input)

# Access by category
for stressor in result.operational_stressors:
    print(f"{stressor.stressor_id}: {stressor.current_intensity}")

# Access by ID
task_density = result.get_stressor("task_density")
print(f"Intensity: {task_density.current_intensity}")
print(f"Accumulated Exposure: {task_density.accumulated_exposure} intensity-days")
print(f"Spike Count: {task_density.spike_count}")

# Summary metrics
print(f"Overall Load: {result.summary_metrics.overall_stressor_load}")
print(f"Operational Total: {result.summary_metrics.total_operational_intensity}")
```

## Testing

Run the test suite:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest tests/ --cov=stressor_model --cov-report=html
```

## Demo

Run the demonstration script:

```bash
python demo.py
```

This will:
- Simulate a 90-day lunar habitat mission
- Display stressor trajectories for all categories
- Generate visualization plots (if matplotlib is available)
- Demonstrate event-triggered modifiers

## Architecture Integration

### TQP Core Integration

The Stressor Model integrates with the TQP Core orchestration layer:

1. **Initialization**: TQP Core calls `model.initialize(config)`
2. **Update Cycle**: TQP Core calls `model.update(update_input)` each timestep
3. **Output Publishing**: Stressor intensities made available to downstream modules

### Downstream Module Consumers

- **Module 04 (Slow/Fast Physiology)**: Uses stressor signals as inputs to physiological adaptation
- **Module 06 (BDI Cycle)**: Incorporates stressor context into cognitive deliberation
- **Module 09 (Logging System)**: Records stressor trajectories for analysis

### Data Flow Constraints

- **One-Way Data Flow**: Stressor Model → Downstream Modules (no feedback)
- **No Psychological Interpretation**: Stressors are neutral computational signals
- **No Circular Dependencies**: Stressor intensities determined solely from mission conditions

## Design Principles

### Architectural Purity

1. **No Psychological Constructs**: Stressors represent objective mission conditions, not subjective experiences
2. **Signal-Based Representation**: Stressors are time-indexed signals analogous to engineering control inputs
3. **Mechanistic Abstraction**: Uses standard differential equations (accumulation, decay) without psychological models

### Modularity

- **Independent Stressor Types**: Each stressor evolves independently
- **Pluggable Intensity Functions**: Easy to add custom temporal dynamics
- **Clean Interfaces**: All interactions via standardized data contracts

### Reproducibility

- **Seeded Randomness**: Identical seeds produce identical outputs
- **Deterministic Baseline**: Most dynamics are deterministic
- **Version Control**: Configuration files and schemas are versioned

## Performance

- **Efficient Updates**: O(N) complexity where N = number of stressors
- **Memory Scaling**: Linear with number of active stressors
- **Typical Performance**: <1% of total simulation loop time for 50 stressors

## Extensibility

### Adding New Stressor Types

1. Define stressor parameters in configuration
2. Specify category and temporal dynamics
3. Register with TQP Core initialization
4. No code changes required for standard dynamics

### Custom Intensity Functions

For non-standard dynamics, subclass `IntensityFunction`:

```python
from stressor_model.intensity_functions import IntensityFunction, StressorState

class CustomDynamics(IntensityFunction):
    def compute(self, state: StressorState, current_time: float, delta_time: float) -> float:
        # Implement custom logic
        return new_intensity
```

## References

- **spec.md**: Complete engineering specification
- **theory_basis.md**: Theoretical foundations and rationale
- **data_contract.md**: Input/output data structures and contracts
- **implementation_notes.md**: Practical implementation guidance

## Version

**Current Version**: 1.0.0  
**Status**: Baseline  
**Date**: December 2025

## License

Part of the 3QP behavioral twin architecture.

## Contact

3QP Development Team
