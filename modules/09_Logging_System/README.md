# Module 09: Logging System

## Overview

The Logging System provides unified, structured logging infrastructure for the 3QP simulation. It captures state snapshots, discrete events, cycle metadata, and aggregate metrics in a deterministic, reproducible format suitable for scientific analysis.

## Key Features

- **Structured Logging**: All logs are structured data with typed fields and schemas
- **Deterministic Output**: Identical simulations produce byte-identical logs (excluding wall-clock time)
- **Four Log Types**: STATE, EVENT, CYCLE, and METRIC logs
- **Batch Organization**: Logs organized in time-step-aligned batch files
- **Index Manifest**: Metadata catalog for efficient querying
- **JSON Lines Format**: Newline-delimited JSON for streaming and compatibility
- **Optional Compression**: gzip compression for closed batch files
- **Validation**: Schema validation ensures data integrity
- **Semantic Neutrality**: Captures raw data without interpretation

## Architecture

### Components

1. **LoggingSystem**: Central coordinator managing all logging operations
2. **LoggingInterface**: Module-specific interface for submitting logs
3. **Serializer**: JSON Lines serialization with deterministic ordering
4. **BatchManager**: Manages batch file creation, rotation, and closure
5. **IndexManifest**: Catalogs batch files with metadata
6. **Log Types**: Structured data classes for each log category

### Directory Structure

```
logs/
  simulation_{id}/
    STATE/
      {module}_{type}_{start}_{end}.jsonl[.gz]
    EVENT/
      {module}_{type}_{start}_{end}.jsonl[.gz]
    CYCLE/
      core_{type}_{start}_{end}.jsonl[.gz]
    METRIC/
      {module}_{type}_{start}_{end}.jsonl[.gz]
    manifest.json
```

## Usage

### Initialize Logging System

```python
from logging_system import LoggingSystem, LoggingConfig
from pathlib import Path

config = LoggingConfig(
    output_directory=Path("./logs"),
    batch_size=1000,
    enable_compression=True,
    streaming_mode=False
)

logging_system = LoggingSystem(config)
logging_system.initialize(simulation_id="sim_001")
```

### Register Module

```python
logger = logging_system.register_module(
    module_id="physiology",
    module_version="1.0.0",
    log_types=["STATE", "EVENT", "METRIC"],
    event_categories=["arousal_spike", "fatigue_threshold"],
    metric_names=["avg_cortisol", "sleep_quality"]
)
```

### Log State Snapshot

```python
logger.log_state(
    timestamp=current_timestep,
    state_dict={
        "cortisol_level": 0.65,
        "heart_rate": 75,
        "fatigue": 0.4
    }
)
```

### Log Event

```python
logger.log_event(
    timestamp=current_timestep,
    event_category="arousal_spike",
    event_data={
        "magnitude": 0.8,
        "trigger": "external_stressor"
    },
    event_id="evt_phys_123"
)
```

### Log Metric

```python
logger.log_metric(
    timestamp_start=0,
    timestamp_end=99,
    metric_name="avg_cortisol",
    metric_value=0.58,
    metric_unit="normalized",
    aggregation_method="MEAN",
    sample_count=100
)
```

### Log Cycle (TQP Core only)

```python
logging_system.log_cycle(
    timestamp=current_timestep,
    cycle_start_time=cycle_start,
    cycle_end_time=cycle_end,
    modules_executed=["physiology", "social_network"],
    cycle_status="COMPLETE"
)
```

### Finalize

```python
logging_system.finalize()  # Close all batches, update manifest
```

## Configuration Options

- `output_directory`: Root directory for log files
- `batch_size`: Time-steps per batch file (default: 1000)
- `enable_compression`: Compress closed batches (default: True)
- `compression_format`: "gzip" or "none" (default: "gzip")
- `streaming_mode`: Write immediately vs. buffer (default: False)
- `buffer_size`: Entries to buffer before flush (default: 100)
- `buffer_flush_interval_ms`: Max time between flushes (default: 1000)
- `state_log_decimation`: Log state every N steps (default: 1)
- `enable_validation`: Validate entries before writing (default: True)

## Log Schemas

### STATE Log

```json
{
  "log_type": "STATE",
  "timestamp": 42,
  "wall_time": "2025-01-01T12:00:00.000Z",
  "module_id": "physiology",
  "state_snapshot": {"cortisol": 0.65, "hr": 75},
  "log_version": "1.0.0"
}
```

### EVENT Log

```json
{
  "log_type": "EVENT",
  "timestamp": 42,
  "wall_time": "2025-01-01T12:00:00.000Z",
  "module_id": "physiology",
  "event_category": "arousal_spike",
  "event_data": {"magnitude": 0.8},
  "log_version": "1.0.0"
}
```

### CYCLE Log

```json
{
  "log_type": "CYCLE",
  "timestamp": 42,
  "wall_time": "2025-01-01T12:00:00.000Z",
  "cycle_duration_ms": 12.5,
  "modules_executed": ["physiology", "social_network"],
  "cycle_status": "COMPLETE",
  "log_version": "1.0.0"
}
```

### METRIC Log

```json
{
  "log_type": "METRIC",
  "timestamp_start": 0,
  "timestamp_end": 99,
  "wall_time": "2025-01-01T12:00:00.000Z",
  "module_id": "physiology",
  "metric_name": "avg_cortisol",
  "metric_value": 0.58,
  "log_version": "1.0.0"
}
```

## Testing

Run the test suite:

```bash
python -m unittest tests.test_logging_system
```

## Demo

Run the demonstration:

```bash
python demo.py
```

This generates sample logs showing all log types and inspects the resulting file structure.

## Integration with TQP Core

The Logging System integrates with TQP Core through:

1. **Time Synchronization**: Uses TQP Core time-steps as primary timestamps
2. **Cycle Coordination**: Receives cycle start/end signals from TQP Core
3. **Module Interface**: Provides LoggingInterface to registered modules
4. **Deterministic Ordering**: Respects module execution order from TQP Core

## Dependencies

- Python 3.9+
- Standard library only (no external dependencies)

## Performance Characteristics

- **Write Throughput**: 100,000+ entries/second (buffered mode)
- **Latency**: <1ms validation, <10ms serialization per entry
- **Storage**: ~100-200 bytes/entry compressed
- **Memory**: Configurable buffer size, default 100 entries

## Design Principles

1. **Semantic Neutrality**: No interpretation of logged data
2. **Determinism**: Reproducible logs across identical runs
3. **Completeness**: Capture sufficient detail for analysis
4. **Extensibility**: Support custom fields and new log types
5. **Transparency**: Self-describing structured format
6. **Efficiency**: Optimized I/O with batching and compression

## Future Enhancements

- Distributed logging for parallel simulations
- Real-time log streaming interface
- Query language for log analysis
- Columnar storage format option
- Log replay and visualization tools

## Version

1.0.0 (December 2025)
