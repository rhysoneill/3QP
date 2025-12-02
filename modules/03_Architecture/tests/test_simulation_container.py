"""
Tests for the SimulationContainer component.
"""

import pytest
from datetime import datetime, timedelta
from architecture import SimulationContainer, SimulationConfig

import sys
from pathlib import Path
tqp_core_path = Path(__file__).parent.parent.parent / "01_TQP_Core"
if str(tqp_core_path) not in sys.path:
    sys.path.insert(0, str(tqp_core_path))

from tqp_core.module_interface import LifecycleHooks


def create_test_config():
    """Create a test configuration."""
    return SimulationConfig(
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


def test_container_initialization():
    """Test basic container initialization."""
    config = create_test_config()
    container = SimulationContainer(config)
    
    assert container.config == config
    assert container.get_current_time() == 0
    assert container.get_current_calendar_time() == datetime(2025, 1, 1)


def test_container_agent_initialization():
    """Test agent initialization."""
    config = create_test_config()
    container = SimulationContainer(config)
    
    container.initialize_agent("agent_1")
    
    assert "agent_1" in container.get_all_agents()
    
    state = container.get_agent_state("agent_1")
    assert state.agent_id == "agent_1"
    assert state.simulation_time == 0
    assert state.state_version == 0


def test_container_duplicate_agent_error():
    """Test that duplicate agent initialization raises error."""
    config = create_test_config()
    container = SimulationContainer(config)
    
    container.initialize_agent("agent_1")
    
    with pytest.raises(ValueError) as exc_info:
        container.initialize_agent("agent_1")
    
    assert "already initialized" in str(exc_info.value)


def test_container_time_advancement():
    """Test time advancement."""
    config = create_test_config()
    container = SimulationContainer(config)
    container.initialize_agent("agent_1")
    
    initial_time = container.get_current_time()
    initial_calendar = container.get_current_calendar_time()
    
    container.advance_time()
    
    assert container.get_current_time() == initial_time + 1
    assert container.get_current_calendar_time() == initial_calendar + timedelta(days=1)
    
    # Agent state should be updated
    state = container.get_agent_state("agent_1")
    assert state.simulation_time == 1
    assert state.state_version == 1


def test_container_lifecycle_hooks():
    """Test lifecycle hook invocation."""
    config = create_test_config()
    container = SimulationContainer(config)
    
    hook_calls = []
    
    hooks = LifecycleHooks()
    hooks.on_initialize = lambda cfg: hook_calls.append(("init", cfg))
    hooks.on_finalize = lambda: hook_calls.append(("finalize",))
    
    container.register_lifecycle_hooks(hooks)
    
    # Initialize
    container.initialize({"test": "data"})
    assert len(hook_calls) == 1
    assert hook_calls[0][0] == "init"
    assert hook_calls[0][1]["test"] == "data"
    
    # Finalize
    container.finalize()
    assert len(hook_calls) == 2
    assert hook_calls[1] == ("finalize",)


def test_container_day_start_hooks():
    """Test day start lifecycle hooks."""
    config = create_test_config()
    container = SimulationContainer(config)
    container.initialize_agent("agent_1")
    
    day_starts = []
    
    hooks = LifecycleHooks()
    hooks.on_day_start = lambda state: day_starts.append(state.simulation_time)
    
    container.register_lifecycle_hooks(hooks)
    
    # Advance time
    container.advance_time()
    
    assert len(day_starts) == 1
    assert day_starts[0] == 1


def test_container_week_start_hooks():
    """Test week start lifecycle hooks."""
    config = create_test_config()
    container = SimulationContainer(config)
    container.initialize_agent("agent_1")
    
    week_starts = []
    
    hooks = LifecycleHooks()
    hooks.on_week_start = lambda state: week_starts.append(state.simulation_time)
    
    container.register_lifecycle_hooks(hooks)
    
    # Advance to day 7 (week start)
    for _ in range(7):
        container.advance_time()
    
    # Week start should trigger on day 7
    assert 7 in week_starts


def test_container_timestep_metadata():
    """Test timestep metadata generation."""
    config = create_test_config()
    container = SimulationContainer(config)
    
    # Start of quarter 1
    metadata = container.get_timestep_metadata()
    assert metadata.mission_phase == "quarter-1"
    assert metadata.phase_day_number == 1
    
    # Advance to quarter 2
    for _ in range(31):
        container.advance_time()
    
    metadata = container.get_timestep_metadata()
    assert metadata.mission_phase == "quarter-2"
    assert metadata.phase_day_number == 1


def test_container_agent_state_validation():
    """Test agent state validation."""
    config = create_test_config()
    container = SimulationContainer(config)
    container.initialize_agent("agent_1")
    
    # Initially valid
    validation_results = container.validate_all_agents()
    assert len(validation_results) == 0
    
    # Corrupt state
    state = container.get_agent_state("agent_1")
    state.resource_state["test_resource"] = -1.0  # Negative resource (invalid)
    
    validation_results = container.validate_all_agents()
    assert "agent_1" in validation_results
    assert len(validation_results["agent_1"]) > 0


def test_container_get_nonexistent_agent():
    """Test that getting nonexistent agent raises error."""
    config = create_test_config()
    container = SimulationContainer(config)
    
    with pytest.raises(KeyError):
        container.get_agent_state("nonexistent")
