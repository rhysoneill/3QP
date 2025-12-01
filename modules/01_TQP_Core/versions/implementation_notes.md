# Implementation Notes: TQP Core Development Guide

## 1. Recommended Implementation Path

### 1.1 Phase 1: Core State Management (Week 1-2)

**Objective:** Implement agent state representation and basic state operations.

**Tasks:**
1. Define `AgentState` data structure in target language
2. Implement state initialization from configuration
3. Implement state snapshot (deep copy) for rollback
4. Implement state validation function
5. Write unit tests for state operations

**Deliverables:**
- `AgentState` class/struct
- `state_manager` module with init/snapshot/validate functions
- Test suite with 100% coverage of state operations

**Success Criteria:**
- State can be initialized, snapshotted, and validated without errors
- State snapshots are independent (modifying one does not affect another)

### 1.2 Phase 2: Time-Step Execution Loop (Week 2-3)

**Objective:** Implement the core update cycle without modules.

**Tasks:**
1. Implement simulation clock (time-step counter, calendar time)
2. Implement time-step execution loop (phases: pre-update, update, commit, post-update)
3. Implement staging state mechanism (delta accumulation)
4. Implement rollback mechanism
5. Write integration tests with mock modules

**Deliverables:**
- `Simulator` class with `run()` method
- `timestep_executor` module with phase functions
- Mock module implementations for testing

**Success Criteria:**
- Simulator can execute 1000 time-steps with mock modules
- Rollback correctly restores previous state after simulated error
- Calendar time correctly tracks mission dates

### 1.3 Phase 3: Module System (Week 3-4)

**Objective:** Implement module registration and invocation.

**Tasks:**
1. Define module interface (registration, update function signature)
2. Implement module registry and priority-based execution ordering
3. Implement delta collection and application
4. Implement slow/fast module scheduling
5. Write tests with real module implementations

**Deliverables:**
- `ModuleRegistry` class
- `module_invoker` module with execution logic
- At least 2 example modules (1 slow, 1 fast)

**Success Criteria:**
- Modules can be dynamically registered and invoked
- Slow modules execute only on schedule, fast modules every step
- Module deltas correctly update agent state

### 1.4 Phase 4: Advanced Features (Week 4-5)

**Objective:** Implement memory buffer, event scheduling, inter-module messaging.

**Tasks:**
1. Implement memory buffer with FIFO eviction
2. Implement event scheduler (priority queue)
3. Implement inter-module message passing
4. Implement RNG management and seeding
5. Write tests for each feature

**Deliverables:**
- `MemoryBuffer` class
- `EventScheduler` class
- `MessageBus` class
- `RNGManager` class

**Success Criteria:**
- Memory buffer correctly evicts old records when full
- Scheduled events are delivered at correct simulation time
- Messages are delivered same-step to target modules
- RNG state is restorable from checkpoint

### 1.5 Phase 5: Error Handling and Checkpointing (Week 5-6)

**Objective:** Implement robust error handling and state persistence.

**Tasks:**
1. Implement exception handling in module invocation
2. Implement error logging and reporting
3. Implement checkpoint save/restore
4. Implement deterministic replay from checkpoint
5. Write fault injection tests

**Deliverables:**
- `ErrorHandler` class
- `CheckpointManager` class
- Fault injection test suite

**Success Criteria:**
- Module exceptions trigger rollback without crashing simulator
- Checkpoints can be saved and restored, resuming simulation
- Deterministic replay produces identical state evolution

### 1.6 Phase 6: Integration and Optimization (Week 6-7)

**Objective:** Integrate all components, optimize performance, prepare for module development.

**Tasks:**
1. Integrate all components into complete simulator
2. Profile and optimize performance bottlenecks
3. Write end-to-end integration tests
4. Document API for module developers
5. Create example modules demonstrating all features

**Deliverables:**
- Complete TQP Core simulator
- Performance benchmarks (time-steps per second)
- Module developer guide
- Example module repository

**Success Criteria:**
- Simulator executes 10,000 time-steps in < 1 minute (with simple modules)
- All integration tests pass
- External developers can implement new modules using documentation

## 2. Order of Operations (Within Time-Step)

The following sequence must be strictly followed within each time-step:

