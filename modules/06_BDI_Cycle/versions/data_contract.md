# Module 06: BDI Cognitive Cycle - Data Contract

## 1. Overview

This document defines the data interface for the BDI Cognitive Cycle module. It specifies the structure, format, and constraints of all data exchanged between the BDI module and TQP Core, establishing a strict contract for inputs received and outputs emitted at each simulation timestep.

## 2. Input Data Contract

### 2.1 Input Structure

The BDI module receives inputs from TQP Core at each timestep according to the following structure:

```
BDIInput := {
    timestep: Integer,
    new_beliefs: Array<BeliefAssertion>,
    configuration_update: Optional<ConfigurationUpdate>,
    control_signal: ControlSignal
}
```

### 2.2 Timestep

```
timestep: Integer >= 0
```

The current simulation timestep. Must be monotonically increasing across successive BDI cycles.

**Constraints**:
- Must be non-negative
- Must be exactly `timestep(t-1) + 1` for sequential cycles
- Must match TQP Core simulation clock

### 2.3 BeliefAssertion

```
BeliefAssertion := {
    predicate: String,
    arguments: Array<Value>,
    confidence: Float,
    source: String
}
```

Represents a belief to be integrated into the agent's belief set.

**Field Specifications**:

#### `predicate`
- **Type**: String
- **Constraints**:
  - Length: 1-128 characters
  - Format: Alphanumeric with underscores (matching `^[a-zA-Z][a-zA-Z0-9_]*$`)
  - Must be registered in domain ontology
- **Example**: `"resource_level"`, `"task_status"`, `"constraint_active"`

#### `arguments`
- **Type**: Array of values
- **Constraints**:
  - Length: 0-16 elements
  - Element types must match predicate signature in domain ontology
- **Example**: `[42, "oxygen", 0.85]`

#### `confidence`
- **Type**: Float
- **Constraints**:
  - Range: [0.0, 1.0]
  - Precision: At least 2 decimal places
- **Semantics**:
  - 1.0 = absolute certainty
  - 0.5 = neutral/uncertain
  - 0.0 = complete disbelief
- **Example**: `0.95`

#### `source`
- **Type**: String
- **Constraints**:
  - Must be one of: `"perception"`, `"inference"`, `"memory"`, `"communication"`, `"external"`
- **Example**: `"perception"`

**Validation Rules**:
1. If `predicate` is unrecognized, reject assertion
2. If `arguments` length or types mismatch predicate signature, reject assertion
3. If `confidence` is out of range, clamp to [0.0, 1.0]
4. If `source` is unrecognized, default to `"external"`

### 2.4 ConfigurationUpdate

```
ConfigurationUpdate := {
    parameter_name: String,
    parameter_value: Value
}
```

Represents a configuration parameter change.

**Field Specifications**:

#### `parameter_name`
- **Type**: String
- **Constraints**: Must be a recognized configuration parameter
- **Recognized Parameters**:
  - `"confidence_decay_rate"`: Float in [0.0, 1.0]
  - `"minimum_confidence_threshold"`: Float in [0.0, 1.0]
  - `"inference_depth_limit"`: Integer >= 0
  - `"belief_retention_window"`: Integer >= 1 (in timesteps)
  - `"desire_retention_window"`: Integer >= 1 (in timesteps)
  - `"max_belief_set_size"`: Integer >= 1
  - `"max_desire_set_size"`: Integer >= 1
  - `"max_intention_set_size"`: Integer >= 1
  - `"intention_selection_policy"`: String in `{"priority", "utility", "constraint_sat"}`

#### `parameter_value`
- **Type**: Type must match expected type for `parameter_name`
- **Constraints**: Must satisfy parameter-specific constraints

**Validation Rules**:
1. If `parameter_name` is unrecognized, reject update
2. If `parameter_value` type or constraints are violated, reject update
3. Configuration updates take effect starting at timestep `t+1`

### 2.5 ControlSignal

```
ControlSignal := String
```

