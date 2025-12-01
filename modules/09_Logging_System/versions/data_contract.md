# Module 09: Language & Log Output System — Data Contract

## 1. Overview

This document defines the data contract between the Logging System and its environment. It specifies the abstract data structures received from simulation modules and produced as structured log artifacts, without describing the internal processing logic or the semantic meaning of the data.

## 2. Contract Scope

### 2.1 Inputs

The Logging System receives structured data objects from:

- **TQP Core (Module 01)**: Cycle synchronization signals and metadata
- **Operational Modules (Modules 02-08)**: State snapshots, event notifications, and metric reports

### 2.2 Outputs

The Logging System produces:

- **Log Record Files**: Serialized collections of structured log entries
- **Index Manifests**: Metadata catalogs describing log file organization
- **Export Packages**: Filtered and formatted log data for downstream consumers

### 2.3 Temporal Context

All data exchanges occur within the context of TQP Core time-step cycles. Inputs arrive during or at cycle boundaries. Outputs persist to storage asynchronously but are timestamped relative to simulation time-steps.

## 3. Input Data Structures

### 3.1 State Update Object

**Source**: Any operational module  
**Trigger**: End of module update execution within time-step  
**Frequency**: Zero or one per module per time-step (configurable)

**Required Fields**:
```
{
  module_id: string,           // Identifier of producing module
  timestamp: integer,          // Simulation time-step index
  state_variables: dictionary  // Key-value pairs of state variable names to values
}
```

**Field Constraints**:
- `module_id`: Must match registered module identifier, max 64 characters
- `timestamp`: Non-negative integer, monotonically increasing
- `state_variables`: Dictionary with string keys, values of types: integer, float, boolean, string, array, or nested dictionary (max depth 5)

**Optional Fields**:
```
{
  delta_from_previous: dictionary,  // Only changed variables since last snapshot
  compression_hint: string          // Suggestion for compression method
}
```

**Validation Rules**:
- Module must be registered before submitting state updates
- Timestamp must equal current TQP Core cycle time-step
- State variable names must be valid identifiers (alphanumeric + underscore)
- No null values permitted for required fields

### 3.2 Event Record

**Source**: Any operational module  
**Trigger**: Detection of discrete event within module  
**Frequency**: Zero to unbounded per module per time-step

**Required Fields**:
```
{
  module_id: string,           // Identifier of producing module
  timestamp: integer,          // Simulation time-step index
  event_category: string,      // Enumerated event type identifier
  event_attributes: dictionary // Event-specific data fields
}
```

**Field Constraints**:
- `module_id`: Must match registered module identifier, max 64 characters
- `timestamp`: Non-negative integer, equal to current time-step
- `event_category`: Must match module's registered event types, max 128 characters
- `event_attributes`: Dictionary with string keys, values of types: integer, float, boolean, string, array, or nested dictionary (max depth 5)

**Optional Fields**:
```
{
  event_id: string,                  // Unique identifier for event instance
  caused_by_events: array of string, // Array of event_id values
  affected_entities: array of string // Array of entity/agent identifiers
}
```

**Validation Rules**:
- Event category must be pre-registered by module
- Event attributes schema must conform to registered event category schema (if defined)
- Timestamp must equal current TQP Core cycle time-step

### 3.3 Metric Report

**Source**: Any operational module  
**Trigger**: End of configured aggregation window  
**Frequency**: Configurable per metric (default: every 10 time-steps)

**Required Fields**:
```
{
  module_id: string,            // Identifier of producing module
  timestamp_start: integer,     // First time-step in aggregation window
  timestamp_end: integer,       // Last time-step in aggregation window (inclusive)
  metric_identifier: string,    // Name of measured quantity
  metric_value: float or integer // Computed metric value
}
```

**Field Constraints**:
- `module_id`: Must match registered module identifier, max 64 characters
- `timestamp_start`: Non-negative integer, <= timestamp_end
- `timestamp_end`: Non-negative integer, <= current time-step
- `metric_identifier`: Must match module's registered metrics, max 128 characters
- `metric_value`: Numerical value (integer or float), finite (no NaN or infinity)

**Optional Fields**:
```
{
  metric_unit: string,              // Physical or logical unit (e.g., "ms", "count")
  aggregation_method: string,       // "SUM", "MEAN", "MAX", "MIN", "MEDIAN", etc.
  sample_count: integer,            // Number of observations aggregated
  statistical_bounds: dictionary    // Confidence intervals or error bars
}
```

**Validation Rules**:
- Timestamp range must align with configured aggregation window boundaries
- Aggregation method must match metric definition (if specified at registration)

### 3.4 Cycle Synchronization Signal

