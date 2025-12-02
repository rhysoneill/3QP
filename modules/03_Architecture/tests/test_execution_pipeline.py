"""
Tests for the ExecutionPipeline component.
"""

import pytest
from architecture import ExecutionPipeline, ExecutionPhase


def test_pipeline_phase_execution_order():
    """Test that phases execute in correct order."""
    pipeline = ExecutionPipeline()
    execution_order = []
    
    # Register handlers for different phases
    for phase in ExecutionPhase:
        def make_handler(p):
            return lambda: execution_order.append(p)
        
        pipeline.register_handler(
            phase,
            "test_module",
            make_handler(phase),
            f"Test handler for {phase.name}"
        )
    
    # Enable validation phase (disabled by default)
    pipeline.enable_phase(ExecutionPhase.POST_STEP_VALIDATION)
    
    # Execute timestep
    pipeline.execute_timestep()
    
    # Verify phases executed in order
    expected_order = list(ExecutionPhase)
    assert execution_order == expected_order


def test_pipeline_multiple_handlers_per_phase():
    """Test that multiple handlers in same phase all execute."""
    pipeline = ExecutionPipeline()
    executions = []
    
    pipeline.register_handler(
        ExecutionPhase.PRE_STEP_SETUP,
        "module1",
        lambda: executions.append("handler1"),
        "Handler 1"
    )
    
    pipeline.register_handler(
        ExecutionPhase.PRE_STEP_SETUP,
        "module2",
        lambda: executions.append("handler2"),
        "Handler 2"
    )
    
    pipeline.execute_phase(ExecutionPhase.PRE_STEP_SETUP)
    
    assert len(executions) == 2
    assert "handler1" in executions
    assert "handler2" in executions


def test_pipeline_disable_phase():
    """Test disabling a phase."""
    pipeline = ExecutionPipeline()
    executed = []
    
    pipeline.register_handler(
        ExecutionPhase.COGNITIVE_UPDATE,
        "test",
        lambda: executed.append("cognitive"),
        "Test"
    )
    
    # Execute with phase enabled
    pipeline.execute_phase(ExecutionPhase.COGNITIVE_UPDATE)
    assert len(executed) == 1
    
    # Disable phase and execute again
    pipeline.disable_phase(ExecutionPhase.COGNITIVE_UPDATE)
    pipeline.execute_phase(ExecutionPhase.COGNITIVE_UPDATE)
    
    assert len(executed) == 1  # No additional execution


def test_pipeline_enable_phase():
    """Test enabling a disabled phase."""
    pipeline = ExecutionPipeline()
    executed = []
    
    pipeline.register_handler(
        ExecutionPhase.POST_STEP_VALIDATION,
        "test",
        lambda: executed.append("validation"),
        "Test"
    )
    
    # POST_STEP_VALIDATION is disabled by default
    pipeline.execute_phase(ExecutionPhase.POST_STEP_VALIDATION)
    assert len(executed) == 0
    
    # Enable and execute
    pipeline.enable_phase(ExecutionPhase.POST_STEP_VALIDATION)
    pipeline.execute_phase(ExecutionPhase.POST_STEP_VALIDATION)
    
    assert len(executed) == 1


def test_pipeline_error_propagation():
    """Test that errors in handlers are propagated."""
    pipeline = ExecutionPipeline()
    
    def failing_handler():
        raise ValueError("Handler error")
    
    pipeline.register_handler(
        ExecutionPhase.CORE_TEMPORAL_UPDATE,
        "test",
        failing_handler,
        "Failing handler"
    )
    
    with pytest.raises(RuntimeError) as exc_info:
        pipeline.execute_phase(ExecutionPhase.CORE_TEMPORAL_UPDATE)
    
    assert "CORE_TEMPORAL_UPDATE" in str(exc_info.value)
    assert "test" in str(exc_info.value)


def test_pipeline_get_current_phase():
    """Test getting the currently executing phase."""
    pipeline = ExecutionPipeline()
    current_phases = []
    
    def capture_phase():
        current_phases.append(pipeline.get_current_phase())
    
    pipeline.register_handler(
        ExecutionPhase.SOCIAL_UPDATE,
        "test",
        capture_phase,
        "Capture phase"
    )
    
    # Not executing initially
    assert pipeline.get_current_phase() is None
    
    # Execute phase
    pipeline.execute_phase(ExecutionPhase.SOCIAL_UPDATE)
    
    # Should have captured the phase during execution
    assert current_phases[0] == ExecutionPhase.SOCIAL_UPDATE
    
    # Not executing after completion
    assert pipeline.get_current_phase() is None


def test_pipeline_get_handlers_for_phase():
    """Test retrieving handlers for a phase."""
    pipeline = ExecutionPipeline()
    
    handler1 = lambda: None
    handler2 = lambda: None
    
    pipeline.register_handler(
        ExecutionPhase.PHYSIOLOGICAL_UPDATE,
        "module1",
        handler1,
        "Handler 1"
    )
    
    pipeline.register_handler(
        ExecutionPhase.PHYSIOLOGICAL_UPDATE,
        "module2",
        handler2,
        "Handler 2"
    )
    
    handlers = pipeline.get_handlers_for_phase(ExecutionPhase.PHYSIOLOGICAL_UPDATE)
    
    assert len(handlers) == 2
    assert handlers[0].module_id == "module1"
    assert handlers[1].module_id == "module2"


def test_pipeline_clear_handlers():
    """Test clearing handlers."""
    pipeline = ExecutionPipeline()
    
    pipeline.register_handler(
        ExecutionPhase.BREAKTHROUGH_EVALUATION,
        "test",
        lambda: None,
        "Test"
    )
    
    assert len(pipeline.get_handlers_for_phase(ExecutionPhase.BREAKTHROUGH_EVALUATION)) == 1
    
    # Clear specific phase
    pipeline.clear_handlers(ExecutionPhase.BREAKTHROUGH_EVALUATION)
    assert len(pipeline.get_handlers_for_phase(ExecutionPhase.BREAKTHROUGH_EVALUATION)) == 0
    
    # Register again and clear all
    pipeline.register_handler(
        ExecutionPhase.BREAKTHROUGH_EVALUATION,
        "test",
        lambda: None,
        "Test"
    )
    
    pipeline.clear_handlers()
    assert len(pipeline.get_handlers_for_phase(ExecutionPhase.BREAKTHROUGH_EVALUATION)) == 0
