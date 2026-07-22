# Phase B: Action/Intent Layer

**Status**: ✅ Complete

## Overview

Phase B implements a minimal, deterministic agentic layer that makes the 3QP system exhibit intentional behavior without modifying the core behavioral physics.

## Design Philosophy

- **Deterministic**: No randomness, no LLM usage in action selection
- **Transparent**: All decisions are inspectable and traceable
- **Additive**: Does not modify core dynamics (monotony, strain, cohesion)
- **Causal**: Actions influence inputs, not state transitions

## Components

### 1. Action Model (`actions.py`)

Defines the finite set of agent actions:

- **WITHDRAW**: Reduce interaction frequency, increase recovery
- **ENGAGE**: Increase interaction frequency and novelty
- **SUPPORT**: Strengthen positive interactions and shared successes
- **ESCALATE**: Raise visibility of issues, prioritize intervention
- **MAINTAIN**: Continue current behavior pattern (default)

**Data Structures**:
- `ActionType`: Enum of action types
- `AgentState`: Read-only snapshot of current state
- `AgentAction`: Action selection with context

### 2. Intent Policy (`intent_policy.py`)

Deterministic rule-based mapping from state to actions.

**Decision Priority** (highest to lowest):
1. **ESCALATE** - Critical conditions requiring attention
2. **WITHDRAW** - Self-protective response to high stress
3. **SUPPORT** - Proactive cohesion maintenance
4. **ENGAGE** - Counter monotony and stagnation
5. **MAINTAIN** - Default steady-state behavior

**Configuration Parameters**:
- Strain thresholds (high: 0.75, very high: 0.9)
- Cohesion thresholds (low: 0.4, critical: 0.25)
- TQ pressure threshold (high: 0.35)
- Monotony threshold (high: 0.6)

All thresholds are tunable via `IntentPolicyConfig`.

### 3. Action Effects (`action_effects.py`)

Maps actions to effects on interaction patterns.

**Effects** (examples):
- `WITHDRAW`: 0.85× workload, 1.30× recovery
- `ENGAGE`: 1.15× workload, +0.15 novelty probability
- `SUPPORT`: 0.95× workload, +0.20 success probability
- `ESCALATE`: 0.90× workload, 1.20× recovery
- `MAINTAIN`: No modifications

**Critical**: Actions modify inputs (workload, recovery, novelty, success), **not** psychological state variables.

### 4. Action Logger (`action_logger.py`)

Tracks all agent actions with full context.

**Capabilities**:
- Log every action with state snapshot
- Compute action frequency statistics
- Extract pre-collapse action sequences
- Generate fingerprint-compatible metadata
- Serialize to JSON

### 5. Agentic Core Model (`agentic_core.py`)

Wrapper that integrates agents with `RuthlessCoreModel`.

**Architecture**:
1. Read state from core dynamics
2. Select action via `IntentPolicy`
3. Apply action effects to inputs
4. Log action
5. Update core dynamics (one step)
6. Repeat

**Modes**:
- `enable_actions=True`: Agentic mode (Phase B)
- `enable_actions=False`: Baseline mode (Phase A)

## Integration

Phase B integrates seamlessly with existing infrastructure:

### Mission Runner

```python
from integration.runtime import run_mission, RuntimeConfig

# Baseline mode (no agents)
result = run_mission(
    runtime_config=config,
    enable_agents=False
)

# Agentic mode (Phase B)
result = run_mission(
    runtime_config=config,
    enable_agents=True
)

# Access action log
if result.action_log:
    stats = result.action_log.get_statistics()
    print(f"Dominant action: {stats['dominant_action']}")
```

### Fingerprint Integration

Action metadata is automatically attached to `FingerprintSchema`:

```python
fingerprint.metadata["action_summary"] = {
    "total_actions": 200,
    "action_counts": {...},
    "action_frequencies": {...},
    "dominant_action": "maintain"
}

fingerprint.metadata["pre_collapse_actions"] = {
    "window_days": 20,
    "action_sequence": ["maintain", "support", "withdraw", ...],
    "dominant_action": "withdraw"
}
```

