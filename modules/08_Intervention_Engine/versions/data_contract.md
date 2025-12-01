# Intervention Engine: Data Contract

## 1. Introduction

This document defines the complete data contract for the Intervention Engine. It specifies:
- All inputs the module receives
- All outputs the module produces
- Timing and granularity of data exchange
- Data shape and constraints in pseudocode form
- Validity rules for all data structures

No semantic interpretation of signals is included. All definitions are structural.

## 2. Input Data Contract

### 2.1 Primary Update Interface

**Function Signature**:
```
InterventionEngine.update(
  time_step: integer,
  input_signals: map<string, float>,
  events: list<Event>
) -> list<InterventionEffect>
```

**Parameters**:

#### `time_step: integer`
- **Description**: Current simulation time-step index
- **Constraints**:
  - Must be non-negative
  - Must be monotonically increasing across consecutive calls
  - Units: discrete time-step (interpretation external to this module)
- **Source**: TQP Core
- **Frequency**: Once per simulation time-step

#### `input_signals: map<string, float>`
- **Description**: Collection of abstract signals from other modules
- **Structure**:
  ```
  {
    "signal_id_1": value_1,
    "signal_id_2": value_2,
    ...
  }
  ```
- **Constraints**:
  - Keys are string identifiers (no semantic meaning enforced)
  - Values are finite floating-point numbers (-∞ < value < +∞)
  - Missing signals are treated as absent (not zero)
  - Duplicate keys are not permitted
- **Source**: TQP Core (aggregated from all modules)
- **Frequency**: Once per simulation time-step

#### `events: list<Event>`
- **Description**: Discrete events that occurred in the current time-step
- **Structure**:
  ```
  Event {
    event_id: string,
    timestamp: integer,
    attributes: map<string, any>
  }
  ```
- **Constraints**:
  - `event_id`: Non-empty string identifier
  - `timestamp`: Must equal `time_step` parameter
  - `attributes`: Optional key-value pairs (structure external to this module)
- **Source**: TQP Core or other modules
- **Frequency**: Zero or more events per time-step

### 2.2 Configuration Interface

**Function Signature**:
```
InterventionEngine.register_intervention(
  config: InterventionConfig
) -> intervention_id: string
```

**Parameters**:

#### `config: InterventionConfig`
- **Description**: Complete specification of an intervention instance
- **Structure**:
  ```
  InterventionConfig {
    id: string,
    category: string,
    type_tag: string,
    activation_conditions: ActivationConditions,
    schedule: Schedule,
    duration: Duration,
    metadata: map<string, any>
  }
  ```
- **Constraints**:
  - `id`: Unique within simulation, non-empty string
  - `category`: One of {scheduled, reactive, compound, recurrent, one-shot}
  - `type_tag`: Non-empty string (no constraints on content)
  - `activation_conditions`: See Section 2.3
  - `schedule`: See Section 2.4
  - `duration`: See Section 2.5
  - `metadata`: Optional, extensible map
- **Source**: External configuration system or TQP Core
- **Frequency**: During simulation initialization or dynamically during runtime

### 2.3 Activation Conditions Structure

```
ActivationConditions {
  condition_type: enum,           // {threshold, temporal, event, compound}
  threshold_condition: ThresholdCondition (optional),
  temporal_condition: TemporalCondition (optional),
  event_condition: EventCondition (optional),
  compound_condition: CompoundCondition (optional)
}

ThresholdCondition {
  signal_id: string,
  operator: enum,                 // {GT, LT, EQ, NEQ, GTE, LTE}
  threshold_value: float,
  duration_required: integer,     // >= 0
  hysteresis_buffer: float        // >= 0 (optional)
}

TemporalCondition {
  start_time: integer,            // >= 0
  end_time: integer (optional),   // > start_time if present
  recurrence_pattern: RecurrencePattern (optional)
}

RecurrencePattern {
  interval: integer,              // > 0
  count: integer,                 // > 0 or null (infinite)
  offset: integer                 // >= 0
}

EventCondition {
  event_id: string,
  event_filter: map<string, any> (optional),
  cooldown_period: integer        // >= 0
}

CompoundCondition {
  conditions: list<ActivationConditions>,  // length >= 2
  logic_operator: enum,           // {AND, OR, XOR}
  evaluation_order: list<integer> (optional)  // indices into conditions list
}
```

**Constraints**:
- Exactly one of the condition type fields must be populated based on `condition_type`
- All time values must be non-negative integers
- All duration values must be positive integers
- Threshold values must be finite floats
- Compound conditions may nest but must not create circular references

### 2.4 Schedule Structure

```
Schedule {
  cadence_type: enum,             // {continuous, intermittent, pulsed}
  active_duration: integer,       // > 0
  inactive_duration: integer,     // >= 0
  phase_alignment: integer        // >= 0 (optional)
}
```

