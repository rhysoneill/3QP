# Module 06: BDI Cognitive Cycle - Implementation Notes

## 1. Purpose

This document provides implementation guidance for the BDI Cognitive Cycle module. It offers recommendations for data structures, algorithms, architectural patterns, and error handling strategies to support efficient and maintainable implementation of the BDI specification. These notes are language-agnostic and focus on architectural principles rather than code-level details.

## 2. Core Data Structures

### 2.1 Belief Set Representation

**Recommended Structure**: Hash table indexed by (predicate, arguments) tuple.

**Rationale**:
- O(1) lookup for belief existence checks
- O(1) insertion and deletion
- Efficient conflict detection during belief revision

**Alternatives**:
- **List/Array**: Simpler but O(n) lookup; suitable for small belief sets (<50 beliefs)
- **Database**: Overkill for typical use cases but may be necessary for very large belief sets (>10,000 beliefs)

**Implementation Considerations**:
1. Use composite keys for hash indexing: `hash(predicate + serialize(arguments))`
2. Maintain secondary index by timestamp for efficient pruning of old beliefs
3. Consider copy-on-write semantics to support rollback if needed

### 2.2 Desire Set Representation

**Recommended Structure**: Priority queue or sorted list indexed by priority/utility.

**Rationale**:
- Efficient retrieval of highest-priority desires during intention selection
- Natural ordering for iteration

**Alternatives**:
- **Unordered set**: Simpler but requires full scan during intention selection
- **Multi-level structure**: Separate queues per priority band for very large desire sets

**Implementation Considerations**:
1. Support efficient re-prioritization when belief state changes
2. Maintain auxiliary index by goal type for conflict detection
3. Consider lazy sorting (sort only when needed) to reduce overhead

### 2.3 Intention Set Representation

**Recommended Structure**: Set with resource allocation tracking.

**Rationale**:
- Intentions are typically small (<10 active intentions)
- Resource conflict detection requires tracking allocations

**Alternatives**:
- **Graph structure**: Useful if intentions have dependency relationships
- **Constraint database**: Useful if complex resource constraints exist

**Implementation Considerations**:
1. Maintain bidirectional mapping: intention → resources, resource → intentions
2. Track commitment level decay if dynamic commitment is used
3. Support atomic intention addition/removal to preserve resource consistency

### 2.4 Domain Ontology

**Recommended Structure**: Schema registry with predicate definitions.

**Rationale**:
- Central validation point for all beliefs, desires, intentions
- Supports extensibility (add new predicates without code changes)

**Structure**:
```
PredicateSchema := {
    name: String,
    argument_types: Array<Type>,
    description: String,
    category: String  // e.g., "state", "goal", "constraint"
}

Ontology := Map<String, PredicateSchema>
```

**Implementation Considerations**:
1. Load ontology at initialization, not per-cycle
2. Validate predicates once during input processing, not repeatedly
3. Support ontology versioning for backward compatibility

## 3. BDI Cycle Implementation Strategy

### 3.1 Phase Separation

**Principle**: Implement each BDI cycle phase as a separate function/module with clear input/output contracts.

**Structure**:
```
BeliefRevisionPhase(old_beliefs, new_assertions, config) → new_beliefs
DesireFormationPhase(beliefs, old_desires, config) → new_desires
IntentionSelectionPhase(beliefs, desires, old_intentions, config) → new_intentions
StateCommitPhase(beliefs, desires, intentions) → persistent_state
```

**Benefits**:
- Independent testing of each phase
- Easy substitution of alternative algorithms
- Clear tracing of state evolution

**Implementation Considerations**:
1. Each phase should be stateless (no hidden global state)
2. Use immutable data structures where possible to avoid aliasing bugs
3. Log phase transitions for debugging

### 3.2 Belief Revision Algorithm

**Recommended Approach**: Confidence-based replacement with optional inference.

**Algorithm Outline**:
```
1. For each new belief assertion:
   a. Validate against ontology
   b. Check for existing belief with same (predicate, arguments)
   c. If exists:
      - If new confidence > old confidence: replace
      - Else: retain old belief
   d. If not exists: add new belief
2. Apply decay to old beliefs (if configured)
3. Prune beliefs below confidence threshold
4. If inference enabled:
   a. Apply inference rules to derive new beliefs
   b. Add inferred beliefs with source="inference"
   c. Bound inference depth to prevent infinite loops
```

