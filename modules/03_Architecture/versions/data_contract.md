# Module 03: Architecture Overview – Data Contract

## 1. Purpose

This document defines the conceptual data exchange interfaces between modules in the 3QP system. It specifies:

- What categories of data may flow between modules
- The directionality of each data flow
- The semantic meaning and structure of exchanged data
- Timing and synchronization requirements
- Global validity constraints

This is an architectural data contract, not an implementation specification. It describes *what* must be communicated, not *how* (e.g., function calls, message passing, shared memory).

## 2. Data Flow Inventory

Each entry below specifies:
- **Source Module → Target Module**
- **Data Category**: High-level description of information transferred
- **Semantics**: Meaning and interpretation of the data
- **Granularity**: Per-agent, system-wide, per-time-step, etc.
- **Timing**: When the data is produced and consumed

---

## 3. Core Foundation → Behavioral Simulation

### 3.1 TQP Core (01) → Breakthrough Impact (02)

**Data Category**: Breakthrough Event Indicator  
**Semantics**: Boolean flag indicating whether a breakthrough event occurred in the current time step, plus contextual metadata (magnitude, phase, temporal position).  
**Granularity**: Per-agent, per-time-step  
**Timing**: Produced after Phase 7 (Breakthrough Evaluation), consumed in Phase 8 (Breakthrough Consequence Propagation)  

**Structure**:
- `breakthrough_occurred`: Boolean
- `breakthrough_magnitude`: Real number (0.0 = no breakthrough, 1.0 = maximum)
- `temporal_phase`: Enumeration (early-quarter, mid-quarter, third-quarter, final-sprint)
- `agent_id`: Identifier

**Validity Constraints**:
- `breakthrough_magnitude` ∈ [0.0, 1.0]
- `breakthrough_occurred = true` implies `breakthrough_magnitude > threshold`

---

### 3.2 TQP Core (01) → SlowFast Physiology (04)

**Data Category**: Temporal State  
**Semantics**: Current temporal phase and deadline proximity, influencing physiological stress responses.  
**Granularity**: Per-agent, per-time-step  
**Timing**: Produced in Phase 3 (Core Temporal Update), consumed in Phase 4 (Physiological Update)  

**Structure**:
- `temporal_phase`: Enumeration (early-quarter, mid-quarter, third-quarter, final-sprint)
- `time_remaining`: Real number (proportion of total period remaining, 0.0 = deadline, 1.0 = start)
- `breakthrough_probability`: Real number ∈ [0.0, 1.0]
- `agent_id`: Identifier

**Validity Constraints**:
- `time_remaining` ∈ [0.0, 1.0]
- `breakthrough_probability` ∈ [0.0, 1.0]

---

### 3.3 TQP Core (01) → BDI Cycle (06)

**Data Category**: Temporal Context  
**Semantics**: Deadline urgency and breakthrough probability, informing action selection and deliberation priorities.  
**Granularity**: Per-agent, per-time-step  
**Timing**: Produced in Phase 3 (Core Temporal Update), consumed in Phase 6 (Cognitive Update)  

**Structure**:
- `temporal_phase`: Enumeration
- `time_remaining`: Real number ∈ [0.0, 1.0]
- `breakthrough_probability`: Real number ∈ [0.0, 1.0]
- `urgency_signal`: Real number (derived metric indicating decision urgency)
- `agent_id`: Identifier

**Validity Constraints**:
- `urgency_signal` increases monotonically as `time_remaining` decreases

---

### 3.4 TQP Core (01) → Stressor Model (07)

**Data Category**: Temporal Phase Context  
**Semantics**: Current temporal phase for calibrating stress sensitivity and environmental demand generation.  
**Granularity**: Per-agent, per-time-step  
**Timing**: Produced in Phase 3 (Core Temporal Update), consumed in Phase 2 (Environmental Update)  

**Structure**:
- `temporal_phase`: Enumeration
- `time_remaining`: Real number ∈ [0.0, 1.0]
- `agent_id`: Identifier

**Validity Constraints**:
- `temporal_phase` transitions are monotonic (early → mid → third-quarter → final-sprint)

---

## 4. Behavioral Simulation → Behavioral Simulation

### 4.1 Stressor Model (07) → SlowFast Physiology (04)

**Data Category**: Stress Load Signals  
**Semantics**: Quantified stressor exposure affecting homeostatic regulation and allostatic load.  
**Granularity**: Per-agent, per-time-step  
**Timing**: Produced in Phase 2 (Environmental Update), consumed in Phase 4 (Physiological Update)  

