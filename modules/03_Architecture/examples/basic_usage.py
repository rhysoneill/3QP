"""
Example demonstrating the Architecture module usage.

This example shows how to:
1. Configure and initialize the orchestrator
2. Register modules
3. Run a simulation
4. Subscribe to events
5. Access simulation results
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add paths
architecture_path = Path(__file__).parent.parent
tqp_core_path = architecture_path.parent / "01_TQP_Core"
sys.path.insert(0, str(architecture_path))
sys.path.insert(0, str(tqp_core_path))

from architecture import Orchestrator, SimulationConfig, Event
from tqp_core.module_interface import ModuleRegistration, Module, LifecycleHooks
from tqp_core.types import ProcessType, AgentState, ModuleInputs, StateDelta


# Example module implementation
class ExamplePhysiologyModule(Module):
    """
    Example physiology module demonstrating module interface.
    """
    
    def __init__(self):
        self.initialized = False
    
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        """
        Update physiology state.
        
        In a real implementation, this would:
        - Read current physiological state
        - Apply physiological dynamics
        - Return state updates
        """
        # Example: Update a simple fatigue metric
        current_fatigue = current_state.internal_vars.get("fatigue", 0.0)
        
        # Fatigue accumulates over time
        new_fatigue = min(1.0, current_fatigue + 0.01)
        
        return StateDelta(
            module_id="physiology",
            internal_var_updates={"fatigue": new_fatigue}
        )
    
    def get_dependencies(self) -> list[str]:
        """This module depends on TQP Core for temporal context."""
        return ["tqp_core"]


class ExampleCognitiveModule(Module):
    """
    Example cognitive module.
    """
    
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        """
        Update cognitive state.
        
        In a real implementation, this would:
        - Process beliefs, desires, intentions
        - Select actions
        - Update cognitive state
        """
        # Example: Simple decision-making based on fatigue
        fatigue = current_state.internal_vars.get("fatigue", 0.0)
        
        # High fatigue reduces cognitive capacity
        cognitive_capacity = max(0.0, 1.0 - fatigue)
        
        return StateDelta(
            module_id="cognitive",
            internal_var_updates={"cognitive_capacity": cognitive_capacity}
        )
    
    def get_dependencies(self) -> list[str]:
        """Depends on physiology for fatigue state."""
        return ["physiology"]


def create_lifecycle_hooks():
    """Create example lifecycle hooks."""
    hooks = LifecycleHooks()
    
    hooks.on_initialize = lambda cfg: print(f"Module initialized with config: {cfg}")
    hooks.on_finalize = lambda: print("Module finalized")
    
    return hooks


def main():
    """Run the example simulation."""
    print("=== 3QP Architecture Example ===\n")
    
    # 1. Configure simulation
    print("1. Configuring simulation...")
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
        metadata={"experiment_id": "example_001"}
    )
    print(f"   Start time: {config.start_time}")
    print(f"   Random seed: {config.random_seed}\n")
    
    # 2. Create orchestrator
    print("2. Creating orchestrator...")
    orchestrator = Orchestrator(config)
    print("   Orchestrator created\n")
    
    # 3. Register modules
    print("3. Registering modules...")
    
    # Register physiology module
    physiology_module = ExamplePhysiologyModule()
    physiology_registration = ModuleRegistration(
        module_id="physiology",
        module_name="Example Physiology",
        module_version="1.0.0",
        process_type=ProcessType.SLOW,
        execution_priority=400,
        module=physiology_module,
        lifecycle_hooks=create_lifecycle_hooks()
    )
    orchestrator.register_module(physiology_registration)
    print("   Registered: physiology")
    
    # Register cognitive module
    cognitive_module = ExampleCognitiveModule()
    cognitive_registration = ModuleRegistration(
        module_id="cognitive",
        module_name="Example Cognitive",
        module_version="1.0.0",
        process_type=ProcessType.FAST,
        execution_priority=300,
        module=cognitive_module,
        lifecycle_hooks=create_lifecycle_hooks()
    )
    orchestrator.register_module(cognitive_registration)
    print("   Registered: cognitive\n")
    
    # 4. Subscribe to events
    print("4. Subscribing to events...")
    
    timestep_count = [0]
    
    def on_timestep_start(event: Event):
        timestep_count[0] += 1
        sim_time = event.payload.get("simulation_time", 0)
        print(f"   Timestep {sim_time} started")
    
    def on_state_snapshot(event: Event):
        agent_id = event.payload.get("agent_id")
        sim_time = event.payload.get("simulation_time")
        # print(f"   State snapshot: {agent_id} at t={sim_time}")
    
    orchestrator.event_bus.subscribe("timestep_start", on_timestep_start)
    orchestrator.event_bus.subscribe("state_snapshot", on_state_snapshot)
    print("   Event handlers subscribed\n")
    
    # 5. Initialize simulation
    print("5. Initializing simulation...")
    orchestrator.initialize(
        agent_ids=["agent_alpha", "agent_beta"],
        config_data={"simulation_mode": "example"}
    )
    print("   Simulation initialized with 2 agents\n")
    
    # 6. Run simulation
    print("6. Running simulation for 10 steps...")
    print("-" * 40)
    orchestrator.run(num_steps=10)
    print("-" * 40)
    print("   Simulation completed\n")
    
    # 7. Analyze results
    print("7. Analyzing results...")
    
    for agent_id in orchestrator.simulation_container.get_all_agents():
        state = orchestrator.simulation_container.get_agent_state(agent_id)
        fatigue = state.internal_vars.get("fatigue", 0.0)
        capacity = state.internal_vars.get("cognitive_capacity", 1.0)
        
        print(f"   {agent_id}:")
        print(f"     - Fatigue: {fatigue:.3f}")
        print(f"     - Cognitive capacity: {capacity:.3f}")
        print(f"     - State version: {state.state_version}")
    
    print()
    
    # 8. Event statistics
    print("8. Event statistics...")
    history = orchestrator.event_bus.get_history()
    print(f"   Total events: {len(history)}")
    
    event_types = {}
    for event in history:
        event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
    
    for event_type, count in event_types.items():
        print(f"   - {event_type}: {count}")
    
    print()
    
    # 9. Finalize
    print("9. Finalizing simulation...")
    orchestrator.finalize()
    print("   Simulation finalized\n")
    
    # 10. Error check
    errors = orchestrator.get_error_records()
    if errors:
        print(f"⚠️  {len(errors)} errors occurred during simulation")
    else:
        print("✓ Simulation completed without errors")
    
    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
