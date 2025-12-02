"""
Configuration for the logging system.
"""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class LoggingConfig:
    """
    Configuration for the logging system.
    
    Attributes:
        output_directory: Root directory for log files
        batch_size: Number of time-steps per batch file (default: 1000)
        enable_compression: Whether to compress closed batch files
        compression_format: Compression method ("gzip", "none")
        streaming_mode: If True, write immediately; if False, buffer in memory
        buffer_size: Number of entries to buffer before flush (batch mode only)
        buffer_flush_interval_ms: Max time between flushes in milliseconds
        enable_state_logs: Enable STATE log type
        enable_event_logs: Enable EVENT log type
        enable_cycle_logs: Enable CYCLE log type
        enable_metric_logs: Enable METRIC log type
        state_log_decimation: Log state every Nth time-step (1 = every step)
        max_record_size_bytes: Maximum size of a single log record
        enable_validation: Validate log entries before writing
    """
    
    output_directory: Path = field(default_factory=lambda: Path("./logs"))
    batch_size: int = 1000
    enable_compression: bool = True
    compression_format: str = "gzip"
    streaming_mode: bool = False  # False = batch mode
    buffer_size: int = 100
    buffer_flush_interval_ms: int = 1000
    
    enable_state_logs: bool = True
    enable_event_logs: bool = True
    enable_cycle_logs: bool = True
    enable_metric_logs: bool = True
    
    state_log_decimation: int = 1  # Log every N time-steps
    
    max_record_size_bytes: int = 1024 * 1024  # 1 MB
    enable_validation: bool = True
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {self.batch_size}")
        if self.buffer_size < 1:
            raise ValueError(f"buffer_size must be >= 1, got {self.buffer_size}")
        if self.buffer_flush_interval_ms < 0:
            raise ValueError(f"buffer_flush_interval_ms must be non-negative")
        if self.state_log_decimation < 1:
            raise ValueError(f"state_log_decimation must be >= 1")
        if self.compression_format not in ["gzip", "none"]:
            raise ValueError(f"compression_format must be 'gzip' or 'none'")
        if self.max_record_size_bytes < 1024:
            raise ValueError(f"max_record_size_bytes must be >= 1024")
        
        # Ensure output directory is a Path object
        if not isinstance(self.output_directory, Path):
            self.output_directory = Path(self.output_directory)
