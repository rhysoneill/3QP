"""
Demo script for Changelog & Notes module.

This script demonstrates:
1. Creating changelog entries
2. Managing version tables
3. Recording freezes
4. Generating reports
5. Validating entries
"""

import tempfile
from pathlib import Path
from datetime import date, datetime

from changelog import (
    ChangelogManager,
    ChangelogValidator,
    Version,
    ChangeType,
    ModuleStatus,
    MarkdownFormatter,
    VersionHelper,
    VersionIncrementRequest,
    FreezeRequest,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_version_operations():
    """Demonstrate version number operations."""
    print_section("Version Number Operations")
    
    # Create versions
    v1 = Version(1, 0, 0)
    print(f"Created version: {v1}")
    
    v2 = Version.from_string("1.5.3")
    print(f"Parsed version from string: {v2}")
    
    # Version increments
    print("\nVersion Increments:")
    print(f"  {v2} + MAJOR = {v2.increment(ChangeType.MAJOR)}")
    print(f"  {v2} + MINOR = {v2.increment(ChangeType.MINOR)}")
    print(f"  {v2} + PATCH = {v2.increment(ChangeType.PATCH)}")
    
    # Pre-release versions
    v_draft = Version(2, 0, 0, prerelease="draft.3")
    print(f"\nPre-release version: {v_draft}")


def demo_validation():
    """Demonstrate validation functionality."""
    print_section("Validation")
    
    validator = ChangelogValidator()
    
    # Test version increment validation
    print("Testing version increment validation:")
    
    # Valid MINOR increment
    errors = validator._validate_version_increment(
        Version(1, 0, 0),
        Version(1, 1, 0),
        ChangeType.MINOR
    )
    print(f"  Valid MINOR (1.0.0 → 1.1.0): {len(errors)} errors")
    
    # Invalid increment (wrong type)
    errors = validator._validate_version_increment(
        Version(1, 0, 0),
        Version(2, 0, 0),
        ChangeType.MINOR  # Should be MAJOR
    )
    print(f"  Invalid increment: {len(errors)} errors")
    if errors:
        print(f"    Error: {errors[0].message}")
    
    # Test version increment request
    print("\nTesting version increment request:")
    request = VersionIncrementRequest(
        module_id="01_TQP_Core",
        current_version=Version(1, 0, 0),
        proposed_version=Version(1, 1, 0),
        change_type=ChangeType.MINOR,
        rationale="Added comprehensive logging support to enable debugging and audit trails for all core operations",
        author_id="developer_1"
    )
    
    result = validator.validate_version_increment_request(request)
    print(f"  Request valid: {result.is_valid}")
    print(f"  Errors: {len(result.errors)}, Warnings: {len(result.warnings)}")
    
    # Test freeze request
    print("\nTesting freeze request:")
    freeze_req = FreezeRequest(
        module_id="01_TQP_Core",
        version=Version(1, 0, 0),
        reviewer_id="tech_lead",
        approval_date=date.today(),
        checklist_complete=True
    )
    
    result = validator.validate_freeze_request(freeze_req)
    print(f"  Freeze request valid: {result.is_valid}")


def demo_changelog_manager():
    """Demonstrate changelog manager functionality."""
    print_section("Changelog Manager")
    
    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ChangelogManager(temp_dir)
        print(f"Initialized changelog manager in: {temp_dir}")
        
        # Create first entry
        print("\n1. Creating changelog entry for MINOR version update:")
        entry1 = manager.create_entry(
            module="01_TQP_Core",
            version_from=Version(1, 0, 0),
            version_to=Version(1, 1, 0),
            change_type=ChangeType.MINOR,
            summary="Added comprehensive logging integration",
            rationale="The TQP Core needed integration with the Logging System (Module 09) to enable "
                     "debugging, audit trails, and performance monitoring. This change adds logging "
                     "hooks throughout the core update cycle and state management operations.",
            files_modified=["core.py", "module_registry.py", "data_contract.md"],
            author="Core Team Developer",
            reviewer="Technical Lead",
            tags=["integration", "logging", "enhancement"]
        )
        
        print(f"  Entry ID: {entry1.entry_id}")
        print(f"  Module: {entry1.module}")
        print(f"  Version: {entry1.version_from} → {entry1.version_to}")
        print(f"  Summary: {entry1.summary}")
        
        # Save entry
        path = manager.save_entry(entry1)
        print(f"  Saved to: {path}")
        
        # Create second entry
        print("\n2. Creating changelog entry for PATCH update:")
        entry2 = manager.create_entry(
            module="01_TQP_Core",
            version_from=Version(1, 1, 0),
            version_to=Version(1, 1, 1),
            change_type=ChangeType.PATCH,
            summary="Fixed documentation typo in README",
            rationale="The README.md file contained an incorrect reference to Module 04 that should have "
                     "been Module 05. This correction ensures accurate cross-module references.",
            files_modified=["README.md"],
            author="Documentation Team",
            reviewer="Technical Lead"
        )
        manager.save_entry(entry2)
        print(f"  Entry ID: {entry2.entry_id}")
        
        # Retrieve entries for module
        print("\n3. Retrieving all entries for module 01_TQP_Core:")
        entries = manager.get_entries_for_module("01_TQP_Core")
        print(f"  Found {len(entries)} entries")
        for e in entries:
            print(f"    - {e.entry_id}: {e.summary[:50]}...")
        
        # Update version table
        print("\n4. Updating version table:")
        manager.update_version_table(
            module_id="01_TQP_Core",
            current_version=Version(1, 1, 1),
            status=ModuleStatus.APPROVED,
        )
        print("  Version table updated")
        
        # Record a freeze
        print("\n5. Recording module freeze:")
        freeze_record = manager.record_freeze(
            module_id="01_TQP_Core",
            version=Version(1, 1, 1),
            approver_id="Project Architect",
            archive_location="/archives/01_TQP_Core/v1.1.1",
            checksum="a1b2c3d4e5f6"
        )
        print(f"  Freeze ID: {freeze_record.freeze_id}")
        print(f"  Version: {freeze_record.version}")
        print(f"  Freeze Date: {freeze_record.freeze_date}")
        print(f"  Approver: {freeze_record.approver_id}")
        
        # Generate revision report
        print("\n6. Generating revision report:")
        report = manager.generate_revision_report(
            start_date=date(2025, 12, 1),
            end_date=date(2025, 12, 31),
            generated_by="System Administrator"
        )
        print(f"  Report ID: {report.metadata.report_id}")
        print(f"  Total Entries: {report.summary.total_entries}")
        print(f"  MAJOR: {report.summary.count_by_type[ChangeType.MAJOR]}")
        print(f"  MINOR: {report.summary.count_by_type[ChangeType.MINOR]}")
        print(f"  PATCH: {report.summary.count_by_type[ChangeType.PATCH]}")
        print(f"  Modules Updated: {', '.join(report.summary.modules_updated)}")


def demo_markdown_formatting():
    """Demonstrate Markdown formatting."""
    print_section("Markdown Formatting")
    
    # Create sample entry
    entry = manager.create_entry(
        module="02_Breakthrough_Impact",
        version_from=Version(1, 0, 0),
        version_to=Version(2, 0, 0),
        change_type=ChangeType.MAJOR,
        summary="Restructured breakthrough detection algorithm",
        rationale="The original algorithm did not properly account for contextual factors in breakthrough "
                 "attribution. This major revision incorporates contextual awareness and changes the "
                 "data contract to include additional input fields.",
        files_modified=["spec.md", "theory_basis.md", "data_contract.md", "implementation_notes.md"],
        author="Research Team Lead",
        reviewer="Project Architect",
        impact_assessment="This change affects Module 06 (BDI Cycle) which consumes breakthrough events. "
                          "Module 06 will need updates to handle new data fields.",
        migration_notes="Existing simulations using v1.x.x will need to provide the new contextual fields "
                       "or use default values.",
        tags=["breaking-change", "algorithm", "data-contract"]
    )
    
    print("Changelog Entry (Markdown format):")
    print("-" * 60)
    markdown = MarkdownFormatter.format_entry(entry)
    print(markdown)


def demo_version_constraints():
    """Demonstrate version constraint checking."""
    print_section("Version Constraint Checking")
    
    current = Version(1, 5, 3)
    print(f"Current version: {current}")
    
    constraints = [
        ">=1.0.0",
        ">=2.0.0",
        "==1.5.3",
        "==1.5.0",
        ">1.5.0",
        "<2.0.0",
    ]
    
    print("\nChecking constraints:")
    for constraint in constraints:
        satisfied = VersionHelper.parse_version_constraint(constraint, current)
        status = "✓" if satisfied else "✗"
        print(f"  {status} {constraint}")


def main():
    """Run all demonstrations."""
    print("\n" + "="*60)
    print("  MODULE 12: CHANGELOG & NOTES - DEMONSTRATION")
    print("="*60)
    
    demo_version_operations()
    demo_validation()
    demo_changelog_manager()
    
    # For markdown formatting, we need a manager instance
    with tempfile.TemporaryDirectory() as temp_dir:
        global manager
        manager = ChangelogManager(temp_dir)
        demo_markdown_formatting()
    
    demo_version_constraints()
    
    print("\n" + "="*60)
    print("  DEMONSTRATION COMPLETE")
    print("="*60 + "\n")
    
    print("Summary:")
    print("  ✓ Version number operations")
    print("  ✓ Entry validation")
    print("  ✓ Changelog management")
    print("  ✓ Markdown formatting")
    print("  ✓ Version constraints")
    print("\nModule 12 provides comprehensive version control and change")
    print("documentation capabilities for the 3QP Project.")


if __name__ == "__main__":
    main()
