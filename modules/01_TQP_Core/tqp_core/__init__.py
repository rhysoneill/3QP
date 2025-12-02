"""
TQP Core Module - Foundation Layer

This module provides the fundamental execution kernel for the 3QP behavioral twin system.
It implements discrete-time state management, module coordination, and temporal synchronization.

Public API:
    - AgentState: Core state representation
    - TQPCore: Main simulation engine
    - ModuleRegistration: Module registration interface
    - StateDelta: Module update output format
    - Supporting data structures and enums
"""

from .types import (
    AgentState,
    StateDelta,
    MemoryRecord,
    GoalObject,
    ScheduledEvent,
    ScheduledEventRequest,
    Message,
    MessageRequest,
    TimestepMetadata,
    ModuleInputs,
    ErrorRecord,
    StateCheckpoint,
    TimestepCompletionEvent,
    ProcessType,
    RecoveryAction,
    ErrorType
)

from .module_interface import (
    ModuleRegistration,
    Module,
    LifecycleHooks
)

from .core import TQPCore

from .config import SimulationConfig

__version__ = "1.0.0"
__all__ = [
    # Core Engine
    "TQPCore",
    "SimulationConfig",
    
    # State Types
    "AgentState",
    "StateDelta",
    
    # Module Interface
    "ModuleRegistration",
    "Module",
    "LifecycleHooks",
    
    # Supporting Types
    "MemoryRecord",
    "GoalObject",
    "ScheduledEvent",
    "ScheduledEventRequest",
    "Message",
    "MessageRequest",
    "TimestepMetadata",
    "ModuleInputs",
    "ErrorRecord",
    "StateCheckpoint",
    "TimestepCompletionEvent",
    
    # Enums
    "ProcessType",
    "RecoveryAction",
    "ErrorType",
]
