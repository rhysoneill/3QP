# Module 06: BDI Cognitive Cycle - Engineering Specification

## 1. Overview

This specification defines the computational architecture of the BDI (Belief-Desire-Intention) Cognitive Cycle for the 3QP behavioral twin system. It establishes formal representations for beliefs, desires, and intentions, and specifies the deterministic update cycle governing their evolution.

## 2. Belief Representation

### 2.1 Belief Structure

A **belief** is a symbolic assertion about the agent's internal or external state. Each belief is represented as a structured tuple:

```
Belief := (predicate, arguments, confidence, timestamp, source)
```

Where:
- `predicate`: A symbolic identifier for the belief type (e.g., `resource_level`, `task_status`, `constraint_active`)
- `arguments`: An ordered list of typed values specifying the belief content
- `confidence`: A numeric value in [0.0, 1.0] representing belief strength (1.0 = absolute certainty)
- `timestamp`: The simulation timestep at which the belief was last updated
- `source`: An identifier indicating the origin of the belief (e.g., `perception`, `inference`, `memory`)

### 2.2 Belief Set

The agent's complete belief state is a **belief set** `B`, defined as:

```
B := {Belief₁, Belief₂, ..., Beliefₙ}
```

Constraints:
- Belief sets must be finite
- No two beliefs may have identical (predicate, arguments) pairs with different confidence values
- If conflicting beliefs exist, resolution rules (Section 3.1) must be applied

### 2.3 Belief Validity

A belief is **valid** if:
1. Its predicate is registered in the domain ontology
2. Its arguments match the expected types for the predicate
3. Its confidence value is in [0.0, 1.0]
4. Its timestamp is ≤ current simulation timestep
5. Its source is a recognized belief origin

Invalid beliefs are rejected during belief revision.

## 3. Belief Update Rules

### 3.1 Belief Revision Phase

At each simulation timestep `t`, the belief set transitions from `B(t-1)` to `B(t)` according to:

1. **Incoming Beliefs**: Receive new belief assertions `Bₙₑw` from TQP Core
2. **Validation**: Filter `Bₙₑw` to retain only valid beliefs
3. **Conflict Resolution**: For each new belief in `Bₙₑw`:
   - If a belief with matching (predicate, arguments) exists in `B(t-1)`:
     - If confidence of new belief > threshold: replace old belief
     - Else: retain old belief
   - Else: add new belief to `B(t)`
4. **Decay**: Apply confidence decay to beliefs older than decay window (if configured)
5. **Pruning**: Remove beliefs with confidence < minimum threshold

### 3.2 Belief Inference

If inference rules are enabled:
- Apply forward-chaining inference rules to derive new beliefs from `B(t)`
- Inference-derived beliefs have source = `inference`
- Inference depth is bounded by configuration parameter

Inference rules are domain-specific and provided by TQP Core configuration.

### 3.3 Belief Persistence

Beliefs persist across timesteps unless:
- They are replaced by conflicting beliefs
- Their confidence decays below minimum threshold
- They are explicitly retracted by TQP Core

## 4. Desire Representation

### 4.1 Desire Structure

A **desire** represents a candidate goal state. Each desire is represented as:

```
Desire := (goal_predicate, goal_arguments, priority, utility, constraints, timestamp)
```

Where:
- `goal_predicate`: Symbolic identifier for the goal type
- `goal_arguments`: Typed values specifying the goal state
- `priority`: Numeric value in [0.0, 1.0] indicating goal importance
- `utility`: Numeric value representing expected value of achieving the goal
- `constraints`: Set of preconditions or restrictions (expressed as belief predicates)
- `timestamp`: Timestep at which the desire was generated

### 4.2 Desire Set

The agent's desire state is a **desire set** `D`, defined as:

```
D := {Desire₁, Desire₂, ..., Desireₘ}
```

Constraints:
- Desire sets must be finite
- Desires may conflict (multiple desires with incompatible constraints)
- No duplicate desires (identical goal predicates and arguments)

### 4.3 Desire Validity

A desire is **valid** if:
1. Its goal predicate is registered in the domain ontology
2. Its goal arguments match expected types
3. Its priority is in [0.0, 1.0]
4. Its constraints reference valid belief predicates
5. Its timestamp is ≤ current simulation timestep

## 5. Desire Formation Rules

### 5.1 Desire Formation Phase