```
1. PRE-UPDATE
   1.1. Increment simulation_time
   1.2. Update calendar_time
   1.3. Snapshot current state to rollback buffer
   1.4. Check for scheduled events, add to delivery queue

2. SLOW-PROCESS UPDATE (if triggered)
   2.1. Determine which slow modules should execute this step
   2.2. For each slow module (in priority order):
        2.2.1. Prepare module_inputs (metadata, events, messages)
        2.2.2. Invoke module.update(current_state, module_inputs)
        2.2.3. Collect returned state_delta
        2.2.4. If exception: log error, abort to rollback
   2.3. Accumulate slow module deltas in staging state

3. FAST-PROCESS UPDATE
   3.1. For each fast module (in priority order):
        3.1.1. Prepare module_inputs
        3.1.2. Invoke module.update(current_state, module_inputs)
        3.1.3. Collect returned state_delta
        3.1.4. If exception: log error, abort to rollback
   3.2. Accumulate fast module deltas in staging state

4. RECONCILIATION
   4.1. Resolve conflicts (fast overrides slow for same variable)
   4.2. Apply all deltas to staging state
   4.3. Process memory_additions (append to buffer, evict if needed)
   4.4. Process scheduled_events (add to scheduler)
   4.5. Process inter_module_messages (deliver to target modules next step)

5. VALIDATION
   5.1. Run state validation checks on staging state
   5.2. If validation fails: log error, abort to rollback

6. COMMIT
   6.1. Increment state_version
   6.2. Replace current_state with staging state (atomic swap)
   6.3. Clear staging state

7. POST-UPDATE
   7.1. Emit state update notifications to observers
   7.2. Emit timestep completion event
   7.3. If checkpoint interval reached: save checkpoint
   7.4. Check termination conditions (timestep limit, external stop signal)

8. ERROR HANDLING (if exception occurred in 2-5)
   8.1. Log full error record (state, module, message)
   8.2. Restore state from rollback buffer
   8.3. Invoke error handler (halt, retry, skip module, etc.)
```

**Critical Invariants:**
- Current state is never modified directly; all updates go through staging
- State is only replaced atomically after successful validation
- Rollback buffer is never modified except in pre-update phase

## 3. Recommended Data Structures and Patterns

### 3.1 Agent State Storage

**Language-specific recommendations:**

**Python:**
```python
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class AgentState:
    agent_id: str
    simulation_time: int
    calendar_time: datetime
    state_version: int
    internal_vars: Dict[str, Union[int, float, bool, str]]
    memory_buffer: List[Dict[str, Any]]
    belief_state: Dict[str, Any]
    goal_state: List[Dict[str, Any]]
    resource_state: Dict[str, float]
    module_state: Dict[str, Any]
```

**Java/C++/Rust:**
Use structs with strongly typed fields. Use hashmaps for dictionaries, vectors for lists.

### 3.2 State Snapshot Strategy

**Option A: Deep Copy (Simple, Slower)**
```python
import copy
rollback_state = copy.deepcopy(current_state)
```

**Option B: Copy-on-Write (Complex, Faster)**
Use immutable data structures. Only copy fields that are modified.

**Recommendation:** Start with deep copy in Phase 1. Optimize to copy-on-write in Phase 6 if performance requires.

### 3.3 Module Registry

**Recommended structure:**
```python
class ModuleRegistry:
    def __init__(self):
        self.modules = {}  # module_id -> ModuleRegistration
        self.slow_modules = []  # sorted by priority
        self.fast_modules = []  # sorted by priority
    
    def register(self, registration: ModuleRegistration):
        self.modules[registration.module_id] = registration
        if registration.process_type == "slow":
            self.slow_modules.append(registration)
            self.slow_modules.sort(key=lambda m: m.execution_priority, reverse=True)
        else:
            self.fast_modules.append(registration)
            self.fast_modules.sort(key=lambda m: m.execution_priority, reverse=True)
```

### 3.4 Event Scheduler

