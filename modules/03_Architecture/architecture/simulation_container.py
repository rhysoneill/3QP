"""
Simulation container managing agent lifecycle and state.

Provides the runtime environment for agent simulations with proper
initialization, time step advancement, and finalization.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

# Import from TQP Core
import sys
from pathlib import Path
tqp_core_path = Path(__file__).parent.parent.parent / "01_TQP_Core"
if str(tqp_core_path) not in sys.path:
    sys.path.insert(0, str(tqp_core_path))

from tqp_core.types import AgentState, TimestepMetadata
from tqp_core.module_interface import LifecycleHooks

logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    """
    Configuration for a simulation run.
    
    Attributes:
        start_time: Calendar start time
        time_step_duration: Duration of each time step
        mission_phases: Map of phase names to day ranges
        random_seed: Seed for reproducibility
        metadata: Additional configuration data
    """
    start_time: datetime
    time_step_duration: timedelta
    mission_phases: Dict[str, tuple[int, int]]  # phase_name -> (start_day, end_day)
    random_seed: int
    metadata: Dict[str, Any]


class SimulationContainer:
    """
    Container managing the runtime environment for agent simulations.
    
    Responsibilities:
    - Agent state initialization and management
    - Time progression and calendar management
    - Lifecycle hook invocation
    - State checkpoint and restoration
    """
    
    def __init__(self, config: SimulationConfig):
        """
        Initialize the simulation container.
        
        Args:
            config: Simulation configuration
        """
        self.config = config
        self._agents: Dict[str, AgentState] = {}
        self._current_time: int = 0
        self._current_calendar_time: datetime = config.start_time
        self._lifecycle_hooks: List[LifecycleHooks] = []
        self._initialized = False
        
        # Set random seed for reproducibility
        import random
        random.seed(config.random_seed)
        
        logger.info(f"Simulation container created with seed {config.random_seed}")
    
    def register_lifecycle_hooks(self, hooks: LifecycleHooks) -> None:
        """
        Register lifecycle hooks from a module.
        
        Args:
            hooks: Lifecycle hooks to register
        """
        self._lifecycle_hooks.append(hooks)
        logger.debug("Registered lifecycle hooks")
    
    def initialize_agent(self, agent_id: str, initial_state: Optional[AgentState] = None) -> None:
        """
        Initialize an agent in the simulation.
        
        Args:
            agent_id: Unique identifier for the agent
            initial_state: Optional initial state (if None, creates default state)
        """
        if agent_id in self._agents:
            raise ValueError(f"Agent '{agent_id}' is already initialized")
        
        if initial_state is None:
            # Create default agent state
            initial_state = AgentState(
                agent_id=agent_id,
                simulation_time=self._current_time,
                calendar_time=self._current_calendar_time,
                state_version=0
            )
        
        self._agents[agent_id] = initial_state
        logger.info(f"Initialized agent: {agent_id}")
    
    def initialize(self, config_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the simulation container.
        
        Invokes on_initialize lifecycle hooks.
        
        Args:
            config_data: Optional configuration data to pass to modules
        """
        if self._initialized:
            logger.warning("Simulation already initialized")
            return
        
        logger.info("Initializing simulation container")
        
        # Invoke on_initialize hooks
        for hooks in self._lifecycle_hooks:
            if hooks.on_initialize is not None:
                try:
                    hooks.on_initialize(config_data or {})
                except Exception as e:
                    logger.error(f"Error in on_initialize hook: {e}", exc_info=True)
                    raise
        
        self._initialized = True
        logger.info("Simulation container initialized")
    
    def advance_time(self) -> None:
        """
        Advance simulation time by one step.
        
        Updates simulation time and calendar time for all agents.
        Invokes day_start and week_start hooks as appropriate.
        """
        self._current_time += 1
        self._current_calendar_time += self.config.time_step_duration
        
        # Update agent states
        for agent_state in self._agents.values():
            agent_state.simulation_time = self._current_time
            agent_state.calendar_time = self._current_calendar_time
            agent_state.state_version += 1
        
        # Check for day/week transitions
        # Assuming daily time steps for now
        is_day_start = True  # TODO: Calculate based on time_step_duration
        is_week_start = self._current_time % 7 == 0
        
        # Invoke lifecycle hooks
        if is_day_start:
            for hooks in self._lifecycle_hooks:
                if hooks.on_day_start is not None:
                    for agent_state in self._agents.values():
                        try:
                            hooks.on_day_start(agent_state)
                        except Exception as e:
                            logger.error(f"Error in on_day_start hook: {e}", exc_info=True)
        
        if is_week_start:
            for hooks in self._lifecycle_hooks:
                if hooks.on_week_start is not None:
                    for agent_state in self._agents.values():
                        try:
                            hooks.on_week_start(agent_state)
                        except Exception as e:
                            logger.error(f"Error in on_week_start hook: {e}", exc_info=True)
        
        logger.debug(f"Advanced to simulation time {self._current_time}")
    
    def get_agent_state(self, agent_id: str) -> AgentState:
        """
        Get the current state of an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent state
            
        Raises:
            KeyError: If agent not found
        """
        return self._agents[agent_id]
    
    def get_all_agents(self) -> List[str]:
        """
        Get list of all agent IDs.
        
        Returns:
            List of agent identifiers
        """
        return list(self._agents.keys())
    
    def get_timestep_metadata(self) -> TimestepMetadata:
        """
        Get metadata for the current time step.
        
        Returns:
            Timestep metadata
        """
        # Determine current mission phase
        current_day = self._current_time  # Assuming daily steps
        mission_phase = "unknown"
        phase_day_number = 0
        
        for phase_name, (start_day, end_day) in self.config.mission_phases.items():
            if start_day <= current_day <= end_day:
                mission_phase = phase_name
                phase_day_number = current_day - start_day + 1
                break
        
        return TimestepMetadata(
            is_day_start=True,  # TODO: Calculate based on time_step_duration
            is_week_start=self._current_time % 7 == 0,
            mission_phase=mission_phase,
            phase_day_number=phase_day_number
        )
    
    def finalize(self) -> None:
        """
        Finalize the simulation.
        
        Invokes on_finalize lifecycle hooks.
        """
        logger.info("Finalizing simulation container")
        
        # Invoke on_finalize hooks
        for hooks in self._lifecycle_hooks:
            if hooks.on_finalize is not None:
                try:
                    hooks.on_finalize()
                except Exception as e:
                    logger.error(f"Error in on_finalize hook: {e}", exc_info=True)
        
        logger.info("Simulation container finalized")
    
    def validate_all_agents(self) -> Dict[str, List[str]]:
        """
        Validate all agent states.
        
        Returns:
            Dictionary mapping agent_id to list of validation errors
        """
        validation_results = {}
        
        for agent_id, agent_state in self._agents.items():
            errors = agent_state.validate()
            if errors:
                validation_results[agent_id] = errors
        
        return validation_results
    
    def get_current_time(self) -> int:
        """
        Get the current simulation time.
        
        Returns:
            Current simulation time step
        """
        return self._current_time
    
    def get_current_calendar_time(self) -> datetime:
        """
        Get the current calendar time.
        
        Returns:
            Current calendar datetime
        """
        return self._current_calendar_time
