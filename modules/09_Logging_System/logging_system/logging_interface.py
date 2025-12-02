"""
Main logging interface and system implementation.

Provides the central logging system that modules interact with to submit
logs and the interface handles modules receive for logging operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import threading
from queue import Queue, Empty
import time

from .config import LoggingConfig
from .types import (
    StateLogEntry,
    EventLogEntry,
    CycleLogEntry,
    MetricLogEntry,
    LogEntry,
    ModuleRegistrationInfo,
    LogType,
)
from .serializer import Serializer
from .batch_manager import BatchManager
from .manifest import IndexManifest


class LoggingInterface:
    """
    Interface provided to modules for logging operations.
    
    Modules receive an instance of this interface and use it to submit
    logs without direct access to the logging system internals.
    """
    
    def __init__(self, module_id: str, logging_system: 'LoggingSystem'):
        """
        Initialize logging interface.
        
        Args:
            module_id: ID of the module this interface is for
            logging_system: Parent logging system
        """
        self.module_id = module_id
        self._system = logging_system
    
    def log_state(
        self,
        timestamp: int,
        state_dict: Dict[str, Any],
        snapshot_id: Optional[str] = None
    ) -> bool:
        """
        Submit a state snapshot log.
        
        Args:
            timestamp: Current simulation time-step
            state_dict: Dictionary of state variable name-value pairs
            snapshot_id: Optional unique identifier for snapshot
            
        Returns:
            True if log accepted, False if rejected
        """
        entry = StateLogEntry(
            timestamp=timestamp,
            wall_time=datetime.utcnow().isoformat() + "Z",
            module_id=self.module_id,
            state_snapshot=state_dict,
            snapshot_id=snapshot_id
        )
        
        return self._system._submit_log(entry)
    
    def log_event(
        self,
        timestamp: int,
        event_category: str,
        event_data: Dict[str, Any],
        event_id: Optional[str] = None,
        caused_by_events: Optional[List[str]] = None,
        affected_entities: Optional[List[str]] = None
    ) -> bool:
        """
        Submit an event log.
        
        Args:
            timestamp: Current simulation time-step
            event_category: Event type identifier
            event_data: Event-specific attributes
            event_id: Optional unique identifier
            caused_by_events: Optional list of causal event IDs
            affected_entities: Optional list of entity IDs
            
        Returns:
            True if log accepted, False if rejected
        """
        entry = EventLogEntry(
            timestamp=timestamp,
            wall_time=datetime.utcnow().isoformat() + "Z",
            module_id=self.module_id,
            event_category=event_category,
            event_data=event_data,
            event_id=event_id,
            causality_chain=caused_by_events,
            related_entity_ids=affected_entities
        )
        
        return self._system._submit_log(entry)
    
    def log_metric(
        self,
        timestamp_start: int,
        timestamp_end: int,
        metric_name: str,
        metric_value: float,
        metric_unit: Optional[str] = None,
        aggregation_method: Optional[str] = None,
        sample_count: Optional[int] = None
    ) -> bool:
        """
        Submit a metric log.
        
        Args:
            timestamp_start: Start of aggregation window
            timestamp_end: End of aggregation window
            metric_name: Metric identifier
            metric_value: Computed metric value
            metric_unit: Optional unit of measurement
            aggregation_method: Optional aggregation method
            sample_count: Optional number of samples
            
        Returns:
            True if log accepted, False if rejected
        """
        entry = MetricLogEntry(
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
            wall_time=datetime.utcnow().isoformat() + "Z",
            module_id=self.module_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            aggregation_method=aggregation_method,
            sample_count=sample_count
        )
        
        return self._system._submit_log(entry)


class LoggingSystem:
    """
    Central logging system for the 3QP simulation.
    
    Manages registration of modules, receipt of log submissions,
    validation, serialization, and storage in batch files.
    """
    
    def __init__(self, config: Optional[LoggingConfig] = None):
        """
        Initialize logging system.
        
        Args:
            config: Logging configuration (uses defaults if None)
        """
        self.config = config or LoggingConfig()
        
        # Create serializer
        compression = self.config.compression_format if self.config.enable_compression else "none"
        self.serializer = Serializer(compression="none")  # Compress only on close
        
        # Create batch manager
        self.batch_manager = BatchManager(self.config, self.serializer)
        
        # Create index manifest
        manifest_path = self.config.output_directory / "manifest.json"
        self.manifest = IndexManifest(manifest_path)
        
        # Module registry
        self.registered_modules: Dict[str, ModuleRegistrationInfo] = {}
        
        # Error tracking
        self.error_count = 0
        self.error_log: List[str] = []
        
        # Submission queue for async mode
        self.log_queue: Optional[Queue] = None
        self.worker_thread: Optional[threading.Thread] = None
        self.shutdown_flag = threading.Event()
        
        # Current timestamp tracking
        self.current_timestamp = 0
        
        # State log decimation counter
        self.state_log_counter: Dict[str, int] = {}
    
    def initialize(self, simulation_id: str) -> None:
        """
        Initialize logging system for a simulation run.
        
        Args:
            simulation_id: Unique identifier for this simulation
        """
        # Initialize manifest
        self.manifest.initialize(simulation_id)
        
        # Create output directory
        self.config.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Start async worker if not in streaming mode
        if not self.config.streaming_mode:
            self.log_queue = Queue(maxsize=self.config.buffer_size * 10)
            self.worker_thread = threading.Thread(
                target=self._worker_loop,
                daemon=True
            )
            self.worker_thread.start()
    
    def register_module(
        self,
        module_id: str,
        module_version: str,
        log_types: List[str],
        event_categories: Optional[List[str]] = None,
        metric_names: Optional[List[str]] = None
    ) -> LoggingInterface:
        """
        Register a module with the logging system.
        
        Args:
            module_id: Unique module identifier
            module_version: Module version string
            log_types: List of log types this module produces
            event_categories: Optional list of event categories
            metric_names: Optional list of metric names
            
        Returns:
            LoggingInterface for the module to use
        """
        registration = ModuleRegistrationInfo(
            module_id=module_id,
            module_version=module_version,
            log_types=log_types,
            event_categories=event_categories or [],
            metric_names=metric_names or []
        )
        
        self.registered_modules[module_id] = registration
        self.state_log_counter[module_id] = 0
        
        return LoggingInterface(module_id, self)
    
    def log_cycle(
        self,
        timestamp: int,
        cycle_start_time: datetime,
        cycle_end_time: datetime,
        modules_executed: List[str],
        cycle_status: str = "COMPLETE",
        module_timings: Optional[Dict[str, float]] = None,
        error_records: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Log a TQP Core cycle completion.
        
        Args:
            timestamp: Completed time-step
            cycle_start_time: Cycle start wall-clock time
            cycle_end_time: Cycle end wall-clock time
            modules_executed: List of module IDs executed
            cycle_status: Completion status
            module_timings: Optional execution times per module
            error_records: Optional error records
            
        Returns:
            True if log accepted
        """
        duration_ms = (cycle_end_time - cycle_start_time).total_seconds() * 1000
        
        entry = CycleLogEntry(
            timestamp=timestamp,
            wall_time=datetime.utcnow().isoformat() + "Z",
            cycle_duration_ms=duration_ms,
            modules_executed=modules_executed,
            cycle_status=cycle_status,
            module_timings=module_timings,
            error_records=error_records
        )
        
        self.current_timestamp = timestamp
        return self._submit_log(entry)
    
    def _submit_log(self, entry: LogEntry) -> bool:
        """
        Internal method to submit a log entry.
        
        Args:
            entry: Log entry to submit
            
        Returns:
            True if accepted, False if rejected
        """
        # Check if logging is enabled for this type
        if isinstance(entry, StateLogEntry) and not self.config.enable_state_logs:
            return False
        if isinstance(entry, EventLogEntry) and not self.config.enable_event_logs:
            return False
        if isinstance(entry, CycleLogEntry) and not self.config.enable_cycle_logs:
            return False
        if isinstance(entry, MetricLogEntry) and not self.config.enable_metric_logs:
            return False
        
        # Apply state log decimation
        if isinstance(entry, StateLogEntry):
            self.state_log_counter[entry.module_id] += 1
            if self.state_log_counter[entry.module_id] % self.config.state_log_decimation != 0:
                return True  # Skip this one, but report success
        
        # Validate if enabled
        if self.config.enable_validation:
            errors = entry.validate()
            if errors:
                self._log_error(f"Validation failed for {entry.log_type}: {errors}")
                return False
        
        # Submit to queue or write directly
        if self.config.streaming_mode:
            return self._write_log(entry)
        else:
            if self.log_queue is not None:
                try:
                    self.log_queue.put(entry, block=False)
                    return True
                except:
                    self._log_error("Log queue full, entry dropped")
                    return False
            return False
    
    def _write_log(self, entry: LogEntry) -> bool:
        """
        Write log entry to batch file.
        
        Args:
            entry: Log entry to write
            
        Returns:
            True if written successfully
        """
        try:
            # Determine log type and timestamp
            if isinstance(entry, MetricLogEntry):
                timestamp = entry.timestamp_end
            else:
                timestamp = entry.timestamp
            
            log_type = entry.log_type
            
            # Get module ID
            if isinstance(entry, CycleLogEntry):
                module_id = "core"
            else:
                module_id = entry.module_id
            
            # Get appropriate batch file
            batch = self.batch_manager.get_batch(module_id, log_type, timestamp)
            
            # Write entry
            return batch.write_entry(entry)
            
        except Exception as e:
            self._log_error(f"Failed to write log: {e}")
            return False
    
    def _worker_loop(self) -> None:
        """Background worker thread for async log writing."""
        buffer: List[LogEntry] = []
        last_flush = time.time()
        
        while not self.shutdown_flag.is_set():
            try:
                # Try to get entries from queue
                try:
                    entry = self.log_queue.get(timeout=0.1)
                    buffer.append(entry)
                except Empty:
                    pass
                
                # Check if we should flush
                current_time = time.time()
                time_since_flush = (current_time - last_flush) * 1000
                
                should_flush = (
                    len(buffer) >= self.config.buffer_size or
                    time_since_flush >= self.config.buffer_flush_interval_ms
                )
                
                if should_flush and buffer:
                    # Write buffered entries
                    for entry in buffer:
                        self._write_log(entry)
                    
                    buffer.clear()
                    last_flush = current_time
                    
            except Exception as e:
                self._log_error(f"Worker thread error: {e}")
        
        # Final flush on shutdown
        for entry in buffer:
            self._write_log(entry)
    
    def _log_error(self, message: str) -> None:
        """Log an internal error."""
        self.error_count += 1
        self.error_log.append(f"[{datetime.utcnow().isoformat()}] {message}")
        
        # Print to stderr
        import sys
        print(f"LOGGING ERROR: {message}", file=sys.stderr)
    
    def finalize(self) -> None:
        """
        Finalize logging system.
        
        Closes all batch files, updates manifest, and shuts down worker thread.
        """
        # Signal shutdown
        self.shutdown_flag.set()
        
        # Wait for worker thread
        if self.worker_thread is not None:
            self.worker_thread.join(timeout=5.0)
        
        # Close all batches
        self.batch_manager.close_all()
        
        # Update manifest with completed batches
        completed = self.batch_manager.get_completed_batches()
        self.manifest.add_batches(completed)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get logging statistics.
        
        Returns:
            Dictionary with statistics
        """
        manifest_stats = self.manifest.get_statistics()
        
        return {
            **manifest_stats,
            "registered_modules": len(self.registered_modules),
            "error_count": self.error_count,
            "active_batches": len(self.batch_manager.active_batches)
        }