Use a priority queue (heap) keyed by `trigger_time`:
```python
import heapq

class EventScheduler:
    def __init__(self):
        self.queue = []  # heap of (trigger_time, event)
    
    def schedule(self, event: ScheduledEventRequest):
        heapq.heappush(self.queue, (event.trigger_time, event))
    
    def get_events_for_time(self, current_time: int) -> List[ScheduledEvent]:
        events = []
        while self.queue and self.queue[0][0] == current_time:
            _, event = heapq.heappop(self.queue)
            events.append(event)
        return events
```

### 3.5 Memory Buffer

Use a deque for efficient FIFO eviction:
```python
from collections import deque

class MemoryBuffer:
    def __init__(self, max_size: int):
        self.buffer = deque(maxlen=max_size)
    
    def add(self, record: MemoryRecord):
        self.buffer.append(record)  # auto-evicts oldest if full
    
    def query(self, filters: Dict[str, Any]) -> List[MemoryRecord]:
        # Apply filters and return matching records
        return [r for r in self.buffer if self._matches_filters(r, filters)]
```

## 4. Module Purity and Isolation Guidelines

### 4.1 Module Development Principles

**DO:**
- Read entire agent state (read-only access)
- Update only owned state variables (by naming convention)
- Add memory records with source_module = self
- Schedule events for self or broadcast
- Send messages to other modules
- Use core-provided RNG for stochastic updates

**DO NOT:**
- Modify another module's state directly
- Delete or modify existing memory records
- Assume execution order relative to other modules (except priority)
- Retain mutable references to agent state across time-steps
- Use external RNG or time sources (breaks determinism)

### 4.2 State Variable Naming Convention

To prevent conflicts, use prefixed variable names:
```
internal_vars = {
    "physio.heart_rate": 72.0,        # owned by physiology module
    "physio.cortisol": 15.0,
    "bdi.current_intention": "task_A", # owned by BDI module
    "social.cohesion": 0.8             # owned by social module
}
```

### 4.3 Testing Module Isolation

Create unit tests that verify:
- Module A's update does not modify Module B's state container
- Module updates are commutative (executing A then B vs. B then A produces same result for non-overlapping variables)
- Modules cannot corrupt core state structures (memory buffer, event queue)

## 5. Future Extension Stubs

### 5.1 Spatial State Extension

Reserve a top-level state field for future spatial tracking:
```python
@dataclass
class AgentState:
    # ... existing fields ...
    spatial_state: Optional[Dict[str, Any]] = None  # future: position, location
```

### 5.2 Multi-Agent Extension

Design state representation to be agent-centric. For multi-agent:
```python
class MultiAgentSimulator:
    def __init__(self):
        self.agents = {}  # agent_id -> AgentState
        self.cores = {}   # agent_id -> TQPCore instance
    
    def step(self):
        # Update all agents in parallel or sequentially
        for agent_id, core in self.cores.items():
            core.step()
```

### 5.3 Alternative Update Strategies

Support pluggable update strategies:
```python
class UpdateStrategy(ABC):
    @abstractmethod
    def execute_step(self, state: AgentState, modules: List[Module]) -> AgentState:
        pass

class SequentialUpdateStrategy(UpdateStrategy):
    # Current implementation: modules execute in priority order

class ParallelUpdateStrategy(UpdateStrategy):
    # Future: modules execute concurrently, deltas merged

class EventDrivenStrategy(UpdateStrategy):
    # Future: modules wake only when events occur
```

## 6. Failure Mode Considerations

### 6.1 Module Timeout

Implement timeout for module updates:
```python
import signal

def invoke_module_with_timeout(module, state, inputs, timeout_sec=1.0):
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Module {module.module_id} exceeded timeout")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_sec)
    try:
        delta = module.update(state, inputs)
    finally:
        signal.alarm(0)  # cancel alarm
    return delta
```

### 6.2 State Corruption Detection

After each commit, optionally run integrity checks:
```python
def validate_state_integrity(state: AgentState) -> List[str]:
    errors = []
    if state.simulation_time < 0:
        errors.append("Negative simulation_time")
    if state.state_version < 0:
        errors.append("Negative state_version")
    for resource, value in state.resource_state.items():
        if value < 0:
            errors.append(f"Negative resource: {resource} = {value}")
    return errors
```

### 6.3 Checkpoint Recovery

