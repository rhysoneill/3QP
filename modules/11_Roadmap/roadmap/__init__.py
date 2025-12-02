"""
Module 11: Implementation Roadmap

This module provides project management and tracking capabilities for the
3QP Behavioral Twin implementation lifecycle. It defines phases, milestones,
gating conditions, and status tracking for the structured development process.
"""

from .types import (
    Phase,
    PhaseStatus,
    ModuleStatus,
    IntegrationStatus,
    MaturityLevel,
    GateCondition,
    ProjectState,
    RiskInfo,
    RiskLevel,
    MilestoneInfo,
    ModuleInfo,
    IntegrationStepInfo,
    PhaseInfo,
    ValidationResult,
)

from .roadmap_manager import (
    RoadmapManager,
    PhaseGate,
    IntegrationStep,
)

from .status_tracker import (
    StatusTracker,
    ProjectMetrics,
)

__version__ = "1.0.0"

__all__ = [
    # Types
    "Phase",
    "PhaseStatus",
    "ModuleStatus",
    "IntegrationStatus",
    "MaturityLevel",
    "GateCondition",
    "ProjectState",
    "RiskInfo",
    "RiskLevel",
    "MilestoneInfo",
    "ModuleInfo",
    "IntegrationStepInfo",
    "PhaseInfo",
    "ValidationResult",
    # Manager
    "RoadmapManager",
    "PhaseGate",
    "IntegrationStep",
    # Tracker
    "StatusTracker",
    "ProjectMetrics",
]
