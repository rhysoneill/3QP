"""
Tests for Changelog & Notes module.

This module tests version control, changelog entry creation, validation,
and other functionality defined in the data contract and specification.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import date, datetime

from changelog import (
    ChangelogManager,
    ChangelogValidator,
    Version,
    ChangeType,
    ChangelogEntry,
    ModuleStatus,
    EntryState,
    VersionIncrementRequest,
    FreezeRequest,
    MarkdownFormatter,
    VersionHelper,
)


class TestVersion:
    """Test Version class functionality."""
    
    def test_version_string_representation(self):
        """Test version to string conversion."""
        v = Version(major=1, minor=2, patch=3)
        assert str(v) == "1.2.3"
        
        v_pre = Version(major=1, minor=2, patch=3, prerelease="draft.1")
        assert str(v_pre) == "1.2.3-draft.1"
    
    def test_version_from_string(self):
        """Test parsing version from string."""
        v = Version.from_string("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert v.prerelease is None
        
        v_pre = Version.from_string("2.0.0-draft.5")
        assert v_pre.major == 2
        assert v_pre.minor == 0
        assert v_pre.patch == 0
        assert v_pre.prerelease == "draft.5"
    
    def test_version_from_string_invalid(self):
        """Test error handling for invalid version strings."""
        with pytest.raises(ValueError):
            Version.from_string("1.2")
        
        with pytest.raises(ValueError):
            Version.from_string("a.b.c")
    
    def test_version_increment_major(self):
        """Test MAJOR version increment."""
        v = Version(1, 5, 3)
        new_v = v.increment(ChangeType.MAJOR)
        assert str(new_v) == "2.0.0"
    
    def test_version_increment_minor(self):
        """Test MINOR version increment."""
        v = Version(1, 5, 3)
        new_v = v.increment(ChangeType.MINOR)
        assert str(new_v) == "1.6.0"
    
    def test_version_increment_patch(self):
        """Test PATCH version increment."""
        v = Version(1, 5, 3)
        new_v = v.increment(ChangeType.PATCH)
        assert str(new_v) == "1.5.4"


class TestChangelogValidator:
    """Test validation logic."""
    
    def test_valid_entry_id_format(self):
        """Test entry ID format validation."""
        validator = ChangelogValidator()
        
        assert validator._is_valid_entry_id("CL-20251201-001")
        assert validator._is_valid_entry_id("CL-20250115-999")
        
        assert not validator._is_valid_entry_id("CL-2025121-001")  # Wrong date format
        assert not validator._is_valid_entry_id("CL-20251201-01")   # Wrong sequence format
        assert not validator._is_valid_entry_id("LOG-20251201-001") # Wrong prefix
    
    def test_entry_id_date_matching(self):
        """Test entry ID date matches entry date."""
        validator = ChangelogValidator()
        
        assert validator._entry_id_matches_date(
            "CL-20251201-001",
            date(2025, 12, 1)
        )
        
        assert not validator._entry_id_matches_date(
            "CL-20251201-001",
            date(2025, 12, 2)
        )
    
    def test_version_increment_validation(self):
        """Test version increment validation."""
        validator = ChangelogValidator()
        
        # Valid MAJOR increment
        errors = validator._validate_version_increment(
            Version(1, 5, 3),
            Version(2, 0, 0),
            ChangeType.MAJOR
        )
        assert len(errors) == 0
        
        # Invalid MAJOR increment (didn't reset minor/patch)
        errors = validator._validate_version_increment(
            Version(1, 5, 3),
            Version(2, 1, 0),
            ChangeType.MAJOR
        )
        assert len(errors) > 0
        
        # Valid MINOR increment
        errors = validator._validate_version_increment(
            Version(1, 5, 3),
            Version(1, 6, 0),
            ChangeType.MINOR
        )
        assert len(errors) == 0
        
        # Valid PATCH increment
        errors = validator._validate_version_increment(
            Version(1, 5, 3),
            Version(1, 5, 4),
            ChangeType.PATCH
        )
        assert len(errors) == 0
    
    def test_version_increment_request_validation(self):
        """Test version increment request validation."""
        validator = ChangelogValidator()
        
        # Valid request
        request = VersionIncrementRequest(
            module_id="01_TQP_Core",
            current_version=Version(1, 0, 0),
            proposed_version=Version(1, 1, 0),
            change_type=ChangeType.MINOR,
            rationale="A" * 150,  # Long enough
            author_id="test_author"
        )
        
        result = validator.validate_version_increment_request(request)
        assert result.is_valid
        
        # Invalid: rationale too short
        request.rationale = "Too short"
        result = validator.validate_version_increment_request(request)
        assert not result.is_valid
    
    def test_freeze_request_validation(self):
        """Test freeze request validation."""
        validator = ChangelogValidator()
        
        # Valid request
        request = FreezeRequest(
            module_id="01_TQP_Core",
            version=Version(1, 0, 0),
            reviewer_id="reviewer",
            approval_date=date.today(),
            checklist_complete=True
        )
        
        result = validator.validate_freeze_request(request)
        assert result.is_valid
        
        # Invalid: pre-release version
        request.version = Version(1, 0, 0, prerelease="draft.1")
        result = validator.validate_freeze_request(request)
        assert not result.is_valid
        
        # Invalid: checklist not complete
        request.version = Version(1, 0, 0)
        request.checklist_complete = False
        result = validator.validate_freeze_request(request)
        assert not result.is_valid


class TestChangelogManager:
    """Test ChangelogManager functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    @pytest.fixture
    def manager(self, temp_dir):
        """Create ChangelogManager instance."""
        return ChangelogManager(str(temp_dir))
    
    def test_initialization(self, manager, temp_dir):
        """Test manager initializes directory structure."""
        assert (temp_dir / "entries").exists()
        assert (temp_dir / "tables").exists()
        assert (temp_dir / "matrices").exists()
        assert (temp_dir / "reports").exists()
        assert (temp_dir / "freezes").exists()
    
    def test_generate_entry_id(self, manager):
        """Test entry ID generation."""
        entry_id = manager.generate_entry_id(date(2025, 12, 1))
        assert entry_id.startswith("CL-20251201-")
        assert len(entry_id) == 15  # CL-YYYYMMDD-NNN (e.g., CL-20251201-001)
    
    def test_create_entry(self, manager):
        """Test creating a changelog entry."""
        entry = manager.create_entry(
            module="01_TQP_Core",
            version_from=Version(1, 0, 0),
            version_to=Version(1, 1, 0),
            change_type=ChangeType.MINOR,
            summary="Added new feature",
            rationale="This feature is needed because " + "x" * 100,
            files_modified=["spec.md", "data_contract.md"],
            author="test_author",
            reviewer="test_reviewer"
        )
        
        assert entry.module == "01_TQP_Core"
        assert str(entry.version_from) == "1.0.0"
        assert str(entry.version_to) == "1.1.0"
        assert entry.change_type == ChangeType.MINOR
    
    def test_create_entry_invalid(self, manager):
        """Test creating invalid entry raises error."""
        with pytest.raises(ValueError):
            manager.create_entry(
                module="01_TQP_Core",
                version_from=Version(1, 0, 0),
                version_to=Version(1, 1, 0),
                change_type=ChangeType.MINOR,
                summary="",  # Empty summary - invalid
                rationale="Short",  # Too short
                files_modified=["spec.md"],
                author="test_author",
                reviewer="test_reviewer"
            )
    
    def test_save_and_load_entry(self, manager):
        """Test saving and loading entries."""
        entry = manager.create_entry(
            module="01_TQP_Core",
            version_from=Version(1, 0, 0),
            version_to=Version(1, 0, 1),
            change_type=ChangeType.PATCH,
            summary="Fixed typo in documentation",
            rationale="Documentation contained incorrect reference that could mislead users",
            files_modified=["README.md"],
            author="test_author",
            reviewer="test_reviewer"
        )
        
        # Save entry
        path = manager.save_entry(entry)
        assert path.exists()
        
        # Load entry
        loaded = manager.load_entry(entry.entry_id)
        assert loaded is not None
        assert loaded.module == entry.module
        assert str(loaded.version_from) == str(entry.version_from)
        assert str(loaded.version_to) == str(entry.version_to)
    
    def test_get_entries_for_module(self, manager):
        """Test retrieving entries by module."""
        # Create multiple entries
        for i in range(3):
            entry = manager.create_entry(
                module="01_TQP_Core",
                version_from=Version(1, 0, i),
                version_to=Version(1, 0, i + 1),
                change_type=ChangeType.PATCH,
                summary=f"Change {i}",
                rationale="x" * 100,
                files_modified=["file.md"],
                author="author",
                reviewer="reviewer"
            )
            manager.save_entry(entry)
        
        # Create entry for different module
        other_entry = manager.create_entry(
            module="02_Breakthrough_Impact",
            version_from=Version(1, 0, 0),
            version_to=Version(1, 1, 0),
            change_type=ChangeType.MINOR,
            summary="Other module change",
            rationale="y" * 100,
            files_modified=["spec.md"],
            author="author",
            reviewer="reviewer"
        )
        manager.save_entry(other_entry)
        
        # Retrieve entries for first module
        entries = manager.get_entries_for_module("01_TQP_Core")
        assert len(entries) == 3
        assert all(e.module == "01_TQP_Core" for e in entries)
    
    def test_update_version_table(self, manager):
        """Test version table updates."""
        manager.update_version_table(
            module_id="01_TQP_Core",
            current_version=Version(1, 0, 0),
            status=ModuleStatus.FROZEN,
            freeze_date=date(2025, 12, 1)
        )
        
        table_path = manager.tables_dir / "version_table.json"
        assert table_path.exists()
    
    def test_record_freeze(self, manager):
        """Test recording a freeze."""
        record = manager.record_freeze(
            module_id="01_TQP_Core",
            version=Version(1, 0, 0),
            approver_id="tech_lead",
            archive_location="/archives/01_TQP_Core/v1.0.0",
            checksum="abc123def456"
        )
        
        assert record.module_id == "01_TQP_Core"
        assert str(record.version) == "1.0.0"
        
        # Check freeze file was created
        freeze_path = manager.freezes_dir / f"{record.freeze_id}.json"
        assert freeze_path.exists()


