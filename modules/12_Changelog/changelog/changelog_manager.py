"""
Changelog Manager - Core functionality for managing changelog entries and version control.

This module provides the primary interface for creating, storing, retrieving, and
validating changelog entries according to the specification and data contract.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional
from .types import (
    ChangelogEntry,
    VersionTableEntry,
    FreezeRecord,
    RevisionReport,
    RevisionReportMetadata,
    RevisionReportSummary,
    Version,
    ChangeType,
    ModuleStatus,
    EntryState,
)
from .validators import ChangelogValidator


class ChangelogManager:
    """
    Main interface for changelog management operations.
    
    This class handles:
    - Creating and storing changelog entries
    - Managing version tables
    - Recording freeze events
    - Generating reports
    - Validating entries
    
    Storage is file-based using structured formats (JSON/Markdown).
    """
    
    def __init__(self, base_directory: str):
        """
        Initialize changelog manager.
        
        Args:
            base_directory: Root directory for changelog storage
        """
        self.base_dir = Path(base_directory)
        self.entries_dir = self.base_dir / "entries"
        self.tables_dir = self.base_dir / "tables"
        self.matrices_dir = self.base_dir / "matrices"
        self.reports_dir = self.base_dir / "reports"
        self.freezes_dir = self.base_dir / "freezes"
        
        # Create directory structure if needed
        self._ensure_directories()
        
        self.validator = ChangelogValidator()
    
    def _ensure_directories(self) -> None:
        """Create directory structure if it doesn't exist."""
        for directory in [
            self.entries_dir,
            self.tables_dir,
            self.matrices_dir,
            self.reports_dir,
            self.freezes_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def generate_entry_id(self, date_obj: Optional[date] = None) -> str:
        """
        Generate unique changelog entry ID.
        
        Format: CL-YYYYMMDD-NNN
        
        Args:
            date_obj: Date for entry (defaults to today)
            
        Returns:
            Generated entry ID
        """
        if date_obj is None:
            date_obj = date.today()
        
        date_str = date_obj.strftime("%Y%m%d")
        
        # Find existing entries for this date
        pattern = f"CL-{date_str}-*.json"
        year_dir = self.entries_dir / str(date_obj.year)
        month_dir = year_dir / f"{date_obj.month:02d}"
        
        if not month_dir.exists():
            sequence = 1
        else:
            existing = list(month_dir.glob(pattern))
            if not existing:
                sequence = 1
            else:
                # Extract sequence numbers and find max
                sequences = []
                for path in existing:
                    try:
                        seq_str = path.stem.split('-')[-1]
                        sequences.append(int(seq_str))
                    except (ValueError, IndexError):
                        continue
                sequence = max(sequences) + 1 if sequences else 1
        
        return f"CL-{date_str}-{sequence:03d}"
    
    def create_entry(
        self,
        module: str,
        version_from: Version,
        version_to: Version,
        change_type: ChangeType,
        summary: str,
        rationale: str,
        files_modified: List[str],
        author: str,
        reviewer: str,
        related_entries: Optional[List[str]] = None,
        **kwargs
    ) -> ChangelogEntry:
        """
        Create a new changelog entry.
        
        Args:
            module: Module identifier
            version_from: Previous version
            version_to: New version
            change_type: Type of change (MAJOR/MINOR/PATCH)
            summary: Brief description (≤200 chars)
            rationale: Detailed explanation
            files_modified: List of modified file paths
            author: Person responsible
            reviewer: Person who approved
            related_entries: Related changelog entry IDs
            **kwargs: Optional fields (impact_assessment, migration_notes, etc.)
            
        Returns:
            Created ChangelogEntry
            
        Raises:
            ValueError: If validation fails
        """
        # Generate entry ID
        entry_id = self.generate_entry_id()
        entry_date = date.today()
        
        # Create entry
        entry = ChangelogEntry(
            entry_id=entry_id,
            date=entry_date,
            module=module,
            version_from=version_from,
            version_to=version_to,
            change_type=change_type,
            summary=summary,
            rationale=rationale,
            files_modified=files_modified,
            author=author,
            reviewer=reviewer,
            related_entries=related_entries or [],
            creation_timestamp=datetime.now(),
            last_modified_timestamp=datetime.now(),
            state=EntryState.DRAFT,
            **kwargs
        )
        
        # Validate
        validation = self.validator.validate_entry(entry)
        if not validation.is_valid:
            error_msgs = [e.message for e in validation.errors]
            raise ValueError(f"Entry validation failed: {'; '.join(error_msgs)}")
        
        return entry
    
    def save_entry(self, entry: ChangelogEntry) -> Path:
        """
        Save changelog entry to disk.
        
        Args:
            entry: ChangelogEntry to save
            
        Returns:
            Path where entry was saved
        """
        # Determine directory structure: entries/YYYY/MM/
        entry_date = entry.date
        year_dir = self.entries_dir / str(entry_date.year)
        month_dir = year_dir / f"{entry_date.month:02d}"
        month_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        file_path = month_dir / f"{entry.entry_id}.json"
        
        # Convert to dict for JSON serialization
        entry_dict = self._entry_to_dict(entry)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(entry_dict, f, indent=2, ensure_ascii=False, default=str)
        
        return file_path
    
    def load_entry(self, entry_id: str) -> Optional[ChangelogEntry]:
        """
        Load changelog entry by ID.
        
        Args:
            entry_id: Entry ID to load
            
        Returns:
            ChangelogEntry if found, None otherwise
        """
        # Parse date from entry_id (format: CL-YYYYMMDD-NNN)
        try:
            date_part = entry_id.split('-')[1]
            year = int(date_part[:4])
            month = int(date_part[4:6])
        except (IndexError, ValueError):
            return None
        
        file_path = self.entries_dir / str(year) / f"{month:02d}" / f"{entry_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            entry_dict = json.load(f)
        
        return self._dict_to_entry(entry_dict)
    
    def get_entries_for_module(
        self,
        module_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[ChangelogEntry]:
        """
        Retrieve all changelog entries for a specific module.
        
        Args:
            module_id: Module identifier
            start_date: Optional filter start date
            end_date: Optional filter end date
            
        Returns:
            List of matching ChangelogEntry objects
        """
        entries = []
        
        # Walk through all entry files
        for year_dir in sorted(self.entries_dir.iterdir()):
            if not year_dir.is_dir():
                continue
            
            for month_dir in sorted(year_dir.iterdir()):
                if not month_dir.is_dir():
                    continue
                
                for entry_file in sorted(month_dir.glob("CL-*.json")):
                    entry = self.load_entry(entry_file.stem)
                    if entry and entry.module == module_id:
                        # Apply date filters
                        if start_date and entry.date < start_date:
                            continue
                        if end_date and entry.date > end_date:
                            continue
                        entries.append(entry)
        
        return entries
    
    def update_version_table(
        self,
        module_id: str,
        current_version: Version,
        status: ModuleStatus,
        freeze_date: Optional[date] = None,
        supersedes: Optional[Version] = None
    ) -> None:
        """
        Update the version table with current module status.
        
        Args:
            module_id: Module identifier
            current_version: Current version number
            status: Module status
            freeze_date: Date of freeze (if applicable)
            supersedes: Previous version this supersedes
        """
        table_path = self.tables_dir / "version_table.json"
        
        # Load existing table
        if table_path.exists():
            with open(table_path, 'r', encoding='utf-8') as f:
                table_data = json.load(f)
        else:
            table_data = {}
        
        # Update entry
        entry = VersionTableEntry(
            module_id=module_id,
            current_version=current_version,
            status=status,
            freeze_date=freeze_date,
            supersedes=supersedes
        )
        
        table_data[module_id] = {
            "current_version": str(current_version),
            "status": status.value,
            "freeze_date": freeze_date.isoformat() if freeze_date else None,
            "supersedes": str(supersedes) if supersedes else None,
        }
        
        # Save updated table
        with open(table_path, 'w', encoding='utf-8') as f:
            json.dump(table_data, f, indent=2)
    
    def record_freeze(
        self,
        module_id: str,
        version: Version,
        approver_id: str,
        archive_location: str,
        checksum: str
    ) -> FreezeRecord:
        """
        Record a module version freeze.
        
        Args:
            module_id: Module identifier
            version: Version being frozen
            approver_id: Person who approved freeze
            archive_location: Path/URI to archived files
            checksum: Hash of archived content
            
        Returns:
            Created FreezeRecord
        """
        freeze_id = f"FREEZE-{module_id}-{version}"
        freeze_date = date.today()
        
        record = FreezeRecord(
            freeze_id=freeze_id,
            module_id=module_id,
            version=version,
            freeze_date=freeze_date,
            approver_id=approver_id,
            archive_location=archive_location,
            checksum=checksum
        )
        
        # Save freeze record
        file_path = self.freezes_dir / f"{freeze_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "freeze_id": record.freeze_id,
                "module_id": record.module_id,
                "version": str(record.version),
                "freeze_date": record.freeze_date.isoformat(),
                "approver_id": record.approver_id,
                "archive_location": record.archive_location,
                "checksum": record.checksum,
            }, f, indent=2)
        
        # Update version table
        self.update_version_table(
            module_id=module_id,
            current_version=version,
            status=ModuleStatus.FROZEN,
            freeze_date=freeze_date
        )
        
        return record
    
    def generate_revision_report(
        self,
        start_date: date,
        end_date: date,
        generated_by: str
    ) -> RevisionReport:
        """
        Generate a revision report for a time period.
        
        Args:
            start_date: Report period start
            end_date: Report period end
            generated_by: Person generating report
            
        Returns:
            RevisionReport
        """
        # Collect all entries in period
        all_entries = []
        for year_dir in sorted(self.entries_dir.iterdir()):
            if not year_dir.is_dir():
                continue
            for month_dir in sorted(year_dir.iterdir()):
                if not month_dir.is_dir():
                    continue
                for entry_file in sorted(month_dir.glob("CL-*.json")):
                    entry = self.load_entry(entry_file.stem)
                    if entry and start_date <= entry.date <= end_date:
                        all_entries.append(entry)
        
        # Calculate summary statistics
        count_by_type = {
            ChangeType.MAJOR: 0,
            ChangeType.MINOR: 0,
            ChangeType.PATCH: 0
        }
        modules_updated = set()
        authors_contributing = set()
        
        for entry in all_entries:
            count_by_type[entry.change_type] += 1
            modules_updated.add(entry.module)
            authors_contributing.add(entry.author)
        
        # Create report
        metadata = RevisionReportMetadata(
            report_id=f"REV-{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}",
            generation_date=date.today(),
            reporting_period_start=start_date,
            reporting_period_end=end_date,
            generated_by=generated_by
        )
        
        summary = RevisionReportSummary(
            total_entries=len(all_entries),
            count_by_type=count_by_type,
            modules_updated=sorted(list(modules_updated)),
            authors_contributing=sorted(list(authors_contributing))
        )
        
        return RevisionReport(
            metadata=metadata,
            summary=summary,
            detailed_entries=all_entries,
            outstanding_issues=[]  # TODO: Implement issue tracking
        )
    
    # Helper methods for serialization
    
    def _entry_to_dict(self, entry: ChangelogEntry) -> dict:
        """Convert ChangelogEntry to dictionary for JSON serialization."""
        return {
            "entry_id": entry.entry_id,
            "date": entry.date.isoformat(),
            "module": entry.module,
            "version_from": str(entry.version_from),
            "version_to": str(entry.version_to),
            "change_type": entry.change_type.value,
            "summary": entry.summary,
            "rationale": entry.rationale,
            "files_modified": entry.files_modified,
            "author": entry.author,
            "reviewer": entry.reviewer,
            "related_entries": entry.related_entries,
            "external_references": entry.external_references,
            "impact_assessment": entry.impact_assessment,
            "migration_notes": entry.migration_notes,
            "tags": entry.tags,
            "creation_timestamp": entry.creation_timestamp.isoformat() if entry.creation_timestamp else None,
            "last_modified_timestamp": entry.last_modified_timestamp.isoformat() if entry.last_modified_timestamp else None,
            "state": entry.state.value,
            "visibility": entry.visibility.value,
        }
    
    def _dict_to_entry(self, data: dict) -> ChangelogEntry:
        """Convert dictionary to ChangelogEntry."""
        return ChangelogEntry(
            entry_id=data["entry_id"],
            date=date.fromisoformat(data["date"]),
            module=data["module"],
            version_from=Version.from_string(data["version_from"]),
            version_to=Version.from_string(data["version_to"]),
            change_type=ChangeType(data["change_type"]),
            summary=data["summary"],
            rationale=data["rationale"],
            files_modified=data["files_modified"],
            author=data["author"],
            reviewer=data["reviewer"],
            related_entries=data.get("related_entries", []),
            external_references=data.get("external_references", []),
            impact_assessment=data.get("impact_assessment"),
            migration_notes=data.get("migration_notes"),
            tags=data.get("tags", []),
            creation_timestamp=datetime.fromisoformat(data["creation_timestamp"]) if data.get("creation_timestamp") else None,
            last_modified_timestamp=datetime.fromisoformat(data["last_modified_timestamp"]) if data.get("last_modified_timestamp") else None,
            state=EntryState(data.get("state", "DRAFT")),
            visibility=data.get("visibility", "INTERNAL"),
        )
