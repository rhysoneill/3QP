"""
Example modules demonstrating the TQP Core module interface.

These modules serve as templates for module developers and test cases for the core.
"""

from tqp_core import (
    Module, AgentState, StateDelta, ModuleInputs,
    MemoryRecord, GoalObject
)


class NullModule(Module):
    """
    Example module that makes no state changes.
    
    Useful for testing the no-op path through the core.
    """
    
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        """Return empty delta."""
        return StateDelta(module_id=module_inputs.module_id)


class CounterModule(Module):
    """
    Example module that increments a counter variable each step.
    
    Demonstrates simple state variable updates.
    """
    
    def __init__(self, module_id: str = "counter"):
        self.module_id = module_id
    
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        """Increment counter variable."""
        current_value = current_state.internal_vars.get(f"{self.module_id}.count", 0)
        
        return StateDelta(
            module_id=self.module_id,
            internal_var_updates={
                f"{self.module_id}.count": current_value + 1
            }
        )


class MemoryLoggerModule(Module):
    """
    Example module that logs events to memory buffer.
    
    Demonstrates memory record creation.
    """
    
    def __init__(self, module_id: str = "memory_logger"):
        self.module_id = module_id
    
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        """Add a memory record each time-step."""
        memory = MemoryRecord(
            timestamp=current_state.simulation_time,
            event_type="timestep_marker",
            event_data={
                "simulation_time": current_state.simulation_time,
                "phase": module_inputs.timestep_metadata.mission_phase
            },
            source_module=self.module_id,
            salience=0.5
        )
        
        return StateDelta(
            module_id=self.module_id,
            memory_additions=[memory]
        )


class StochasticModule(Module):
    """
    Example module that uses RNG for probabilistic updates.
    
    Demonstrates deterministic randomness using core-provided RNG.
    """
    
    def __init__(self, module_id: str = "stochastic", core_rng=None):
        self.module_id = module_id
        self.core_rng = core_rng
    
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        """Update variable with random value."""
        if self.core_rng is None:
            import random
            value = random.uniform(0, 1)
        else:
            value = self.core_rng.uniform(0, 1)
        
        return StateDelta(
            module_id=self.module_id,
            internal_var_updates={
                f"{self.module_id}.random_value": value
            }
        )


class GoalManagerModule(Module):
    """
    Example module that manages agent goals.
    
    Demonstrates goal creation, updating, and deletion.
    """
    
    def __init__(self, module_id: str = "goal_manager"):
        self.module_id = module_id
        self._step_count = 0
    
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        """Manage goals based on simulation time."""
        self._step_count += 1
        goal_updates = {}
        
        # Add a new goal every 10 steps
        if self._step_count % 10 == 0:
            goal = GoalObject(
                goal_id=f"goal_{self._step_count}",
                goal_type="test_goal",
                priority=0.5,
                goal_data={"created_at": current_state.simulation_time}
            )
            goal_updates[goal.goal_id] = goal
        
        # Remove old goals (older than 30 steps)
        for goal in current_state.goal_state:
            created_at = goal.goal_data.get("created_at", 0)
            if current_state.simulation_time - created_at > 30:
                goal_updates[goal.goal_id] = None  # Delete
        
        return StateDelta(
            module_id=self.module_id,
            goal_updates=goal_updates if goal_updates else None
        )


class ResourceModule(Module):
    """
    Example module that manages resource levels.
    
    Demonstrates additive resource updates.
    """
    
    def __init__(self, module_id: str = "resource"):
        self.module_id = module_id
    
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        """Update resource levels."""
        # Deplete energy, restore on day boundaries
        energy_delta = 5.0 if module_inputs.timestep_metadata.is_day_start else -1.0
        
        return StateDelta(
            module_id=self.module_id,
            resource_updates={
                "energy": energy_delta,
                "cognitive_load": -0.5  # Slight recovery
            }
        )


class MessageSenderModule(Module):
    """
    Example module that sends inter-module messages.
    
    Demonstrates message passing.
    """
    
    def __init__(self, module_id: str = "sender", target_module: str = "receiver"):
        self.module_id = module_id
        self.target_module = target_module
    
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        """Send a message every 5 steps."""
        from tqp_core import MessageRequest
        
        if current_state.simulation_time % 5 == 0:
            message = MessageRequest(
                to_module=self.target_module,
                message_type="ping",
                message_payload={"timestamp": current_state.simulation_time}
            )
            
            return StateDelta(
                module_id=self.module_id,
                inter_module_messages=[message]
            )
        
        return StateDelta(module_id=self.module_id)


class MessageReceiverModule(Module):
    """
    Example module that receives and processes inter-module messages.
    """
    
    def __init__(self, module_id: str = "receiver"):
        self.module_id = module_id
        self.messages_received = 0
    
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        """Count received messages."""
        self.messages_received += len(module_inputs.inter_module_messages)
        
        return StateDelta(
            module_id=self.module_id,
            internal_var_updates={
                f"{self.module_id}.messages_received": self.messages_received
            }
        )