**Structure**:
- `total_stress_load`: Real number (aggregate stress exposure)
- `stressor_components`: Array of (stressor_type, magnitude) pairs
  - `stressor_type`: Enumeration (workload, interpersonal, environmental, internal)
  - `magnitude`: Real number ≥ 0.0
- `agent_id`: Identifier

**Validity Constraints**:
- `total_stress_load = sum(magnitude for all stressor_components)`
- All magnitudes ≥ 0.0

---

### 4.2 Stressor Model (07) → BDI Cycle (06)

**Data Category**: Environmental Demands  
**Semantics**: External and internal stressors influencing cognitive deliberation, attention allocation, and goal prioritization.  
**Granularity**: Per-agent, per-time-step  
**Timing**: Produced in Phase 2 (Environmental Update), consumed in Phase 6 (Cognitive Update)  

**Structure**:
- `demand_level`: Real number (overall demand on cognitive resources)
- `stressor_salience`: Array of (stressor_type, salience_weight) pairs
- `agent_id`: Identifier

**Validity Constraints**:
- `demand_level` ≥ 0.0
- `salience_weight` ∈ [0.0, 1.0] for each stressor

---

### 4.3 Social Network (05) → BDI Cycle (06)

**Data Category**: Social Influence Vectors  
**Semantics**: Relational context and social influence signals affecting beliefs, desires, and intentions.  
**Granularity**: Per-agent, per-time-step  
**Timing**: Produced in Phase 5 (Social Update), consumed in Phase 6 (Cognitive Update)  

**Structure**:
- `social_influence_signals`: Array of (source_agent_id, influence_type, magnitude)
  - `influence_type`: Enumeration (normative, informational, coercive, peer_pressure)
  - `magnitude`: Real number (strength of influence)
- `network_position_metrics`: Object
  - `centrality`: Real number (network centrality measure)
  - `isolation_index`: Real number (degree of social isolation)
- `agent_id`: Identifier

**Validity Constraints**:
- `magnitude` ≥ 0.0 for all influence signals
- `centrality` and `isolation_index` are normalized ∈ [0.0, 1.0]

---

### 4.4 SlowFast Physiology (04) → BDI Cycle (06)

**Data Category**: Physiological State Affecting Cognition  
**Semantics**: Current physiological state influencing cognitive capacity, emotional state, and decision-making.  
**Granularity**: Per-agent, per-time-step  
**Timing**: Produced in Phase 4 (Physiological Update), consumed in Phase 6 (Cognitive Update)  

**Structure**:
- `cognitive_capacity`: Real number ∈ [0.0, 1.0] (available mental resources)
- `arousal_level`: Real number (physiological activation)
- `fatigue_level`: Real number ≥ 0.0 (accumulated fatigue)
- `emotional_valence`: Real number ∈ [-1.0, 1.0] (negative to positive)
- `agent_id`: Identifier

**Validity Constraints**:
- High `fatigue_level` implies low `cognitive_capacity`
- Extreme `arousal_level` may reduce `cognitive_capacity` (inverted-U relationship)

---

## 5. Intervention Engine → Modules

### 5.1 Intervention Engine (08) → TQP Core (01)

**Data Category**: Temporal Interventions  
**Semantics**: External actions modifying breakthrough probability or temporal dynamics (e.g., deadline extension, checkpoint introduction).  
**Granularity**: Per-agent or system-wide, episodic (not every time step)  
**Timing**: Applied in Phase 1 (Pre-Step Setup)  

**Structure**:
- `intervention_type`: Enumeration (deadline_extension, checkpoint_addition, temporal_reframing)
- `magnitude`: Real number (strength of intervention effect)
- `target_agent_id`: Identifier (or null for system-wide)
- `duration`: Integer (number of time steps the intervention remains active)

**Validity Constraints**:
- `magnitude` > 0.0
- `duration` ≥ 1

---

### 5.2 Intervention Engine (08) → SlowFast Physiology (04)

**Data Category**: Physiological Interventions  
**Semantics**: External actions affecting physiological state (e.g., rest breaks, relaxation techniques, physical activity).  
**Granularity**: Per-agent, episodic  
**Timing**: Applied in Phase 1 (Pre-Step Setup)  

**Structure**:
- `intervention_type`: Enumeration (rest_break, exercise, relaxation, pharmacological)
- `effect_on_arousal`: Real number (delta to arousal level)
- `effect_on_fatigue`: Real number (delta to fatigue level)
- `target_agent_id`: Identifier

