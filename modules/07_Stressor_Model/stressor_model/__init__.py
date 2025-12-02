"""
Lunar Mission Stressor Model

Provides time-varying stressor signals representing mission-relevant demands
in isolated, confined environments. Part of the 3QP behavioral twin architecture.

This module generates external demand signals (stressors) without interpreting
psychological states or behavioral responses, maintaining clean architectural
separation between signal generation and response mechanisms.
"""

from .stressor_model import StressorModel
from .types import (
    StressorCategory,
    StressorIntensityVector,
    StressorValue,
    StressorMetadata,
    MissionConfig,
    StressorParameterSet,
    UpdateCycleInput,
    SpikeEvent,
    NoiseConfig,
    NoiseType,
    EventType,
    PhaseType,
    PhaseDefinition,
    ScheduledEvent,
    StressorModifier,
    StateFlags,
    SummaryMetrics,
    TriggeredEvent,
)

__version__ = "1.0.0"
__all__ = [
    "StressorModel",
    "StressorCategory",
    "StressorIntensityVector",
    "StressorValue",
    "StressorMetadata",
    "MissionConfig",
    "StressorParameterSet",
    "UpdateCycleInput",
    "SpikeEvent",
    "NoiseConfig",
    "NoiseType",
    "EventType",
    "PhaseType",
    "PhaseDefinition",
    "ScheduledEvent",
    "StressorModifier",
    "StateFlags",
    "SummaryMetrics",
    "TriggeredEvent",
]