class TestMarkdownFormatter:
    """Test Markdown formatting utilities."""
    
    def test_format_entry(self):
        """Test formatting changelog entry as Markdown."""
        entry = ChangelogEntry(
            entry_id="CL-20251201-001",
            date=date(2025, 12, 1),
            module="01_TQP_Core",
            version_from=Version(1, 0, 0),
            version_to=Version(1, 1, 0),
            change_type=ChangeType.MINOR,
            summary="Added new feature",
            rationale="Feature needed for XYZ",
            files_modified=["spec.md"],
            author="author",
            reviewer="reviewer",
            related_entries=[],
            state=EntryState.APPROVED
        )
        
        markdown = MarkdownFormatter.format_entry(entry)
        
        assert "## Entry: CL-20251201-001" in markdown
        assert "**Module**: 01_TQP_Core" in markdown
        assert "**Version**: 1.0.0 → 1.1.0" in markdown


class TestVersionHelper:
    """Test version helper utilities."""
    
    def test_parse_version_constraint_gte(self):
        """Test >= constraint parsing."""
        assert VersionHelper.parse_version_constraint(">=1.0.0", Version(1, 0, 0))
        assert VersionHelper.parse_version_constraint(">=1.0.0", Version(1, 5, 0))
        assert VersionHelper.parse_version_constraint(">=1.0.0", Version(2, 0, 0))
        assert not VersionHelper.parse_version_constraint(">=1.5.0", Version(1, 0, 0))
    
    def test_parse_version_constraint_exact(self):
        """Test == constraint parsing."""
        assert VersionHelper.parse_version_constraint("==1.0.0", Version(1, 0, 0))
        assert not VersionHelper.parse_version_constraint("==1.0.0", Version(1, 0, 1))
    
    def test_compare_versions(self):
        """Test version comparison."""
        v1 = Version(1, 0, 0)
        v2 = Version(1, 5, 0)
        v3 = Version(2, 0, 0)
        
        assert VersionHelper.compare_versions(v1, v2) < 0
        assert VersionHelper.compare_versions(v2, v1) > 0
        assert VersionHelper.compare_versions(v1, v1) == 0
        assert VersionHelper.compare_versions(v1, v3) < 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