**Validity Constraints**:
- Effects may be positive or negative depending on intervention type

---

### 5.3 Intervention Engine (08) → Social Network (05)

**Data Category**: Social Structure Interventions  
**Semantics**: External modifications to social network structure (e.g., team reorganization, new connections).  
**Granularity**: System-wide or agent-pair, episodic  
**Timing**: Applied in Phase 1 (Pre-Step Setup)  

**Structure**:
- `intervention_type`: Enumeration (add_edge, remove_edge, weight_adjustment, team_restructure)
- `source_agent_id`: Identifier
- `target_agent_id`: Identifier
- `new_edge_weight`: Real number (if adding/modifying connection)

**Validity Constraints**:
- Edge weights must satisfy network topology constraints

---

### 5.4 Intervention Engine (08) → BDI Cycle (06)

**Data Category**: Cognitive Interventions  
**Semantics**: External actions modifying beliefs, desires, or intentions (e.g., goal setting, cognitive reappraisal).  
**Granularity**: Per-agent, episodic  
**Timing**: Applied in Phase 1 (Pre-Step Setup)  

**Structure**:
- `intervention_type`: Enumeration (goal_setting, belief_update, intention_injection, cognitive_reframing)
- `target_belief_or_goal`: String (identifier for affected mental state)
- `modification`: Object (structure depends on intervention type)
- `target_agent_id`: Identifier

**Validity Constraints**:
- Modifications must respect BDI consistency constraints (beliefs, desires, intentions must remain coherent)

---

### 5.5 Intervention Engine (08) → Stressor Model (07)

**Data Category**: Environmental Interventions  
**Semantics**: External modifications to stressor exposure (e.g., workload reduction, environmental improvements).  
**Granularity**: Per-agent or system-wide, episodic  
**Timing**: Applied in Phase 1 (Pre-Step Setup)  

**Structure**:
- `intervention_type`: Enumeration (workload_reduction, environmental_improvement, stressor_removal)
- `affected_stressor_type`: Enumeration (workload, interpersonal, environmental, internal)
- `magnitude`: Real number (reduction in stressor intensity)
- `target_agent_id`: Identifier (or null for system-wide)

**Validity Constraints**:
- `magnitude` ≥ 0.0 (interventions reduce, not increase, stressors)

---

## 6. Breakthrough Impact → Modules

### 6.1 Breakthrough Impact (02) → SlowFast Physiology (04)

**Data Category**: Physiological Consequences of Breakthrough  
**Semantics**: Immediate and delayed physiological effects following a breakthrough event (e.g., arousal spike, fatigue reduction).  
**Granularity**: Per-agent, episodic (only when breakthrough occurs)  
**Timing**: Applied in Phase 8 (Breakthrough Consequence Propagation)  

**Structure**:
- `arousal_delta`: Real number (change in arousal level)
- `fatigue_delta`: Real number (change in fatigue level)
- `emotional_valence_delta`: Real number (change in emotional state)
- `agent_id`: Identifier

**Validity Constraints**:
- Typically `arousal_delta` > 0.0 (breakthroughs are activating)
- Typically `emotional_valence_delta` > 0.0 (breakthroughs are positive events)

---

### 6.2 Breakthrough Impact (02) → Social Network (05)

**Data Category**: Social Consequences of Breakthrough  
**Semantics**: Changes to social network structure or edge weights following a breakthrough (e.g., increased centrality, status changes).  
**Granularity**: Per-agent, episodic  
**Timing**: Applied in Phase 8 (Breakthrough Consequence Propagation)  

**Structure**:
- `status_change`: Real number (change in social status or influence)
- `edge_weight_updates`: Array of (connected_agent_id, weight_delta) pairs
- `agent_id`: Identifier

**Validity Constraints**:
- Social consequences may be positive (increased status) or negative (envy, competition)

---

### 6.3 Breakthrough Impact (02) → BDI Cycle (06)

**Data Category**: Cognitive Consequences of Breakthrough  
**Semantics**: Updates to beliefs, desires, or intentions following a breakthrough (e.g., increased self-efficacy, revised goals).  
**Granularity**: Per-agent, episodic  
**Timing**: Applied in Phase 8 (Breakthrough Consequence Propagation)  

**Structure**:
- `belief_updates`: Array of (belief_id, new_confidence) pairs
- `desire_intensity_changes`: Array of (desire_id, delta) pairs
- `intention_revisions`: Array of (intention_id, revision_type) pairs
- `agent_id`: Identifier

