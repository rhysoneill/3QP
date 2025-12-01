# Technical Specification: TQP Core Internal Engine

## 1. Overview

The TQP Core is a discrete-time simulation engine responsible for advancing agent internal state through sequential time-steps. It maintains a single authoritative representation of agent state, coordinates update contributions from external modules, and enforces temporal consistency across slow and fast processes.

The engine operates as a deterministic state machine with optional stochastic components. All state transitions are traceable, reproducible, and auditable.

## 2. Agent Internal State Model

### 2.1 State Representation

Agent state is represented as a structured container with the following components:

**Core State Variables:**
- `agent_id`: unique identifier (string)
- `simulation_time`: current time-step counter (integer)
- `calendar_time`: mission-relative date and time (datetime)
- `state_version`: monotonic version counter for state snapshots (integer)

**State Variable Collections:**
- `internal_vars`: dictionary of scalar state variables (float, int, bool)
- `memory_buffer`: time-indexed event and experience storage (list of records)
- `belief_state`: propositional belief representation (dictionary)
- `goal_state`: active goals and priorities (list of goal objects)
- `resource_state`: cognitive and physical resource levels (dictionary)

**Module-Specific State Containers:**
Each external module (02–12) may register a dedicated state container:
- `module_state[module_id]`: arbitrary structured data owned by module

The core does not interpret module-specific containers. It only ensures they are preserved across time-steps and made available during module update calls.

### 2.2 State Immutability and Versioning

- Each committed state receives a unique `state_version` identifier
- State is immutable once committed; updates produce new state versions
- Previous state versions may be retained for rollback or replay

### 2.3 Memory Structures

The `memory_buffer` is a time-ordered list of memory records with schema:
```
{
  "timestamp": simulation_time,
  "event_type": string,
  "event_data": arbitrary structured data,
  "source_module": module_id,
  "salience": float [0.0, 1.0]
}
```

Memory records are never modified after insertion. External modules may query memory but cannot delete or alter existing records.

## 3. Core Update Cycle

### 3.1 Time-Step Execution Loop

Each time-step executes the following sequence:

1. **Pre-Update Phase:**
   - Increment `simulation_time`
   - Update `calendar_time` based on configured time-step duration
   - Snapshot current state for rollback

2. **Slow-Process Update Phase:**
   - If conditions met (e.g., daily or weekly boundary), invoke slow-process modules
   - Collect state deltas from slow modules
   - Apply deltas to staging state

3. **Fast-Process Update Phase:**
   - Invoke fast-process modules (may execute multiple times per time-step)
   - Collect state deltas from fast modules
   - Apply deltas to staging state

4. **Reconciliation Phase:**
   - Resolve conflicts between slow and fast updates (precedence rules defined below)
   - Validate state integrity constraints
   - Finalize staging state

5. **Commit Phase:**
   - Increment `state_version`
   - Commit staging state as current state
   - Emit state update notifications to observer modules

6. **Post-Update Phase:**
   - Log state transition if debugging enabled
   - Check for simulation termination conditions

### 3.2 Update Delta Format

Modules return state deltas as structured dictionaries:
```
{
  "module_id": string,
  "internal_var_updates": {variable_name: new_value},
  "memory_additions": [list of memory records],
  "belief_updates": {belief_id: new_belief_value},
  "goal_updates": {goal_id: goal_object or null for deletion},
  "resource_updates": {resource_name: delta_value},
  "module_state_update": arbitrary structured data
}
```

Modules may provide partial updates. Omitted fields are unchanged.

### 3.3 Module Update Invocation

Registered modules provide an update function with signature:
```
update(current_state, module_inputs) -> state_delta
```

Where:
- `current_state`: read-only view of complete agent state
- `module_inputs`: time-step-specific input data for the module
- `state_delta`: structured delta as defined above

The core invokes modules in a predefined execution order specified in the simulation configuration.

## 4. Time-Step Semantics

### 4.1 Configurable Time Granularity

The simulation supports configurable time-step durations:
- **Fine-grained:** 1-minute to 1-hour steps (intra-day resolution)
- **Coarse-grained:** daily or weekly steps

Time-step duration is fixed at simulation initialization.

### 4.2 Calendar Alignment

The engine maintains alignment between `simulation_time` (integer step count) and `calendar_time` (datetime):
```
calendar_time = mission_start_datetime + (simulation_time * timestep_duration)
```

Day, week, and phase boundaries are computed from `calendar_time`.

### 4.3 Event Scheduling

Modules may schedule future events by inserting scheduled records into a priority queue:
```
{
  "trigger_time": future simulation_time,
  "event_type": string,
  "event_payload": arbitrary data,
  "target_module": module_id
}
```

The core delivers scheduled events to target modules at the specified `trigger_time`.

## 5. Slow–Fast Process Reconciliation

### 5.1 Process Classification

Modules are classified as:
- **Slow processes:** update at daily or weekly boundaries (e.g., long-term goal adjustment, cumulative stress)
- **Fast processes:** update at every time-step (e.g., momentary affect, immediate cognitive load)

