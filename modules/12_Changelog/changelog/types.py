"""
Module 12: Changelog & Notes - Type Definitions

This module defines data structures for version control and change documentation
as specified in the data contract. These types support changelog entries,
version tracking, dependency management, and freeze records.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional


class ChangeType(Enum):
    """Type of change according to semantic versioning."""
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    PATCH = "PATCH"


class Urgency(Enum):
    """Urgency level for module update notifications."""
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"


class ModuleStatus(Enum):
    """Lifecycle status of a module version."""
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    FROZEN = "FROZEN"
    DEPRECATED = "DEPRECATED"


class EntryState(Enum):
    """State of a changelog entry."""
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"


class Visibility(Enum):
    """Visibility level of changelog entries."""
    INTERNAL = "INTERNAL"
    PUBLIC = "PUBLIC"


class DependencyType(Enum):
    """Type of cross-module dependency."""
    INFORMATIONAL = "INFORMATIONAL"
    STRUCTURAL = "STRUCTURAL"
    DATA_FLOW = "DATA_FLOW"


class ErrorType(Enum):
    """Type of version control error."""
    INCORRECT_VERSION = "INCORRECT_VERSION"
    MISSING_ENTRY = "MISSING_ENTRY"
    CONFLICT = "CONFLICT"
    CORRUPTION = "CORRUPTION"


@dataclass
class Version:
    """
    Semantic version number.
    
    Format: MAJOR.MINOR.PATCH[-prerelease]
    """
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of version."""
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            return f"{base}-{self.prerelease}"
        return base
    
    @classmethod
    def from_string(cls, version_str: str) -> 'Version':
        """
        Parse version from string format.
        
        Args:
            version_str: Version string (e.g., "1.2.3" or "1.2.3-draft.1")
            
        Returns:
            Version instance
            
        Raises:
            ValueError: If version string is invalid
        """
        if '-' in version_str:
            base, prerelease = version_str.split('-', 1)
        else:
            base = version_str
            prerelease = None
        
        parts = base.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")
        
        try:
            major, minor, patch = map(int, parts)
        except ValueError:
            raise ValueError(f"Version parts must be integers: {version_str}")
        
        return cls(major=major, minor=minor, patch=patch, prerelease=prerelease)
    
    def increment(self, change_type: ChangeType) -> 'Version':
        """
        Create new version by incrementing according to change type.
        
        Args:
            change_type: Type of version increment
            
        Returns:
            New Version instance
        """
        if change_type == ChangeType.MAJOR:
            return Version(major=self.major + 1, minor=0, patch=0)
        elif change_type == ChangeType.MINOR:
            return Version(major=self.major, minor=self.minor + 1, patch=0)
        else:  # PATCH
            return Version(major=self.major, minor=self.minor, patch=self.patch + 1)


@dataclass
class ModuleUpdateNotification:
    """
    Notification of a module modification.
    
    Required input as specified in data contract section 2.1.
    """
    module_id: str
    files_modified: List[str]
    modification_summary: str
    author_id: str
    timestamp: datetime
    related_modules: List[str] = field(default_factory=list)
    urgency: Urgency = Urgency.ROUTINE


@dataclass
class VersionIncrementRequest:
    """
    Request to assign a new version number.
    
    Required input as specified in data contract section 2.2.
    """
    module_id: str
    current_version: Version
    proposed_version: Version
    change_type: ChangeType
    rationale: str
    author_id: str


@dataclass
class FreezeRequest:
    """
    Request to freeze a module version.
    
    Required input as specified in data contract section 2.3.
    """
    module_id: str
    version: Version
    reviewer_id: str
    approval_date: date
    checklist_complete: bool


@dataclass
class DependencyDeclaration:
    """
    Cross-module dependency declaration.
    
    Required input as specified in data contract section 2.4.
    """
    source_module: str
    target_module: str
    dependency_type: DependencyType
    version_constraint: str


@dataclass
class ErrorReport:
    """
    Report of a version control error.
    
    Required input as specified in data contract section 2.5.
    """
    error_type: ErrorType
    description: str
    affected_modules: List[str]
    reporter_id: str
    discovery_date: date


@dataclass
class ChangelogEntry:
    """
    Structured changelog entry.
    
    Output format as specified in data contract section 3.1.
    """
    entry_id: str
    date: date
    module: str
    version_from: Version
    version_to: Version
    change_type: ChangeType
    summary: str
    rationale: str
    files_modified: List[str]
    author: str
    reviewer: str
    related_entries: List[str] = field(default_factory=list)
    
    # Optional fields
    external_references: List[str] = field(default_factory=list)
    impact_assessment: Optional[str] = None
    migration_notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Metadata
    creation_timestamp: Optional[datetime] = None
    last_modified_timestamp: Optional[datetime] = None
    state: EntryState = EntryState.DRAFT
    visibility: Visibility = Visibility.INTERNAL


@dataclass
class VersionTableEntry:
    """
    Entry in the system-wide version table.
    
    Output format as specified in data contract section 3.2.
    """
    module_id: str
    current_version: Version
    status: ModuleStatus
    freeze_date: Optional[date] = None
    supersedes: Optional[Version] = None


@dataclass
class FreezeRecord:
    """
    Record of a frozen version.
    
    Output format as specified in data contract section 3.5.
    """
    freeze_id: str
    module_id: str
    version: Version
    freeze_date: date
    approver_id: str
    archive_location: str
    checksum: str


@dataclass
class TraceabilityEntry:
    """
    Entry in the traceability matrix.
    
    Output format as specified in data contract section 3.4.
    """
    source_module: str
    target_module: str
    dependency_type: DependencyType
    source_version: Version
    target_version_required: str
    last_verified: date


@dataclass
class RevisionReportMetadata:
    """
    Metadata for revision reports.
    
    Part of output format specified in data contract section 3.3.
    """
    report_id: str
    generation_date: date
    reporting_period_start: date
    reporting_period_end: date
    generated_by: str


@dataclass
class RevisionReportSummary:
    """
    Summary statistics for revision reports.
    
    Part of output format specified in data contract section 3.3.
    """
    total_entries: int
    count_by_type: dict[ChangeType, int]
    modules_updated: List[str]
    authors_contributing: List[str]


@dataclass
class RevisionReport:
    """
    Complete revision report.
    
    Output format as specified in data contract section 3.3.
    """
    metadata: RevisionReportMetadata
    summary: RevisionReportSummary
    detailed_entries: List[ChangelogEntry]
    outstanding_issues: List[str]


@dataclass
class ValidationError:
    """Error found during validation."""
    field: str
    message: str
    severity: str  # "ERROR", "WARNING"


@dataclass
class ValidationResult:
    """Result of validating a changelog entry or request."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