**Validity Constraints**:
- Belief confidence ∈ [0.0, 1.0]
- Revisions must maintain BDI coherence

---

### 6.4 Breakthrough Impact (02) → Stressor Model (07)

**Data Category**: Environmental Consequences of Breakthrough  
**Semantics**: Changes to stressor exposure following a breakthrough (e.g., workload reduction due to progress, increased expectations).  
**Granularity**: Per-agent, episodic  
**Timing**: Applied in Phase 8 (Breakthrough Consequence Propagation)  

**Structure**:
- `stressor_intensity_changes`: Array of (stressor_type, delta) pairs
- `agent_id`: Identifier

**Validity Constraints**:
- Consequences may be positive (reduced workload) or negative (increased expectations)

---

## 7. All Modules → Logging System

### 7.1 Any Module → Logging System (09)

**Data Category**: State Snapshots and Events  
**Semantics**: Complete state of a module at a given time step, plus discrete events (e.g., breakthrough occurrence, intervention application).  
**Granularity**: Per-module, per-time-step  
**Timing**: Emitted in Phase 9 (State Logging)  

**Structure**:
- `timestamp`: Integer (simulation time step)
- `module_id`: Enumeration (01–12)
- `agent_id`: Identifier (if per-agent state)
- `state_snapshot`: Object (module-specific structure)
- `events`: Array of (event_type, event_data) pairs

**Validity Constraints**:
- All state must be serializable
- Logs must be append-only (no retroactive modification)
- Logs must include sufficient information for complete state reconstruction

---

## 8. Global Data Constraints

### 8.1 Identifier Consistency
All agent identifiers must be globally unique and consistent across modules. Identifier format is defined at system initialization and remains fixed throughout simulation.

### 8.2 Temporal Consistency
All time-dependent data references the same global simulation time. Modules may not operate on different time scales without explicit synchronization.

### 8.3 Unit Consistency
All quantitative data uses consistent units:
- Probabilities: [0.0, 1.0]
- Proportions: [0.0, 1.0]
- Time: Integer time steps (or explicit time duration units if defined)
- Magnitudes: Real numbers with documented scales

### 8.4 Nullability
Unless explicitly documented, all data fields are non-nullable. Optional data must be represented with explicit null/None values or default sentinels.

### 8.5 Immutability
Data transferred between modules is conceptually immutable. Modules receive copies or read-only references. Modifications do not propagate backward to the source.

### 8.6 Versioning
Data structures are versioned. Modules declare which data contract version they comply with. Breaking changes to data structures require coordinated updates across modules.

---

## 9. Synchronization Semantics

### 9.1 Producer-Consumer Timing
Data is produced by the source module during its designated phase and consumed by the target module during its phase. Consumers must not read data before it is produced.

### 9.2 Synchronous Updates
All modules within a time step execute sequentially according to the phase ordering defined in `spec.md`. No asynchronous or parallel updates occur unless explicitly coordinated.

### 9.3 State Validity
Data passed between modules must satisfy all documented validity constraints. Invalid data constitutes a critical error.

---

## 10. Data Flow Prohibition Summary

The following data flows are architecturally prohibited:

- **Behavioral Modules → TQP Core**: Behavioral modules observe but do not modify core temporal dynamics.
- **Logging System → Any Module**: Logs are write-only during runtime.
- **Circular Flows**: No module may send data to a module that transitively sends data back.
- **Direct State Mutation**: Modules do not directly modify each other's internal state; all communication is through defined interfaces.

---

## 11. Extensibility

### 11.1 Adding New Data Flows
New data flows may be added if they:
- Do not introduce circular dependencies
- Are documented in this contract
- Satisfy global constraints
- Are validated by integration tests

### 11.2 Deprecating Data Flows
Data flows may be deprecated if:
- Dependent modules are updated to no longer require them
- A major version increment is triggered
- Migration guides are provided

---

## 12. Contract Compliance

All module implementations must demonstrate compliance with this data contract through:

- **Interface Tests**: Verify that modules produce and consume data matching documented structures
- **Constraint Validation**: Verify that all validity constraints are satisfied
- **Integration Tests**: Verify that data flows correctly through the system end-to-end

Non-compliance is a critical defect.

---

**Document Status**: Active  
**Version**: 1.0.0  
**Last Updated**: December 1, 2025  
**Maintained By**: Systems Architect
