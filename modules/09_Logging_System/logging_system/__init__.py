"""
3QP Logging System

Unified logging infrastructure for structured, deterministic log capture
across all simulation modules.
"""

from .logging_interface import LoggingSystem, LoggingInterface
from .types import (
    LogType,
    StateLogEntry,
    EventLogEntry,
    CycleLogEntry,
    MetricLogEntry,
    LogEntry,
)
from .config import LoggingConfig

__all__ = [
    "LoggingSystem",
    "LoggingInterface",
    "LoggingConfig",
    "LogType",
    "StateLogEntry",
    "EventLogEntry",
    "CycleLogEntry",
    "MetricLogEntry",
    "LogEntry",
]

__version__ = "1.0.0"
