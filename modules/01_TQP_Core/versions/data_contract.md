# Data Contract: TQP Core Interfaces

## 1. Overview

This document defines the data interfaces between the TQP Core and external modules. The core operates as a central data hub: modules submit state deltas and the core emits updated agent state.

All data types are specified using language-agnostic pseudocode. Implementers should map these to native types in their target language.

## 2. Core Input Interfaces

### 2.1 Configuration Data (Initialization)

**Provided by:** Simulation controller or configuration file  
**Consumed by:** TQP Core  
**Timing:** Once at simulation initialization

```
SimulationConfig {
  mission_start_datetime: DateTime,
  timestep_duration_minutes: Integer,
  total_timesteps: Integer,
  random_seed: Integer (optional, null for non-deterministic),
  checkpoint_frequency: Integer (timesteps between checkpoints),
  max_memory_buffer_size: Integer,
  module_config: Dictionary<ModuleID, ModuleConfigObject>
}
```

**Constraints:**
- `timestep_duration_minutes` must be in [1, 10080] (1 minute to 1 week)
- `total_timesteps` must be positive
- `checkpoint_frequency` must be positive

### 2.2 Module Registration Data

**Provided by:** External modules during initialization  
**Consumed by:** TQP Core  
**Timing:** Once per module at initialization

```
ModuleRegistration {
  module_id: String (unique identifier),
  module_name: String (human-readable),
  module_version: String,
  process_type: Enum("slow", "fast"),
  execution_priority: Integer (higher executes first),
  update_function: Callable<UpdateFunction>,
  lifecycle_hooks: Dictionary<HookName, Callable> (optional)
}
```

**Constraints:**
- `module_id` must be unique across all registered modules
- `execution_priority` must be in [0, 1000]
- `update_function` must implement the signature defined in section 2.3

### 2.3 Module Update Functions (Each Time-Step)

**Provided by:** External modules  
**Consumed by:** TQP Core during time-step execution  
**Timing:** Every time-step (fast) or on schedule (slow)

**Function Signature:**
```
update_function(current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta
```

**Input: AgentState** (read-only snapshot)
```
AgentState {
  agent_id: String,
  simulation_time: Integer,
  calendar_time: DateTime,
  state_version: Integer,
  internal_vars: Dictionary<String, Scalar>,
  memory_buffer: List<MemoryRecord>,
  belief_state: Dictionary<String, Any>,
  goal_state: List<GoalObject>,
  resource_state: Dictionary<String, Float>,
  module_state: Dictionary<ModuleID, Any>
}
```

**Input: ModuleInputs**
```
ModuleInputs {
  module_id: String,
  timestep_metadata: TimestepMetadata,
  scheduled_events: List<ScheduledEvent> (events for this module this timestep),
  inter_module_messages: List<Message> (messages from other modules)
}

TimestepMetadata {
  is_day_start: Boolean,
  is_week_start: Boolean,
  mission_phase: String (e.g., "pre-mission", "quarter-1", "quarter-2", ...),
  phase_day_number: Integer (day within current phase)
}
```

**Output: StateDelta**
```
StateDelta {
  module_id: String (must match caller),
  internal_var_updates: Dictionary<String, Scalar> (optional),
  memory_additions: List<MemoryRecord> (optional),
  belief_updates: Dictionary<String, Any> (optional),
  goal_updates: Dictionary<String, GoalObject | Null> (optional, null = delete),
  resource_updates: Dictionary<String, Float> (optional, delta values),
  module_state_update: Any (optional, replaces entire module state for this module),
  scheduled_events: List<ScheduledEventRequest> (optional),
  inter_module_messages: List<MessageRequest> (optional)
}
```

**Constraints:**
- All updates are optional (omit or use empty dictionary/list if no change)
- `resource_updates` values are additive deltas (e.g., +2.5 or -1.0)
- `internal_var_updates` values are replacement values (not deltas)

### 2.4 Supporting Data Structures

**MemoryRecord:**
```
MemoryRecord {
  timestamp: Integer (simulation_time),
  event_type: String,
  event_data: Dictionary<String, Any>,
  source_module: String (module_id),
  salience: Float [0.0, 1.0]
}
```

**GoalObject:**
```
GoalObject {
  goal_id: String (unique),
  goal_type: String,
  priority: Float [0.0, 1.0],
  goal_data: Dictionary<String, Any>
}
```

**ScheduledEvent:**
```
ScheduledEvent {
  event_id: String (unique),
  trigger_time: Integer (simulation_time when scheduled),
  event_type: String,
  event_payload: Dictionary<String, Any>,
  source_module: String (module that scheduled it)
}
```

**ScheduledEventRequest:**
```
ScheduledEventRequest {
  trigger_time: Integer (future simulation_time),
  event_type: String,
  event_payload: Dictionary<String, Any>,
  target_module: String (recipient module_id, or "broadcast")
}
```

**Message / MessageRequest:**
```
Message {
  from_module: String (module_id),
  to_module: String (module_id or "broadcast"),
  message_type: String,
  message_payload: Dictionary<String, Any>
}
```

## 3. Core Output Interfaces

### 3.1 Updated Agent State (Each Time-Step)

**Emitted by:** TQP Core after commit phase  
**Consumed by:** Observer modules, logging systems, validation modules  
**Timing:** Every time-step

**Data Structure:** Same as `AgentState` in section 2.3, with updated values.

