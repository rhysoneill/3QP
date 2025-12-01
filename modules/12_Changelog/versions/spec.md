# Module 12: Changelog & Notes — Technical Specification

## 1. Overview

This specification defines the complete change management framework for the 3QP Project. It establishes rules for version numbering, changelog entry structure, documentation lifecycle phases, module freezing procedures, and cross-module traceability requirements.

All changes to any module documentation (Modules 01-12) must be recorded according to the procedures defined herein.

## 2. Version Number Format

### 2.1 Semantic Versioning

All modules shall use semantic versioning with the format:

```
MAJOR.MINOR.PATCH
```

Where:

- **MAJOR**: Incremented when architectural changes break compatibility with prior versions or fundamentally alter module scope
- **MINOR**: Incremented when new sections, subsections, or significant clarifications are added without breaking existing interpretations
- **PATCH**: Incremented for corrections, typographical fixes, formatting updates, or minor clarifications

### 2.2 Version Increment Rules

- Initial module release: `1.0.0`
- First correction after release: `1.0.1`
- First minor addition: `1.1.0`
- First breaking change: `2.0.0`

When MAJOR is incremented, MINOR and PATCH reset to 0.  
When MINOR is incremented, PATCH resets to 0.

### 2.3 Pre-Release Versions

Modules under development may use pre-release tags:

```
MAJOR.MINOR.PATCH-draft.N
```

Example: `1.0.0-draft.3`

Draft versions are not subject to freeze procedures and may change without changelog entries.

## 3. Changelog Entry Structure

### 3.1 Required Fields

Each changelog entry MUST include:

| Field | Type | Description |
|-------|------|-------------|
| `entry_id` | String | Unique identifier (format: `CL-YYYYMMDD-NNN`) |
| `date` | ISO-8601 Date | Date of change approval |
| `module` | String | Module identifier (e.g., `01_TQP_Core`) |
| `version_from` | Version | Previous version number |
| `version_to` | Version | New version number |
| `change_type` | Enum | One of: `MAJOR`, `MINOR`, `PATCH` |
| `summary` | String | Brief description (≤200 characters) |
| `rationale` | Text | Detailed explanation of why change was made |
| `files_modified` | List | Relative paths to all modified files |
| `author` | String | Person or role responsible for change |
| `reviewer` | String | Person or role who approved change |
| `related_entries` | List | IDs of related changelog entries (if applicable) |

### 3.2 Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `external_references` | List | Citations, URLs, or document references |
| `impact_assessment` | Text | Description of downstream effects on other modules |
| `migration_notes` | Text | Guidance for transitioning from previous version |

### 3.3 Entry Format

Changelog entries shall be stored in structured format (markdown tables, YAML, or JSON). Example:

```markdown
## Entry: CL-20251201-001

- **Date**: 2025-12-01
- **Module**: 01_TQP_Core
- **Version**: 1.0.0 → 1.1.0
- **Change Type**: MINOR
- **Summary**: Added section on temporal resolution requirements
- **Rationale**: Clarification needed for integration with Module 04 (SlowFast Physiology)
- **Files Modified**: `spec.md`, `data_contract.md`
- **Author**: Systems Architect
- **Reviewer**: Technical Lead
- **Related Entries**: CL-20251128-003
```

## 4. Module Version Freezing

### 4.1 Freeze Definition

A module version is "frozen" when all five documentation files reach a stable state and are approved for use as the authoritative reference for that version. Once frozen, the version SHALL NOT be modified.

### 4.2 Freeze Procedure

1. All five files (`README.md`, `spec.md`, `theory_basis.md`, `data_contract.md`, `implementation_notes.md`) must be reviewed and approved
2. A changelog entry documenting the freeze must be created
3. Version number must be assigned (no `-draft` suffix)
4. All files must be tagged or archived with version identifier
5. Freeze record must be added to the system-wide version table

### 4.3 Post-Freeze Modifications

Any modification to a frozen version requires:

- Creation of a new version number (following increment rules)
- New changelog entry explaining the modification
- Re-execution of freeze procedure for the new version

### 4.4 Emergency Corrections

Critical errors in frozen versions may be corrected via PATCH increment. Such corrections must:

- Be limited to factual errors, broken references, or critical omissions
- NOT alter the fundamental meaning or scope of the module
- Be documented with explicit justification in the changelog entry

## 5. Documentation Lifecycle

### 5.1 Lifecycle Phases

| Phase | Description | Version Format | Changeable |
|-------|-------------|----------------|------------|
| **Draft** | Initial development, frequent changes expected | `X.Y.Z-draft.N` | Yes, without changelog |
| **Review** | Under evaluation, changes tracked but not frozen | `X.Y.Z-review.N` | Yes, with informal tracking |
| **Approved** | Ready for freeze, awaiting final sign-off | `X.Y.Z-approved` | No |
| **Frozen** | Immutable reference version | `X.Y.Z` | No |
| **Deprecated** | Superseded by newer version | `X.Y.Z` (marked deprecated) | No |

### 5.2 Transition Requirements

- **Draft → Review**: All five files must be complete and internally consistent
- **Review → Approved**: All reviewer comments must be resolved or explicitly deferred
- **Approved → Frozen**: Formal sign-off by designated authority required
- **Frozen → Deprecated**: New frozen version must exist before prior version is deprecated

### 5.3 Review Cycles

Modules in Review phase may undergo multiple iterations. Each iteration should be tracked with incremented review numbers (e.g., `1.0.0-review.1`, `1.0.0-review.2`).

## 6. Cross-Module Traceability

### 6.1 Dependency Tracking

When a module references or depends on another module, the changelog entry must:

- Identify all affected modules
- Document the nature of the dependency (informational, structural, data flow)
- List any version compatibility requirements

### 6.2 Impact Assessment

Changes to one module may necessitate updates to others. Changelog entries for significant changes must include:

- List of potentially impacted modules
- Assessment of whether changes are breaking or non-breaking
- Timeline for propagating changes to dependent modules

### 6.3 Traceability Matrix

The project shall maintain a traceability matrix documenting:

- Which modules reference which other modules
- Which data contracts depend on outputs from other modules
- Which theoretical frameworks are shared across modules

This matrix must be updated whenever cross-module dependencies are created or modified.

## 7. System-Wide Version Governance

### 7.1 Project Version Numbering

The overall 3QP Project has its own version number, independent of individual module versions. Project versions follow the same semantic versioning format.

A new project version is released when:

- All modules have reached frozen state for a coordinated release
- A significant milestone is achieved
- External publication or distribution occurs

### 7.2 Version Compatibility

Modules should maintain backward compatibility within MAJOR versions when feasible. Breaking changes require:

- Explicit justification in the changelog
- MAJOR version increment
- Documentation of migration path from previous MAJOR version

### 7.3 Version Table

A system-wide version table must be maintained, showing:

| Module | Current Version | Status | Freeze Date | Supersedes |
|--------|----------------|--------|-------------|------------|
| 01_TQP_Core | 1.0.0 | Frozen | 2025-11-15 | — |
| 02_Breakthrough_Impact | 1.1.0 | Frozen | 2025-11-20 | 1.0.0 |
| ... | ... | ... | ... | ... |

This table provides a snapshot of the entire system's version state at any point in time.

## 8. Storage and Retention

### 8.1 Changelog Storage

Changelog entries shall be stored in:

- A centralized changelog file within Module 12's directory
- Optional per-module changelog files for convenience
- Structured format enabling automated parsing and querying

### 8.2 Version Archival

All frozen module versions must be:

- Archived in a version control system (e.g., Git tags)
- Stored in immutable format (e.g., read-only directories or signed archives)
- Backed up with the same rigor as primary project data

### 8.3 Retention Period

All changelog entries and frozen versions shall be retained indefinitely. Deletion of archived versions is prohibited except in extraordinary circumstances requiring formal authorization.

### 8.4 Access and Retrieval

The system must support:

- Retrieval of any frozen version by version number
- Query of changelog entries by date, module, author, or change type
- Generation of version history reports

## 9. Update Review and Approval

### 9.1 Author Responsibilities

Authors of module updates must:

- Prepare complete changelog entries before submitting changes
- Ensure all required fields are populated
- Verify that version number increments are correct
- Document rationale with sufficient detail for future understanding

### 9.2 Reviewer Responsibilities

Reviewers must:

- Verify technical accuracy of changes
- Confirm appropriateness of version increment
- Assess impact on other modules
- Approve or request revisions

### 9.3 Approval Authority

Approval authority is assigned based on change type:

| Change Type | Approval Required From |
|-------------|------------------------|
| PATCH | Module maintainer |
| MINOR | Module maintainer + technical lead |
| MAJOR | Module maintainer + technical lead + project architect |

### 9.4 Conflict Resolution

If multiple authors submit conflicting changes:

1. Changes are merged in chronological order of approval
2. Later changes must reference earlier changes in `related_entries`
3. If conflicts cannot be resolved, technical lead escalates to project architect

## 10. Error Handling

### 10.1 Incorrect Versioning

If a version number is assigned incorrectly:

- Create a corrective changelog entry
- Re-tag or re-archive with correct version
- Deprecate incorrect version
- Document error in both changelog entries

### 10.2 Missing Changelog Entries

If a change is discovered without a corresponding changelog entry:

- Create a retroactive changelog entry with `[RETROACTIVE]` marker
- Document discovery date in addition to original change date
- Include explanation of why entry was initially omitted

### 10.3 Conflicting Changes

If two changelog entries describe incompatible modifications:

- Halt further changes to the affected module
- Convene review with all involved parties
- Create resolution plan with explicit rationale
- Document resolution in new changelog entry referencing both original entries

### 10.4 Lost or Corrupted Versions

If a frozen version is lost or corrupted:

- Immediately document the loss in a changelog entry
- Attempt reconstruction from backups
- If reconstruction is impossible, mark version as `LOST` in version table
- Assess impact on dependent modules and publications

## 11. Extensibility

### 11.1 Adding New Modules

When new modules (13+) are added to the project:

- Module 12 specifications apply without modification
- New module must follow same documentation structure
- Changelog entry must document module creation
- Version table must be updated

### 11.2 Adding Submodules

If existing modules are subdivided into submodules:

- Submodules inherit parent module's version initially
- Submodules thereafter version independently
- Changelog must document submodule creation and rationale
- Traceability matrix must be updated to reflect new structure

### 11.3 Custom Fields

Projects may extend changelog entry structure with custom fields:

- Custom fields must be documented in Module 12 itself
- Custom fields are optional unless explicitly required by project policy
- Custom fields must not conflict with required fields

### 11.4 Alternative Storage Formats

While this specification describes markdown-based storage, alternative formats (databases, structured repositories) may be used provided:

- All required fields are captured
- Retrieval and query capabilities are maintained
- Human readability is preserved (via export or query interface)
- Archival and backup requirements are met

## 12. Compliance

All project contributors are responsible for adhering to the procedures defined in this specification. Non-compliance may result in:

- Rejection of submitted changes
- Required rework and resubmission
- Escalation to project leadership for repeated violations

Compliance is essential to maintaining the scientific integrity and reproducibility of the 3QP Project.