**Source**: TQP Core (Module 01)  
**Trigger**: Completion of all module updates in time-step  
**Frequency**: Exactly once per time-step

**Required Fields**:
```
{
  timestamp: integer,                  // Completed time-step index
  cycle_start_wall_time: string,       // ISO 8601 timestamp of cycle start
  cycle_end_wall_time: string,         // ISO 8601 timestamp of cycle end
  modules_executed: array of string,   // Module IDs that updated this cycle
  cycle_completion_status: string      // "COMPLETE", "PARTIAL", "ERROR"
}
```

**Field Constraints**:
- `timestamp`: Non-negative integer, sequential
- `cycle_start_wall_time`: ISO 8601 format with timezone, UTC preferred
- `cycle_end_wall_time`: ISO 8601 format, must be >= cycle_start_wall_time
- `modules_executed`: Array of registered module IDs
- `cycle_completion_status`: Enumerated value from allowed set

**Optional Fields**:
```
{
  module_execution_times: dictionary,  // Map of module_id to duration in ms
  memory_peak_mb: float,               // Peak memory usage during cycle
  error_details: array of dictionary   // Error records if status != COMPLETE
}
```

**Validation Rules**:
- Timestamp must increment by 1 from previous cycle
- All module IDs in modules_executed must be registered

## 4. Output Data Structures

### 4.1 Log Record (Generic Schema)

**Format**: JSON object (single line in JSON Lines files)  
**Audience**: Downstream analysis tools, archival systems

**Common Fields** (present in all log record types):
```
{
  log_type: string,        // "STATE", "EVENT", "CYCLE", or "METRIC"
  timestamp: integer,      // Simulation time-step reference
  wall_time: string,       // ISO 8601 timestamp of log creation
  log_version: string      // Schema version (semantic version format)
}
```

**Type-Specific Fields**: Additional fields dependent on log_type value (see Sections 4.2-4.5)

### 4.2 State Log Record

**Output from**: State Update Object input

**Complete Schema**:
```
{
  log_type: "STATE",
  timestamp: integer,
  wall_time: string,
  module_id: string,
  state_snapshot: dictionary,
  log_version: string,
  
  // Optional fields
  snapshot_id: string,
  delta_encoding: boolean,
  compression_method: string
}
```

**Field Semantics**:
- `state_snapshot`: Direct serialization of input state_variables dictionary
- `delta_encoding`: True if snapshot contains only changed variables
- `compression_method`: Applied compression (e.g., "gzip", "none")

**Size Estimate**: 100-1000 bytes uncompressed, 20-200 bytes compressed

### 4.3 Event Log Record

**Output from**: Event Record input

**Complete Schema**:
```
{
  log_type: "EVENT",
  timestamp: integer,
  wall_time: string,
  module_id: string,
  event_category: string,
  event_data: dictionary,
  log_version: string,
  
  // Optional fields
  event_id: string,
  causality_chain: array of string,
  severity_level: string,
  related_entity_ids: array of string
}
```

**Field Semantics**:
- `event_data`: Direct serialization of input event_attributes dictionary
- `causality_chain`: Copy of input caused_by_events array
- `related_entity_ids`: Copy of input affected_entities array

**Size Estimate**: 50-500 bytes uncompressed, 10-100 bytes compressed

### 4.4 Cycle Log Record

**Output from**: Cycle Synchronization Signal input

**Complete Schema**:
```
{
  log_type: "CYCLE",
  timestamp: integer,
  wall_time: string,
  cycle_duration_ms: float,
  modules_executed: array of string,
  cycle_status: string,
  log_version: string,
  
  // Optional fields
  module_timings: dictionary,
  memory_usage_mb: float,
  error_records: array of dictionary
}
```

**Field Semantics**:
- `cycle_duration_ms`: Computed from cycle_end_wall_time - cycle_start_wall_time
- `cycle_status`: Copy of input cycle_completion_status
- `module_timings`: Copy of input module_execution_times

**Size Estimate**: 200-500 bytes uncompressed, 40-100 bytes compressed

### 4.5 Metric Log Record

**Output from**: Metric Report input

**Complete Schema**:
```
{
  log_type: "METRIC",
  timestamp_start: integer,
  timestamp_end: integer,
  wall_time: string,
  module_id: string,
  metric_name: string,
  metric_value: float or integer,
  log_version: string,
  
  // Optional fields
  metric_unit: string,
  aggregation_method: string,
  sample_count: integer,
  confidence_bounds: dictionary
}
```

**Field Semantics**:
- `metric_name`: Copy of input metric_identifier
- `metric_value`: Direct copy of input metric_value
- `confidence_bounds`: Copy of input statistical_bounds

