# TQP Core Module

The **TQP Core** is the foundational execution kernel for the 3QP behavioral twin system. It provides discrete-time simulation, agent state management, and module coordination.

## Overview

The TQP Core implements a hybrid dynamical system that:
- Maintains authoritative agent internal state
- Coordinates updates from external behavioral modules
- Enforces temporal consistency across slow and fast processes
- Supports deterministic and stochastic simulation modes
- Provides event scheduling, memory management, and inter-module messaging

## Architecture

### Core Components

1. **AgentState** - Structured representation of agent internal state
2. **TQPCore** - Main simulation engine
3. **ModuleRegistry** - Module registration and execution ordering
4. **Support Systems** - Memory buffer, event scheduler, message bus, RNG manager

### Module Interface

External modules implement the `Module` abstract base class:

```python
from tqp_core import Module, AgentState, StateDelta, ModuleInputs

class MyModule(Module):
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        # Read current state (immutable)
        # Compute state changes
        # Return delta
        return StateDelta(module_id="my_module", ...)
```

## Quick Start

### Installation

```bash
cd modules/01_TQP_Core
pip install -e .
```

### Basic Usage

```python
from datetime import datetime
from tqp_core import TQPCore, SimulationConfig, ModuleRegistration, ProcessType
from examples.example_modules import CounterModule

# 1. Create configuration
config = SimulationConfig(
    mission_start_datetime=datetime(2025, 1, 1),
    timestep_duration_minutes=60,
    total_timesteps=168,  # One week
    random_seed=42
)

# 2. Initialize core
core = TQPCore(config)

# 3. Register modules
core.register_module(ModuleRegistration(
    module_id="counter",
    module_name="Counter Module",
    module_version="1.0.0",
    process_type=ProcessType.FAST,
    execution_priority=100,
    module=CounterModule()
))

# 4. Initialize and run
core.initialize()
core.run()

# 5. Access results
final_state = core.get_current_state()
print(f"Final time: {final_state.simulation_time}")
```

## Key Features

### Discrete-Time Simulation
- Fixed time-step execution
- Configurable temporal granularity (minutes to weeks)
- Calendar-aligned phase detection

### Multi-Rate Processes
- **Fast modules**: Execute every time-step
- **Slow modules**: Execute on day/week boundaries
- Automatic conflict resolution

### Memory Management
- Time-ordered FIFO buffer
- Automatic eviction when capacity reached
- Queryable with filters

### Event Scheduling
- Schedule future events for specific modules
- Priority queue implementation
- Broadcast support

### Inter-Module Messaging
- Same-timestep message delivery
- Unicast and broadcast modes
- Isolated communication

### Deterministic RNG
- Seedable random number generation
- Checkpoint/restore support
- Reproducible stochastic simulations

### Error Handling
- Automatic state rollback on errors
- Configurable recovery strategies
- Comprehensive error logging

## Project Structure

```
01_TQP_Core/
├── tqp_core/              # Main package
│   ├── __init__.py        # Public API
│   ├── types.py           # Data structures
│   ├── config.py          # Configuration
│   ├── module_interface.py  # Module interface
│   ├── module_registry.py   # Module management
│   ├── support_systems.py   # Memory, events, RNG
│   └── core.py            # Main engine
├── examples/              # Example modules
│   └── example_modules.py
├── tests/                 # Test suite
│   └── test_tqp_core.py
├── demo.py                # Demonstration script
├── setup.py               # Package setup
└── README.md              # This file
```

## Running the Demo

```bash
python demo.py
```

This demonstrates:
- Module registration
- Simulation execution
- State evolution
- Observer callbacks

## Running Tests

```bash
python -m unittest discover tests
```

Test coverage includes:
- State validation
- Module registration and ordering
- Time-step execution
- Memory buffer operations
- Event scheduling
- Message passing
- Deterministic randomness

## Module Development Guide

### 1. Implement Module Interface

```python
from tqp_core import Module, AgentState, StateDelta, ModuleInputs

class MyBehavioralModule(Module):
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        # Access current state (read-only)
        current_value = current_state.internal_vars.get("my_var", 0)
        
        # Compute updates
        new_value = current_value + 1
        
        # Return delta
        return StateDelta(
            module_id="my_module",
            internal_var_updates={"my_var": new_value}
        )
```

