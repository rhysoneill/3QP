"""
BDI Cognitive Cycle Module for 3QP System.

This module implements the Belief-Desire-Intention (BDI) cognitive architecture
for the 3QP behavioral twin system. It provides symbolic representation and
deterministic update cycles for cognitive state evolution.
"""

from .types import (
    Belief,
    BeliefAssertion,
    Desire,
    Intention,
    BDIInput,
    BDIOutput,
    BDIConfig,
    Status,
    CycleStatistics,
    DomainOntology,
    PredicateSchema,
    ControlSignal,
    ConstraintSpec,
    ConfigurationUpdate,
)
from .belief_revision import BeliefRevisionEngine
from .desire_formation import DesireFormationEngine, GoalGenerationRule
from .intention_selection import IntentionSelectionEngine, ResourceManager
from .bdi_module import BDIModule

__all__ = [
    "Belief",
    "BeliefAssertion",
    "Desire",
    "Intention",
    "BDIInput",
    "BDIOutput",
    "BDIConfig",
    "Status",
    "CycleStatistics",
    "DomainOntology",
    "PredicateSchema",
    "ControlSignal",
    "ConstraintSpec",
    "ConfigurationUpdate",
    "BeliefRevisionEngine",
    "DesireFormationEngine",
    "GoalGenerationRule",
    "IntentionSelectionEngine",
    "ResourceManager",
    "BDIModule",
]

__version__ = "1.0.0"
