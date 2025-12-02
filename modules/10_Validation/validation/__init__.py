"""
Module 10: Validation Framework

Provides comprehensive validation infrastructure for the 3QP system including:
- Structural validation
- Data integrity validation
- Deterministic reproducibility checks
- Integration validation
- Temporal validation
- Metric validation
"""

from .types import (
    ValidationCategory,
    ValidationResult,
    ValidationConfiguration,
    ValidationReport,
    ModuleInitializationStatus,
    ModuleStateSnapshot,
    ConsistencySignals,
    IntegrityIndicators,
    ValidationFailure,
    ValidationWarning,
    ReproducibilityCertificate,
    ValidationIntensity,
    LogLevel,
    Threshold,
    InitializationResult,
)

from .validation_hooks import ValidationHooks, ModuleValidationAdapter

from .orchestrator import ValidationOrchestrator

from .reproducibility import ReproducibilityManager

from .report_generator import ReportGenerator

__version__ = "0.1.0"

__all__ = [
    "ValidationCategory",
    "ValidationResult",
    "ValidationConfiguration",
    "ValidationReport",
    "ModuleInitializationStatus",
    "ModuleStateSnapshot",
    "ConsistencySignals",
    "IntegrityIndicators",
    "ValidationFailure",
    "ValidationWarning",
    "ReproducibilityCertificate",
    "ValidationIntensity",
    "LogLevel",
    "Threshold",
    "InitializationResult",
    "ValidationHooks",
    "ModuleValidationAdapter",
    "ValidationOrchestrator",
    "ReproducibilityManager",
    "ReportGenerator",
]