Controls BDI cycle execution.

**Allowed Values**:
- `"run"`: Execute normal BDI cycle
- `"pause"`: Skip cycle, retain state
- `"reset"`: Clear all beliefs, desires, intentions; reinitialize
- `"step"`: Execute single cycle, then pause

**Default**: `"run"`

### 2.6 Input Timing

- Inputs must be provided at the start of each timestep
- All input data structures must be complete (no partial inputs)
- If input is malformed or missing, BDI module emits error status and skips cycle

## 3. Output Data Contract

### 3.1 Output Structure

The BDI module emits outputs to TQP Core at the end of each timestep according to the following structure:

```
BDIOutput := {
    timestep: Integer,
    beliefs: Array<Belief>,
    desires: Array<Desire>,
    intentions: Array<Intention>,
    cycle_statistics: CycleStatistics,
    status: Status
}
```

### 3.2 Timestep

```
timestep: Integer >= 0
```

The timestep at which this output was generated. Must match the input timestep.

### 3.3 Belief

```
Belief := {
    predicate: String,
    arguments: Array<Value>,
    confidence: Float,
    timestamp: Integer,
    source: String
}
```

Represents a belief in the agent's current belief set.

**Field Specifications**:

#### `predicate`
- **Type**: String
- **Format**: Matches input `BeliefAssertion.predicate` format
- **Example**: `"resource_level"`

#### `arguments`
- **Type**: Array of values
- **Format**: Matches input `BeliefAssertion.arguments` format
- **Example**: `[42, "oxygen", 0.85]`

#### `confidence`
- **Type**: Float
- **Range**: [0.0, 1.0]
- **Example**: `0.95`

#### `timestamp`
- **Type**: Integer >= 0
- **Semantics**: Timestep at which belief was last updated
- **Constraint**: `timestamp <= current timestep`
- **Example**: `42`

#### `source`
- **Type**: String
- **Values**: Same as input `BeliefAssertion.source`
- **Example**: `"inference"`

**Guarantees**:
1. All beliefs have valid predicates (registered in ontology)
2. All beliefs have confidence >= minimum threshold
3. No duplicate beliefs (unique predicate + arguments)
4. Belief count <= `max_belief_set_size`

### 3.4 Desire

```
Desire := {
    goal_predicate: String,
    goal_arguments: Array<Value>,
    priority: Float,
    utility: Float,
    constraints: Array<ConstraintSpec>,
    timestamp: Integer
}
```

Represents a desire in the agent's current desire set.

**Field Specifications**:

#### `goal_predicate`
- **Type**: String
- **Format**: Alphanumeric with underscores
- **Example**: `"achieve_resource_level"`

#### `goal_arguments`
- **Type**: Array of values
- **Example**: `["oxygen", 0.95]`

#### `priority`
- **Type**: Float
- **Range**: [0.0, 1.0]
- **Semantics**:
  - 1.0 = highest priority
  - 0.0 = lowest priority
- **Example**: `0.8`

#### `utility`
- **Type**: Float
- **Range**: Real numbers (typically [0.0, 100.0])
- **Semantics**: Expected value of achieving goal
- **Example**: `45.2`

#### `constraints`
- **Type**: Array of constraint specifications
- **Format**: Each constraint is a belief predicate pattern that must be satisfied
- **Example**: `[{"predicate": "resource_available", "arguments": ["oxygen"]}]`

#### `timestamp`
- **Type**: Integer >= 0
- **Semantics**: Timestep at which desire was generated
- **Example**: `42`

**Guarantees**:
1. All goal predicates are valid
2. No duplicate desires (unique goal_predicate + goal_arguments)
3. Desire count <= `max_desire_set_size`

### 3.5 Intention

```
Intention := {
    goal_predicate: String,
    goal_arguments: Array<Value>,
    commitment_level: Float,
    resources: Array<String>,
    plan_id: Optional<String>,
    timestamp: Integer
}
```

Represents an intention in the agent's current intention set.

**Field Specifications**:

