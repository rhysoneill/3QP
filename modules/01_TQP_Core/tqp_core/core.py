"""
TQP Core simulation engine.

This is the main execution kernel that coordinates all modules and manages
agent state evolution over time.
"""

import copy
import time as wall_time
import uuid
from datetime import timedelta
from typing import Dict, List, Optional, Callable

from .config import SimulationConfig
from .types import (
    AgentState, StateDelta, ModuleInputs, TimestepMetadata,
    ErrorRecord, ErrorType, RecoveryAction, TimestepCompletionEvent,
    StateCheckpoint, MemoryRecord, Message
)
from .module_interface import ModuleRegistration
from .module_registry import ModuleRegistry
from .support_systems import MemoryBuffer, EventScheduler, MessageBus, RNGManager


class TQPCore:
    """
    Main simulation engine for the 3QP behavioral twin system.
    
    The core maintains agent state, coordinates module updates, and enforces
    temporal consistency across slow and fast processes.
    """
    
    def __init__(self, config: SimulationConfig, agent_id: str = "agent_001"):
        """
        Initialize TQP Core engine.
        
        Args:
            config: Simulation configuration
            agent_id: Unique identifier for this agent
        """
        self.config = config
        self.agent_id = agent_id
        
        # State management
        self.current_state: Optional[AgentState] = None
        self.staging_state: Optional[AgentState] = None
        self.rollback_buffer: List[AgentState] = []
        
        # Module management
        self.module_registry = ModuleRegistry()
        
        # Supporting systems
        self.memory_buffer = MemoryBuffer(config.max_memory_buffer_size)
        self.event_scheduler = EventScheduler()
        self.message_bus = MessageBus()
        self.rng_manager = RNGManager(config.random_seed)
        
        # Observers and callbacks
        self.state_observers: List[Callable[[AgentState], None]] = []
        self.timestep_observers: List[Callable[[TimestepCompletionEvent], None]] = []
        
        # Runtime state
        self.is_initialized = False
        self.is_running = False
        self.stop_requested = False
        
        # Error tracking
        self.error_log: List[ErrorRecord] = []
    
    def initialize(self, initial_state: Optional[AgentState] = None) -> None:
        """
        Initialize the simulation.
        
        Args:
            initial_state: Optional initial agent state (creates default if None)
        """
        if self.is_initialized:
            raise RuntimeError("Core is already initialized")
        
        # Validate module dependencies
        self.module_registry.validate_dependencies()
        
        # Initialize state
        if initial_state is None:
            self.current_state = self._create_default_state()
        else:
            self.current_state = initial_state
        
        # Validate initial state
        errors = self.current_state.validate()
        if errors:
            raise ValueError(f"Initial state validation failed: {errors}")
        
        # Initialize memory buffer with any existing memories
        for memory in self.current_state.memory_buffer:
            self.memory_buffer.add(memory)
        
        # Call module initialization hooks
        for registration in self.module_registry.get_all_modules():
            if registration.lifecycle_hooks and registration.lifecycle_hooks.on_initialize:
                module_config = self.config.module_config.get(registration.module_id, {})
                registration.lifecycle_hooks.on_initialize(module_config)
        
        self.is_initialized = True
    
    def _create_default_state(self) -> AgentState:
        """Create default initial agent state."""
        return AgentState(
            agent_id=self.agent_id,
            simulation_time=0,
            calendar_time=self.config.mission_start_datetime,
            state_version=0
        )
    
    def register_module(self, registration: ModuleRegistration) -> None:
        """
        Register a module with the core.
        
        Args:
            registration: Module registration data
        """
        if self.is_initialized:
            raise RuntimeError("Cannot register modules after initialization")
        
        self.module_registry.register(registration)
    
    def add_state_observer(self, observer: Callable[[AgentState], None]) -> None:
        """Register a callback to receive state updates."""
        self.state_observers.append(observer)
    
    def add_timestep_observer(self, observer: Callable[[TimestepCompletionEvent], None]) -> None:
        """Register a callback to receive timestep completion events."""
        self.timestep_observers.append(observer)
    
    def get_current_state(self) -> AgentState:
        """Get current agent state (read-only copy)."""
        if not self.current_state:
            raise RuntimeError("Core not initialized")
        return copy.deepcopy(self.current_state)
    
    def get_rng(self):
        """Get managed RNG instance for modules."""
        return self.rng_manager.get_rng()
    
    def step(self) -> bool:
        """
        Execute a single time-step.
        
        Returns:
            True if step completed successfully, False if error occurred
        """
        if not self.is_initialized:
            raise RuntimeError("Core not initialized. Call initialize() first.")
        
        step_start_time = wall_time.time()
        modules_executed = []
        
        try:
            # Phase 1: Pre-update
            self._pre_update_phase()
            
            # Phase 2: Slow-process update (if triggered)
            slow_deltas = self._slow_update_phase()
            modules_executed.extend([d.module_id for d in slow_deltas])
            
            # Phase 3: Fast-process update
            fast_deltas = self._fast_update_phase()
            modules_executed.extend([d.module_id for d in fast_deltas])
            
            # Phase 4: Reconciliation
            self._reconciliation_phase(slow_deltas, fast_deltas)
            
            # Phase 5: Validation
            self._validation_phase()
            
            # Phase 6: Commit
            self._commit_phase()
            
            # Phase 7: Post-update
            elapsed_ms = (wall_time.time() - step_start_time) * 1000
            self._post_update_phase(modules_executed, elapsed_ms)
            
            return True
            
        except Exception as e:
            # Error handling
            self._handle_error(e, "core", modules_executed)
            return False
    
    def _pre_update_phase(self) -> None:
        """Phase 1: Increment time, snapshot state for rollback."""
        # Increment simulation time
        self.current_state.simulation_time += 1
        
        # Update calendar time
        delta = timedelta(minutes=self.config.timestep_duration_minutes)
        self.current_state.calendar_time += delta
        
        # Snapshot for rollback
        self.rollback_buffer.append(copy.deepcopy(self.current_state))
        if len(self.rollback_buffer) > 10:  # Keep last 10 snapshots
            self.rollback_buffer.pop(0)
        
        # Create staging state
        self.staging_state = copy.deepcopy(self.current_state)
    
    def _slow_update_phase(self) -> List[StateDelta]:
        """Phase 2: Execute slow-process modules if triggered."""
        metadata = self._get_timestep_metadata()
        deltas = []
        
        # Only execute slow modules on day/week boundaries or specific triggers
        if metadata.is_day_start or metadata.is_week_start:
            slow_modules = self.module_registry.get_slow_modules()
            
            for registration in slow_modules:
                try:
                    delta = self._invoke_module(registration, metadata)
                    if delta:
                        deltas.append(delta)
                        # Apply messages immediately so later modules can receive them
                        if delta.inter_module_messages:
                            for message_request in delta.inter_module_messages:
                                self.message_bus.send(delta.module_id, message_request)
                except Exception as e:
                    self._handle_module_error(e, registration.module_id)
                    raise
        
        return deltas
    
    def _fast_update_phase(self) -> List[StateDelta]:
        """Phase 3: Execute fast-process modules."""
        metadata = self._get_timestep_metadata()
        deltas = []
        
        fast_modules = self.module_registry.get_fast_modules()
        
        for registration in fast_modules:
            try:
                delta = self._invoke_module(registration, metadata)
                if delta:
                    deltas.append(delta)
                    # Apply messages immediately so later modules can receive them
                    if delta.inter_module_messages:
                        for message_request in delta.inter_module_messages:
                            self.message_bus.send(delta.module_id, message_request)
            except Exception as e:
                self._handle_module_error(e, registration.module_id)
                raise
        
        return deltas
    
    def _invoke_module(self, registration: ModuleRegistration, metadata: TimestepMetadata) -> Optional[StateDelta]:
        """
        Invoke a module's update function.
        
        Args:
            registration: Module registration
            metadata: Timestep metadata
            
        Returns:
            StateDelta or None
        """
        # Get scheduled events for this module
        scheduled_events = self.event_scheduler.get_events_for_time(
            self.current_state.simulation_time,
            registration.module_id
        )
        
        # Get messages for this module
        messages = self.message_bus.get_messages_for_module(registration.module_id)
        
        # Prepare inputs
        module_inputs = ModuleInputs(
            module_id=registration.module_id,
            timestep_metadata=metadata,
            scheduled_events=scheduled_events,
            inter_module_messages=messages
        )
        
        # Call lifecycle hooks if appropriate
        if registration.lifecycle_hooks:
            if metadata.is_day_start and registration.lifecycle_hooks.on_day_start:
                registration.lifecycle_hooks.on_day_start(self.current_state)
            if metadata.is_week_start and registration.lifecycle_hooks.on_week_start:
                registration.lifecycle_hooks.on_week_start(self.current_state)
        
        # Invoke update function
        delta = registration.module.update(
            copy.deepcopy(self.current_state),  # Read-only copy
            module_inputs
        )
        
        return delta
    
    def _reconciliation_phase(self, slow_deltas: List[StateDelta], fast_deltas: List[StateDelta]) -> None:
        """
        Phase 4: Apply deltas to staging state with conflict resolution.
        
        Fast module updates take precedence over slow updates for same variable.
        """
        # Apply slow deltas first
        for delta in slow_deltas:
            self._apply_delta(delta)
        
        # Apply fast deltas (overrides slow)
        for delta in fast_deltas:
            self._apply_delta(delta)
        
        # Update memory buffer
        self.staging_state.memory_buffer = self.memory_buffer.get_all()
        
        # Clear message bus (messages delivered this timestep)
        self.message_bus.clear()
    
    def _apply_delta(self, delta: StateDelta) -> None:
        """
        Apply a state delta to the staging state.
        
        Args:
            delta: State delta from module update
        """
        # Update internal variables
        if delta.internal_var_updates:
            self.staging_state.internal_vars.update(delta.internal_var_updates)
        
        # Add memory records
        if delta.memory_additions:
            for memory in delta.memory_additions:
                self.memory_buffer.add(memory)
        
        # Update beliefs
        if delta.belief_updates:
            self.staging_state.belief_state.update(delta.belief_updates)
        
        # Update goals
        if delta.goal_updates:
            for goal_id, goal_obj in delta.goal_updates.items():
                if goal_obj is None:
                    # Delete goal
                    self.staging_state.goal_state = [
                        g for g in self.staging_state.goal_state if g.goal_id != goal_id
                    ]
                else:
                    # Update or add goal
                    existing = [g for g in self.staging_state.goal_state if g.goal_id == goal_id]
                    if existing:
                        idx = self.staging_state.goal_state.index(existing[0])
                        self.staging_state.goal_state[idx] = goal_obj
                    else:
                        self.staging_state.goal_state.append(goal_obj)
        
        # Update resources (additive)
        if delta.resource_updates:
            for resource, delta_value in delta.resource_updates.items():
                current = self.staging_state.resource_state.get(resource, 0.0)
                self.staging_state.resource_state[resource] = current + delta_value
        
        # Update module state
        if delta.module_state_update is not None:
            self.staging_state.module_state[delta.module_id] = delta.module_state_update
        
        # Schedule events
        if delta.scheduled_events:
            for event_request in delta.scheduled_events:
                self.event_scheduler.schedule(event_request)
        
        # Note: Messages are sent during module execution phase
        # to ensure same-timestep delivery
    
    def _validation_phase(self) -> None:
        """Phase 5: Validate staging state integrity."""
        errors = self.staging_state.validate()
        if errors:
            raise ValueError(f"State validation failed: {'; '.join(errors)}")
    
    def _commit_phase(self) -> None:
        """Phase 6: Commit staging state as current state."""
        self.staging_state.state_version += 1
        self.current_state = self.staging_state
        self.staging_state = None
    
    def _post_update_phase(self, modules_executed: List[str], elapsed_ms: float) -> None:
        """Phase 7: Emit notifications, checkpointing, termination checks."""
        # Notify observers
        for observer in self.state_observers:
            observer(copy.deepcopy(self.current_state))
        
        # Emit timestep completion event
        event = TimestepCompletionEvent(
            simulation_time=self.current_state.simulation_time,
            calendar_time=self.current_state.calendar_time,
            state_version=self.current_state.state_version,
            elapsed_wall_time_ms=elapsed_ms,
            modules_executed=modules_executed,
            errors_occurred=[]
        )
        
        for observer in self.timestep_observers:
            observer(event)
        
        # Checkpoint if needed
        if self.current_state.simulation_time % self.config.checkpoint_frequency == 0:
            self._create_checkpoint()
    
    def _get_timestep_metadata(self) -> TimestepMetadata:
        """Generate metadata for current timestep."""
        # TODO: Implement proper phase detection
        # For now, use simple day/week boundary detection
        
        prev_time = self.current_state.simulation_time - 1
        prev_calendar = self.config.mission_start_datetime + timedelta(
            minutes=prev_time * self.config.timestep_duration_minutes
        )
        current_calendar = self.current_state.calendar_time
        
        is_day_start = (
            self.current_state.simulation_time == 0 or
            prev_calendar.date() != current_calendar.date()
        )
        
        is_week_start = (
            self.current_state.simulation_time == 0 or
            prev_calendar.isocalendar()[1] != current_calendar.isocalendar()[1]
        )
        
        # Calculate mission phase (simplified)
        days_elapsed = (current_calendar - self.config.mission_start_datetime).days
        
        if days_elapsed < 0:
            mission_phase = "pre-mission"
            phase_day = 0
        else:
            # Assume 90-day quarters
            quarter = days_elapsed // 90
            phase_day = days_elapsed % 90
            
            if quarter == 0:
                mission_phase = "quarter-1"
            elif quarter == 1:
                mission_phase = "quarter-2"
            elif quarter == 2:
                mission_phase = "quarter-3"
            elif quarter == 3:
                mission_phase = "quarter-4"
            else:
                mission_phase = "post-mission"
        
        return TimestepMetadata(
            is_day_start=is_day_start,
            is_week_start=is_week_start,
            mission_phase=mission_phase,
            phase_day_number=phase_day
        )
    
    def _handle_error(self, error: Exception, source: str, modules_executed: List[str]) -> None:
        """Handle an error during time-step execution."""
        error_record = ErrorRecord(
            error_id=str(uuid.uuid4()),
            simulation_time=self.current_state.simulation_time,
            module_id=source,
            error_type=ErrorType.MODULE_EXCEPTION,
            error_message=str(error),
            stack_trace=None,  # Could capture traceback here
            state_snapshot=copy.deepcopy(self.current_state),
            recovery_action=RecoveryAction.ROLLBACK
        )
        
        self.error_log.append(error_record)
        
        # Rollback to previous state
        if self.rollback_buffer:
            self.current_state = self.rollback_buffer[-1]
    
    def _handle_module_error(self, error: Exception, module_id: str) -> None:
        """Handle module-specific error."""
        # Log and re-raise for now
        # Could implement more sophisticated error handling
        raise error
    
    def _create_checkpoint(self) -> StateCheckpoint:
        """Create a state checkpoint."""
        checkpoint = StateCheckpoint(
            checkpoint_id=f"ckpt_{self.current_state.simulation_time}",
            simulation_time=self.current_state.simulation_time,
            state_version=self.current_state.state_version,
            full_agent_state=copy.deepcopy(self.current_state),
            rng_state=self.rng_manager.get_state()
        )
        
        # TODO: Persist checkpoint to storage
        return checkpoint
    
    def run(self, num_steps: Optional[int] = None) -> None:
        """
        Run the simulation for a specified number of steps or until completion.
        
        Args:
            num_steps: Number of steps to run (None = run to total_timesteps)
        """
        if not self.is_initialized:
            raise RuntimeError("Core not initialized. Call initialize() first.")
        
        if num_steps is None:
            num_steps = self.config.total_timesteps
        
        self.is_running = True
        self.stop_requested = False
        
        for i in range(num_steps):
            if self.stop_requested:
                break
            
            if self.current_state.simulation_time >= self.config.total_timesteps:
                break
            
            success = self.step()
            if not success:
                # Error occurred, decide whether to continue
                break
        
        self.is_running = False
        self._finalize()
    
    def stop(self) -> None:
        """Request simulation stop."""
        self.stop_requested = True
    
    def _finalize(self) -> None:
        """Call finalization hooks."""
        for registration in self.module_registry.get_all_modules():
            if registration.lifecycle_hooks and registration.lifecycle_hooks.on_finalize:
                registration.lifecycle_hooks.on_finalize()
