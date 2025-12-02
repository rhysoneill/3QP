"""
Core data types for TQP system.

This module defines all data structures used in agent state representation,
module communication, and system operation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from enum import Enum


# Scalar type alias
Scalar = Union[int, float, bool, str]


class ProcessType(Enum):
    """Module execution classification."""
    SLOW = "slow"
    FAST = "fast"


class ErrorType(Enum):
    """Types of errors that can occur during simulation."""
    MODULE_EXCEPTION = "module_exception"
    VALIDATION_FAILURE = "validation_failure"
    STATE_CORRUPTION = "state_corruption"
    TIMEOUT = "timeout"


class RecoveryAction(Enum):
    """Actions to take when an error occurs."""
    ROLLBACK = "rollback"
    HALT = "halt"
    SKIP_MODULE = "skip_module"
    RETRY = "retry"


@dataclass
class MemoryRecord:
    """
    A single memory entry in the agent's memory buffer.
    
    Memory records are immutable once created and indexed by timestamp.
    """
    timestamp: int  # simulation_time when created
    event_type: str
    event_data: Dict[str, Any]
    source_module: str
    salience: float  # [0.0, 1.0]
    
    def __post_init__(self):
        """Validate memory record constraints."""
        if not 0.0 <= self.salience <= 1.0:
            raise ValueError(f"salience must be in [0.0, 1.0], got {self.salience}")


@dataclass
class GoalObject:
    """
    Represents an agent goal with priority and associated data.
    """
    goal_id: str  # unique identifier
    goal_type: str
    priority: float  # [0.0, 1.0]
    goal_data: Dict[str, Any]
    
    def __post_init__(self):
        """Validate goal constraints."""
        if not 0.0 <= self.priority <= 1.0:
            raise ValueError(f"priority must be in [0.0, 1.0], got {self.priority}")


@dataclass
class ScheduledEvent:
    """
    An event delivered to a module at a scheduled time.
    """
    event_id: str  # unique identifier
    trigger_time: int  # simulation_time when this event was scheduled for
    event_type: str
    event_payload: Dict[str, Any]
    source_module: str


@dataclass
class ScheduledEventRequest:
    """
    A request to schedule a future event.
    """
    trigger_time: int  # future simulation_time
    event_type: str
    event_payload: Dict[str, Any]
    target_module: str  # recipient module_id, or "broadcast"


@dataclass
class Message:
    """
    Inter-module message delivered within same time-step.
    """
    from_module: str
    to_module: str  # module_id or "broadcast"
    message_type: str
    message_payload: Dict[str, Any]


@dataclass
class MessageRequest:
    """
    Request to send a message to another module.
    """
    to_module: str  # module_id or "broadcast"
    message_type: str
    message_payload: Dict[str, Any]


@dataclass
class TimestepMetadata:
    """
    Contextual information about the current time-step.
    """
    is_day_start: bool
    is_week_start: bool
    mission_phase: str  # e.g., "pre-mission", "quarter-1", etc.
    phase_day_number: int  # day within current phase


@dataclass
class ModuleInputs:
    """
    Inputs provided to a module's update function.
    """
    module_id: str
    timestep_metadata: TimestepMetadata
    scheduled_events: List[ScheduledEvent] = field(default_factory=list)
    inter_module_messages: List[Message] = field(default_factory=list)


@dataclass
class AgentState:
    """
    Complete representation of agent internal state at a point in time.
    
    This is the central data structure of the TQP system. All modules
    read from and write to agent state through defined interfaces.
    """
    # Core identifiers
    agent_id: str
    simulation_time: int
    calendar_time: datetime
    state_version: int
    
    # State variable collections
    internal_vars: Dict[str, Scalar] = field(default_factory=dict)
    memory_buffer: List[MemoryRecord] = field(default_factory=list)
    belief_state: Dict[str, Any] = field(default_factory=dict)
    goal_state: List[GoalObject] = field(default_factory=list)
    resource_state: Dict[str, float] = field(default_factory=dict)
    
    # Module-specific state containers
    module_state: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """
        Validate state integrity constraints.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Check monotonicity
        if self.simulation_time < 0:
            errors.append(f"simulation_time must be non-negative, got {self.simulation_time}")
        if self.state_version < 0:
            errors.append(f"state_version must be non-negative, got {self.state_version}")
        
        # Check resource state non-negativity
        for resource, value in self.resource_state.items():
            if value < 0:
                errors.append(f"resource '{resource}' must be non-negative, got {value}")
        
        # Check goal priorities
        for goal in self.goal_state:
            if not 0.0 <= goal.priority <= 1.0:
                errors.append(f"goal '{goal.goal_id}' priority must be in [0.0, 1.0], got {goal.priority}")
        
        # Check memory salience
        for i, memory in enumerate(self.memory_buffer):
            if not 0.0 <= memory.salience <= 1.0:
                errors.append(f"memory[{i}] salience must be in [0.0, 1.0], got {memory.salience}")
        
        return errors


@dataclass
class StateDelta:
    """
    Module output representing proposed changes to agent state.
    
    All fields are optional. Omitted fields indicate no change.
    """
    module_id: str
    
    # State updates (optional)
    internal_var_updates: Optional[Dict[str, Scalar]] = None
    memory_additions: Optional[List[MemoryRecord]] = None
    belief_updates: Optional[Dict[str, Any]] = None
    goal_updates: Optional[Dict[str, Optional[GoalObject]]] = None  # None value = delete
    resource_updates: Optional[Dict[str, float]] = None  # additive deltas
    module_state_update: Optional[Any] = None
    
    # Communication (optional)
    scheduled_events: Optional[List[ScheduledEventRequest]] = None
    inter_module_messages: Optional[List[MessageRequest]] = None


@dataclass
class ErrorRecord:
    """
    Record of an error that occurred during simulation.
    """
    error_id: str
    simulation_time: int
    module_id: str  # source of error, or "core"
    error_type: ErrorType
    error_message: str
    stack_trace: Optional[str] = None
    state_snapshot: Optional[AgentState] = None
    recovery_action: RecoveryAction = RecoveryAction.HALT


@dataclass
class TimestepCompletionEvent:
    """
    Event emitted after each time-step completion.
    """
    simulation_time: int
    calendar_time: datetime
    state_version: int
    elapsed_wall_time_ms: float
    modules_executed: List[str]
    errors_occurred: List[ErrorRecord] = field(default_factory=list)


@dataclass
class StateCheckpoint:
    """
    Complete state checkpoint for serialization and restoration.
    """
    checkpoint_id: str
    simulation_time: int
    state_version: int
    full_agent_state: AgentState
    rng_state: Any  # opaque binary blob
    metadata: Dict[str, Any] = field(default_factory=dict)