**Implementation Considerations**:
1. Pre-compile inference rules at initialization for performance
2. Use forward-chaining for tractable inference (backward-chaining may be too expensive)
3. Consider caching inference results to avoid redundant derivations

### 3.3 Desire Formation Algorithm

**Recommended Approach**: Rule-based triggering with conflict resolution.

**Algorithm Outline**:
```
1. For each goal generation rule:
   a. Check if trigger pattern matches current beliefs
   b. If match: instantiate desire from goal template
   c. Compute priority using priority function
2. Merge new desires with retained old desires
3. Identify conflicting desires (incompatible constraints)
4. Resolve conflicts using configured policy (priority/utility)
5. Prune low-priority desires below threshold
```

**Implementation Considerations**:
1. Use pattern matching library for trigger pattern evaluation
2. Cache rule matches to avoid redundant computation
3. Support incremental desire formation (avoid re-generating all desires each cycle)

### 3.4 Intention Selection Algorithm

**Recommended Approach**: Greedy selection with resource constraints.

**Algorithm Outline**:
```
1. Retain intentions from previous cycle that remain valid
2. Identify candidate desires (not already committed)
3. Filter candidates:
   a. Remove desires conflicting with retained intentions
   b. Remove desires violating resource constraints
   c. Remove desires below commitment threshold
4. Sort candidates by priority or utility
5. Greedily select candidates until resource limits reached
6. Allocate resources to selected intentions
```

**Implementation Considerations**:
1. Use constraint satisfaction solver for complex resource allocation (if needed)
2. Support incremental intention updates (avoid full re-selection each cycle)
3. Log rejected candidates for debugging

### 3.5 Cycle Timing and Performance

**Target**: BDI cycle should complete within 10-100ms for typical scenarios.

**Performance Bottlenecks**:
1. Belief inference (exponential in inference depth)
2. Desire conflict resolution (quadratic in desire set size)
3. Intention selection (polynomial in constraint complexity)

**Optimization Strategies**:
1. Bound inference depth (default: 2-3 levels)
2. Use early termination in conflict detection
3. Cache expensive computations (inference results, conflict checks)
4. Profile cycle phases to identify bottlenecks

## 4. Error Handling and Robustness

### 4.1 Input Validation

**Principle**: Fail fast on invalid inputs; emit error status rather than corrupting state.

**Validation Checklist**:
1. Timestep is sequential
2. All belief assertions have valid predicates
3. All confidence values are in [0.0, 1.0]
4. Configuration updates reference recognized parameters
5. Control signals are recognized

**Error Response**:
- Reject invalid inputs
- Log error details
- Emit error status to TQP Core
- Preserve state from previous timestep

### 4.2 State Consistency

**Principle**: Ensure belief, desire, and intention sets remain consistent after each cycle.

**Consistency Invariants**:
1. No duplicate beliefs (unique predicate + arguments)
2. No duplicate desires (unique goal_predicate + goal_arguments)
3. No duplicate intentions (unique goal_predicate + goal_arguments)
4. All intentions correspond to valid desires
5. Resource allocations are non-overlapping

**Enforcement Strategy**:
1. Validate invariants at end of each cycle phase
2. Use assertions or runtime checks during development
3. Disable checks in production for performance (if validated during testing)

### 4.3 Infinite Loop Prevention

**Risk**: Inference rules may create infinite derivation chains.

**Prevention Strategies**:
1. Bound inference depth (hard limit, e.g., 5 levels)
2. Track derived beliefs to prevent re-derivation
3. Detect cycles in inference graph and terminate

**Implementation**:
```
InferenceEngine maintains:
- derived_beliefs: Set of beliefs generated this cycle
- derivation_depth: Current depth counter

For each inference step:
- Increment depth
- If depth > limit: terminate
- If derived belief already in derived_beliefs: skip
```

### 4.4 Resource Exhaustion

**Risk**: Belief/desire/intention sets exceed memory limits.

**Prevention Strategies**:
1. Enforce maximum set sizes via configuration
2. Prune low-priority/low-confidence elements when limits reached
3. Log warnings when approaching limits

**Implementation**:
```
When adding belief/desire/intention:
- Check if set size >= max_size
- If yes:
  - Remove lowest-priority/lowest-confidence element
  - Log warning
  - Add new element
```

## 5. Architectural Isolation

### 5.1 Module Boundaries

**Principle**: BDI module must not directly interact with other 3QP modules.

**Enforcement**:
1. All inputs flow through TQP Core input interface
2. All outputs flow through TQP Core output interface
3. No direct function calls or shared state with other modules