At each timestep `t`, the desire set transitions from `D(t-1)` to `D(t)` according to:

1. **Goal Generation**: Apply goal generation rules to `B(t)` to produce candidate desires `Dᶜᵃⁿᵈ`
2. **Validation**: Filter `Dᶜᵃⁿᵈ` to retain only valid desires
3. **Merging**: Combine `D(t-1)` and `Dᶜᵃⁿᵈ`, removing duplicates
4. **Consistency Check**: Identify and resolve desire conflicts according to conflict resolution policy
5. **Pruning**: Remove desires that are:
   - Unsatisfiable (constraints inconsistent with `B(t)`)
   - Obsolete (timestamp older than retention window)
   - Below minimum priority threshold

### 5.2 Goal Generation Rules

Goal generation rules map belief states to desires:

```
Rule := (trigger_pattern, goal_template, priority_function)
```

Where:
- `trigger_pattern`: A pattern of beliefs that activates the rule
- `goal_template`: A template for constructing the desire
- `priority_function`: A function computing priority from belief values

Rules are domain-specific and provided by TQP Core configuration.

### 5.3 Desire Conflict Resolution

When desires conflict (incompatible constraints):
1. Identify conflict set `C ⊆ D(t)`
2. Apply resolution policy:
   - **Priority-based**: Retain desire with highest priority
   - **Utility-based**: Retain desire with highest utility
   - **Custom**: Apply domain-specific resolution function
3. Remove non-selected desires from `D(t)`

## 6. Intention Representation

### 6.1 Intention Structure

An **intention** represents a committed goal. Each intention is represented as:

```
Intention := (goal_predicate, goal_arguments, commitment_level, resources, plan_id, timestamp)
```

Where:
- `goal_predicate`: Symbolic identifier for the committed goal
- `goal_arguments`: Typed values specifying the goal state
- `commitment_level`: Numeric value in [0.0, 1.0] indicating commitment strength
- `resources`: Set of resource identifiers allocated to this intention
- `plan_id`: Optional reference to an execution plan (if plans are used)
- `timestamp`: Timestep at which the intention was adopted

### 6.2 Intention Set

The agent's committed goals are an **intention set** `I`, defined as:

```
I := {Intention₁, Intention₂, ..., Intentionₖ}
```

Constraints:
- Intention sets must be finite
- Intentions must be mutually consistent (no conflicting resource allocations)
- No duplicate intentions (identical goal predicates and arguments)

### 6.3 Intention Validity

An intention is **valid** if:
1. It corresponds to a valid desire
2. Its commitment level is in [0.0, 1.0]
3. Its resource allocations do not exceed available resources
4. Its timestamp is ≤ current simulation timestep

## 7. Intention Selection Rules

### 7.1 Intention Selection Phase

At each timestep `t`, the intention set transitions from `I(t-1)` to `I(t)` according to:

1. **Persistence**: Retain intentions from `I(t-1)` that remain valid
2. **Candidate Generation**: Select desires from `D(t)` as candidates for commitment
3. **Filtering**: Remove candidates that:
   - Conflict with persisting intentions
   - Violate resource constraints
   - Have priority below commitment threshold
4. **Selection**: Apply selection policy to choose new intentions from candidates
5. **Resource Allocation**: Assign resources to new intentions
6. **Commitment**: Add selected intentions to `I(t)`

### 7.2 Intention Selection Policies

**Priority-Based Selection**:
- Order candidates by priority descending
- Commit to candidates in order until resource limits reached

**Utility-Based Selection**:
- Order candidates by utility descending
- Commit to candidates in order until resource limits reached

**Constraint Satisfaction**:
- Formulate intention selection as constraint satisfaction problem
- Maximize total utility subject to consistency and resource constraints

Selection policy is specified by TQP Core configuration.

### 7.3 Intention Reconsideration

Intentions may be reconsidered at each timestep:
- If belief state changes invalidate intention preconditions
- If higher-priority desires emerge
- If resource availability changes

Reconsideration policy determines conditions under which intentions are dropped.

## 8. BDI Cycle Sequencing

### 8.1 Cycle Phases

The BDI cycle executes in strict phase order at each timestep:

```
1. Belief Revision Phase
   ↓
2. Desire Formation Phase
   ↓
3. Intention Selection Phase
   ↓
4. State Commit Phase
```

