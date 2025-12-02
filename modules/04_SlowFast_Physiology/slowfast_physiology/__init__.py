"""
Module 04: Slow-Fast Physiology Model

A hybrid dynamical system component for 3QP simulation framework
maintaining physiological state variables on two distinct timescales.
"""

from .types import (
    PhysiologyState,
    PhysiologyParameters,
    TimescaleConfig,
    PhysiologyInitConfig,
    SlowTimeInput,
    FastTimeInput,
    SlowTimeOutput,
    FastTimeOutput,
    PhysiologyDerivedOutput,
    StatusCode
)

from .physiology_module import PhysiologyModule

__version__ = "1.0.0"
__all__ = [
    "PhysiologyModule",
    "PhysiologyState",
    "PhysiologyParameters",
    "TimescaleConfig",
    "PhysiologyInitConfig",
    "SlowTimeInput",
    "FastTimeInput",
    "SlowTimeOutput",
    "FastTimeOutput",
    "PhysiologyDerivedOutput",
    "StatusCode"
]
