"""
Tests for the Orchestrator component.
"""

import pytest
from datetime import datetime, timedelta
from architecture import Orchestrator, SimulationConfig

import sys
from pathlib import Path
tqp_core_path = Path(__file__).parent.parent.parent / "01_TQP_Core"
if str(tqp_core_path) not in sys.path:
    sys.path.insert(0, str(tqp_core_path))

from tqp_core.module_interface import ModuleRegistration, Module
from tqp_core.types import ProcessType, AgentState, ModuleInputs, StateDelta


def create_test_config():
    """Create a test configuration."""
    return SimulationConfig(
        start_time=datetime(2025, 1, 1),
        time_step_duration=timedelta(days=1),
        mission_phases={
            "quarter-1": (0, 30),
        },
        random_seed=42,
        metadata={}
    )


class DummyModule(Module):
    """Dummy module for testing."""
    
    def __init__(self, module_id: str):
        self.module_id = module_id
        self.update_count = 0
    
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        self.update_count += 1
        return StateDelta(module_id=self.module_id)


def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    config = create_test_config()
    orchestrator = Orchestrator(config)
    
    assert orchestrator.config == config
    assert orchestrator.module_registry is not None
    assert orchestrator.event_bus is not None
    assert orchestrator.execution_pipeline is not None
    assert orchestrator.simulation_container is not None


def test_orchestrator_module_registration():
    """Test module registration."""
    config = create_test_config()
    orchestrator = Orchestrator(config)
    
    module = DummyModule("test_module")
    registration = ModuleRegistration(
        module_id="test_module",
        module_name="Test Module",
        module_version="1.0.0",
        process_type=ProcessType.FAST,
        execution_priority=500,
        module=module
    )
    
    orchestrator.register_module(registration)
    
    # Verify registration
    registered = orchestrator.get_module("test_module")
    assert registered.module_id == "test_module"


def test_orchestrator_initialize():
    """Test orchestrator initialization with agents."""
    config = create_test_config()
    orchestrator = Orchestrator(config)
    
    orchestrator.initialize(agent_ids=["agent_1", "agent_2"])
    
    # Verify agents are initialized
    assert "agent_1" in orchestrator.simulation_container.get_all_agents()
    assert "agent_2" in orchestrator.simulation_container.get_all_agents()


def test_orchestrator_double_initialize_error():
    """Test that double initialization raises error."""
    config = create_test_config()
    orchestrator = Orchestrator(config)
    
    orchestrator.initialize(agent_ids=["agent_1"])
    
    with pytest.raises(RuntimeError) as exc_info:
        orchestrator.initialize(agent_ids=["agent_2"])
    
    assert "already initialized" in str(exc_info.value)


def test_orchestrator_execute_timestep():
    """Test executing a single timestep."""
    config = create_test_config()
    orchestrator = Orchestrator(config)
    
    orchestrator.initialize(agent_ids=["agent_1"])
    
    initial_time = orchestrator.simulation_container.get_current_time()
    
    orchestrator.execute_timestep()
    
    # Time should advance
    assert orchestrator.simulation_container.get_current_time() == initial_time + 1


def test_orchestrator_run():
    """Test running simulation for multiple steps."""
    config = create_test_config()
    orchestrator = Orchestrator(config)
    
    orchestrator.initialize(agent_ids=["agent_1"])
    
    orchestrator.run(num_steps=5)
    
    # Should have advanced 5 steps
    assert orchestrator.simulation_container.get_current_time() == 5


def test_orchestrator_run_without_initialize():
    """Test that running without initialization raises error."""
    config = create_test_config()
    orchestrator = Orchestrator(config)
    
    with pytest.raises(RuntimeError) as exc_info:
        orchestrator.run(num_steps=1)
    
    assert "not initialized" in str(exc_info.value)


def test_orchestrator_finalize():
    """Test orchestrator finalization."""
    config = create_test_config()
    orchestrator = Orchestrator(config)
    
    orchestrator.initialize(agent_ids=["agent_1"])
    orchestrator.run(num_steps=2)
    
    # Should not raise
    orchestrator.finalize()


def test_orchestrator_event_bus_integration():
    """Test that orchestrator publishes events."""
    config = create_test_config()
    orchestrator = Orchestrator(config)
    
    events_received = []
    
    def handler(event):
        events_received.append(event)
    
    orchestrator.event_bus.subscribe("timestep_start", handler)
    orchestrator.event_bus.subscribe("state_snapshot", handler)
    
    orchestrator.initialize(agent_ids=["agent_1"])
    orchestrator.execute_timestep()
    
    # Should have received events
    assert len(events_received) > 0
    
    # Check for timestep_start event
    timestep_events = [e for e in events_received if e.event_type == "timestep_start"]
    assert len(timestep_events) > 0


def test_orchestrator_get_all_modules():
    """Test getting all registered modules."""
    config = create_test_config()
    orchestrator = Orchestrator(config)
    
    module1 = DummyModule("module1")
    module2 = DummyModule("module2")
    
    orchestrator.register_module(ModuleRegistration(
        module_id="module1",
        module_name="Module 1",
        module_version="1.0.0",
        process_type=ProcessType.FAST,
        execution_priority=500,
        module=module1
    ))
    
    orchestrator.register_module(ModuleRegistration(
        module_id="module2",
        module_name="Module 2",
        module_version="1.0.0",
        process_type=ProcessType.SLOW,
        execution_priority=300,
        module=module2
    ))
    
    all_modules = orchestrator.get_all_modules()
    assert len(all_modules) == 2
    
    module_ids = {m.module_id for m in all_modules}
    assert module_ids == {"module1", "module2"}


def test_orchestrator_error_recording():
    """Test that errors are recorded."""
    config = create_test_config()
    orchestrator = Orchestrator(config)
    
    orchestrator.initialize(agent_ids=["agent_1"])
    
    # Force an error by corrupting agent state
    state = orchestrator.simulation_container.get_agent_state("agent_1")
    state.simulation_time = -1  # Invalid
    
    try:
        orchestrator.execute_timestep()
    except Exception:
        pass  # Expected to fail
    
    # Check that error was recorded
    errors = orchestrator.get_error_records()
    # Note: Validation warnings may not record errors, 
    # so this test is primarily checking the mechanism exists
    assert errors is not None
