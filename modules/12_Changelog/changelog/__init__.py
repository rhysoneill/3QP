"""
Module 12: Changelog & Notes

This module provides version control and change documentation management
for the 3QP Project. It defines data structures, validation rules, and
management interfaces for maintaining rigorous changelog discipline.

Note: This is a documentation/process module with no runtime simulation logic.
It supports project management rather than agent simulation.
"""

from .types import (
    # Enums
    ChangeType,
    Urgency,
    ModuleStatus,
    EntryState,
    Visibility,
    DependencyType,
    ErrorType,
    
    # Core types
    Version,
    ChangelogEntry,
    VersionTableEntry,
    FreezeRecord,
    TraceabilityEntry,
    RevisionReport,
    RevisionReportMetadata,
    RevisionReportSummary,
    
    # Input types
    ModuleUpdateNotification,
    VersionIncrementRequest,
    FreezeRequest,
    DependencyDeclaration,
    ErrorReport,
    
    # Validation
    ValidationError,
    ValidationResult,
)

from .changelog_manager import ChangelogManager
from .validators import ChangelogValidator
from .utils import (
    MarkdownFormatter,
    FileSystemHelper,
    VersionHelper,
)

__version__ = "1.0.0"

__all__ = [
    # Enums
    "ChangeType",
    "Urgency",
    "ModuleStatus",
    "EntryState",
    "Visibility",
    "DependencyType",
    "ErrorType",
    
    # Core types
    "Version",
    "ChangelogEntry",
    "VersionTableEntry",
    "FreezeRecord",
    "TraceabilityEntry",
    "RevisionReport",
    "RevisionReportMetadata",
    "RevisionReportSummary",
    
    # Input types
    "ModuleUpdateNotification",
    "VersionIncrementRequest",
    "FreezeRequest",
    "DependencyDeclaration",
    "ErrorReport",
    
    # Validation
    "ValidationError",
    "ValidationResult",
    
    # Manager
    "ChangelogManager",
    "ChangelogValidator",
    
    # Utilities
    "MarkdownFormatter",
    "FileSystemHelper",
    "VersionHelper",
]