#### `goal_predicate`
- **Type**: String
- **Format**: Matches `Desire.goal_predicate` format
- **Example**: `"achieve_resource_level"`

#### `goal_arguments`
- **Type**: Array of values
- **Format**: Matches `Desire.goal_arguments` format
- **Example**: `["oxygen", 0.95]`

#### `commitment_level`
- **Type**: Float
- **Range**: [0.0, 1.0]
- **Semantics**:
  - 1.0 = fully committed
  - 0.0 = no commitment (intention should be dropped)
- **Example**: `0.9`

#### `resources`
- **Type**: Array of strings
- **Semantics**: Resource identifiers allocated to this intention
- **Example**: `["processing_unit_1", "memory_bank_A"]`

#### `plan_id`
- **Type**: Optional string
- **Semantics**: Reference to execution plan (if planning is enabled)
- **Example**: `"plan_42"` or `null`

#### `timestamp`
- **Type**: Integer >= 0
- **Semantics**: Timestep at which intention was adopted
- **Example**: `42`

**Guarantees**:
1. All intentions correspond to valid desires
2. No duplicate intentions (unique goal_predicate + goal_arguments)
3. Resource allocations are consistent (no resource assigned to multiple intentions)
4. Intention count <= `max_intention_set_size`

### 3.6 CycleStatistics

```
CycleStatistics := {
    beliefs_added: Integer,
    beliefs_removed: Integer,
    beliefs_updated: Integer,
    desires_added: Integer,
    desires_removed: Integer,
    intentions_added: Integer,
    intentions_removed: Integer,
    inference_rule_applications: Integer,
    conflicts_resolved: Integer,
    cycle_duration_ms: Float
}
```

Provides statistics about the BDI cycle execution.

**Field Specifications**:
- All integer fields are non-negative
- `cycle_duration_ms`: Execution time in milliseconds (for profiling)

**Example**:
```
{
    beliefs_added: 3,
    beliefs_removed: 1,
    beliefs_updated: 5,
    desires_added: 2,
    desires_removed: 0,
    intentions_added: 1,
    intentions_removed: 0,
    inference_rule_applications: 12,
    conflicts_resolved: 1,
    cycle_duration_ms: 8.3
}
```

### 3.7 Status

```
Status := {
    code: String,
    message: Optional<String>
}
```

Indicates BDI cycle execution status.

**Field Specifications**:

#### `code`
- **Type**: String
- **Allowed Values**:
  - `"success"`: Cycle completed normally
  - `"warning"`: Cycle completed with warnings (see message)
  - `"error"`: Cycle failed (see message)
  - `"skipped"`: Cycle skipped due to pause signal

#### `message`
- **Type**: Optional string
- **Content**: Human-readable description of warnings or errors
- **Example**: `"Belief set size limit reached; oldest beliefs pruned"`

**Examples**:
```
{ "code": "success", "message": null }
{ "code": "warning", "message": "Inference depth limit reached" }
{ "code": "error", "message": "Domain ontology not loaded" }
```

### 3.8 Output Timing

- Outputs are emitted at the end of each timestep
- All output data structures are complete and consistent
- Outputs reflect state *after* BDI cycle execution

## 4. Data Flow Sequence

### 4.1 Nominal Cycle

```
t=0: TQP Core → BDIInput(t=0) → BDI Module
     BDI Module executes cycle
     BDI Module → BDIOutput(t=0) → TQP Core

t=1: TQP Core → BDIInput(t=1) → BDI Module
     BDI Module executes cycle
     BDI Module → BDIOutput(t=1) → TQP Core

...
```

### 4.2 Error Handling

```
t=k: TQP Core → BDIInput(t=k) → BDI Module
     BDI Module detects error
     BDI Module → BDIOutput(t=k, status.code="error") → TQP Core
     TQP Core decides whether to continue or halt simulation
```

### 4.3 Pause/Resume

