"""
Module interface definitions and registration.

This module defines the contract that all external modules must implement
to integrate with the TQP Core.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Dict, Optional
from .types import AgentState, StateDelta, ModuleInputs, ProcessType


class LifecycleHooks:
    """
    Optional lifecycle hooks that modules can implement.
    
    All methods are optional. If not needed, leave as None.
    """
    
    def __init__(self):
        self.on_initialize: Optional[Callable[[Dict], None]] = None
        self.on_day_start: Optional[Callable[[AgentState], None]] = None
        self.on_week_start: Optional[Callable[[AgentState], None]] = None
        self.on_phase_transition: Optional[Callable[[str, str], None]] = None
        self.on_finalize: Optional[Callable[[], None]] = None


class Module(ABC):
    """
    Abstract base class for TQP modules.
    
    Concrete modules should inherit from this class and implement
    the update method.
    """
    
    @abstractmethod
    def update(self, current_state: AgentState, module_inputs: ModuleInputs) -> StateDelta:
        """
        Update function called by the core each time-step.
        
        Args:
            current_state: Read-only snapshot of complete agent state
            module_inputs: Time-step-specific inputs for this module
            
        Returns:
            StateDelta with proposed state changes
        """
        pass
    
    def get_dependencies(self) -> list[str]:
        """
        Return list of module IDs this module depends on.
        
        Dependencies must execute before this module.
        """
        return []


@dataclass
class ModuleRegistration:
    """
    Registration data for a module.
    
    Attributes:
        module_id: Unique identifier (e.g., "physiology", "bdi")
        module_name: Human-readable name
        module_version: Version string
        process_type: Whether this is a slow or fast process
        execution_priority: Higher values execute first (0-1000)
        module: Module instance implementing the update interface
        lifecycle_hooks: Optional lifecycle callback functions
    """
    module_id: str
    module_name: str
    module_version: str
    process_type: ProcessType
    execution_priority: int
    module: Module
    lifecycle_hooks: Optional[LifecycleHooks] = None
    
    def __post_init__(self):
        """Validate registration constraints."""
        if not 0 <= self.execution_priority <= 1000:
            raise ValueError(
                f"execution_priority must be in [0, 1000], "
                f"got {self.execution_priority}"
            )
