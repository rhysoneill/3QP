"""
Data types for the logging system.

Defines all structured log entry types and validation schemas.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from datetime import datetime


LOG_VERSION = "1.0.0"


class LogType(Enum):
    """Log category enumeration."""
    STATE = "STATE"
    EVENT = "EVENT"
    CYCLE = "CYCLE"
    METRIC = "METRIC"


class CycleStatus(Enum):
    """Cycle completion status."""
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


@dataclass
class StateLogEntry:
    """
    State snapshot log entry.
    
    Captures point-in-time snapshot of module internal state variables.
    """
    log_type: str = "STATE"
    timestamp: int = 0
    wall_time: str = ""
    module_id: str = ""
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    log_version: str = LOG_VERSION
    
    # Optional fields
    snapshot_id: Optional[str] = None
    delta_encoding: Optional[bool] = None
    compression_method: Optional[str] = None
    
    def validate(self) -> List[str]:
        """Validate required fields and constraints."""
        errors = []
        
        if not self.module_id:
            errors.append("module_id is required")
        if self.timestamp < 0:
            errors.append(f"timestamp must be non-negative, got {self.timestamp}")
        if not self.wall_time:
            errors.append("wall_time is required")
        if not isinstance(self.state_snapshot, dict):
            errors.append("state_snapshot must be a dictionary")
            
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "log_type": self.log_type,
            "timestamp": self.timestamp,
            "wall_time": self.wall_time,
            "module_id": self.module_id,
            "state_snapshot": self.state_snapshot,
            "log_version": self.log_version,
        }
        
        if self.snapshot_id is not None:
            result["snapshot_id"] = self.snapshot_id
        if self.delta_encoding is not None:
            result["delta_encoding"] = self.delta_encoding
        if self.compression_method is not None:
            result["compression_method"] = self.compression_method
            
        return result


@dataclass
class EventLogEntry:
    """
    Discrete event log entry.
    
    Records discrete occurrences, transitions, and threshold crossings.
    """
    log_type: str = "EVENT"
    timestamp: int = 0
    wall_time: str = ""
    module_id: str = ""
    event_category: str = ""
    event_data: Dict[str, Any] = field(default_factory=dict)
    log_version: str = LOG_VERSION
    
    # Optional fields
    event_id: Optional[str] = None
    causality_chain: Optional[List[str]] = None
    severity_level: Optional[str] = None
    related_entity_ids: Optional[List[str]] = None
    
    def validate(self) -> List[str]:
        """Validate required fields and constraints."""
        errors = []
        
        if not self.module_id:
            errors.append("module_id is required")
        if self.timestamp < 0:
            errors.append(f"timestamp must be non-negative, got {self.timestamp}")
        if not self.wall_time:
            errors.append("wall_time is required")
        if not self.event_category:
            errors.append("event_category is required")
        if not isinstance(self.event_data, dict):
            errors.append("event_data must be a dictionary")
            
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "log_type": self.log_type,
            "timestamp": self.timestamp,
            "wall_time": self.wall_time,
            "module_id": self.module_id,
            "event_category": self.event_category,
            "event_data": self.event_data,
            "log_version": self.log_version,
        }
        
        if self.event_id is not None:
            result["event_id"] = self.event_id
        if self.causality_chain is not None:
            result["causality_chain"] = self.causality_chain
        if self.severity_level is not None:
            result["severity_level"] = self.severity_level
        if self.related_entity_ids is not None:
            result["related_entity_ids"] = self.related_entity_ids
            
        return result


@dataclass
class CycleLogEntry:
    """
    TQP Core execution cycle log entry.
    
    Documents execution metadata for each simulation cycle.
    """
    log_type: str = "CYCLE"
    timestamp: int = 0
    wall_time: str = ""
    cycle_duration_ms: float = 0.0
    modules_executed: List[str] = field(default_factory=list)
    cycle_status: str = "COMPLETE"
    log_version: str = LOG_VERSION
    
    # Optional fields
    module_timings: Optional[Dict[str, float]] = None
    memory_usage_mb: Optional[float] = None
    error_records: Optional[List[Dict[str, Any]]] = None
    
    def validate(self) -> List[str]:
        """Validate required fields and constraints."""
        errors = []
        
        if self.timestamp < 0:
            errors.append(f"timestamp must be non-negative, got {self.timestamp}")
        if not self.wall_time:
            errors.append("wall_time is required")
        if self.cycle_duration_ms < 0:
            errors.append(f"cycle_duration_ms must be non-negative, got {self.cycle_duration_ms}")
        if not isinstance(self.modules_executed, list):
            errors.append("modules_executed must be a list")
        if self.cycle_status not in ["COMPLETE", "PARTIAL", "ERROR"]:
            errors.append(f"cycle_status must be COMPLETE, PARTIAL, or ERROR, got {self.cycle_status}")
            
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "log_type": self.log_type,
            "timestamp": self.timestamp,
            "wall_time": self.wall_time,
            "cycle_duration_ms": self.cycle_duration_ms,
            "modules_executed": self.modules_executed,
            "cycle_status": self.cycle_status,
            "log_version": self.log_version,
        }
        
        if self.module_timings is not None:
            result["module_timings"] = self.module_timings
        if self.memory_usage_mb is not None:
            result["memory_usage_mb"] = self.memory_usage_mb
        if self.error_records is not None:
            result["error_records"] = self.error_records
            
        return result


@dataclass
class MetricLogEntry:
    """
    Aggregate metric log entry.
    
    Captures numerical measurements and statistical summaries.
    """
    log_type: str = "METRIC"
    timestamp_start: int = 0
    timestamp_end: int = 0
    wall_time: str = ""
    module_id: str = ""
    metric_name: str = ""
    metric_value: Union[float, int] = 0
    log_version: str = LOG_VERSION
    
    # Optional fields
    metric_unit: Optional[str] = None
    aggregation_method: Optional[str] = None
    sample_count: Optional[int] = None
    confidence_bounds: Optional[Dict[str, Any]] = None
    
    def validate(self) -> List[str]:
        """Validate required fields and constraints."""
        errors = []
        
        if not self.module_id:
            errors.append("module_id is required")
        if self.timestamp_start < 0:
            errors.append(f"timestamp_start must be non-negative, got {self.timestamp_start}")
        if self.timestamp_end < 0:
            errors.append(f"timestamp_end must be non-negative, got {self.timestamp_end}")
        if self.timestamp_start > self.timestamp_end:
            errors.append(f"timestamp_start must be <= timestamp_end")
        if not self.wall_time:
            errors.append("wall_time is required")
        if not self.metric_name:
            errors.append("metric_name is required")
        if not isinstance(self.metric_value, (int, float)):
            errors.append("metric_value must be numeric")
            
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "log_type": self.log_type,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "wall_time": self.wall_time,
            "module_id": self.module_id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "log_version": self.log_version,
        }
        
        if self.metric_unit is not None:
            result["metric_unit"] = self.metric_unit
        if self.aggregation_method is not None:
            result["aggregation_method"] = self.aggregation_method
        if self.sample_count is not None:
            result["sample_count"] = self.sample_count
        if self.confidence_bounds is not None:
            result["confidence_bounds"] = self.confidence_bounds
            
        return result


# Union type for all log entries
LogEntry = Union[StateLogEntry, EventLogEntry, CycleLogEntry, MetricLogEntry]


@dataclass
class ModuleRegistrationInfo:
    """Information about a registered module for logging."""
    module_id: str
    module_version: str
    log_types: List[str]  # Which log types this module produces
    event_categories: List[str] = field(default_factory=list)  # Registered event types
    metric_names: List[str] = field(default_factory=list)  # Registered metrics
    schema_extensions: Dict[str, Any] = field(default_factory=dict)  # Extension field schemas


@dataclass
class BatchMetadata:
    """Metadata for a log batch file."""
    file_path: str
    module_id: str
    log_type: str
    timestamp_start: int
    timestamp_end: int
    record_count: int
    file_size_bytes: int
    checksum: str
    compression: str
    status: str  # "active", "closed", "archived"