Each phase must complete before the next begins. No parallel execution across phases.

### 8.2 Cycle Timing

- **Timestep Duration**: Defined by TQP Core simulation clock
- **Phase Execution**: All phases execute within a single timestep
- **Synchronization**: BDI cycle is synchronous with TQP Core orchestration

### 8.3 Cycle Termination

The BDI cycle terminates when:
- Simulation ends
- TQP Core suspends BDI processing
- Fatal error occurs (Section 10)

## 9. State Persistence

### 9.1 Persistent State

The following structures persist across timesteps:
- Belief set `B`
- Desire set `D`
- Intention set `I`
- Configuration parameters
- Domain ontology

### 9.2 State Storage

State storage requirements:
- Belief set: O(n) where n = number of beliefs
- Desire set: O(m) where m = number of desires
- Intention set: O(k) where k = number of intentions

Maximum sizes are configurable to bound memory usage.

### 9.3 State Serialization

State must be serializable for:
- Checkpointing
- State transfer between simulation runs
- Debugging and inspection

Serialization format is defined by TQP Core.

## 10. Error Handling

### 10.1 Malformed Belief Structures

If a belief fails validation:
- Log error with belief details
- Reject belief
- Continue processing remaining beliefs

### 10.2 Malformed Desire Structures

If a desire fails validation:
- Log error with desire details
- Reject desire
- Continue processing remaining desires

### 10.3 Malformed Intention Structures

If an intention fails validation:
- Log error with intention details
- Reject intention
- Continue with existing intentions

### 10.4 Fatal Errors

Fatal errors trigger cycle termination:
- Domain ontology corruption
- State storage failure
- Infinite inference loop detected
- Configuration parameter invalid

Fatal errors are reported to TQP Core for handling.

## 11. Integration Hooks

### 11.1 Input Interface

The BDI module receives inputs from TQP Core:

```
Input := {
    new_beliefs: Set<Belief>,
    configuration_updates: Optional<ConfigUpdate>,
    control_signal: ControlSignal
}
```

Where:
- `new_beliefs`: Beliefs to be integrated into `B(t)`
- `configuration_updates`: Changes to BDI parameters
- `control_signal`: Cycle control (run, pause, reset)

### 11.2 Output Interface

The BDI module emits outputs to TQP Core:

```
Output := {
    current_beliefs: Set<Belief>,
    current_desires: Set<Desire>,
    current_intentions: Set<Intention>,
    cycle_status: Status
}
```

Where:
- `current_beliefs`: Complete belief set `B(t)`
- `current_desires`: Complete desire set `D(t)`
- `current_intentions`: Complete intention set `I(t)`
- `cycle_status`: Success, error, or warning indicators

### 11.3 Timing Constraints

- Inputs must be received before cycle start
- Outputs must be emitted before timestep end
- No inter-phase communication with TQP Core

## 12. Constraints

### 12.1 Scope Constraints

The BDI module **must not**:
- Generate behavioral outputs
- Process emotional or affective states
- Interface directly with physiology, social network, or stressor modules
- Execute domain-specific planning algorithms (unless explicitly configured)
- Make assumptions about agent personality or narrative context

### 12.2 Computational Constraints

- Cycle execution time must be bounded by timestep duration
- Memory usage must respect configured limits
- Inference depth must be bounded to prevent infinite loops

### 12.3 Determinism Constraints

- For identical inputs and initial state, the BDI cycle produces identical outputs
- No stochastic processes unless explicitly seeded by TQP Core
- Update rules are fully deterministic

## 13. Extensibility

### 13.1 Future Cognitive Layers

The BDI architecture supports extension with additional cognitive structures:
- Meta-cognitive monitoring
- Learning and adaptation mechanisms
- Multi-agent coordination primitives

Extensions must preserve the isolation of BDI from affective and behavioral systems.

### 13.2 Custom Update Rules

Domain-specific update rules may be added via configuration:
- Custom belief inference rules
- Custom goal generation rules
- Custom intention selection policies

Custom rules must conform to the interfaces defined in this specification.

### 13.3 Alternative BDI Implementations

The specification permits alternative implementations provided they:
- Preserve the BDI cycle phase ordering
- Maintain the input/output interfaces
- Respect the isolation constraints
- Produce deterministic outputs

## 14. Version

This specification describes Module 06: BDI Cognitive Cycle, Version 1.0.
