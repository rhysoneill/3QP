"""
Validators - Validation logic for changelog entries and related data.

This module implements the validation rules specified in the data contract
to ensure changelog entries, version numbers, and other data meet requirements.
"""

from datetime import date
from typing import List
from .types import (
    ChangelogEntry,
    Version,
    ChangeType,
    ValidationResult,
    ValidationError,
    VersionIncrementRequest,
    FreezeRequest,
)


class ChangelogValidator:
    """
    Validator for changelog entries and related structures.
    
    Implements validation rules from data contract section 6 and 7.
    """
    
    def validate_entry(self, entry: ChangelogEntry) -> ValidationResult:
        """
        Validate a complete changelog entry.
        
        Args:
            entry: ChangelogEntry to validate
            
        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []
        
        # Required field validation
        if not entry.entry_id:
            errors.append(ValidationError("entry_id", "Entry ID is required", "ERROR"))
        elif not self._is_valid_entry_id(entry.entry_id):
            errors.append(ValidationError(
                "entry_id",
                "Entry ID must follow format CL-YYYYMMDD-NNN",
                "ERROR"
            ))
        
        if not entry.module:
            errors.append(ValidationError("module", "Module ID is required", "ERROR"))
        
        if not entry.summary:
            errors.append(ValidationError("summary", "Summary is required", "ERROR"))
        elif len(entry.summary) > 200:
            errors.append(ValidationError(
                "summary",
                f"Summary must be ≤200 characters (got {len(entry.summary)})",
                "ERROR"
            ))
        
        if not entry.rationale:
            errors.append(ValidationError("rationale", "Rationale is required", "ERROR"))
        elif len(entry.rationale) < 100:
            warnings.append(ValidationError(
                "rationale",
                f"Rationale should be ≥100 characters for clarity (got {len(entry.rationale)})",
                "WARNING"
            ))
        
        if not entry.files_modified:
            errors.append(ValidationError(
                "files_modified",
                "At least one modified file must be listed",
                "ERROR"
            ))
        
        if not entry.author:
            errors.append(ValidationError("author", "Author is required", "ERROR"))
        
        if not entry.reviewer:
            errors.append(ValidationError("reviewer", "Reviewer is required", "ERROR"))
        
        # Version validation
        version_errors = self._validate_version_increment(
            entry.version_from,
            entry.version_to,
            entry.change_type
        )
        errors.extend(version_errors)
        
        # Date validation
        if entry.date > date.today():
            errors.append(ValidationError(
                "date",
                "Entry date cannot be in the future",
                "ERROR"
            ))
        
        # Entry ID date consistency
        if not self._entry_id_matches_date(entry.entry_id, entry.date):
            errors.append(ValidationError(
                "entry_id",
                "Entry ID date does not match entry date",
                "ERROR"
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_version_increment_request(
        self,
        request: VersionIncrementRequest
    ) -> ValidationResult:
        """
        Validate a version increment request.
        
        Args:
            request: VersionIncrementRequest to validate
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        # Check version increment matches change type
        version_errors = self._validate_version_increment(
            request.current_version,
            request.proposed_version,
            request.change_type
        )
        errors.extend(version_errors)
        
        # Check rationale length
        if len(request.rationale) < 100:
            errors.append(ValidationError(
                "rationale",
                "Rationale must be at least 100 characters",
                "ERROR"
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_freeze_request(self, request: FreezeRequest) -> ValidationResult:
        """
        Validate a freeze request.
        
        Args:
            request: FreezeRequest to validate
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        if not request.checklist_complete:
            errors.append(ValidationError(
                "checklist_complete",
                "Checklist must be complete before freezing",
                "ERROR"
            ))
        
        if request.approval_date > date.today():
            errors.append(ValidationError(
                "approval_date",
                "Approval date cannot be in the future",
                "ERROR"
            ))
        
        # Check version is not a pre-release
        if request.version.prerelease:
            errors.append(ValidationError(
                "version",
                "Cannot freeze a pre-release version",
                "ERROR"
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_version_increment(
        self,
        version_from: Version,
        version_to: Version,
        change_type: ChangeType
    ) -> List[ValidationError]:
        """
        Validate that version increment follows semantic versioning rules.
        
        Args:
            version_from: Previous version
            version_to: New version
            change_type: Declared change type
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check versions are not identical
        if str(version_from) == str(version_to):
            errors.append(ValidationError(
                "version",
                "Version must change",
                "ERROR"
            ))
            return errors
        
        # Calculate expected version
        expected_version = version_from.increment(change_type)
        
        # Check if actual matches expected
        if str(version_to) != str(expected_version):
            errors.append(ValidationError(
                "version",
                f"Version increment does not match change type. "
                f"Expected {expected_version} for {change_type.value}, got {version_to}",
                "ERROR"
            ))
        
        # Additional checks for specific change types
        if change_type == ChangeType.MAJOR:
            if version_to.major != version_from.major + 1:
                errors.append(ValidationError(
                    "version",
                    "MAJOR change must increment major version by exactly 1",
                    "ERROR"
                ))
            if version_to.minor != 0 or version_to.patch != 0:
                errors.append(ValidationError(
                    "version",
                    "MAJOR change must reset minor and patch to 0",
                    "ERROR"
                ))
        
        elif change_type == ChangeType.MINOR:
            if version_to.major != version_from.major:
                errors.append(ValidationError(
                    "version",
                    "MINOR change must not change major version",
                    "ERROR"
                ))
            if version_to.minor != version_from.minor + 1:
                errors.append(ValidationError(
                    "version",
                    "MINOR change must increment minor version by exactly 1",
                    "ERROR"
                ))
            if version_to.patch != 0:
                errors.append(ValidationError(
                    "version",
                    "MINOR change must reset patch to 0",
                    "ERROR"
                ))
        
        elif change_type == ChangeType.PATCH:
            if version_to.major != version_from.major:
                errors.append(ValidationError(
                    "version",
                    "PATCH change must not change major version",
                    "ERROR"
                ))
            if version_to.minor != version_from.minor:
                errors.append(ValidationError(
                    "version",
                    "PATCH change must not change minor version",
                    "ERROR"
                ))
            if version_to.patch != version_from.patch + 1:
                errors.append(ValidationError(
                    "version",
                    "PATCH change must increment patch version by exactly 1",
                    "ERROR"
                ))
        
        return errors
    
    def _is_valid_entry_id(self, entry_id: str) -> bool:
        """
        Check if entry ID follows required format: CL-YYYYMMDD-NNN
        
        Args:
            entry_id: Entry ID to validate
            
        Returns:
            True if valid format
        """
        if not entry_id.startswith("CL-"):
            return False
        
        parts = entry_id.split('-')
        if len(parts) != 3:
            return False
        
        # Check date part (YYYYMMDD)
        date_part = parts[1]
        if len(date_part) != 8:
            return False
        
        try:
            year = int(date_part[:4])
            month = int(date_part[4:6])
            day = int(date_part[6:8])
            # Validate it's a real date
            date(year, month, day)
        except (ValueError, TypeError):
            return False
        
        # Check sequence part (NNN)
        seq_part = parts[2]
        if len(seq_part) != 3:
            return False
        
        try:
            int(seq_part)
        except ValueError:
            return False
        
        return True
    
    def _entry_id_matches_date(self, entry_id: str, entry_date: date) -> bool:
        """
        Check if entry ID date component matches the entry date.
        
        Args:
            entry_id: Entry ID
            entry_date: Entry date
            
        Returns:
            True if dates match
        """
        if not self._is_valid_entry_id(entry_id):
            return False
        
        date_part = entry_id.split('-')[1]
        expected_date_str = entry_date.strftime("%Y%m%d")
        
        return date_part == expected_date_str