**Benefits**:
- Independent testing
- Module substitution without affecting other systems
- Clear responsibility boundaries

### 5.2 Cognitive vs. Affective Separation

**Principle**: BDI module does not model emotions or affective states.

**Enforcement**:
1. Domain ontology excludes emotional predicates (e.g., "afraid", "happy", "stressed")
2. Belief/desire representations are purely symbolic
3. No affective appraisal functions in BDI logic

**If Affective Integration is Needed**:
- Affective states are inputs from external module (e.g., SlowFast Physiology)
- BDI treats affective inputs as abstract beliefs (e.g., `arousal_level(high)`)
- BDI does not interpret or process affective semantics

### 5.3 Cognitive vs. Behavioral Separation

**Principle**: BDI module does not generate behaviors or actions.

**Enforcement**:
1. BDI outputs are cognitive states (beliefs, desires, intentions)
2. Behavioral mappings are handled by TQP Core or downstream modules
3. No action selection or execution logic in BDI module

**If Behavioral Integration is Needed**:
- Downstream module maps intentions → behaviors
- BDI emits intentions; behavioral module consumes them
- BDI does not track behavior execution status (unless provided as belief input)

## 6. Configuration Management

### 6.1 Configuration Parameters

**Core Parameters**:
- `confidence_decay_rate`: Rate at which belief confidence decays (default: 0.0, i.e., no decay)
- `minimum_confidence_threshold`: Minimum confidence for belief retention (default: 0.1)
- `inference_depth_limit`: Maximum inference chain length (default: 3)
- `belief_retention_window`: Timesteps before old beliefs are pruned (default: 100)
- `desire_retention_window`: Timesteps before old desires are pruned (default: 50)
- `max_belief_set_size`: Maximum number of beliefs (default: 1000)
- `max_desire_set_size`: Maximum number of desires (default: 100)
- `max_intention_set_size`: Maximum number of intentions (default: 10)
- `intention_selection_policy`: Policy for selecting intentions (default: "priority")

**Configuration Loading**:
1. Load configuration at module initialization
2. Support runtime updates via `ConfigurationUpdate` input
3. Validate configuration parameters before applying

### 6.2 Domain-Specific Configuration

**Domain Ontology**:
- Loaded from external file or provided by TQP Core
- Defines predicates, types, and constraints
- Versioned for compatibility

**Goal Generation Rules**:
- Loaded from external file or provided by TQP Core
- Defines trigger patterns and goal templates
- Domain-specific (varies by mission scenario)

**Inference Rules**:
- Optional; loaded if inference is enabled
- Defines derivation patterns
- Domain-specific

## 7. Testing and Validation

### 7.1 Unit Testing Strategy

**Test Coverage**:
1. Belief revision logic (conflict resolution, decay, pruning)
2. Desire formation logic (rule triggering, conflict detection)
3. Intention selection logic (resource allocation, commitment)
4. Input validation and error handling
5. State persistence and serialization

**Test Fixtures**:
- Synthetic belief/desire/intention sets
- Predefined domain ontologies
- Mock inputs from TQP Core

### 7.2 Integration Testing Strategy

**Test Coverage**:
1. Full BDI cycle execution over multiple timesteps
2. Configuration updates mid-simulation
3. Error recovery and state consistency
4. Performance under load (large belief/desire sets)

**Test Scenarios**:
- Normal operation
- Configuration changes
- Malformed inputs
- Resource exhaustion
- Inference loops

### 7.3 Validation Against Specification

**Validation Checklist**:
1. Belief revision follows specified rules (Section 3 of spec.md)
2. Desire formation follows specified rules (Section 5 of spec.md)
3. Intention selection follows specified rules (Section 7 of spec.md)
4. Input/output formats match data contract (data_contract.md)
5. Timing and sequencing match specification (Section 8 of spec.md)

**Validation Tools**:
- Schema validators for input/output formats
- Assertions for invariant checking
- Trace logs for cycle phase execution

## 8. Extensibility and Versioning

### 8.1 Adding New Predicates

**Process**:
1. Define predicate schema (name, argument types, category)
2. Add schema to domain ontology
3. Optionally define goal generation rules referencing new predicate
4. Optionally define inference rules referencing new predicate

**Backward Compatibility**:
- Old beliefs/desires/intentions remain valid
- New predicates do not affect existing logic

### 8.2 Adding New BDI Cycle Phases