**Constraints**:
- `active_duration`: Number of time-steps intervention remains active
- `inactive_duration`: For recurrent interventions, time-steps before re-arming (ignored for one-shot)
- `phase_alignment`: If present, intervention activates only when `(time_step % phase_alignment) == 0`

### 2.5 Duration Structure

```
Duration {
  max_duration: integer,          // > 0 or null (infinite)
  decay_type: enum,               // {none, linear, exponential} (optional)
  decay_rate: float               // > 0 (required if decay_type != none)
}
```

**Constraints**:
- `max_duration`: Maximum time-steps intervention can remain active (null = no limit)
- `decay_type`: Structural decay pattern (does not interpret meaning)
- `decay_rate`: Rate parameter for decay function (units external to this module)

## 3. Output Data Contract

### 3.1 Primary Output: Intervention Effects

**Return Type**:
```
list<InterventionEffect>

InterventionEffect {
  intervention_id: string,
  effect_type: enum,              // {ACTIVATION, DEACTIVATION, STATE_CHANGE}
  timestamp: integer,
  signal_values: map<string, float>
}
```

**Structure**:
- `intervention_id`: Unique identifier of the intervention that emitted this effect
- `effect_type`: Type of state change that occurred
- `timestamp`: Time-step index when effect occurred (matches input `time_step`)
- `signal_values`: Abstract signals emitted by this intervention

**Constraints**:
- Zero or more effects may be returned per `update()` call
- Effects are ordered by intervention priority (high to low)
- Signal values must be finite floats
- Signal keys must be non-empty strings

**Consumers**: TQP Core (broadcasts to all modules)

**Frequency**: Once per simulation time-step (empty list if no effects)

### 3.2 Query Outputs

#### Get Intervention State

**Function Signature**:
```
InterventionEngine.get_state(
  intervention_id: string
) -> InterventionState
```

**Return Type**:
```
InterventionState {
  id: string,
  current_state: enum,            // {UNINITIALIZED, ARMED, ACTIVE, SUSPENDED, EXPIRED, CANCELLED}
  time_activated: integer,        // null if never activated
  time_last_transition: integer,
  active_duration_elapsed: integer  // time-steps in ACTIVE state
}
```

**Constraints**:
- Returns null if `intervention_id` does not exist
- All time values are time-step indices

#### List Active Interventions

**Function Signature**:
```
InterventionEngine.list_active_interventions() -> list<string>
```

**Return Type**:
- List of intervention IDs currently in ACTIVE state
- Ordered by activation time (earliest first)
- Empty list if no interventions are active

#### Get Intervention History

**Function Signature**:
```
InterventionEngine.get_intervention_history(
  intervention_id: string,
  start_time: integer,
  end_time: integer
) -> list<StateTransitionRecord>
```

**Return Type**:
```
StateTransitionRecord {
  timestamp: integer,
  from_state: enum,
  to_state: enum,
  trigger: string                 // Description of activation trigger (optional)
}
```

**Constraints**:
- Returns empty list if `intervention_id` does not exist or no transitions in time range
- `start_time` and `end_time` are inclusive bounds
- Records are ordered chronologically

## 4. Timing and Granularity

### 4.1 Temporal Resolution

- **Base unit**: Simulation time-step (duration unspecified, external to module)
- **Update frequency**: Once per time-step
- **Minimum activation duration**: 1 time-step
- **Time-step alignment**: All state transitions occur at time-step boundaries (no intra-step transitions)

### 4.2 Update Cycle Timing

```
For each time-step t:
  1. TQP Core collects signals from all modules
  2. TQP Core invokes InterventionEngine.update(t, signals, events)
  3. Intervention Engine evaluates all conditions
  4. Intervention Engine executes state transitions
  5. Intervention Engine returns list<InterventionEffect>
  6. TQP Core broadcasts effects to all modules
  7. Cycle repeats at t+1
```

### 4.3 Synchronization Requirements

- **Input signals**: Must reflect state at the END of time-step t-1 (beginning of t)
- **Output effects**: Represent state changes occurring DURING time-step t
- **Downstream consumption**: Effects are consumed at the BEGINNING of time-step t+1

This ensures consistent causal ordering across all modules.

## 5. Data Validity Rules

### 5.1 Input Validation

**Rule I1**: `time_step` must be non-negative and monotonically increasing
- **Violation handling**: Reject update, log error

**Rule I2**: `input_signals` keys must be non-empty strings
- **Violation handling**: Ignore invalid keys, log warning

**Rule I3**: `input_signals` values must be finite floats
- **Violation handling**: Treat as missing signal, log warning

**Rule I4**: `events` timestamps must match `time_step`
- **Violation handling**: Ignore event, log warning