```
t=k: TQP Core → BDIInput(t=k, control_signal="pause") → BDI Module
     BDI Module skips cycle
     BDI Module → BDIOutput(t=k, status.code="skipped") → TQP Core

t=k+1: TQP Core → BDIInput(t=k+1, control_signal="run") → BDI Module
       BDI Module resumes normal execution
```

## 5. Validity Rules

### 5.1 Input Validity

An input is **valid** if:
1. `timestep` is non-negative and sequential
2. All `BeliefAssertion` structures satisfy field constraints
3. `ConfigurationUpdate` (if present) references recognized parameters
4. `control_signal` is a recognized value

Invalid inputs trigger error status and cycle skip.

### 5.2 Output Validity

An output is **valid** if:
1. `timestep` matches input timestep
2. All `Belief`, `Desire`, `Intention` structures satisfy field constraints
3. No duplicate beliefs, desires, or intentions
4. Set sizes respect configured limits
5. Resource allocations are consistent

Output validity is guaranteed by the BDI module implementation.

## 6. Data Volume Estimates

### 6.1 Typical Sizes

For a representative 3QP simulation:

- **Belief set**: 10-100 beliefs per timestep
- **Desire set**: 5-20 desires per timestep
- **Intention set**: 1-5 intentions per timestep
- **Input size**: ~1-10 KB per timestep
- **Output size**: ~5-50 KB per timestep

### 6.2 Maximum Sizes

Configured limits ensure bounded resource usage:

- **Max belief set**: Configurable, default 1000
- **Max desire set**: Configurable, default 100
- **Max intention set**: Configurable, default 10

## 7. Serialization Format

### 7.1 Recommended Format

The data contract is format-agnostic, but JSON is recommended for:
- Human readability
- Tool support
- Schema validation

### 7.2 Example JSON Serialization

**Input Example**:
```json
{
  "timestep": 42,
  "new_beliefs": [
    {
      "predicate": "resource_level",
      "arguments": ["oxygen", 0.85],
      "confidence": 0.95,
      "source": "perception"
    }
  ],
  "configuration_update": null,
  "control_signal": "run"
}
```

**Output Example**:
```json
{
  "timestep": 42,
  "beliefs": [
    {
      "predicate": "resource_level",
      "arguments": ["oxygen", 0.85],
      "confidence": 0.95,
      "timestamp": 42,
      "source": "perception"
    }
  ],
  "desires": [
    {
      "goal_predicate": "maintain_resource_level",
      "goal_arguments": ["oxygen", 0.9],
      "priority": 0.8,
      "utility": 50.0,
      "constraints": [],
      "timestamp": 42
    }
  ],
  "intentions": [
    {
      "goal_predicate": "maintain_resource_level",
      "goal_arguments": ["oxygen", 0.9],
      "commitment_level": 0.9,
      "resources": ["resource_manager"],
      "plan_id": null,
      "timestamp": 42
    }
  ],
  "cycle_statistics": {
    "beliefs_added": 1,
    "beliefs_removed": 0,
    "beliefs_updated": 0,
    "desires_added": 1,
    "desires_removed": 0,
    "intentions_added": 1,
    "intentions_removed": 0,
    "inference_rule_applications": 0,
    "conflicts_resolved": 0,
    "cycle_duration_ms": 2.1
  },
  "status": {
    "code": "success",
    "message": null
  }
}
```

## 8. Versioning

This data contract is versioned independently from module implementation. Current version: **1.0**.

Breaking changes to the contract require version increment and migration support.

## 9. Contract Enforcement

### 9.1 Pre-Conditions

TQP Core must ensure:
- Inputs conform to contract specifications
- Timestep sequencing is correct
- Domain ontology is loaded before first cycle

### 9.2 Post-Conditions

BDI module must ensure:
- Outputs conform to contract specifications
- State consistency is maintained
- Errors are reported via status field

### 9.3 Contract Violations

Contract violations are implementation bugs and must be reported to module maintainers.

## 10. Version

This data contract describes Module 06: BDI Cognitive Cycle, Version 1.0.