Implement graceful degradation if checkpoint load fails:
```python
def load_checkpoint_or_reinitialize(checkpoint_path, config):
    try:
        state = load_checkpoint(checkpoint_path)
        return state
    except Exception as e:
        logger.warning(f"Checkpoint load failed: {e}. Reinitializing.")
        return initialize_state(config)
```

### 6.4 Module Dependency Failures

If module A depends on module B's output:
```python
def check_module_dependencies(modules: List[Module]) -> Dict[str, List[str]]:
    dependencies = {}
    for module in modules:
        dependencies[module.module_id] = module.get_dependencies()  # optional method
    # Verify dependencies are registered and have higher priority
    for module_id, deps in dependencies.items():
        for dep in deps:
            if dep not in modules:
                raise ValueError(f"Module {module_id} depends on unregistered module {dep}")
```

## 7. Performance Optimization Checklist

### 7.1 Profiling

Profile the following hotspots:
- State deep copy (if using deep copy strategy)
- Module invocation overhead (function call, serialization)
- Memory buffer queries (if filtering is complex)
- Event scheduler operations (heap push/pop)

### 7.2 Optimizations to Try (Phase 6)

1. **State Copy Optimization:** Replace deep copy with structural sharing
2. **Module Batching:** Invoke multiple modules in parallel (if thread-safe)
3. **Lazy Evaluation:** Compute derived state variables only when accessed
4. **Memory Buffer Indexing:** Add indices on frequently queried fields (event_type, timestamp)
5. **Delta Compression:** Store only changed variables in checkpoints

### 7.3 Performance Targets

- **Small simulation (10 modules):** > 1000 timesteps/second
- **Medium simulation (50 modules):** > 100 timesteps/second
- **Large simulation (100 modules):** > 10 timesteps/second

These are rough guidelines. Actual performance depends on module complexity.

## 8. Documentation and Testing Requirements

### 8.1 API Documentation

Generate API documentation for:
- `AgentState` structure
- `ModuleRegistration` interface
- `StateDelta` structure
- Core public methods (`run`, `step`, `checkpoint`, `restore`)

Use docstrings and auto-documentation tools (Sphinx, Doxygen, etc.).

### 8.2 Test Coverage

Achieve the following coverage:
- **Unit tests:** 100% of core state management, module invocation, error handling
- **Integration tests:** All phases of time-step execution with mock modules
- **Regression tests:** Known failure modes (module exception, state corruption, timeout)
- **Performance tests:** Timestep execution time under various module counts

### 8.3 Example Modules

Provide at least 3 example modules:
1. **NullModule:** Returns empty delta (tests no-op path)
2. **CounterModule:** Increments a counter variable each step (tests simple update)
3. **StochasticModule:** Uses RNG to update a variable (tests determinism)

## 9. Integration with Other Modules (Future)

### 9.1 Module Development Workflow

Once TQP Core is complete, external module developers should:
1. Read this specification and `data_contract.md`
2. Implement `ModuleRegistration` and `update_function`
3. Write unit tests for module in isolation
4. Integrate with TQP Core using example modules as templates
5. Run integration tests with other modules

### 9.2 Module Testing Framework

Provide a test harness:
```python
class ModuleTestHarness:
    def __init__(self, module: Module, core: TQPCore):
        self.module = module
        self.core = core
    
    def test_module(self, initial_state: AgentState, num_steps: int):
        self.core.initialize(initial_state)
        for _ in range(num_steps):
            self.core.step()
        return self.core.get_current_state()
```

### 9.3 Continuous Integration

Set up CI pipeline that:
- Runs all unit and integration tests on each commit
- Generates test coverage reports
- Benchmarks performance and flags regressions
- Validates example modules still work

## 10. Summary Checklist

Before declaring TQP Core complete:

- [ ] All Phase 1-6 deliverables implemented
- [ ] All unit and integration tests pass
- [ ] API documentation generated and reviewed
- [ ] Example modules demonstrate all features
- [ ] Performance meets targets (or limitations documented)
- [ ] Error handling covers all identified failure modes
- [ ] Checkpointing and deterministic replay verified
- [ ] Module developer guide written and reviewed
- [ ] Code reviewed by at least one other engineer
- [ ] Ready for handoff to external module development teams

**Estimated Total Effort:** 6-7 weeks for a single experienced engineer, or 4-5 weeks for a two-person team.
