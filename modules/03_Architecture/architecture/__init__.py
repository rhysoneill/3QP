"""
Module 03: Architecture Overview

This module implements the system orchestrator and integration layer for the 3QP system.
It provides:
- Module registry and dependency injection
- Event bus for inter-module communication
- Simulation container and lifecycle management
- Execution pipeline with phase sequencing

Complies with Architecture Version 1.0.0
"""

from .orchestrator import Orchestrator
from .event_bus import EventBus, Event
from .simulation_container import SimulationContainer, SimulationConfig
from .execution_pipeline import ExecutionPipeline, ExecutionPhase

__version__ = "1.0.0"
__all__ = [
    "Orchestrator",
    "EventBus",
    "Event",
    "SimulationContainer",
    "SimulationConfig",
    "ExecutionPipeline",
    "ExecutionPhase",
]