**Size Estimate**: 50-200 bytes uncompressed, 10-40 bytes compressed

## 5. Output File Structures

### 5.1 Log Batch File

**Format**: JSON Lines (.jsonl file extension)  
**Organization**: One log record per line, newline-delimited

**File Naming Convention**:
```
{module_id}_{log_type}_{timestamp_start}_{timestamp_end}.jsonl
```

**Example**:
```
mod_01_STATE_00000000_00000999.jsonl
mod_02_EVENT_00001000_00001999.jsonl
core_CYCLE_00000000_00000999.jsonl
```

**Batch Boundaries**:
- Default: 1000 time-steps per batch file
- Configurable per deployment
- Batch files closed and rotated at boundary time-steps

**Compression**:
- Optional gzip compression: `.jsonl.gz` extension
- Applied after batch file closed (no further appends)

### 5.2 Index Manifest

**Format**: JSON object  
**Purpose**: Catalog of available log batch files with metadata

**Schema**:
```
{
  manifest_version: string,              // Manifest schema version
  simulation_id: string,                 // Unique identifier for simulation run
  creation_time: string,                 // ISO 8601 timestamp of manifest creation
  batches: array of {
    file_path: string,                   // Relative path to batch file
    module_id: string,                   // Module producing these logs
    log_type: string,                    // Log category
    timestamp_start: integer,            // First time-step in batch
    timestamp_end: integer,              // Last time-step in batch
    record_count: integer,               // Number of log entries in batch
    file_size_bytes: integer,            // File size on disk
    checksum: string,                    // SHA-256 hash of file contents
    compression: string,                 // "gzip", "none", etc.
    status: string                       // "active", "closed", "archived"
  }
}
```

**Update Frequency**: Manifest updated when:
- New batch file created
- Batch file rotated and closed
- Batch file compressed or archived

### 5.3 Export Package

**Format**: Directory or compressed archive (.zip or .tar.gz)  
**Purpose**: Filtered subset of logs for downstream analysis

**Contents**:
- Subset of log batch files matching export query
- Export-specific index manifest
- Provenance metadata file

**Provenance Metadata Schema**:
```
{
  export_id: string,                     // Unique identifier for this export
  export_time: string,                   // ISO 8601 timestamp of export creation
  source_simulation_id: string,          // Simulation run identifier
  filter_criteria: {
    timestamp_range: {
      start: integer,                    // Inclusive start time-step
      end: integer                       // Inclusive end time-step
    },
    module_ids: array of string,         // Modules included (empty = all)
    log_types: array of string           // Log types included (empty = all)
  },
  record_count: integer,                 // Total records in export
  file_count: integer,                   // Number of batch files included
  total_size_bytes: integer              // Total size of export
}
```

## 6. Timing Contracts

### 6.1 Input Timing Constraints

**State Update Objects**:
- Must be submitted during or at end of time-step specified by timestamp field
- Submission after time-step completion results in rejection

**Event Records**:
- Must be submitted during time-step specified by timestamp field
- May be submitted anytime within time-step execution window
- Multiple events may arrive in arbitrary order within single time-step

**Metric Reports**:
- Must be submitted after timestamp_end has completed
- May be submitted up to 10 time-steps after window closes (configurable grace period)
- Late submission results in warning but data accepted

**Cycle Synchronization Signals**:
- Sent by TQP Core immediately after all modules complete updates
- Guaranteed to arrive before next cycle begins

### 6.2 Output Timing Guarantees

**Log Record Writing**:
- State and Metric logs written within 1 second of submission (batch mode)
- Event logs written immediately (streaming mode)
- Cycle logs written immediately after receiving synchronization signal

**Batch File Rotation**:
- Occurs within 1 time-step of batch boundary crossing
- No logs for time-steps beyond boundary written to old batch file

**Manifest Updates**:
- Index manifest updated within 10 seconds of batch file rotation
- Guaranteed consistent view after update completes

**Export Generation**:
- Export package available within 1 minute for queries under 100,000 records
- Larger exports scale linearly: ~100,000 records per minute

## 7. Data Validity Rules

### 7.1 Input Validation

On receiving input data structures, Logging System validates:

1. **Schema Conformance**: All required fields present with correct types
2. **Timestamp Validity**: Timestamp values non-negative and within acceptable range
3. **Module Registration**: Module ID corresponds to registered module
4. **Enumeration Conformance**: Enumerated fields match allowed value sets
5. **Referential Integrity**: Referenced IDs (event_id, entity_id) exist in system

**Validation Failure Response**:
- Input rejected (not logged)
- Error message returned to submitting module
- Error logged to system error stream
- Simulation continues unless error rate exceeds threshold

