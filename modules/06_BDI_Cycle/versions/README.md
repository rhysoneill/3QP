# Module 06: BDI Cognitive Cycle

## Purpose

The BDI Cognitive Cycle module defines the computational architecture governing agent internal states structured as Beliefs, Desires, and Intentions. This module provides the formal representation and update mechanisms for these three cognitive primitives, establishing the reasoning substrate upon which agent decision-making operates within the 3QP behavioral twin framework.

This module does not define behaviors, emotions, physiological responses, or social dynamics. It concerns only the symbolic structures and cycle logic that maintain and update the agent's cognitive state.

## Scope

The BDI Cognitive Cycle module encompasses:

- **Belief Representation**: Formal structures encoding the agent's internal model of state, environment, and constraints
- **Desire Representation**: Formal structures encoding candidate goals, objectives, or target states
- **Intention Representation**: Formal structures encoding committed goals selected from the desire set
- **Update Cycle Sequencing**: The temporal ordering and rules governing transitions between belief revision, desire formation, and intention selection
- **State Persistence**: Mechanisms for maintaining cognitive state across simulation timesteps
- **Integration Hooks**: Abstract interfaces through which the BDI module receives inputs and emits outputs to TQP Core

## Boundaries

This module explicitly **does not** include:

- Emotional states or affective processing
- Behavioral execution or action selection
- Physiological state or autonomic responses
- Stressor exposure or stress mechanisms
- Social network influence or interpersonal dynamics
- Cognitive biases, heuristics, or psychological constructs
- Intervention mechanisms or coping strategies
- Narrative, personality, or character attributes

The BDI module operates as a purely symbolic reasoning layer, isolated from all affective, somatic, and behavioral subsystems.

## High-Level BDI Update Cycle

The BDI cycle executes in discrete phases at each simulation timestep:

1. **Belief Revision Phase**: The agent updates its belief set based on incoming state information, reconciling new data with existing beliefs according to formal update rules
2. **Desire Formation Phase**: The agent generates or updates its desire set based on the revised belief state, applying domain-specific constraints to candidate goals
3. **Intention Selection Phase**: The agent commits to a subset of desires as intentions, applying selection criteria that may consider resource constraints, consistency requirements, or prioritization rules
4. **State Commit Phase**: The updated belief, desire, and intention structures are persisted for use in subsequent cycles

Each phase operates deterministically on symbolic structures, with no stochastic or probabilistic elements unless explicitly specified by TQP Core configuration.

## Integration with TQP Core

The BDI module interacts with TQP Core through abstract interfaces:

- **Inputs**: The module receives structured state updates from TQP Core at each simulation timestep, which may include environmental observations, internal state signals, or constraint updates
- **Outputs**: The module emits the current belief set, desire set, and selected intentions to TQP Core, which may route this information to other modules or use it for decision-making logic
- **Timing**: The BDI cycle executes synchronously with TQP Core simulation timesteps, ensuring deterministic state evolution

The BDI module does not directly communicate with other modules (physiology, social network, stressor model, etc.). All inter-module communication is mediated by TQP Core according to its orchestration logic.

## Architectural Position

Within the 3QP architecture, the BDI Cognitive Cycle serves as the symbolic reasoning layer that provides structured internal state for agent modeling. It operates independently of:

- Module 04 (SlowFast Physiology): No direct coupling to autonomic or somatic state
- Module 05 (Social Network): No direct coupling to interpersonal dynamics
- Module 07 (Stressor Model): No direct coupling to stressor exposure or stress response
- Module 08 (Intervention Engine): No direct coupling to coping or mitigation mechanisms

The module's isolation ensures that cognitive state evolution follows formal, traceable rules independent of affective or behavioral systems.

## Version

This document describes Module 06: BDI Cognitive Cycle, Version 1.0.

## Related Documentation

- `spec.md`: Full engineering specification of BDI representations and cycle logic
- `theory_basis.md`: Computational rationale for the BDI architecture
- `data_contract.md`: Input/output data formats and constraints
- `implementation_notes.md`: Guidance for cognition subsystem implementation
