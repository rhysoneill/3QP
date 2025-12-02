"""
Execution pipeline managing the 10-phase simulation cycle.

Implements the phase sequencing defined in the Architecture specification.
"""

from enum import Enum
from typing import List, Callable, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class ExecutionPhase(Enum):
    """
    Simulation execution phases as defined in Architecture spec Section 3.
    
    Each time step progresses through these phases in order.
    """
    PRE_STEP_SETUP = 1              # Logging initialization, intervention application
    ENVIRONMENTAL_UPDATE = 2        # Stressor model updates
    CORE_TEMPORAL_UPDATE = 3        # TQP Core advances breakthrough probability
    PHYSIOLOGICAL_UPDATE = 4        # SlowFast Physiology updates
    SOCIAL_UPDATE = 5               # Social Network updates
    COGNITIVE_UPDATE = 6            # BDI Cycle deliberation
    BREAKTHROUGH_EVALUATION = 7     # TQP Core evaluates breakthrough
    BREAKTHROUGH_PROPAGATION = 8    # Breakthrough Impact propagates consequences
    STATE_LOGGING = 9               # All modules emit state
    POST_STEP_VALIDATION = 10       # Optional validation checks


@dataclass
class PhaseHandler:
    """
    Handler for a specific execution phase.
    
    Attributes:
        phase: Execution phase this handler belongs to
        module_id: Module that owns this handler
        handler: Callable that executes the phase logic
        description: Human-readable description
    """
    phase: ExecutionPhase
    module_id: str
    handler: Callable[[], None]
    description: str


class ExecutionPipeline:
    """
    Manages the sequential execution of simulation phases.
    
    The pipeline ensures modules execute in the correct order per the
    Architecture specification, with proper error handling and logging.
    """
    
    def __init__(self):
        """Initialize the execution pipeline."""
        self._handlers: Dict[ExecutionPhase, List[PhaseHandler]] = {
            phase: [] for phase in ExecutionPhase
        }
        self._current_phase: Optional[ExecutionPhase] = None
        self._phase_enabled: Dict[ExecutionPhase, bool] = {
            phase: True for phase in ExecutionPhase
        }
        # Post-step validation is optional by default
        self._phase_enabled[ExecutionPhase.POST_STEP_VALIDATION] = False
    
    def register_handler(
        self,
        phase: ExecutionPhase,
        module_id: str,
        handler: Callable[[], None],
        description: str
    ) -> None:
        """
        Register a handler for a specific phase.
        
        Args:
            phase: Execution phase
            module_id: ID of the module registering the handler
            handler: Callable to execute during this phase
            description: Description of what the handler does
        """
        phase_handler = PhaseHandler(
            phase=phase,
            module_id=module_id,
            handler=handler,
            description=description
        )
        self._handlers[phase].append(phase_handler)
        logger.debug(
            f"Registered handler for {phase.name}: {module_id} - {description}"
        )
    
    def execute_phase(self, phase: ExecutionPhase) -> None:
        """
        Execute all handlers for a specific phase.
        
        Args:
            phase: Phase to execute
            
        Raises:
            RuntimeError: If a handler fails and error handling policy requires halt
        """
        if not self._phase_enabled[phase]:
            logger.debug(f"Phase {phase.name} is disabled, skipping")
            return
        
        self._current_phase = phase
        handlers = self._handlers[phase]
        
        logger.debug(f"Executing phase {phase.name} ({len(handlers)} handlers)")
        
        for handler_info in handlers:
            try:
                logger.debug(
                    f"  [{handler_info.module_id}] {handler_info.description}"
                )
                handler_info.handler()
            except Exception as e:
                logger.error(
                    f"Error in {phase.name} handler for module "
                    f"'{handler_info.module_id}': {e}",
                    exc_info=True
                )
                # Re-raise to propagate to orchestrator error handling
                raise RuntimeError(
                    f"Phase {phase.name} failed in module '{handler_info.module_id}'"
                ) from e
        
        self._current_phase = None
    
    def execute_timestep(self) -> None:
        """
        Execute a complete time step (all phases in sequence).
        
        Raises:
            RuntimeError: If any phase fails
        """
        logger.info("Beginning time step execution")
        
        for phase in ExecutionPhase:
            self.execute_phase(phase)
        
        logger.info("Time step execution completed")
    
    def enable_phase(self, phase: ExecutionPhase) -> None:
        """
        Enable a phase for execution.
        
        Args:
            phase: Phase to enable
        """
        self._phase_enabled[phase] = True
        logger.info(f"Enabled phase: {phase.name}")
    
    def disable_phase(self, phase: ExecutionPhase) -> None:
        """
        Disable a phase (it will be skipped during execution).
        
        Args:
            phase: Phase to disable
        """
        self._phase_enabled[phase] = False
        logger.info(f"Disabled phase: {phase.name}")
    
    def get_current_phase(self) -> Optional[ExecutionPhase]:
        """
        Get the currently executing phase.
        
        Returns:
            Current phase, or None if not executing
        """
        return self._current_phase
    
    def get_handlers_for_phase(self, phase: ExecutionPhase) -> List[PhaseHandler]:
        """
        Get all registered handlers for a phase.
        
        Args:
            phase: Phase to query
            
        Returns:
            List of phase handlers
        """
        return self._handlers[phase].copy()
    
    def clear_handlers(self, phase: Optional[ExecutionPhase] = None) -> None:
        """
        Clear handlers for a phase or all phases.
        
        Args:
            phase: Phase to clear (if None, clears all phases)
        """
        if phase is None:
            for p in ExecutionPhase:
                self._handlers[p].clear()
            logger.info("Cleared all phase handlers")
        else:
            self._handlers[phase].clear()
            logger.info(f"Cleared handlers for phase: {phase.name}")
