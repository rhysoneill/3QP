"""
Demonstration of TQP Core functionality.

This script shows how to:
1. Configure and initialize the core
2. Register modules
3. Run a simulation
4. Observe state evolution
"""

from datetime import datetime
from tqp_core import (
    TQPCore, SimulationConfig, ModuleRegistration,
    ProcessType, AgentState
)
from examples.example_modules import (
    CounterModule, MemoryLoggerModule, ResourceModule,
    MessageSenderModule, MessageReceiverModule
)


def main():
    print("=" * 70)
    print("TQP Core Demonstration")
    print("=" * 70)
    print()
    
    # Step 1: Create configuration
    print("Step 1: Creating simulation configuration...")
    config = SimulationConfig(
        mission_start_datetime=datetime(2025, 1, 1, 0, 0, 0),
        timestep_duration_minutes=60,  # 1-hour timesteps
        total_timesteps=168,  # One week
        random_seed=42,
        checkpoint_frequency=24,  # Daily checkpoints
        max_memory_buffer_size=500
    )
    print(f"  - Mission start: {config.mission_start_datetime}")
    print(f"  - Timestep duration: {config.timestep_duration_minutes} minutes")
    print(f"  - Total timesteps: {config.total_timesteps}")
    print()
    
    # Step 2: Create core
    print("Step 2: Initializing TQP Core...")
    core = TQPCore(config, agent_id="demo_agent")
    print(f"  - Agent ID: {core.agent_id}")
    print()
    
    # Step 3: Register modules
    print("Step 3: Registering modules...")
    
    # Counter module (fast process)
    counter = CounterModule("counter")
    core.register_module(ModuleRegistration(
        module_id="counter",
        module_name="Step Counter",
        module_version="1.0.0",
        process_type=ProcessType.FAST,
        execution_priority=100,
        module=counter
    ))
    print("  ✓ Registered Counter Module (fast, priority 100)")
    
    # Memory logger (fast process)
    logger = MemoryLoggerModule("logger")
    core.register_module(ModuleRegistration(
        module_id="logger",
        module_name="Memory Logger",
        module_version="1.0.0",
        process_type=ProcessType.FAST,
        execution_priority=90,
        module=logger
    ))
    print("  ✓ Registered Memory Logger Module (fast, priority 90)")
    
    # Resource manager (slow process)
    resource = ResourceModule("resource")
    core.register_module(ModuleRegistration(
        module_id="resource",
        module_name="Resource Manager",
        module_version="1.0.0",
        process_type=ProcessType.SLOW,  # Only runs on day boundaries
        execution_priority=80,
        module=resource
    ))
    print("  ✓ Registered Resource Module (slow, priority 80)")
    
    # Message sender and receiver
    sender = MessageSenderModule("sender", "receiver")
    receiver = MessageReceiverModule("receiver")
    
    core.register_module(ModuleRegistration(
        module_id="sender",
        module_name="Message Sender",
        module_version="1.0.0",
        process_type=ProcessType.FAST,
        execution_priority=110,
        module=sender
    ))
    print("  ✓ Registered Message Sender Module (fast, priority 110)")
    
    core.register_module(ModuleRegistration(
        module_id="receiver",
        module_name="Message Receiver",
        module_version="1.0.0",
        process_type=ProcessType.FAST,
        execution_priority=70,
        module=receiver
    ))
    print("  ✓ Registered Message Receiver Module (fast, priority 70)")
    print()
    
    # Step 4: Initialize with custom state
    print("Step 4: Initializing agent state...")
    initial_state = AgentState(
        agent_id="demo_agent",
        simulation_time=0,
        calendar_time=config.mission_start_datetime,
        state_version=0,
        resource_state={
            "energy": 100.0,
            "cognitive_load": 0.0
        }
    )
    core.initialize(initial_state)
    print("  ✓ Agent state initialized")
    print()
    
    # Step 5: Add observers
    print("Step 5: Adding observers...")
    timestep_count = [0]
    
    def timestep_observer(event):
        timestep_count[0] += 1
        if timestep_count[0] % 24 == 0:  # Report daily
            print(f"  Day {timestep_count[0] // 24} completed "
                  f"(timestep {event.simulation_time}, "
                  f"{event.elapsed_wall_time_ms:.2f}ms)")
    
    core.add_timestep_observer(timestep_observer)
    print("  ✓ Observers registered")
    print()
    
    # Step 6: Run simulation
    print("Step 6: Running simulation...")
    print(f"  Simulating {config.total_timesteps} timesteps...")
    print()
    
    core.run(num_steps=config.total_timesteps)
    
    print()
    print("  ✓ Simulation complete")
    print()
    
    # Step 7: Report results
    print("Step 7: Final state summary")
    print("-" * 70)
    
    final_state = core.get_current_state()
    
    print(f"Final simulation time: {final_state.simulation_time}")
    print(f"Final calendar time: {final_state.calendar_time}")
    print(f"State version: {final_state.state_version}")
    print()
    
    print("Internal variables:")
    for key, value in sorted(final_state.internal_vars.items()):
        print(f"  {key}: {value}")
    print()
    
    print("Resource state:")
    for key, value in sorted(final_state.resource_state.items()):
        print(f"  {key}: {value:.2f}")
    print()
    
    print(f"Memory buffer size: {len(final_state.memory_buffer)}")
    print(f"Goals: {len(final_state.goal_state)}")
    print()
    
    print("=" * 70)
    print("Demonstration complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