**Delivery Mechanism:**
- Push: core invokes registered observer callbacks with new state
- Pull: external systems query core for current state via API

### 3.2 Time-Step Completion Notification

**Emitted by:** TQP Core after commit phase  
**Consumed by:** All modules, simulation controller  
**Timing:** Every time-step

```
TimestepCompletionEvent {
  simulation_time: Integer,
  calendar_time: DateTime,
  state_version: Integer,
  elapsed_wall_time_ms: Float (performance metric),
  modules_executed: List<ModuleID>,
  errors_occurred: List<ErrorRecord> (empty if no errors)
}
```

### 3.3 State Checkpoint (Periodic)

**Emitted by:** TQP Core at configured checkpoint intervals  
**Consumed by:** Checkpoint storage system  
**Timing:** Every N time-steps (configured)

```
StateCheckpoint {
  checkpoint_id: String (unique),
  simulation_time: Integer,
  state_version: Integer,
  full_agent_state: AgentState,
  rng_state: RNGState (opaque binary blob),
  metadata: Dictionary<String, Any>
}
```

**Constraints:**
- Checkpoints must be sufficient to restore simulation from that point
- RNG state must be serializable and restorable

### 3.4 Error Reports

**Emitted by:** TQP Core when errors occur  
**Consumed by:** Error handling and logging systems  
**Timing:** As errors occur

```
ErrorRecord {
  error_id: String (unique),
  simulation_time: Integer,
  module_id: String (source of error, or "core"),
  error_type: Enum("module_exception", "validation_failure", "state_corruption", "timeout"),
  error_message: String,
  stack_trace: String (optional),
  state_snapshot: AgentState (pre-error state),
  recovery_action: Enum("rollback", "halt", "skip_module", "retry")
}
```

## 4. Data Exchange Timing and Frequency

### 4.1 Update Frequencies by Module Type

**Fast Modules:**
- Invoked every time-step
- Expected to return deltas in < 100ms (performance guideline)

**Slow Modules:**
- Invoked on schedule (e.g., daily: when `is_day_start == true`)
- Expected to return deltas in < 1000ms (performance guideline)

### 4.2 Memory Buffer Management

- Core appends new memory records from all modules after each time-step
- If buffer exceeds `max_memory_buffer_size`, oldest records are evicted (FIFO)
- Modules should not assume persistent access to old memory records beyond the configured buffer size

### 4.3 Inter-Module Message Delivery

- Messages sent during time-step T are delivered at time-step T (same-step delivery)
- Broadcast messages are delivered to all registered modules except sender
- No guaranteed ordering for messages from different modules

## 5. Validity Constraints and Invariants

### 5.1 State Variable Constraints

The core enforces the following constraints after each commit:
- `simulation_time` is monotonically increasing
- `state_version` is monotonically increasing
- `calendar_time` is consistent with `simulation_time` and `timestep_duration`
- All values in `resource_state` are non-negative
- All `priority` values in `goal_state` are in [0.0, 1.0]
- All `salience` values in `memory_buffer` are in [0.0, 1.0]

Modules must not submit deltas that would violate these constraints.

### 5.2 Module Isolation Invariant

A module may only update:
- `internal_vars` entries it owns (by convention, prefixed with module_id)
- Its own entry in `module_state[module_id]`
- Shared resources (e.g., `resource_state`) via additive deltas

A module must NOT:
- Directly modify another module's `module_state` container
- Delete or modify existing memory records (only add new ones)

The core does not enforce ownership by variable name but relies on module discipline.

### 5.3 Data Type Contracts

- `Scalar` types: Integer, Float, Boolean, String
- `Dictionary` keys are always String
- `Any` type: modules and core agree on serialization format (e.g., JSON-compatible structures)

## 6. Extension Points for Future Modules

### 6.1 Custom State Containers

Future modules may request custom top-level state containers by:
1. Declaring the container name and schema during registration
2. Providing initialization values
3. Updating via `module_state_update` in deltas

Example: Module 04 (Physiology) might request a `physio_state` container with nested dictionaries for heart rate, cortisol levels, etc.

### 6.2 Custom Lifecycle Hooks

Future modules may implement additional hooks:
- `on_phase_transition(old_phase, new_phase)`
- `on_anomaly_detected(anomaly_data)`
- `on_intervention_applied(intervention_data)`

The core will invoke these hooks if implemented by the module.

### 6.3 Query APIs

Modules may request structured queries against agent state:
- Memory queries: `query_memory(filters, sort_by, limit)`
- Goal queries: `query_goals(type, priority_threshold)`
- Belief queries: `query_beliefs(pattern)`

These query functions are provided by the core and return filtered subsets of state.

## 7. Implementation Notes

### 7.1 Serialization

All data structures must be serializable to:
- JSON (for configuration files and checkpoints)
- Binary formats (for performance-critical paths)

Modules should avoid non-serializable objects (e.g., function pointers, file handles) in state containers.

### 7.2 Versioning

The data contract is versioned. Future changes will:
- Add optional fields (backward compatible)
- Deprecate fields with warnings (forward compatible)
- Introduce breaking changes only with major version increments

Modules should declare the data contract version they implement.

### 7.3 Testing

Modules should provide mock implementations of `update_function` for core testing:
- Null update: returns empty delta
- Deterministic update: returns fixed delta independent of state
- Stochastic update: returns random delta using core RNG

The core will use these mocks for regression testing.
