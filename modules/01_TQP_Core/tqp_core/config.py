"""
Simulation configuration data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class SimulationConfig:
    """
    Configuration for a TQP simulation run.
    
    Attributes:
        mission_start_datetime: Real or simulated mission start time
        timestep_duration_minutes: Duration of each time-step in minutes
        total_timesteps: Total number of time-steps to simulate
        random_seed: Seed for deterministic RNG (None for non-deterministic)
        checkpoint_frequency: Number of timesteps between checkpoints
        max_memory_buffer_size: Maximum number of memory records to retain
        module_config: Module-specific configuration dictionaries
    """
    mission_start_datetime: datetime
    timestep_duration_minutes: int
    total_timesteps: int
    random_seed: Optional[int] = None
    checkpoint_frequency: int = 100
    max_memory_buffer_size: int = 1000
    module_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration constraints."""
        if not 1 <= self.timestep_duration_minutes <= 10080:
            raise ValueError(
                f"timestep_duration_minutes must be in [1, 10080], "
                f"got {self.timestep_duration_minutes}"
            )
        
        if self.total_timesteps <= 0:
            raise ValueError(
                f"total_timesteps must be positive, got {self.total_timesteps}"
            )
        
        if self.checkpoint_frequency <= 0:
            raise ValueError(
                f"checkpoint_frequency must be positive, got {self.checkpoint_frequency}"
            )
        
        if self.max_memory_buffer_size <= 0:
            raise ValueError(
                f"max_memory_buffer_size must be positive, got {self.max_memory_buffer_size}"
            )
