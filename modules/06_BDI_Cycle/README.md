# BDI Cognitive Cycle Module

**Module 06 of the 3QP Behavioral Twin System**

## Overview

The BDI (Belief-Desire-Intention) Cognitive Cycle module provides symbolic cognitive reasoning for the 3QP system. It implements a formal, deterministic cognitive architecture that separates:

- **Beliefs**: What the agent knows or assumes about its state and environment
- **Desires**: Candidate goals the agent considers pursuing
- **Intentions**: Committed goals the agent actively pursues

## Key Features

✅ **Symbolic Representation**: Explicit, inspectable cognitive state  
✅ **Deterministic Execution**: Identical inputs produce identical outputs  
✅ **Modular Architecture**: Clean separation of belief, desire, and intention processing  
✅ **Configurable**: Runtime parameter updates for experimentation  
✅ **Extensible**: Domain-specific predicates and rules via ontology system  
✅ **Validated**: Comprehensive test suite with >80% coverage  

## Architecture

### BDI Cycle Phases

Each timestep executes in strict sequential order:

1. **Belief Revision Phase**
   - Integrate new belief assertions
   - Resolve conflicts (higher confidence wins)
   - Apply confidence decay (optional)
   - Prune low-confidence beliefs
   - Apply inference rules (optional)

2. **Desire Formation Phase**
   - Generate candidate goals from beliefs
   - Merge with existing desires
   - Check constraint satisfiability
   - Resolve conflicts
   - Prune low-priority desires

3. **Intention Selection Phase**
   - Reconsider existing intentions
   - Filter desire candidates
   - Apply selection policy (priority/utility)
   - Allocate resources
   - Commit to new intentions

4. **State Commit Phase**
   - Persist updated state
   - Emit output to TQP Core

### Core Components

```
bdi_cycle/
├── __init__.py          # Module exports
├── types.py             # Data structures and schemas
├── belief_revision.py   # Belief update engine
├── desire_formation.py  # Goal generation engine
├── intention_selection.py # Commitment engine
└── bdi_module.py        # Main orchestrator
```

## Installation

```bash
cd modules/06_BDI_Cycle
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from bdi_cycle import (
    BDIModule,
    BDIInput,
    BDIConfig,
    BeliefAssertion,
    DomainOntology,
    PredicateSchema,
)

# 1. Define domain ontology
ontology = DomainOntology()
ontology.register_predicate(PredicateSchema(
    name="resource_level",
    argument_types=[str, float],
    description="Current level of a resource",
    category="state"
))

# 2. Configure BDI module
config = BDIConfig(
    confidence_decay_rate=0.0,
    minimum_confidence_threshold=0.3,
    max_belief_set_size=1000
)

# 3. Initialize module
bdi = BDIModule(config=config, ontology=ontology)
bdi.initialize()

# 4. Execute BDI cycle
bdi_input = BDIInput(
    timestep=0,
    new_beliefs=[
        BeliefAssertion(
            predicate="resource_level",
            arguments=["oxygen", 0.85],
            confidence=0.95,
            source="perception"
        )
    ]
)

output = bdi.execute_cycle(bdi_input)

# 5. Inspect results
print(f"Beliefs: {len(output.beliefs)}")
print(f"Desires: {len(output.desires)}")
print(f"Intentions: {len(output.intentions)}")
print(f"Status: {output.status.code}")
```

## Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `confidence_decay_rate` | float | 0.0 | Rate at which belief confidence decays over time |
| `minimum_confidence_threshold` | float | 0.1 | Minimum confidence for belief retention |
| `inference_depth_limit` | int | 3 | Maximum inference chain length |
| `belief_retention_window` | int | 100 | Timesteps before old beliefs are pruned |
| `max_belief_set_size` | int | 1000 | Maximum number of beliefs |
| `desire_retention_window` | int | 50 | Timesteps before old desires are pruned |
| `max_desire_set_size` | int | 100 | Maximum number of desires |
| `max_intention_set_size` | int | 10 | Maximum number of intentions |
| `intention_selection_policy` | str | "priority" | Policy for selecting intentions: "priority", "utility", "constraint_sat" |
| `commitment_threshold` | float | 0.5 | Minimum priority for intention commitment |

