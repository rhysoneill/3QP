# Intervention Engine

## Overview

The Intervention Engine is a pure structural subsystem for managing intervention lifecycles within the 3QP simulation framework. It provides abstract, domain-agnostic mechanisms for scheduling, triggering, and managing interventions without semantic interpretation.

## Key Features

- **Multiple Activation Modes**: Threshold-based, time-based, event-based, and compound conditions
- **Flexible Scheduling**: Continuous, intermittent, and pulsed cadences
- **State Machine Management**: Well-defined lifecycle states with legal transitions
- **Priority-Based Ordering**: Deterministic effect emission ordering
- **Recurrent Interventions**: Support for repeating intervention patterns
- **Extensible Architecture**: Plugin-based condition evaluation system

## Installation

```bash
cd modules/08_Intervention_Engine
pip install -e .
```

## Quick Start

```python
from intervention_engine import (
    InterventionEngine,
    InterventionConfig,
    ThresholdCondition,
    Schedule,
    Duration,
    ConditionOperator,
    CadenceType
)

# Create engine
engine = InterventionEngine()

# Configure a threshold-based intervention
config = InterventionConfig(
    id="example_intervention",
    category="reactive",
    type_tag="threshold_example",
    activation_conditions=ThresholdCondition(
        signal_id="signal_alpha",
        operator=ConditionOperator.GT,
        threshold_value=0.7
    ),
    schedule=Schedule(
        cadence_type=CadenceType.CONTINUOUS,
        active_duration=5
    ),
    duration=Duration()
)

# Register intervention
engine.register_intervention(config)

# Update with signals
effects = engine.update(
    time_step=1,
    input_signals={"signal_alpha": 0.8}
)

# Check intervention state
state = engine.get_state("example_intervention")
print(f"State: {state.current_state}")
```

## Architecture

### Core Components

1. **Types** (`types.py`): Data structures for interventions, conditions, and effects
2. **Conditions** (`conditions.py`): Condition evaluation logic
3. **Registry** (`registry.py`): Intervention storage and state machine management
4. **Engine** (`engine.py`): Main update cycle and coordination

### Intervention Lifecycle States

- `UNINITIALIZED`: Not yet configured
- `ARMED`: Monitoring for activation conditions
- `ACTIVE`: Currently executing
- `SUSPENDED`: Temporarily paused
- `EXPIRED`: Lifecycle complete
- `CANCELLED`: Manually terminated

### Condition Types

1. **ThresholdCondition**: Activate when signal crosses threshold
2. **TemporalCondition**: Activate at specific time-steps
3. **EventCondition**: Activate in response to discrete events
4. **CompoundCondition**: Combine multiple conditions with AND/OR/XOR logic

## Integration with 3QP

The Intervention Engine integrates with the TQP Core module through:

- **Input**: Receives abstract signals and events from TQP Core
- **Output**: Emits intervention effects as signals
- **No Direct Dependencies**: Only depends on TQP Core, never on domain modules

### Example Integration

```python
# TQP Core collects signals from all modules
signals = {
    "signal_from_stressor": 0.85,
    "signal_from_physiology": 0.62
}

# TQP Core invokes intervention engine
effects = intervention_engine.update(
    time_step=current_time,
    input_signals=signals,
    events=current_events
)

# TQP Core broadcasts effects to all modules
for effect in effects:
    event_bus.publish(effect)
```

## Testing

Run the test suite:

```bash
cd modules/08_Intervention_Engine
python -m pytest tests/
```

Run the demo:

```bash
python demo.py
```

## Design Principles

1. **Structural Abstraction**: No domain knowledge or semantic interpretation
2. **Signal Anonymization**: All signals are abstract identifiers
3. **Data-Only Interfaces**: No function calls between modules
4. **Deterministic Behavior**: Reproducible across runs with same inputs
5. **Fail-Safe Defaults**: Missing signals treated as condition not met

## Configuration Examples

### Scheduled Intervention

```python
config = InterventionConfig(
    id="daily_briefing",
    category="recurrent",
    type_tag="scheduled",
    activation_conditions=TemporalCondition(
        start_time=0,
        recurrence_pattern=RecurrencePattern(
            interval=24,  # Daily
            count=None    # Infinite
        )
    ),
    schedule=Schedule(
        cadence_type=CadenceType.PULSED,
        active_duration=1
    ),
    duration=Duration()
)
```

### Reactive Intervention

```python
config = InterventionConfig(
    id="stress_response",
    category="reactive",
    type_tag="threshold",
    activation_conditions=ThresholdCondition(
        signal_id="stress_indicator",
        operator=ConditionOperator.GT,
        threshold_value=0.8,
        duration_required=3  # Must persist for 3 steps
    ),
    schedule=Schedule(
        cadence_type=CadenceType.CONTINUOUS,
        active_duration=10
    ),
    duration=Duration(max_duration=20)
)
```

### Compound Intervention

```python
config = InterventionConfig(
    id="multi_condition",
    category="compound",
    type_tag="complex",
    activation_conditions=CompoundCondition(
        conditions=[
            ThresholdCondition(
                signal_id="metric_a",
                operator=ConditionOperator.GT,
                threshold_value=0.7
            ),
            EventCondition(
                event_id="trigger_event"
            )
        ],
        logic_operator=LogicOperator.AND
    ),
    schedule=Schedule(
        cadence_type=CadenceType.CONTINUOUS,
        active_duration=5
    ),
    duration=Duration()
)
```

## API Reference

### InterventionEngine

**Main Methods:**

- `update(time_step, input_signals, events)`: Execute one time-step
- `register_intervention(config)`: Register new intervention
- `remove_intervention(intervention_id)`: Remove intervention
- `get_state(intervention_id)`: Get current state
- `list_active_interventions()`: List all active interventions
- `get_intervention_history(intervention_id, start_time, end_time)`: Get state history

### InterventionConfig

**Required Fields:**

- `id`: Unique identifier
- `category`: Intervention category (scheduled, reactive, compound, recurrent, one-shot)
- `type_tag`: Type descriptor for filtering
- `activation_conditions`: Condition object
- `schedule`: Schedule object
- `duration`: Duration object

**Optional Fields:**

- `metadata`: Extensible key-value pairs
- `priority`: Activation ordering (higher = processed first)

## Performance Characteristics

- **Update Complexity**: O(N × C) where N = interventions, C = conditions
- **Memory Footprint**: ~1 KB per intervention
- **Scalability Target**: ≥1000 concurrent interventions, <1ms update latency

## Extensibility

The engine supports:

- **Custom Condition Types**: Implement condition interface and register
- **Extended Metadata**: Arbitrary key-value pairs in configuration
- **Plugin Architecture**: Add new evaluators without modifying core

## Dependencies

- **Upstream**: TQP Core (Module 01)
- **Downstream**: None
- **External**: Python 3.8+ (no external packages required)

## License

Part of the 3QP simulation framework.

## Contact

For questions or issues, refer to the main 3QP repository.
