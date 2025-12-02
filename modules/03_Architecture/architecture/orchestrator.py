"""
System orchestrator coordinating all modules and managing simulation execution.

The Orchestrator is the central integration point that:
- Manages module registration and dependency injection
- Coordinates execution through the pipeline
- Routes data between modules via the event bus
- Manages the simulation container and lifecycle
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

# Import from TQP Core
import sys
from pathlib import Path
tqp_core_path = Path(__file__).parent.parent.parent / "01_TQP_Core"
if str(tqp_core_path) not in sys.path:
    sys.path.insert(0, str(tqp_core_path))

from tqp_core.module_interface import ModuleRegistration, Module
from tqp_core.module_registry import ModuleRegistry
from tqp_core.types import AgentState, ModuleInputs, StateDelta, ErrorRecord, ErrorType, RecoveryAction

from .event_bus import EventBus, Event
from .execution_pipeline import ExecutionPipeline, ExecutionPhase
from .simulation_container import SimulationContainer, SimulationConfig

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    System orchestrator managing the complete 3QP simulation lifecycle.
    
    The orchestrator is the integration layer that coordinates all modules,
    manages data flow, and ensures correct execution sequencing per the
    Architecture specification.
    
    Responsibilities:
    - Module registration and dependency resolution
    - Execution pipeline configuration
    - Event bus coordination
    - Simulation container management
    - Error handling and recovery
    """
    
    def __init__(self, config: SimulationConfig):
        """
        Initialize the orchestrator.
        
        Args:
            config: Simulation configuration
        """
        self.config = config
        
        # Core components
        self.module_registry = ModuleRegistry()
        self.event_bus = EventBus()
        self.execution_pipeline = ExecutionPipeline()
        self.simulation_container = SimulationContainer(config)
        
        # State tracking
        self._initialized = False
        self._running = False
        self._error_records: List[ErrorRecord] = []
        
        logger.info("Orchestrator initialized")
    
    def register_module(self, registration: ModuleRegistration) -> None:
        """
        Register a module with the orchestrator.
        
        Args:
            registration: Module registration data
        """
        # Register with module registry
        self.module_registry.register(registration)
        
        # Register lifecycle hooks with simulation container
        if registration.lifecycle_hooks is not None:
            self.simulation_container.register_lifecycle_hooks(registration.lifecycle_hooks)
        
        logger.info(
            f"Registered module: {registration.module_id} "
            f"(v{registration.module_version}, priority={registration.execution_priority})"
        )
    
    def initialize(self, agent_ids: List[str], config_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the orchestrator and all registered modules.
        
        Args:
            agent_ids: List of agent IDs to initialize
            config_data: Optional configuration data for modules
            
        Raises:
            ValueError: If dependencies are invalid
            RuntimeError: If initialization fails
        """
        if self._initialized:
            raise RuntimeError("Orchestrator already initialized")
        
        logger.info("Initializing orchestrator")
        
        # Validate module dependencies
        try:
            self.module_registry.validate_dependencies()
        except ValueError as e:
            logger.error(f"Module dependency validation failed: {e}")
            raise
        
        # Initialize simulation container
        self.simulation_container.initialize(config_data)
        
        # Initialize agents
        for agent_id in agent_ids:
            self.simulation_container.initialize_agent(agent_id)
        
        # Build execution pipeline
        self._build_execution_pipeline()
        
        self._initialized = True
        logger.info(f"Orchestrator initialized with {len(agent_ids)} agents")
    
    def _build_execution_pipeline(self) -> None:
        """
        Build the execution pipeline by registering phase handlers.
        
        This method maps modules to their appropriate execution phases
        based on the Architecture specification.
        """
        # TODO: This is a placeholder implementation
        # In a full implementation, modules would register their own phase handlers
        # or the orchestrator would map modules to phases based on configuration
        
        # For now, we register a basic handler for each phase
        logger.info("Building execution pipeline")
        
        # Register phase handlers (module-specific logic would go here)
        self.execution_pipeline.register_handler(
            ExecutionPhase.PRE_STEP_SETUP,
            "orchestrator",
            self._pre_step_setup,
            "Pre-step initialization"
        )
        
        self.execution_pipeline.register_handler(
            ExecutionPhase.STATE_LOGGING,
            "orchestrator",
            self._state_logging,
            "Log all module states"
        )
        
        logger.info("Execution pipeline built")
    
    def _pre_step_setup(self) -> None:
        """Phase 1: Pre-step setup handler."""
        # Publish time step start event
        event = Event(
            event_type="timestep_start",
            source_module="orchestrator",
            payload={
                "simulation_time": self.simulation_container.get_current_time(),
                "calendar_time": self.simulation_container.get_current_calendar_time().isoformat()
            },
            simulation_time=self.simulation_container.get_current_time()
        )
        self.event_bus.publish(event)
        
        # TODO: Apply queued interventions
    
    def _state_logging(self) -> None:
        """Phase 9: State logging handler."""
        # Publish state snapshot event
        for agent_id in self.simulation_container.get_all_agents():
            state = self.simulation_container.get_agent_state(agent_id)
            
            event = Event(
                event_type="state_snapshot",
                source_module="orchestrator",
                payload={
                    "agent_id": agent_id,
                    "simulation_time": state.simulation_time,
                    "state_version": state.state_version
                },
                simulation_time=state.simulation_time
            )
            self.event_bus.publish(event)
    
    def execute_timestep(self) -> None:
        """
        Execute a single simulation time step.
        
        Advances time and executes all phases in the pipeline.
        
        Raises:
            RuntimeError: If orchestrator not initialized or execution fails
        """
        if not self._initialized:
            raise RuntimeError("Orchestrator not initialized")
        
        logger.info(
            f"Executing time step {self.simulation_container.get_current_time() + 1}"
        )
        
        try:
            # Advance simulation time
            self.simulation_container.advance_time()
            
            # Execute pipeline
            self.execution_pipeline.execute_timestep()
            
            # Validate agent states
            validation_results = self.simulation_container.validate_all_agents()
            if validation_results:
                logger.warning(f"Agent validation errors: {validation_results}")
                # TODO: Handle validation failures per error policy
            
        except Exception as e:
            logger.error(f"Time step execution failed: {e}", exc_info=True)
            
            # Record error
            error_record = ErrorRecord(
                error_id=f"error_{len(self._error_records)}",
                simulation_time=self.simulation_container.get_current_time(),
                module_id="orchestrator",
                error_type=ErrorType.MODULE_EXCEPTION,
                error_message=str(e),
                recovery_action=RecoveryAction.HALT
            )
            self._error_records.append(error_record)
            
            raise
    
    def run(self, num_steps: int) -> None:
        """
        Run the simulation for a specified number of steps.
        
        Args:
            num_steps: Number of time steps to execute
            
        Raises:
            RuntimeError: If orchestrator not initialized or execution fails
        """
        if not self._initialized:
            raise RuntimeError("Orchestrator not initialized")
        
        if self._running:
            raise RuntimeError("Simulation already running")
        
        logger.info(f"Starting simulation run for {num_steps} steps")
        self._running = True
        
        try:
            for step in range(num_steps):
                self.execute_timestep()
                
                # Check for halt conditions
                if self._should_halt():
                    logger.warning("Simulation halted due to error condition")
                    break
        
        finally:
            self._running = False
        
        logger.info("Simulation run completed")
    
    def _should_halt(self) -> bool:
        """
        Check if simulation should halt.
        
        Returns:
            True if simulation should stop
        """
        # Check for critical errors requiring halt
        for error in self._error_records:
            if error.recovery_action == RecoveryAction.HALT:
                return True
        
        return False
    
    def finalize(self) -> None:
        """
        Finalize the orchestrator and all modules.
        
        Invokes lifecycle finalization hooks and cleans up resources.
        """
        logger.info("Finalizing orchestrator")
        
        # Finalize simulation container
        self.simulation_container.finalize()
        
        # Publish finalization event
        event = Event(
            event_type="simulation_finalized",
            source_module="orchestrator",
            payload={
                "total_steps": self.simulation_container.get_current_time(),
                "errors": len(self._error_records)
            },
            simulation_time=self.simulation_container.get_current_time()
        )
        self.event_bus.publish(event)
        
        logger.info("Orchestrator finalized")
    
    def get_error_records(self) -> List[ErrorRecord]:
        """
        Get all error records from the simulation.
        
        Returns:
            List of error records
        """
        return self._error_records.copy()
    
    def get_module(self, module_id: str) -> ModuleRegistration:
        """
        Get a registered module by ID.
        
        Args:
            module_id: Module identifier
            
        Returns:
            Module registration
            
        Raises:
            KeyError: If module not found
        """
        return self.module_registry.get_module(module_id)
    
    def get_all_modules(self) -> List[ModuleRegistration]:
        """
        Get all registered modules.
        
        Returns:
            List of module registrations
        """
        return self.module_registry.get_all_modules()