## Usage

### Basic Example

```python
from agents import AgenticCoreModel, IntentPolicy, ActionEffects
from ruthless_core import RuthlessCoreConfig

# Configure core dynamics
core_config = RuthlessCoreConfig(mission_length_days=200)

# Create agentic model
model = AgenticCoreModel(
    core_config=core_config,
    enable_actions=True
)

# Run simulation
output, action_logger = model.run(mission_name="test_mission")

# Analyze actions
stats = action_logger.get_statistics()
print(f"Total actions: {stats['total_actions']}")
print(f"Action counts: {stats['action_counts']}")
```

### Custom Policy Configuration

```python
from agents import IntentPolicyConfig, IntentPolicy

# Configure custom thresholds
policy_config = IntentPolicyConfig(
    high_strain_threshold=0.8,  # More tolerant of strain
    low_cohesion_threshold=0.3,  # Lower cohesion triggers
)

policy = IntentPolicy(config=policy_config)

model = AgenticCoreModel(
    core_config=core_config,
    intent_policy=policy
)
```

### Analyze Pre-Collapse Behavior

```python
# Get actions before collapse
pre_collapse = action_logger.log.get_pre_collapse_actions(
    collapse_day=124,
    window_days=20
)

# Find dominant pre-collapse action
dominant = action_logger.log.get_dominant_pre_collapse_action(
    collapse_day=124
)

print(f"Crew exhibited {dominant} behavior before collapse")
```

## Demonstration

Run the Phase B demonstration:

```bash
python agents/demo_phase_b.py
```

This will:
1. Run baseline mission (no agents)
2. Run agentic mission (with agents)
3. Compare results
4. Show action decision transparency
5. Display fingerprint integration

## Validation

Phase B meets all requirements:

✅ **Action Model**: 5 semantic actions defined  
✅ **Intent Policy**: Deterministic, threshold-based, no randomness  
✅ **Action Effects**: Influence inputs, not psychological state  
✅ **Action Logging**: Complete with state snapshots and metadata  
✅ **Fingerprint Integration**: Action stats attached to `run_metadata`  
✅ **Transparency**: All decisions are inspectable and traceable  
✅ **Additive**: Does not modify Phase A components  

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    AgenticCoreModel                         │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Read State  │ -> │ IntentPolicy │ -> │ActionEffects │  │
│  │  (S,C,M,Q)  │    │  (select)    │    │  (modulate)  │  │
│  └─────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                    │         │
│         v                   v                    v         │
│  ┌─────────────────────────────────────────────────────┐  │
│  │          RuthlessCoreModel (unchanged)              │  │
│  │  M(t+1) ← update_monotony(M(t), novelty)            │  │
│  │  S(t+1) ← update_strain(S(t), M, workload, recovery)│  │
│  │  C(t+1) ← update_cohesion(C(t), S, Q, success)      │  │
│  └─────────────────────────────────────────────────────┘  │
│         │                                                  │
│         v                                                  │
│  ┌─────────────┐                                           │
│  │ActionLogger │                                           │
│  └─────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

## Key Insights

1. **Separation of Concerns**: Agent logic is completely separate from physics
2. **Input Modulation**: Actions shape the environment, not the psychology
3. **Deterministic Agency**: Agentic behavior without non-determinism
4. **Full Traceability**: Every decision is logged with rationale
5. **Backward Compatible**: Can run in baseline mode (Phase A)

## Next Steps (Phase C - Out of Scope)

Phase B is complete and locked. Future work includes:

- LLM integration for dialogue generation
- Multi-agent social texture
- Narrative overlay
- Advanced intervention strategies

**Do not modify Phase B components for Phase C work.**

## Files

```
agents/
├── __init__.py              # Module exports
├── actions.py               # Action types and state
├── intent_policy.py         # Deterministic action selection
├── action_effects.py        # Input modulation
├── action_logger.py         # Action tracking and analysis
├── agentic_core.py          # Wrapper around RuthlessCoreModel
├── demo_phase_b.py          # Demonstration script
└── README.md                # This file
```

## Version

Phase B v1.0 - December 2025
