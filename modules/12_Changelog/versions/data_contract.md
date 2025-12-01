# Module 12: Changelog & Notes — Data Contract

## 1. Overview

This data contract defines the inputs, outputs, metadata requirements, timing triggers, and constraints for the Changelog & Notes module. Unlike other modules that specify simulation data flows, this contract describes the *process-level data* required to maintain version control and change documentation across the 3QP Project.

## 2. Inputs

### 2.1 Module Update Notifications

**Source**: Any module author or maintainer  
**Trigger**: When any of the five core files (`README.md`, `spec.md`, `theory_basis.md`, `data_contract.md`, `implementation_notes.md`) in any module is modified

**Required Fields**:

| Field Name | Data Type | Description | Constraints |
|------------|-----------|-------------|-------------|
| `module_id` | String | Module identifier | Must match existing module directory name |
| `files_modified` | List[String] | Relative paths to modified files | Each path must exist within module |
| `modification_summary` | String | Brief description of changes | 50-200 characters |
| `author_id` | String | Identifier of person making change | Must be registered project contributor |
| `timestamp` | ISO-8601 DateTime | Time modification was completed | UTC format |

**Optional Fields**:

| Field Name | Data Type | Description |
|------------|-----------|-------------|
| `related_modules` | List[String] | Other modules potentially affected |
| `urgency` | Enum | One of: `ROUTINE`, `URGENT`, `CRITICAL` |

### 2.2 Version Increment Requests

**Source**: Module authors or technical leads  
**Trigger**: When a set of modifications is ready to be assigned a new version number

**Required Fields**:

| Field Name | Data Type | Description | Constraints |
|------------|-----------|-------------|-------------|
| `module_id` | String | Module identifier | Must match existing module |
| `current_version` | Version | Existing version number | Format: `X.Y.Z` |
| `proposed_version` | Version | Requested new version | Must follow increment rules |
| `change_type` | Enum | One of: `MAJOR`, `MINOR`, `PATCH` | Must align with version increment |
| `rationale` | Text | Detailed justification | Minimum 100 characters |
| `author_id` | String | Requestor identifier | Must be registered contributor |

### 2.3 Freeze Requests

**Source**: Technical leads or project architect  
**Trigger**: When a module version is ready to be made immutable

**Required Fields**:

| Field Name | Data Type | Description | Constraints |
|------------|-----------|-------------|-------------|
| `module_id` | String | Module identifier | Must match existing module |
| `version` | Version | Version to freeze | Must be in `approved` state |
| `reviewer_id` | String | Identifier of approving authority | Must have approval privileges |
| `approval_date` | ISO-8601 Date | Date of formal approval | Cannot be future date |
| `checklist_complete` | Boolean | Confirmation all files reviewed | Must be `true` |

### 2.4 Cross-Module Dependency Declarations

**Source**: Module authors  
**Trigger**: When a module references or depends on another module

**Required Fields**:

| Field Name | Data Type | Description | Constraints |
|------------|-----------|-------------|-------------|
| `source_module` | String | Module declaring dependency | Must match existing module |
| `target_module` | String | Module being depended upon | Must match existing module |
| `dependency_type` | Enum | One of: `INFORMATIONAL`, `STRUCTURAL`, `DATA_FLOW` | — |
| `version_constraint` | String | Required version range | Format: `>=X.Y.Z`, `==X.Y.Z`, etc. |

### 2.5 Error Reports

**Source**: Any project contributor  
**Trigger**: When versioning errors, missing entries, or conflicts are discovered

**Required Fields**:

| Field Name | Data Type | Description | Constraints |
|------------|-----------|-------------|-------------|
| `error_type` | Enum | One of: `INCORRECT_VERSION`, `MISSING_ENTRY`, `CONFLICT`, `CORRUPTION` | — |
| `description` | Text | Detailed error description | Minimum 50 characters |
| `affected_modules` | List[String] | Modules impacted by error | At least one module |
| `reporter_id` | String | Identifier of person reporting | Must be registered contributor |
| `discovery_date` | ISO-8601 Date | When error was identified | Cannot be future date |

## 3. Outputs

### 3.1 Changelog Entries

**Consumer**: Project contributors, external reviewers, auditors  
**Format**: Structured markdown, YAML, or JSON

**Required Fields**:

| Field Name | Data Type | Description | Constraints |
|------------|-----------|-------------|-------------|
| `entry_id` | String | Unique entry identifier | Format: `CL-YYYYMMDD-NNN` |
| `date` | ISO-8601 Date | Date of change approval | — |
| `module` | String | Module identifier | Must match existing module |
| `version_from` | Version | Previous version | Format: `X.Y.Z` |
| `version_to` | Version | New version | Format: `X.Y.Z` |
| `change_type` | Enum | One of: `MAJOR`, `MINOR`, `PATCH` | — |
| `summary` | String | Brief description | ≤200 characters |
| `rationale` | Text | Detailed explanation | ≥100 characters |
| `files_modified` | List[String] | Paths to modified files | Non-empty list |
| `author` | String | Person responsible | — |
| `reviewer` | String | Person who approved | — |
| `related_entries` | List[String] | Related changelog IDs | May be empty |

**Optional Fields**:

| Field Name | Data Type | Description |
|------------|-----------|-------------|
| `external_references` | List[String] | Citations, URLs, documents |
| `impact_assessment` | Text | Downstream effects description |
| `migration_notes` | Text | Transition guidance |
| `tags` | List[String] | Categorization keywords |

### 3.2 Version Tables

**Consumer**: Project contributors, management, external reviewers  
**Format**: Markdown table or CSV

**Required Columns**:

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `module_id` | String | Module identifier |
| `current_version` | Version | Latest frozen version |
| `status` | Enum | One of: `DRAFT`, `REVIEW`, `APPROVED`, `FROZEN`, `DEPRECATED` |
| `freeze_date` | ISO-8601 Date | Date version was frozen (if applicable) |
| `supersedes` | Version | Previous version replaced by this one |

**Example**:

```markdown
| Module | Current Version | Status | Freeze Date | Supersedes |
|--------|-----------------|--------|-------------|------------|
| 01_TQP_Core | 1.0.0 | Frozen | 2025-11-15 | — |
| 02_Breakthrough_Impact | 1.1.0 | Frozen | 2025-11-20 | 1.0.0 |
```

### 3.3 Revision Reports

**Consumer**: Technical leads, project architect, external auditors  
**Format**: Structured document (markdown or PDF)

**Required Sections**:

1. **Report Metadata**
   - Report ID
   - Generation date
   - Reporting period
   - Generated by (author ID)

2. **Summary Statistics**
   - Total changelog entries in period
   - Count by change type (MAJOR, MINOR, PATCH)
   - Modules updated
   - Authors contributing

3. **Detailed Entries**
   - Full changelog entries for reporting period
   - Ordered chronologically

4. **Outstanding Issues**
   - Error reports not yet resolved
   - Pending freeze requests
   - Conflicting changes awaiting resolution

### 3.4 Traceability Matrix

**Consumer**: Technical leads, systems architect  
**Format**: Structured table or graph

**Required Information**:

| Field Name | Data Type | Description |
|------------|-----------|-------------|
| `source_module` | String | Module with dependency |
| `target_module` | String | Module being depended upon |
| `dependency_type` | Enum | Type of dependency |
| `source_version` | Version | Version of source module |
| `target_version_required` | String | Version constraint for target |
| `last_verified` | ISO-8601 Date | Date dependency was last confirmed |

### 3.5 Freeze Records

**Consumer**: All project contributors  
**Format**: Structured entry in project archive

**Required Fields**:

| Field Name | Data Type | Description |
|------------|-----------|-------------|
| `freeze_id` | String | Unique freeze identifier |
| `module_id` | String | Module frozen |
| `version` | Version | Version number frozen |
| `freeze_date` | ISO-8601 Date | Date of freeze |
| `approver_id` | String | Authority who approved |
| `archive_location` | String | Path or URI to archived files |
| `checksum` | String | Hash of archived content (for integrity) |

## 4. Metadata Requirements

### 4.1 Entry-Level Metadata

Every changelog entry must include:

- **Creation timestamp**: When entry was first drafted
- **Last modified timestamp**: When entry was last updated
- **State**: One of `DRAFT`, `UNDER_REVIEW`, `APPROVED`
- **Visibility**: One of `INTERNAL`, `PUBLIC`

### 4.2 Module-Level Metadata

Each module must maintain:

- **Version history**: List of all prior versions
- **Current maintainer**: Person or role responsible
- **Last review date**: Most recent comprehensive review
- **Next review due**: Scheduled review date (if applicable)

### 4.3 Project-Level Metadata

The overall project must track:

- **Project version**: Overall 3QP version number
- **Release dates**: Dates of formal project releases
- **Active modules**: Count and list of modules in active development
- **Frozen modules**: Count and list of modules in frozen state

## 5. Timing and Procedural Triggers

### 5.1 Immediate Triggers

The following events require immediate changelog entry creation:

- MAJOR version increment
- Module freeze
- Error discovery affecting frozen versions
- Deprecation of a frozen version

**Timing requirement**: Changelog entry must be created within 24 hours of event.

### 5.2 Batched Triggers

The following events may be batched for periodic changelog updates:

- PATCH version increments for minor corrections
- Informational cross-references between modules
- Review state transitions (draft → review → approved)

**Timing requirement**: Changelog entry must be created within 1 week of event.

### 5.3 Periodic Reviews

Version tables and traceability matrices must be reviewed and updated:

- **Monthly**: During active development phases
- **Quarterly**: During maintenance phases
- **Before any formal release**: To ensure accuracy

### 5.4 Milestone-Based Triggers

Revision reports must be generated:

- At the end of each development sprint or cycle
- Before external presentations or publications
- Upon request from project leadership

## 6. Constraints on Valid Entries

### 6.1 Version Number Constraints

- Version numbers must follow semantic versioning format: `MAJOR.MINOR.PATCH`
- Version increments must be exactly one step (cannot skip from `1.0.0` to `1.2.0`)
- Pre-release tags must follow format: `-draft.N` or `-review.N`
- Version numbers are immutable once frozen

### 6.2 Entry ID Constraints

- Entry IDs must be unique across entire project
- Entry IDs must follow format: `CL-YYYYMMDD-NNN`
- Sequential numbering within a single day must have no gaps
- Entry IDs cannot be reused even if an entry is deprecated

### 6.3 Cross-Reference Constraints

- All `related_entries` must reference existing changelog entry IDs
- All `related_modules` must reference existing module IDs
- Circular dependencies must be explicitly documented and justified
- References to external documents must include stable URIs or DOIs when available

### 6.4 Temporal Constraints

- Dates must not be in the future (except for scheduled reviews)
- `version_from` must exist before `version_to` is created
- Freeze date must be after all modification dates for files in that version
- Deprecation date must be after freeze date

### 6.5 Authority Constraints

- Authors must be registered project contributors
- Reviewers must have appropriate authorization level for change type
- Approvers for freeze requests must be technical leads or higher
- Error reports may be submitted by any contributor but must be reviewed by leads

## 7. Data Validation Rules

### 7.1 Pre-Submission Validation

Before a changelog entry is submitted, the following must be verified:

- All required fields are populated
- Version numbers are valid and follow increment rules
- File paths exist within specified module
- Author and reviewer IDs are registered
- Dates are in correct format and within valid ranges

### 7.2 Post-Submission Validation

After submission, automated or manual checks should verify:

- No duplicate entry IDs exist
- Cross-references resolve to valid targets
- Version sequence is consistent (no gaps or conflicts)
- Change type matches version increment magnitude

### 7.3 Periodic Audit

Quarterly audits should verify:

- All frozen versions have corresponding changelog entries
- Version table matches actual module states
- Traceability matrix reflects current dependencies
- No orphaned or dangling references exist

## 8. Data Retention and Archival

### 8.1 Retention Policy

- All changelog entries: **Permanent retention**
- All version tables: **Permanent retention**
- Revision reports: **Minimum 5 years**
- Freeze records: **Permanent retention**
- Error reports: **Minimum 3 years after resolution**

### 8.2 Archival Format

Archived data must be stored in:

- Human-readable format (markdown, JSON, YAML)
- Machine-parsable format for automated queries
- Checksummed or signed to ensure integrity
- Multiple redundant locations for disaster recovery

### 8.3 Access Control

- Changelog entries: Read access for all contributors, write access for authorized maintainers
- Freeze records: Read-only for all contributors
- Error reports: Read access for all contributors, resolution authority limited to leads

## 9. Integration with External Systems

### 9.1 Version Control Systems

Changelog data should integrate with version control (e.g., Git) by:

- Tagging frozen versions with version numbers
- Storing changelog entries in repository
- Linking commit histories to changelog entries

### 9.2 Documentation Generators

Changelog data should be structured to support:

- Automated generation of release notes
- Dynamic version history displays
- Dependency graphs and traceability visualizations

### 9.3 Publication Systems

When results are published, changelog data enables:

- Precise citation of module versions
- Reproducibility statements with version references
- Supplementary material documenting model configuration

## 10. Summary

This data contract defines the process-level information flows required to maintain rigorous version control and change documentation. It specifies:

- **Inputs**: Notifications, requests, and reports triggering changelog activities
- **Outputs**: Entries, tables, reports, matrices, and freeze records
- **Metadata**: Required tracking information at entry, module, and project levels
- **Timing**: When activities must occur
- **Constraints**: Rules ensuring validity and consistency
- **Validation**: Checks to prevent errors and maintain integrity
- **Retention**: Long-term preservation requirements
- **Integration**: Connections to external tools and systems

By adhering to this data contract, the 3QP Project ensures that its change management system operates with the rigor and transparency necessary for scientific credibility and long-term maintainability.