**Example**: Adding a "meta-cognitive monitoring" phase.

**Process**:
1. Define phase interface (input/output)
2. Insert phase into cycle sequence
3. Update state structures to accommodate new phase outputs
4. Update data contract to include new outputs

**Considerations**:
- Preserve determinism
- Maintain architectural isolation
- Avoid breaking existing integrations

### 8.3 Alternative BDI Implementations

**Examples**:
- Logic-based BDI (using first-order logic for belief representation)
- Probabilistic BDI (using Bayesian networks for belief revision)
- Hybrid BDI (combining symbolic and subsymbolic components)

**Requirements**:
- Must conform to input/output data contract
- Must preserve cycle sequencing
- Must maintain determinism (or explicitly declare stochastic elements)
- Must respect architectural isolation

## 9. Performance Profiling

### 9.1 Key Metrics

**Cycle-Level Metrics**:
- Total cycle duration (ms)
- Per-phase duration (ms)
- Belief set size
- Desire set size
- Intention set size

**Operation-Level Metrics**:
- Belief lookups per cycle
- Inference rule applications per cycle
- Conflict resolutions per cycle

### 9.2 Profiling Tools

**Recommended Approaches**:
1. Instrument cycle phases with timers
2. Log metrics to cycle statistics output
3. Aggregate metrics across simulation run
4. Visualize performance trends over time

**Bottleneck Identification**:
- If belief revision is slow: reduce inference depth or optimize rule matching
- If desire formation is slow: optimize trigger pattern matching
- If intention selection is slow: simplify resource constraints

## 10. Debugging and Diagnostics

### 10.1 Logging Strategy

**Log Levels**:
1. **Error**: Fatal errors, invalid inputs, state corruption
2. **Warning**: Resource limits reached, conflicts detected
3. **Info**: Cycle start/end, phase transitions, state summaries
4. **Debug**: Detailed belief/desire/intention changes, rule applications

**Recommended Logging**:
- Log at **Info** level by default
- Enable **Debug** level for troubleshooting
- Always log **Error** and **Warning** levels

### 10.2 State Inspection

**Mechanisms**:
1. Serialize complete state (beliefs, desires, intentions) at each timestep
2. Provide inspection interface for querying current state
3. Support state snapshots for rollback testing

**Use Cases**:
- Debugging unexpected agent behavior
- Validating belief revision logic
- Analyzing desire formation patterns

### 10.3 Trace Replay

**Mechanism**: Record input/output sequences and replay for debugging.

**Process**:
1. Record all inputs (BDIInput) for each timestep
2. Record all outputs (BDIOutput) for each timestep
3. Replay inputs to reproduce behavior
4. Compare outputs to detect regressions

**Benefits**:
- Deterministic debugging
- Regression testing
- Performance profiling on realistic traces

## 11. Deployment Considerations

### 11.1 Initialization

**Steps**:
1. Load domain ontology
2. Load goal generation rules (if used)
3. Load inference rules (if used)
4. Load configuration parameters
5. Initialize empty belief/desire/intention sets
6. Validate all loaded data

**Failure Handling**:
- If initialization fails, emit error and halt
- Do not allow partial initialization

### 11.2 Runtime Operation

**Assumptions**:
- TQP Core provides valid inputs at each timestep
- Simulation clock advances deterministically
- No external state corruption

**Monitoring**:
- Track cycle execution time
- Monitor memory usage
- Log errors and warnings

### 11.3 Shutdown

**Steps**:
1. Complete current BDI cycle
2. Serialize final state (for checkpointing)
3. Release resources
4. Log shutdown status

## 12. Summary of Recommendations

### 12.1 Data Structures

- Use hash tables for belief sets (fast lookup)
- Use priority queues for desire sets (efficient prioritization)
- Use sets with resource tracking for intention sets

### 12.2 Algorithms

- Confidence-based belief revision (simple and effective)
- Rule-based desire formation (extensible and transparent)
- Greedy intention selection (efficient and deterministic)

### 12.3 Architecture

- Strictly separate BDI phases
- Isolate BDI from affective and behavioral systems
- Interface only through TQP Core

### 12.4 Robustness

- Validate all inputs
- Enforce consistency invariants
- Prevent infinite loops and resource exhaustion

### 12.5 Extensibility

- Support domain-specific ontologies and rules
- Allow alternative BDI implementations
- Version data contracts for compatibility

## 13. Version

These implementation notes describe Module 06: BDI Cognitive Cycle, Version 1.0.