### 7.2 Output Validation

Before writing log records, Logging System validates:

1. **Required Field Completeness**: All required fields for log_type present
2. **Timestamp Monotonicity**: Timestamps within batch file non-decreasing
3. **Serialization Validity**: Data structure serializable to target format
4. **Size Constraints**: Serialized record does not exceed maximum size (default: 1 MB)

**Validation Failure Response**:
- Log record quarantined
- Error logged to system error stream
- Warning issued to system operator
- Simulation continues

### 7.3 File Integrity Validation

On batch file rotation, Logging System validates:

1. **Format Validity**: File parseable as JSON Lines
2. **Record Count Match**: Number of records matches expected count
3. **Checksum Computation**: SHA-256 hash computed and stored in manifest
4. **Timestamp Coverage**: First and last timestamps match batch boundary expectations

**Validation Failure Response**:
- File marked as corrupt in manifest
- File quarantined to separate directory
- Alert issued to system operator
- Investigation required before subsequent analysis

## 8. Error Conditions and Handling

### 8.1 Input Error Conditions

| Error Condition | Detection Method | Response |
|----------------|------------------|----------|
| Missing required field | Schema validation | Reject input, return error |
| Invalid data type | Type checking | Reject input, return error |
| Unknown module ID | Registry lookup | Reject input, return error |
| Timestamp out of range | Range checking | Reject input, return error |
| Malformed data structure | Parser exception | Reject input, log exception |

### 8.2 Output Error Conditions

| Error Condition | Detection Method | Response |
|----------------|------------------|----------|
| Disk write failure | I/O exception | Retry with backoff, buffer in memory |
| Disk full | I/O exception | Alert operator, suspend logging |
| Serialization failure | Encoder exception | Quarantine record, log error |
| File corruption | Checksum mismatch | Quarantine file, alert operator |

### 8.3 Error Propagation

- Input errors returned synchronously to calling module
- Output errors logged asynchronously (do not block module execution)
- Critical errors (disk full, corruption) propagate to TQP Core for possible simulation halt

## 9. Performance Contracts

### 9.1 Throughput Requirements

The Logging System must sustain:

- **State Logs**: 1,000 submissions per second
- **Event Logs**: 10,000 submissions per second
- **Metric Logs**: 100 submissions per second
- **Cycle Logs**: 100 submissions per second

Total aggregate: 100,000 log operations per second

### 9.2 Latency Requirements

- **Input Validation**: < 1 ms per submission
- **Serialization**: < 10 ms per record
- **Disk Write** (batch mode): < 100 ms per flush
- **Disk Write** (streaming mode): < 10 ms per record

### 9.3 Storage Requirements

For 1 million time-steps with 100 modules:

- **Uncompressed**: ~10 GB
- **Compressed**: ~2 GB
- **Index Overhead**: < 1% of total size

Scales linearly with time-step count and module count.

## 10. Extension Points

### 10.1 Custom Input Fields

Modules may include extension fields in input data structures:

- Field names must use prefix `ext_{module_id}_`
- Extension fields are optional and not validated by core system
- Extension fields pass through to output log records unchanged

### 10.2 Custom Log Types

Future versions may introduce new log_type values:

- New types registered via logging system configuration
- Existing consumers ignore unknown log types (forward compatibility)
- New consumers query manifest for available log types

### 10.3 Custom Serialization Formats

Alternative output formats may be supported:

- Implement serialization/deserialization interface
- Register format with format identifier string
- Configure per log type or globally
- All formats must preserve field semantics exactly

## 11. Versioning

### 11.1 Input Schema Versioning

Input data structures are not explicitly versioned. Changes to input schemas require:

- Coordinated updates to modules and logging system
- Backward compatibility maintained via optional fields
- Breaking changes require major version increment of entire system

### 11.2 Output Schema Versioning

Output log records include `log_version` field:

- Format: Semantic versioning (MAJOR.MINOR.PATCH)
- MAJOR increment: Breaking changes to required fields or field semantics
- MINOR increment: Addition of new optional fields
- PATCH increment: Documentation clarifications, no schema change

### 11.3 File Format Versioning

Batch files and manifests include format version identifiers:

- Enable gradual migration to new formats
- Readers must check version before parsing
- Version-specific parsers maintained for each supported version

## 12. Summary

This data contract specifies the precise structures exchanged between the Logging System and its environment. Modules provide State Update Objects, Event Records, and Metric Reports according to defined schemas. The Logging System produces Log Records organized in batch files, indexed by manifests, and packaged for export. Timing, validity, and performance contracts ensure reliable and deterministic operation supporting scientific reproducibility.