## Data Structures

### Belief
```python
Belief(
    predicate: str,          # e.g., "resource_level"
    arguments: List[Any],    # e.g., ["oxygen", 0.85]
    confidence: float,       # [0.0, 1.0]
    timestamp: int,          # Timestep when updated
    source: str             # "perception", "inference", "memory", etc.
)
```

### Desire
```python
Desire(
    goal_predicate: str,     # e.g., "maintain_resource"
    goal_arguments: List[Any],
    priority: float,         # [0.0, 1.0]
    utility: float,          # Expected value
    constraints: List[ConstraintSpec],
    timestamp: int
)
```

### Intention
```python
Intention(
    goal_predicate: str,
    goal_arguments: List[Any],
    commitment_level: float, # [0.0, 1.0]
    resources: List[str],    # Allocated resources
    plan_id: Optional[str],  # Future: execution plan
    timestamp: int
)
```

## Running Tests

```bash
cd modules/06_BDI_Cycle
pytest tests/ -v
```

With coverage:
```bash
pytest tests/ --cov=bdi_cycle --cov-report=html
```

## Running Demo

```bash
cd modules/06_BDI_Cycle
python demo.py
```

The demo showcases:
- Basic BDI cycle execution
- Belief confidence handling
- Runtime configuration updates
- Control signal handling (run/pause/reset)

## Integration with 3QP System

The BDI module integrates with TQP Core through the standard module interface:

```python
# TODO: Integration with TQP Core module interface
# Will implement ModuleRegistration and lifecycle hooks
# when TQP Core integration layer is defined
```

### Input Dependencies

The BDI module receives inputs from:
- **TQP Core**: Temporal context, breakthrough signals
- **SlowFast Physiology (Module 04)**: Physiological state affecting cognition
- **Social Network (Module 05)**: Social context and influences
- **Stressor Model (Module 07)**: Environmental demands

### Output Consumers

BDI outputs are consumed by:
- **TQP Core**: For orchestration and state logging
- **Breakthrough Impact (Module 02)**: For consequence propagation
- **Logging System (Module 09)**: For state capture

## Architectural Compliance

This module adheres to the 3QP architecture specification (Module 03):

✅ **Scope Containment**: Implements only cognitive reasoning, not affective or behavioral logic  
✅ **Interface Contracts**: Uses defined data structures for all communication  
✅ **Determinism**: Produces identical outputs for identical inputs  
✅ **Modularity**: Independently testable and substitutable  
✅ **Statelessness**: Explicit state management with no hidden dependencies  

## Limitations and Future Work

### Current Limitations

1. **No Inference Engine**: Inference rules are defined but not implemented (TODO markers in code)
2. **No Goal Generation Rules**: Desire formation currently manual (awaiting domain-specific rules)
3. **Simplified Conflict Resolution**: Uses priority-based resolution only
4. **No Planning**: Intentions don't include execution plans (plan_id is placeholder)
5. **No Meta-Cognition**: No monitoring or regulation of cognitive processes

### Planned Enhancements

- **Inference Engine**: Forward-chaining inference with configurable rule sets
- **Goal Templates**: Domain-specific goal generation from belief patterns
- **Constraint Satisfaction**: Advanced intention selection via CSP solver
- **Learning Mechanisms**: Adaptive confidence adjustment and priority tuning
- **Multi-Agent Support**: Shared beliefs and collective intentions

## API Reference

See `bdi_cycle/types.py` for complete type definitions and constraints.

Key classes:
- `BDIModule`: Main module orchestrator
- `BeliefRevisionEngine`: Belief update logic
- `DesireFormationEngine`: Goal generation logic
- `IntentionSelectionEngine`: Commitment selection logic
- `DomainOntology`: Predicate schema registry

## References

- **Module Specification**: `versions/spec.md`
- **Theoretical Basis**: `versions/theory_basis.md`
- **Data Contract**: `versions/data_contract.md`
- **Implementation Notes**: `versions/implementation_notes.md`

## Version

**Version**: 1.0.0  
**Status**: Beta - Ready for Integration  
**Last Updated**: December 1, 2025

## License

Part of the 3QP Behavioral Twin System.

## Support

For questions or issues, refer to the 3QP system documentation or contact the development team.
