"""
Demo script for Module 03: Architecture Overview

This script demonstrates the core functionality of the Architecture module
including orchestration, event handling, and simulation execution.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add module paths
module_root = Path(__file__).parent
architecture_path = module_root
tqp_core_path = module_root.parent / "01_TQP_Core"

# Ensure paths are added in correct order
if str(tqp_core_path) not in sys.path:
    sys.path.insert(0, str(tqp_core_path))
if str(architecture_path) not in sys.path:
    sys.path.insert(0, str(architecture_path))

from architecture import (
    Orchestrator,
    EventBus,
    ExecutionPipeline,
    SimulationContainer,
    SimulationConfig,
    ExecutionPhase,
    Event
)

from tqp_core.module_interface import ModuleRegistration, Module, LifecycleHooks
from tqp_core.types import ProcessType, AgentState, ModuleInputs, StateDelta


def demo_event_bus():
    """Demonstrate EventBus functionality."""
    print("\n" + "="*60)
    print("DEMO 1: EventBus - Publish/Subscribe Communication")
    print("="*60)
    
    bus = EventBus()
    
    # Subscribe to events
    events_received = []
    
    def handler(event: Event):
        events_received.append(event)
        print(f"  📨 Received: {event.event_type} from {event.source_module}")
        print(f"     Payload: {event.payload}")
    
    bus.subscribe("test_event", handler)
    bus.subscribe("breakthrough", handler)
    
    # Publish events
    print("\nPublishing events...")
    
    event1 = Event(
        event_type="test_event",
        source_module="demo",
        payload={"message": "Hello, EventBus!"}
    )
    bus.publish(event1)
    
    event2 = Event(
        event_type="breakthrough",
        source_module="tqp_core",
        payload={"agent_id": "agent_1", "magnitude": 0.85}
    )
    bus.publish(event2)
    
    print(f"\n✓ Total events received: {len(events_received)}")
    print(f"✓ Event history size: {len(bus.get_history())}")
    print(f"✓ Event types with subscribers: {bus.get_all_event_types()}")


def demo_execution_pipeline():
    """Demonstrate ExecutionPipeline functionality."""
    print("\n" + "="*60)
    print("DEMO 2: ExecutionPipeline - Phase Sequencing")
    print("="*60)
    
    pipeline = ExecutionPipeline()
    
    # Register handlers for different phases
    print("\nRegistering phase handlers...")
    
    execution_log = []
    
    def make_handler(phase_name):
        def handler():
            execution_log.append(phase_name)
            print(f"  ▶ Executing: {phase_name}")
        return handler
    
    pipeline.register_handler(
        ExecutionPhase.PRE_STEP_SETUP,
        "demo",
        make_handler("Pre-Step Setup"),
        "Initialize time step"
    )
    
    pipeline.register_handler(
        ExecutionPhase.CORE_TEMPORAL_UPDATE,
        "demo",
        make_handler("Core Temporal Update"),
        "Update breakthrough probability"
    )
    
    pipeline.register_handler(
        ExecutionPhase.PHYSIOLOGICAL_UPDATE,
        "demo",
        make_handler("Physiological Update"),
        "Update physiology state"
    )
    
    pipeline.register_handler(
        ExecutionPhase.COGNITIVE_UPDATE,
        "demo",
        make_handler("Cognitive Update"),
        "Update BDI state"
    )
    
    pipeline.register_handler(
        ExecutionPhase.STATE_LOGGING,
        "demo",
        make_handler("State Logging"),
        "Log all states"
    )
    
    # Execute timestep
    print("\nExecuting time step...")
    pipeline.execute_timestep()
    
    print(f"\n✓ Executed {len(execution_log)} phases")
    print(f"✓ Phases executed in order: {', '.join(execution_log)}")


def demo_simulation_container():
    """Demonstrate SimulationContainer functionality."""
    print("\n" + "="*60)
    print("DEMO 3: SimulationContainer - Agent Lifecycle")
    print("="*60)
    
    config = SimulationConfig(
        start_time=datetime(2025, 1, 1),
        time_step_duration=timedelta(days=1),
        mission_phases={
            "quarter-1": (0, 30),
            "quarter-2": (31, 60),
        },
        random_seed=42,
        metadata={"demo": "simulation_container"}
    )
    
    container = SimulationContainer(config)
    
    # Track lifecycle events
    lifecycle_events = []
    
    hooks = LifecycleHooks()
    hooks.on_initialize = lambda cfg: lifecycle_events.append(f"Initialize: {cfg.get('demo')}")
    hooks.on_day_start = lambda state: lifecycle_events.append(f"Day start: t={state.simulation_time}")
    
    container.register_lifecycle_hooks(hooks)
    
    print("\nInitializing container...")
    container.initialize({"demo": "test"})
    
    print("\nInitializing agents...")
    container.initialize_agent("agent_alpha")
    container.initialize_agent("agent_beta")
    
    print(f"  Agents: {container.get_all_agents()}")
    
    print("\nAdvancing time...")
    for i in range(3):
        container.advance_time()
        print(f"  Step {i+1}: t={container.get_current_time()}, "
              f"{container.get_current_calendar_time().strftime('%Y-%m-%d')}")
    
    print("\nTimestep metadata:")
    metadata = container.get_timestep_metadata()
    print(f"  Mission phase: {metadata.mission_phase}")
    print(f"  Phase day: {metadata.phase_day_number}")
    print(f"  Week start: {metadata.is_week_start}")
    
    print(f"\n✓ Lifecycle events: {len(lifecycle_events)}")
    for event in lifecycle_events:
        print(f"  - {event}")
    
    container.finalize()


class SimpleModule(Module):
    """Simple demo module."""
    
    def __init__(self, module_id: str):
        self.module_id = module_id
        self.update_count = 0
    
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        self.update_count += 1
        return StateDelta(
            module_id=self.module_id,
            internal_var_updates={f"{self.module_id}_updates": self.update_count}
        )


def demo_orchestrator():
    """Demonstrate full Orchestrator functionality."""
    print("\n" + "="*60)
    print("DEMO 4: Orchestrator - Complete Integration")
    print("="*60)
    
    config = SimulationConfig(
        start_time=datetime(2025, 1, 1),
        time_step_duration=timedelta(days=1),
        mission_phases={
            "quarter-1": (0, 10),
        },
        random_seed=123,
        metadata={"experiment": "demo"}
    )
    
    orchestrator = Orchestrator(config)
    
    # Register modules
    print("\nRegistering modules...")
    
    module1 = SimpleModule("module_a")
    registration1 = ModuleRegistration(
        module_id="module_a",
        module_name="Module A",
        module_version="1.0.0",
        process_type=ProcessType.FAST,
        execution_priority=500,
        module=module1
    )
    orchestrator.register_module(registration1)
    print("  ✓ Registered: module_a")
    
    module2 = SimpleModule("module_b")
    registration2 = ModuleRegistration(
        module_id="module_b",
        module_name="Module B",
        module_version="1.0.0",
        process_type=ProcessType.SLOW,
        execution_priority=300,
        module=module2
    )
    orchestrator.register_module(registration2)
    print("  ✓ Registered: module_b")
    
    # Subscribe to events
    event_count = [0]
    
    def event_handler(event: Event):
        event_count[0] += 1
    
    orchestrator.event_bus.subscribe("timestep_start", event_handler)
    orchestrator.event_bus.subscribe("state_snapshot", event_handler)
    
    # Initialize
    print("\nInitializing simulation...")
    orchestrator.initialize(agent_ids=["agent_1", "agent_2"])
    print(f"  Agents: {orchestrator.simulation_container.get_all_agents()}")
    
    # Run
    print("\nRunning simulation for 5 steps...")
    orchestrator.run(num_steps=5)
    
    print(f"\n✓ Final simulation time: {orchestrator.simulation_container.get_current_time()}")
    print(f"✓ Events published: {event_count[0]}")
    print(f"✓ Registered modules: {len(orchestrator.get_all_modules())}")
    
    # Check agent states
    print("\nAgent final states:")
    for agent_id in orchestrator.simulation_container.get_all_agents():
        state = orchestrator.simulation_container.get_agent_state(agent_id)
        print(f"  {agent_id}:")
        print(f"    - Simulation time: {state.simulation_time}")
        print(f"    - State version: {state.state_version}")
        print(f"    - Internal vars: {state.internal_vars}")
    
    # Finalize
    orchestrator.finalize()
    
    print("\n✓ Orchestrator finalized successfully")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("Module 03: Architecture Overview - Demonstration")
    print("="*60)
    print("\nThis demo showcases the four main components:")
    print("  1. EventBus - Publish/subscribe event system")
    print("  2. ExecutionPipeline - Phase-based execution sequencing")
    print("  3. SimulationContainer - Agent lifecycle management")
    print("  4. Orchestrator - Complete system integration")
    
    try:
        demo_event_bus()
        demo_execution_pipeline()
        demo_simulation_container()
        demo_orchestrator()
        
        print("\n" + "="*60)
        print("✓ All demos completed successfully!")
        print("="*60)
        print("\nThe Architecture module is working correctly.")
        print("Ready for integration with behavioral modules.")
        print()
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
