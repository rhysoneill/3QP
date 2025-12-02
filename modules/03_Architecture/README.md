# Module 03: Architecture Overview

## Overview

The Architecture module provides the system orchestrator and integration layer for the 3QP system. It implements the modular architecture defined in the specification, managing module registration, dependency injection, event-based communication, and execution sequencing.

**Version**: 1.0.0  
**Complies with Architecture Version**: 1.0.0

## Components

### Orchestrator
Central coordination point that manages the entire simulation lifecycle:
- Module registration and dependency resolution
- Simulation initialization and finalization
- Time step execution coordination
- Error handling and recovery

### EventBus
Publish/subscribe event system enabling loosely-coupled inter-module communication:
- Event subscription and publication
- Event history tracking
- Type-safe event handling

### ExecutionPipeline
Manages the 10-phase simulation cycle defined in the Architecture specification:
- Phase handler registration
- Sequential phase execution
- Phase enable/disable control
- Error propagation

### SimulationContainer
Runtime environment for agent simulations:
- Agent state initialization and management
- Time progression and calendar management
- Lifecycle hook invocation
- State validation

## Key Features

- **Modular Design**: Clean separation between orchestration logic and behavioral modules
- **Deterministic Execution**: Ensures reproducibility through controlled sequencing
- **Event-Driven Architecture**: Modules communicate through events, not direct coupling
- **Lifecycle Management**: Proper initialization, execution, and finalization hooks
- **Error Handling**: Structured error recording and recovery policies
- **Validation Support**: Built-in state validation at each time step

## Installation

```bash
cd modules/03_Architecture
pip install -e .
```

For development with testing dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

### Basic Setup

```python
from datetime import datetime, timedelta
from architecture import Orchestrator, SimulationConfig

# Configure simulation
config = SimulationConfig(
    start_time=datetime(2025, 1, 1),
    time_step_duration=timedelta(days=1),
    mission_phases={
        "quarter-1": (0, 30),
        "quarter-2": (31, 60),
        "quarter-3": (61, 90),
        "quarter-4": (91, 120)
    },
    random_seed=42,
    metadata={}
)

# Create orchestrator
orchestrator = Orchestrator(config)

# Register modules
# (Module registration code here)

# Initialize simulation
orchestrator.initialize(agent_ids=["agent_1", "agent_2"])

# Run simulation
orchestrator.run(num_steps=120)

# Finalize
orchestrator.finalize()
```

### Module Registration

```python
from tqp_core.module_interface import ModuleRegistration, Module, LifecycleHooks
from tqp_core.types import ProcessType, AgentState, ModuleInputs, StateDelta

class MyModule(Module):
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        # Module logic here
        return StateDelta(module_id="my_module")

registration = ModuleRegistration(
    module_id="my_module",
    module_name="My Module",
    module_version="1.0.0",
    process_type=ProcessType.FAST,
    execution_priority=500,
    module=MyModule()
)

orchestrator.register_module(registration)
```

### Event Bus Usage

```python
from architecture import Event

# Subscribe to events
def handle_breakthrough(event: Event):
    print(f"Breakthrough occurred: {event.payload}")

orchestrator.event_bus.subscribe("breakthrough_occurred", handle_breakthrough)

# Publish events (typically done by modules)
event = Event(
    event_type="breakthrough_occurred",
    source_module="tqp_core",
    payload={"agent_id": "agent_1", "magnitude": 0.85},
    simulation_time=42
)
orchestrator.event_bus.publish(event)
```

## Architecture Compliance

This module implements the integration layer as specified in Module 03 Architecture specification. It enforces:

- **Acyclic Dependencies**: Module dependency validation prevents cycles
- **Deterministic Execution**: Sequential phase execution ensures reproducibility
- **Phase Sequencing**: 10-phase execution pipeline per specification
- **Explicit Data Flows**: All inter-module communication via event bus or module interfaces
- **Lifecycle Management**: Proper initialization, execution, and finalization

## Integration with Other Modules

The Architecture module integrates with:

- **TQP Core (01)**: Uses module interface definitions and type system
- **All Behavioral Modules**: Orchestrates execution and manages state
- **Logging System (09)**: Coordinates state logging in Phase 9
- **Validation (10)**: Optionally enables validation in Phase 10

## Testing

Run tests:

```bash
pytest tests/
```

With coverage:

```bash
pytest --cov=architecture tests/
```

## Documentation

- `versions/spec.md`: Technical specification
- `versions/theory_basis.md`: Architectural principles and rationale
- `versions/data_contract.md`: Inter-module data flow specifications
- `versions/implementation_notes.md`: Implementation guidance

## Limitations and Future Work

Current implementation provides:
- ✅ Module registration and dependency validation
- ✅ Execution pipeline with 10 phases
- ✅ Event bus for inter-module communication
- ✅ Simulation container with lifecycle management
- ✅ Basic error recording

Future enhancements:
- [ ] Advanced error recovery strategies
- [ ] State checkpoint/restore functionality
- [ ] Performance profiling and optimization
- [ ] Parallel module execution (where dependencies allow)
- [ ] Dynamic module loading and hot-swapping

## Contributing

All changes must:
1. Comply with Architecture specification v1.0.0
2. Maintain deterministic execution guarantees
3. Include tests demonstrating correctness
4. Update documentation accordingly

## License

Part of the 3QP research project.