**Rule I5**: Intervention configurations must reference registered signals
- **Violation handling**: Reject configuration, return error

### 5.2 Output Validation

**Rule O1**: All emitted `signal_values` must have finite float values
- **Enforcement**: Engine validates before returning effects

**Rule O2**: `timestamp` in effects must match input `time_step`
- **Enforcement**: Engine sets programmatically

**Rule O3**: `intervention_id` in effects must correspond to existing intervention
- **Enforcement**: Engine validates before emitting

### 5.3 State Consistency Rules

**Rule S1**: Only one intervention may have a given `id`
- **Enforcement**: Registration rejects duplicate IDs

**Rule S2**: State transitions must follow legal transition matrix (see spec.md)
- **Enforcement**: Engine rejects illegal transitions, reverts to last valid state

**Rule S3**: Active interventions must have `time_activated` set
- **Enforcement**: Engine sets programmatically during ARMED → ACTIVE transition

## 6. Extensibility and Versioning

### 6.1 Schema Version

All data structures include implicit schema version. Current version: `1.0.0`

### 6.2 Forward Compatibility

New fields may be added to structures with the following constraints:
- New fields must be optional or have default values
- Existing fields must not change type or semantics
- Parsers must ignore unknown fields (permissive parsing)

### 6.3 Backward Compatibility

Implementations must support loading configurations from:
- Current schema version (1.0.0)
- Future schema versions (with unknown field tolerance)

### 6.4 Deprecated Fields

If a field is deprecated in a future version:
- It must remain parseable (no parse errors)
- Its behavior may become a no-op
- A migration utility must be provided

## 7. Example Data Flows

### 7.1 Threshold-Based Activation Example

**Input (time-step 100)**:
```
time_step: 100
input_signals: {
  "signal_alpha": 0.75,
  "signal_beta": 1.2
}
events: []
```

**Intervention Configuration**:
```
{
  id: "intervention_001",
  category: "reactive",
  activation_conditions: {
    condition_type: "threshold",
    threshold_condition: {
      signal_id: "signal_alpha",
      operator: "GT",
      threshold_value: 0.7,
      duration_required: 3
    }
  },
  schedule: {
    cadence_type: "continuous",
    active_duration: 10
  }
}
```

**Output (assuming condition satisfied for 3 consecutive steps)**:
```
[
  {
    intervention_id: "intervention_001",
    effect_type: "ACTIVATION",
    timestamp: 100,
    signal_values: {
      "intervention_001_active": 1.0
    }
  }
]
```

### 7.2 Temporal Activation Example

**Input (time-step 50)**:
```
time_step: 50
input_signals: {}
events: []
```

**Intervention Configuration**:
```
{
  id: "intervention_002",
  category: "scheduled",
  activation_conditions: {
    condition_type: "temporal",
    temporal_condition: {
      start_time: 50,
      recurrence_pattern: {
        interval: 20,
        count: 5,
        offset: 0
      }
    }
  },
  schedule: {
    cadence_type: "pulsed",
    active_duration: 1
  }
}
```

**Output (time-step 50)**:
```
[
  {
    intervention_id: "intervention_002",
    effect_type: "ACTIVATION",
    timestamp: 50,
    signal_values: {
      "intervention_002_pulse": 1.0
    }
  }
]
```

**Subsequent Outputs**:
- Time-step 70, 90, 110, 130: Same activation pattern

### 7.3 Event-Based Activation Example

**Input (time-step 200)**:
```
time_step: 200
input_signals: {}
events: [
  {
    event_id: "event_gamma",
    timestamp: 200,
    attributes: {
      "severity": "high"
    }
  }
]
```

**Intervention Configuration**:
```
{
  id: "intervention_003",
  category: "reactive",
  activation_conditions: {
    condition_type: "event",
    event_condition: {
      event_id: "event_gamma",
      event_filter: {
        "severity": "high"
      },
      cooldown_period: 10
    }
  },
  schedule: {
    cadence_type: "continuous",
    active_duration: 5
  }
}
```

**Output (time-step 200)**:
```
[
  {
    intervention_id: "intervention_003",
    effect_type: "ACTIVATION",
    timestamp: 200,
    signal_values: {
      "intervention_003_active": 1.0
    }
  }
]
```

## 8. Summary

This data contract fully specifies the structural interface of the Intervention Engine. All inputs, outputs, timing constraints, and validity rules are defined in abstract, domain-agnostic terms. Implementations adhering to this contract will be interoperable and verifiable.

**Key Principles**:
- All signals are abstract (no semantic interpretation)
- All time values are discrete time-step indices
- All state transitions are deterministic and reproducible
- All data structures support forward and backward compatibility

This contract is sufficient for independent implementation and integration testing.
