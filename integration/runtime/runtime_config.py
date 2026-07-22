"""
Runtime Configuration for Phase 5 Integration Harness

Provides mission parameters and runtime options for the Phase 5 wrapper
around the Ruthless Core Model.

This module does NOT modify the core engine - it only configures how
the runtime layer wraps and executes it.
"""

from dataclasses import dataclass, field
from typing import Optional
import json
from pathlib import Path


@dataclass
class RuntimeConfig:
    """
    Runtime configuration for Phase 5 mission simulation.
    
    This configuration controls the runtime harness behavior, NOT the
    underlying Ruthless Core Model parameters (those are set via
    RuthlessCoreConfig).
    
    Attributes:
        mission_name: Human-readable mission identifier
        mission_length_days: Total mission duration
        output_dir: Directory for simulation outputs
        enable_validation: Whether to run trajectory validation
        enable_logging: Whether to log outputs to files
        verbose: Whether to print detailed progress
    """
    mission_name: str = "default_mission"
    mission_length_days: int = 200
    output_dir: str = "output"
    enable_validation: bool = True
    enable_logging: bool = True
    verbose: bool = True
    
    # Optional: Path to custom RuthlessCoreConfig parameters
    core_config_override: Optional[dict] = None
    
    # Optional: Crew preset name for personality-based configuration
    # If set, uses crew personality mapping instead of default config
    crew_preset: Optional[str] = None
    
    @classmethod
    def from_json(cls, filepath: str) -> "RuntimeConfig":
        """
        Load runtime configuration from JSON file.
        
        Args:
            filepath: Path to JSON configuration file
            
        Returns:
            RuntimeConfig instance
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    @classmethod
    def from_dict(cls, data: dict) -> "RuntimeConfig":
        """
        Create runtime configuration from dictionary.
        
        Args:
            data: Configuration parameters as dict
            
        Returns:
            RuntimeConfig instance
        """
        return cls(**data)
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "mission_name": self.mission_name,
            "mission_length_days": self.mission_length_days,
            "output_dir": self.output_dir,
            "enable_validation": self.enable_validation,
            "enable_logging": self.enable_logging,
            "verbose": self.verbose,
            "core_config_override": self.core_config_override,
            "crew_preset": self.crew_preset,
        }
    
    def save_json(self, filepath: str):
        """
        Save configuration to JSON file.
        
        Args:
            filepath: Path to save configuration
        """
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def get_output_path(self) -> Path:
        """Get output directory as Path object, creating if needed."""
        path = Path(self.output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


def get_default_config() -> RuntimeConfig:
    """
    Get default runtime configuration.
    
    Returns:
        RuntimeConfig with sensible defaults
    """
    return RuntimeConfig(
        mission_name="baseline_tqp_mission",
        mission_length_days=200,
        output_dir="output",
        enable_validation=True,
        enable_logging=True,
        verbose=True,
    )


def create_example_config(filepath: str = "runtime_config_example.json"):
    """
    Create an example runtime configuration file.
    
    Args:
        filepath: Path to save example configuration
    """
    config = get_default_config()
    config.mission_name = "example_mission"
    config.save_json(filepath)
    print(f"Example configuration saved to {filepath}")