### 2. Register with Core

```python
from tqp_core import ModuleRegistration, ProcessType

registration = ModuleRegistration(
    module_id="my_module",
    module_name="My Behavioral Module",
    module_version="1.0.0",
    process_type=ProcessType.FAST,  # or ProcessType.SLOW
    execution_priority=100,  # Higher executes first
    module=MyBehavioralModule()
)

core.register_module(registration)
```

### 3. State Variable Naming Convention

Use prefixed variable names to avoid conflicts:

```python
internal_var_updates={
    "my_module.counter": 10,
    "my_module.state": "active"
}
```

### 4. Lifecycle Hooks (Optional)

```python
from tqp_core import LifecycleHooks

hooks = LifecycleHooks()
hooks.on_initialize = lambda config: print("Module initialized")
hooks.on_day_start = lambda state: print("Day started")

registration = ModuleRegistration(
    # ... other parameters ...
    lifecycle_hooks=hooks
)
```

## Data Contracts

### AgentState Structure

```python
@dataclass
class AgentState:
    agent_id: str
    simulation_time: int
    calendar_time: datetime
    state_version: int
    internal_vars: Dict[str, Scalar]
    memory_buffer: List[MemoryRecord]
    belief_state: Dict[str, Any]
    goal_state: List[GoalObject]
    resource_state: Dict[str, float]
    module_state: Dict[str, Any]
```

### StateDelta Structure

```python
@dataclass
class StateDelta:
    module_id: str
    internal_var_updates: Optional[Dict[str, Scalar]] = None
    memory_additions: Optional[List[MemoryRecord]] = None
    belief_updates: Optional[Dict[str, Any]] = None
    goal_updates: Optional[Dict[str, Optional[GoalObject]]] = None
    resource_updates: Optional[Dict[str, float]] = None
    module_state_update: Optional[Any] = None
    scheduled_events: Optional[List[ScheduledEventRequest]] = None
    inter_module_messages: Optional[List[MessageRequest]] = None
```

## Time-Step Execution Sequence

1. **Pre-Update**: Increment time, snapshot state
2. **Slow Update**: Execute slow modules (if triggered)
3. **Fast Update**: Execute fast modules
4. **Reconciliation**: Apply deltas, resolve conflicts
5. **Validation**: Check state integrity
6. **Commit**: Atomically update state
7. **Post-Update**: Notify observers, checkpoint

## Performance Characteristics

Typical performance (on modern hardware):
- **Small simulations** (10 modules): >1000 timesteps/second
- **Medium simulations** (50 modules): >100 timesteps/second
- **Large simulations** (100 modules): >10 timesteps/second

*Actual performance depends on module complexity*

## Integration with Other Modules

The TQP Core serves as the foundation for all other 3QP modules:

- **Module 02 (Breakthrough Impact)**: Uses core for temporal dynamics
- **Module 04 (SlowFast Physiology)**: Registers as slow/fast processes
- **Module 05 (Social Network)**: Uses messaging for agent interactions
- **Module 06 (BDI Cycle)**: Updates beliefs, desires, intentions
- **Module 07 (Stressor Model)**: Feeds environmental stress signals
- **Module 08 (Intervention Engine)**: Applies external perturbations
- **Module 09 (Logging System)**: Observes all state transitions
- **Module 10 (Validation)**: Validates state invariants

## Extensibility

The core supports future extensions:

- **Spatial state**: Reserved container for location tracking
- **Multi-agent**: Parallel core instances per agent
- **Event-driven**: Alternative to time-stepped execution
- **Custom lifecycle hooks**: Extensible callback system

## Version History

- **1.0.0** (2025-12-01): Initial implementation
  - Core state management
  - Module coordination
  - Multi-rate processes
  - Event scheduling
  - Deterministic execution

## References

- [Technical Specification](versions/spec.md)
- [Data Contract](versions/data_contract.md)
- [Implementation Notes](versions/implementation_notes.md)
- [Theory Basis](versions/theory_basis.md)

## License

Part of the 3QP behavioral twin system.

## Contact

For questions or issues, refer to the main 3QP repository.