This classification is specified in simulation configuration.

### 5.2 Update Ordering

Within a time-step:
1. Slow modules execute first (if triggered)
2. Fast modules execute second
3. Reconciliation applies fast updates over slow updates for overlapping variables

### 5.3 Conflict Resolution

If slow and fast modules update the same state variable:
- Fast module updates take precedence (override)
- Slow module updates are logged as baseline adjustments
- Conflicts are flagged in debug logs for review

Alternative reconciliation strategies (e.g., weighted average) may be configured per variable.

## 6. Hooks for External Modules

### 6.1 Module Registration

External modules register with the core during initialization:
```
register_module(
  module_id: string,
  update_function: callable,
  process_type: "slow" | "fast",
  execution_priority: integer
)
```

Higher priority values execute earlier within the same process type.

### 6.2 Data Exchange Hooks

The core provides the following hooks for modules:

- **State Read Hook:** modules access current state (read-only)
- **State Write Hook:** modules submit state deltas (write to staging)
- **Memory Query Hook:** modules query memory buffer with filters
- **Event Scheduling Hook:** modules schedule future events
- **Inter-Module Messaging Hook:** modules send data to other modules (delivered same time-step)

All hooks enforce isolation: modules cannot directly modify other modules' state containers.

### 6.3 Lifecycle Hooks

Modules may optionally implement:
- `on_initialize(config)`: called once at simulation start
- `on_day_start(calendar_time)`: called at day boundaries
- `on_week_start(calendar_time)`: called at week boundaries
- `on_phase_transition(old_phase, new_phase)`: called when mission phase changes
- `on_finalize()`: called at simulation end

## 7. Determinism vs. Stochasticity

### 7.1 Deterministic Mode

In deterministic mode:
- Random number generator is seeded with a fixed value at initialization
- All module updates are reproducible given the same inputs
- State evolution is identical across repeated runs

### 7.2 Stochastic Mode

In stochastic mode:
- Random seed is derived from system entropy or user-specified seed
- Modules may use RNG for probabilistic updates
- State trajectories vary across runs

### 7.3 RNG Management

The core provides a managed RNG instance to all modules:
```
rng = core.get_rng()
value = rng.uniform(0, 1)
```

This ensures RNG state is checkpointed and restorable for replay.

## 8. Error Handling

### 8.1 Module Update Failures

If a module update function raises an exception:
1. The core logs the error with full context (state, module, time-step)
2. The staging state is rolled back to the pre-update snapshot
3. Simulation is paused or halted based on error severity configuration
4. Error is reported to the calling process with diagnostic data

### 8.2 State Validation

After each commit phase, the core validates:
- State variables are within defined ranges
- Required fields are present and non-null
- Module state containers are well-formed
- Memory buffer size is within limits

Validation failures trigger rollback and error reporting.

### 8.3 Rollback Mechanism

The core maintains a rollback buffer of recent state snapshots (configurable depth). On error:
- Current state reverts to the last valid snapshot
- Simulation may retry the failed time-step with diagnostic logging enabled
- Persistent failures halt the simulation

## 9. Computational Efficiency Considerations

### 9.1 State Representation

- Use efficient data structures (e.g., hash maps for state variables, deque for memory buffer)
- Avoid deep copying; use copy-on-write for state snapshots
- Prune memory buffer to fixed maximum size (FIFO eviction)

### 9.2 Module Invocation Overhead

- Minimize data serialization between core and modules
- Use shared memory views where possible
- Batch inter-module messages for delivery

### 9.3 Logging and Checkpointing

- Defer expensive logging operations to background threads
- Use incremental checkpointing (delta-based state saves)
- Provide configurable checkpoint frequency (e.g., every 100 steps)

### 9.4 Scalability

The core is designed for single-agent simulation. Multi-agent extensions would require:
- Parallel state update pipelines per agent
- Inter-agent synchronization mechanisms (not specified here)

## 10. Extensibility for Later Modules

### 10.1 Module Interface Stability

The core's module interface is versioned. Future changes preserve backward compatibility via:
- Optional parameters with default values
- Versioned state delta schemas
- Deprecation warnings for obsolete hooks

### 10.2 Custom State Variables

Modules may define custom state variables by:
1. Declaring variable name and type in module registration
2. Providing initialization values
3. Updating via standard delta mechanism

The core treats custom variables opaquely.

### 10.3 Plugin Architecture

The core supports dynamically loaded modules via plugin discovery:
- Modules are loaded from a configured directory at initialization
- Module metadata (name, version, dependencies) is validated
- Load order respects inter-module dependencies

### 10.4 Extension Points

Future capabilities may be added via:
- New lifecycle hooks (e.g., `on_anomaly_detected`)
- Additional state containers (e.g., `spatial_state` for location tracking)
- Alternative update strategies (e.g., event-driven vs. time-stepped)

All extensions must preserve the core update cycle semantics and module isolation guarantees.
