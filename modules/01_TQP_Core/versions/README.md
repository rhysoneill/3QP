# Module 01: TQP Core — Deep Internal Engine

## Purpose

The TQP Core module serves as the global internal update engine for the 3QP (Third-Quarter Phenomenon) Behavioral Twin simulation system. It executes the discrete-time simulation loop, manages agent internal state progression, and coordinates data exchange between all subsystem modules.

## Scope

This module encompasses:
- Agent internal state representation and storage
- Time-step execution logic
- State variable update orchestration
- Synchronization of slow and fast temporal processes
- Data ingestion from external modules
- Data emission to external modules
- Simulation clock management
- Deterministic and stochastic update control

## Role Within 3QP

The TQP Core is the execution kernel of the behavioral twin. It does not implement behavioral theories, physiological models, social dynamics, or intervention logic. Instead, it provides the computational substrate that allows those external modules to update agent state in a coordinated, time-consistent manner.

All causal trajectories emerge from the interaction of this engine with data provided by specialized modules. The core ensures temporal coherence and maintains the integrity of the simulation state across update cycles.

## Responsibilities

- Execute discrete time-step updates at configurable intervals
- Maintain agent internal state variables and memory structures
- Invoke update hooks for external modules at appropriate time points
- Reconcile slow-process (weekly/daily) and fast-process (intra-day) updates
- Enforce update ordering and data validity constraints
- Provide rollback and error recovery mechanisms
- Log state transitions for debugging and validation
- Support deterministic replay for verification

## Boundaries: What This Module Does NOT Do

The TQP Core does NOT:
- Implement social network dynamics or relationship models
- Compute physiological states (stress, arousal, fatigue)
- Define stressor events or mission scenarios
- Execute BDI (Belief-Desire-Intention) cognitive cycles
- Generate or apply interventions
- Perform logging beyond internal state checkpointing
- Validate behavioral realism or scientific accuracy
- Simulate mission-specific events

Those functions are handled by dedicated modules (02–12) that interface with TQP Core via defined data contracts.

## Expected Interfaces

### Input Interfaces
- Configuration data: simulation parameters, time-step granularity, agent initialization
- Module update functions: registered callbacks from external modules
- External state deltas: computed state changes from subsystem modules

### Output Interfaces
- Current agent state snapshot: exposed to all modules at each time-step
- Time-step metadata: current simulation time, step count, phase
- Update completion signals: notifications to modules after state commits

### Control Interfaces
- Simulation start/stop/pause
- Time-step advance triggers
- Checkpoint save/restore
- Error and rollback handling

## Implementation Status

This specification is implementation-ready. The module can be built as a standalone component with mock external modules for testing. Integration with other modules requires only adherence to the data contracts defined in `data_contract.md`.
